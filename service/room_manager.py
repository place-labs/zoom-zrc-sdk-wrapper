"""
Room Manager - Manages multiple Zoom Room connections
"""

import asyncio
import functools
import logging
import sqlite3
import os
import threading
from collections import deque
from contextlib import closing, contextmanager
from time import perf_counter
from typing import Deque, Dict, Optional, Set, Tuple

try:
    import zrc_sdk
except ImportError:
    print("ERROR: zrc_sdk module not found. Run '../build.sh' first.")
    raise

logger = logging.getLogger(__name__)

# ZRCSDKError: the command reached the SDK but the room is unreachable. The SDK's
# GetConnectionState can still report Connected in this "zombie" state, so a
# command returning this is the ground truth that the connection is actually dead.
NOT_CONNECT_TO_ZOOMROOM = 11


# ===== SDK call latency monitor =====

class SDKCallMonitor:
    """Times synchronous SDK calls made on the event-loop thread and flags any
    slow enough to stall the whole service.

    Every SDK method call blocks the single asyncio loop for its duration (the
    SDK is main-thread-affine and the bindings don't release the GIL — see
    ARCHITECTURE.md → Threading model). So a call over `slow_ms` freezes every
    room's REST + WS for that long. This makes that visible in production: it logs a warning per slow call
    and keeps rolling stats readable via /health, turning "does a real SDK call
    block?" from a guess into observed data.

    Threshold defaults to 50 ms, overridable with ZRC_SDK_SLOW_MS. Wrap a call:

        with mgr.sdk_monitor.measure(f"RetryToPairRoom[{room_id}]"):
            result = room_service.RetryToPairRoom()
    """

    _KEEP_SLOWEST = 20

    def __init__(self, slow_ms: Optional[float] = None):
        raw = slow_ms if slow_ms is not None else os.environ.get("ZRC_SDK_SLOW_MS", "50")
        try:
            self.slow_ms = float(raw)
        except (TypeError, ValueError):
            # RoomManager() is built at module import — a raise here crash-loops
            # the container on a malformed env var (PRODUCTION-REVIEW.md 2.5a).
            logger.warning(f"ZRC_SDK_SLOW_MS={raw!r} is not a number — using 50")
            self.slow_ms = 50.0
        self.calls = 0
        self.slow_calls = 0
        self.max_ms = 0.0
        self.slowest = []   # rolling list of the most recent slow calls

    @contextmanager
    def measure(self, label: str):
        start = perf_counter()
        try:
            yield
        finally:
            ms = (perf_counter() - start) * 1000.0
            self.calls += 1
            if ms > self.max_ms:
                self.max_ms = ms
            if ms >= self.slow_ms:
                self.slow_calls += 1
                self.slowest.append({"call": label, "ms": round(ms, 1)})
                del self.slowest[:-self._KEEP_SLOWEST]
                logger.warning(
                    f"SLOW SDK call: {label} took {ms:.0f}ms (>{self.slow_ms:.0f}ms) "
                    f"— blocks the event loop, stalling all rooms for that long"
                )

    def stats(self) -> dict:
        return {
            "calls": self.calls,
            "slow_calls": self.slow_calls,
            "slow_ms_threshold": self.slow_ms,
            "max_ms": round(self.max_ms, 1),
            "slowest": list(self.slowest),
        }


# ===== SDK Sink Implementation =====

class SDKSinkImpl:
    """Simple SDK sink with default values"""

    def OnGetDeviceManufacturer(self) -> str:
        return "ZoomRoomsWrapper"

    def OnGetDeviceModel(self) -> str:
        return "v1.0"

    def OnGetDeviceSerialNumber(self) -> str:
        # Device identity is how Zoom distinguishes controller instances. It MUST be
        # unique per running instance — two instances sharing a serial/MAC collide and
        # pairing fails with DEVICE_NOT_EXIST (100). Override via env for local/dev so
        # it doesn't clash with the deployed pod. Default preserves production identity.
        return os.environ.get("ZRC_DEVICE_SERIAL", "SDK-WRAPPER-001")

    def OnGetDeviceMacAddress(self) -> str:
        return os.environ.get("ZRC_DEVICE_MAC", "00:00:00:00:00:01")

    def OnGetDeviceIP(self) -> str:
        return "127.0.0.1"

    def OnGetFirmwareVersion(self) -> str:
        return "1.0.0"

    def OnGetAppName(self) -> str:
        return "Zoom Rooms Microservice"

    def OnGetAppVersion(self) -> str:
        return "1.0.0"

    def OnGetAppDeveloper(self) -> str:
        return "Custom"

    def OnGetAppContact(self) -> str:
        return "support@example.com"

    def OnGetAppContentDirPath(self) -> str:
        # SDK stores paired room data in this directory
        # CRITICAL: Contains third_zrc_data.db with room credentials and tokens
        # This MUST be persisted across container restarts
        data_dir = os.path.expanduser("~/.zoom/data")
        os.makedirs(data_dir, exist_ok=True)
        return data_dir


# ===== Event broadcasting helpers =====

def _enum_name(value):
    """Return the SDK enum name for a pybind11 enum (falls back to str()).

    Used for all true enums; raw int32_t result/error codes are emitted numerically instead.
    """
    return getattr(value, "name", None) or str(value)


# Per-type field list for real pybind structs (module 'zrc_sdk'): their fields are
# type-level properties, so one dir() per type suffices — dir() is the expensive
# part of serialization and runs on SDK threads holding the GIL
# (PRODUCTION-REVIEW.md 4a). Other objects keep exact per-instance semantics.
_FIELD_NAMES_CACHE: Dict[type, Tuple[str, ...]] = {}


def _pybind_to_jsonable(v, _depth=0):
    """Recursively convert a pybind11 value (struct / enum / primitive) to a JSON-able form.

    Keeps the wrapper a faithful passthrough: every bound field is emitted and field
    curation is left to the consumer (the logic module). Enums become their name;
    nested structs become dicts; primitives pass through unchanged. Fully defensive —
    never raises (bounded depth, per-field guards) so it can't break an SDK callback.
    """
    if _depth > 8:
        return str(v)
    if hasattr(type(v), "__members__"):          # pybind11 enum -> name
        return v.name
    if v is None or isinstance(v, (bool, int, float, str)):
        return v
    if isinstance(v, (list, tuple)):
        return [_pybind_to_jsonable(x, _depth + 1) for x in v]
    # Nested pybind struct: dict of its readable, non-callable fields.
    t = type(v)
    if getattr(t, "__module__", None) == "zrc_sdk":
        names = _FIELD_NAMES_CACHE.get(t)
        if names is None:
            names = tuple(a for a in dir(v) if not a.startswith("_"))
            _FIELD_NAMES_CACHE[t] = names
    else:
        names = tuple(a for a in dir(v) if not a.startswith("_"))
    out = {}
    for attr in names:
        try:
            val = getattr(v, attr)
            if callable(val):
                continue
            out[attr] = _pybind_to_jsonable(val, _depth + 1)
        except Exception:
            continue
    return out or str(v)


def _participant_json(p):
    """Serialize a bound MeetingParticipant to JSON, passing through all fields."""
    return _pybind_to_jsonable(p)


def _hot(fn):
    """Gate a HIGH-FREQUENCY, PURE-EMIT sink callback on having WS listeners.

    emit()'s kwargs are evaluated in the callback's frame before emit() runs, so
    without this the full payload is serialized (recursive reflection, on the SDK
    thread, holding the GIL) and then dropped when nobody is subscribed — the
    REST-only common case (PRODUCTION-REVIEW.md 4a). Only for callbacks with no
    side effects beyond emit. Managers without has_listeners (e.g. the contract
    test's capture manager) always run the callback.
    """
    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        mgr = getattr(self, "mgr", None)
        if mgr is not None:
            has = getattr(mgr, "has_listeners", None)
            if has is not None and not has(self.room_id):
                return
        return fn(self, *args, **kwargs)
    return wrapper


class _Broadcaster:
    """Mixin giving a sink an `emit()` that fans a flat event to WebSocket subscribers.

    `mgr` (the RoomManager) is injected after construction; if unset, emit is a no-op.
    Swallows all exceptions so a broadcast failure can never propagate into the C++ SDK.
    """
    mgr = None

    def emit(self, event, **fields):
        mgr = getattr(self, "mgr", None)
        if mgr is None:
            return
        try:
            mgr.broadcast_event(self.room_id, {"event": event, **fields})
        except Exception as e:
            logger.error(f"[{self.room_id}] broadcast {event} failed: {e}")

    def _set_threadsafe(self, event):
        """Set an asyncio.Event from an SDK callback thread.

        asyncio objects are single-thread; the only safe crossing is the loop's
        call_soon_threadsafe (locks + wakes the selector). A direct set() only
        appears to work because the heartbeat happens to pump the loop — and
        raises outright under PYTHONASYNCIODEBUG=1. Falls back to a direct set
        when no loop is bound (tests, pre-startup)."""
        mgr = getattr(self, "mgr", None)
        loop = getattr(mgr, "_event_loop", None) if mgr is not None else None
        if loop is not None:
            loop.call_soon_threadsafe(event.set)
        else:
            event.set()


# ===== Callback Sinks for Events =====

class ZoomRoomsServiceSink(_Broadcaster):
    """Callback sink for room service events"""

    def __init__(self, room_id: str):
        self.room_id = room_id
        self.pair_result: Optional[int] = None
        self.pair_event = asyncio.Event()

    def OnPairRoomResult(self, result: int):
        """Called when pairing completes (success or failure)"""
        logger.info(f"[{self.room_id}] OnPairRoomResult: {result}")
        self.pair_result = result
        self._set_threadsafe(self.pair_event)
        self.emit("OnPairRoomResult", result=int(result))

    def OnRoomUnpairedReason(self, reason: int):
        """Called when room is unpaired"""
        logger.warning(f"[{self.room_id}] Room unpaired, reason: {reason}")
        self.emit("OnRoomUnpairedReason", reason=_enum_name(reason))
        # An unpaired room can't be recovered by retrying -> stop and don't restart.
        mgr = getattr(self, "mgr", None)
        if mgr is not None:
            mgr.mark_unpaired(self.room_id)


class PreMeetingServiceSink(_Broadcaster):
    """Callback sink for pre-meeting service events"""

    def __init__(self, room_id: str):
        self.room_id = room_id
        self.connection_state = None
        self.connected_event = asyncio.Event()

    def OnZRConnectionStateChanged(self, state):
        """Called when connection state changes"""
        logger.info(f"[{self.room_id}] Connection state changed: {state}")
        self.connection_state = state
        if state == zrc_sdk.ConnectionStateConnected:
            self._set_threadsafe(self.connected_event)
        self.emit("OnZRConnectionStateChanged", state=_enum_name(state))
        # Self-healing: keep a paired room connected without any consumer involvement.
        mgr = getattr(self, "mgr", None)
        if mgr is not None:
            if state == zrc_sdk.ConnectionStateConnected:
                mgr.cancel_reconnect(self.room_id)
            elif state == zrc_sdk.ConnectionStateDisconnected:
                mgr.schedule_reconnect(self.room_id)

    def OnShutdownOSNot(self, restart_os: bool):
        """Called when shutdown notification received"""
        logger.info(f"[{self.room_id}] Shutdown OS notification: restart={restart_os}")
        self.emit("OnShutdownOSNot", restartOS=restart_os)


class MeetingListHelperSink(_Broadcaster):
    """Callback sink for meeting list helper events"""

    def __init__(self, room_id: str):
        self.room_id = room_id
        self._pending_list_futures: Deque[asyncio.Future] = deque()
        self._lock = threading.Lock()

    def create_list_future(self) -> asyncio.Future:
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        with self._lock:
            self._pending_list_futures.append(future)
        return future

    def cancel_list_future(self, future: asyncio.Future) -> None:
        with self._lock:
            try:
                self._pending_list_futures.remove(future)
            except ValueError:
                pass
        if not future.done():
            future.cancel()

    def _pop_next_pending(self) -> Optional[asyncio.Future]:
        with self._lock:
            while self._pending_list_futures:
                future = self._pending_list_futures.popleft()
                if not future.done():
                    return future
        return None

    def OnUpdateMeetingList(self, result: int, meeting_list):
        """Called when meeting list changes or a ListMeeting result arrives"""
        # Broadcast the change to live subscribers regardless of pending requests.
        self.emit("OnUpdateMeetingList", result=_enum_name(result), count=len(meeting_list),
                  meetings=_pybind_to_jsonable(meeting_list))
        # Resolve a pending REST request waiting on the full list, if any.
        future = self._pop_next_pending()
        if not future:
            logger.debug(f"[{self.room_id}] Meeting list update received with no pending request")
            return
        payload: Tuple[int, list] = (int(result), meeting_list)
        future.get_loop().call_soon_threadsafe(future.set_result, payload)

    def OnUpdatedScheduleCalendarEventNotification(self, schedule_result: int):
        logger.debug(f"[{self.room_id}] Schedule calendar event result: {schedule_result}")
        self.emit("OnUpdatedScheduleCalendarEventNotification", result=_enum_name(schedule_result))

    def OnUpdatedDeleteCalendarEventNotification(self, delete_result: int):
        logger.debug(f"[{self.room_id}] Delete calendar event result: {delete_result}")
        self.emit("OnUpdatedDeleteCalendarEventNotification", result=_enum_name(delete_result))

    def OnShowUpcomingMeetingAlertResult(self, result: int, meeting_item):
        logger.debug(f"[{self.room_id}] Show upcoming meeting alert result: {result}")
        self.emit("OnShowUpcomingMeetingAlertResult", result=int(result),
                  meetingItem=_pybind_to_jsonable(meeting_item))

    def OnCloseUpcomingMeetingAlertResult(self, result: int):
        logger.debug(f"[{self.room_id}] Close upcoming meeting alert result: {result}")
        self.emit("OnCloseUpcomingMeetingAlertResult", result=int(result))

    def OnMeetingWillReleaseAutomatically(self, meeting_item):
        logger.debug(f"[{self.room_id}] Meeting will release automatically notification received")
        self.emit("OnMeetingWillReleaseAutomatically", meetingItem=_pybind_to_jsonable(meeting_item))

class MeetingReminderSink(_Broadcaster):
    """Callback sink for reminder notifications"""
    def __init__(self, room_id: str):
        self.room_id = room_id
        self._lock = threading.Lock()

    def OnConsentNotification(self, info):
        logger.debug(f"[{self.room_id}] Consent notification result: {info.type}")
        self.emit("OnConsentNotification", info=_pybind_to_jsonable(info))

    def OnMeetingReminderNotification(self, reminder_content):
        logger.debug(f"[{self.room_id}] meeting reminder result: {reminder_content}")
        self.emit("OnMeetingReminderNotification", reminderContent=_pybind_to_jsonable(reminder_content))

    def OnCustomizedReminderNotification(self, customized_content):
        logger.debug(f"[{self.room_id}] customized reminder result: {customized_content}")
        self.emit("OnCustomizedReminderNotification", customizedContent=_pybind_to_jsonable(customized_content))

    def OnCombinedConsentNotification(self, combined_consent):
        logger.debug(f"[{self.room_id}] combined consent notification result: {combined_consent}")
        self.emit("OnCombinedConsentNotification", combinedConsent=_pybind_to_jsonable(combined_consent))

    def OnPrivacyAlertNotification(self, action, alert_type, message):
        logger.debug(f"[{self.room_id}] privacy alert notificationt: {action}, {alert_type}")
        self.emit("OnPrivacyAlertNotification", action=_enum_name(action), alertType=_enum_name(alert_type),
                  message=_pybind_to_jsonable(message))

    def OnMessageEventNotification(self, message_event):
        logger.debug(f"[{self.room_id}] message event notification result: {message_event}")
        self.emit("OnMessageEventNotification", messageEvent=_enum_name(message_event))

    def OnInactiveDetectionNotification(self, is_show_prompt, auto_end_time):
        logger.debug(f"[{self.room_id}] inactive detection notification result: {auto_end_time}")
        self.emit("OnInactiveDetectionNotification", isShowPrompt=is_show_prompt, autoEndTime=int(auto_end_time))


class MeetingServiceSink(_Broadcaster):
    """Callback sink for meeting service events (status, start/exit, waiting for host)"""

    def __init__(self, room_id: str):
        self.room_id = room_id
        self.meeting_status = None

    def OnStartMeetingResult(self, result: int):
        logger.info(f"[{self.room_id}] Start meeting result: {result}")
        self.emit("OnStartMeetingResult", result=int(result))

    def OnUpdateMeetingStatus(self, meeting_status):
        self.meeting_status = meeting_status
        logger.info(f"[{self.room_id}] Meeting status changed: {meeting_status}")
        self.emit("OnUpdateMeetingStatus", status=_enum_name(meeting_status))

    def OnConfReadyNotification(self):
        logger.info(f"[{self.room_id}] Conference ready")
        self.emit("OnConfReadyNotification")

    def OnUpdateMeetingInfoNotification(self, meeting_info):
        logger.debug(f"[{self.room_id}] Meeting info updated")
        self.emit("OnUpdateMeetingInfoNotification", meetingInfo=_pybind_to_jsonable(meeting_info))

    def OnExitMeetingNotification(self, result: int, reason: int):
        logger.info(f"[{self.room_id}] Exited meeting (result={result}, reason={reason})")
        self.emit("OnExitMeetingNotification", result=int(result), reason=_enum_name(reason))

    def OnStartMeetingWithHostKeyResult(self, result: int):
        logger.info(f"[{self.room_id}] Start meeting with host key result: {result}")
        self.emit("OnStartMeetingWithHostKeyResult", result=int(result))

    def OnJBHWaitingHostNotification(self, show_wait_for_host_dialog: bool, reason: int):
        logger.info(f"[{self.room_id}] Waiting for host: show={show_wait_for_host_dialog}, reason={reason}")
        self.emit("OnJBHWaitingHostNotification", showWaitForHostDialog=show_wait_for_host_dialog, reason=_enum_name(reason))

    def OnMeetingWillStopAutomatically(self):
        logger.info(f"[{self.room_id}] Meeting will stop automatically in 10 minutes")
        self.emit("OnMeetingWillStopAutomatically")

    def OnExtendMeetingResult(self, extend_mins: int):
        logger.info(f"[{self.room_id}] Meeting extended by {extend_mins} minutes")
        self.emit("OnExtendMeetingResult", extendMins=int(extend_mins))


class ParticipantHelperSink(_Broadcaster):
    """Callback sink for participant roster events (join/leave/update, host change)"""

    def __init__(self, room_id: str):
        self.room_id = room_id

    def OnInitMeetingParticipants(self, participants, total_participants_count, need_cleanup, session):
        logger.info(f"[{self.room_id}] Participants initialized: {total_participants_count} total (session={session})")
        self.emit("OnInitMeetingParticipants",
                  participants=[_participant_json(p) for p in participants],
                  totalParticipantsCount=int(total_participants_count),
                  needCleanUp=need_cleanup, session=_enum_name(session))

    def OnUserJoin(self, participants, session):
        names = [p.userName for p in participants]
        logger.info(f"[{self.room_id}] User(s) joined: {names} (session={session})")
        self.emit("OnUserJoin", participants=[_participant_json(p) for p in participants], session=_enum_name(session))

    def OnUserLeave(self, participants, session):
        names = [p.userName for p in participants]
        logger.info(f"[{self.room_id}] User(s) left: {names} (session={session})")
        self.emit("OnUserLeave", participants=[_participant_json(p) for p in participants], session=_enum_name(session))

    @_hot
    def OnUserUpdate(self, participants, session):
        logger.debug(f"[{self.room_id}] {len(participants)} participant(s) updated (session={session})")
        self.emit("OnUserUpdate", participants=[_participant_json(p) for p in participants], session=_enum_name(session))

    def OnHostChangedNotification(self, host_user_id: int, am_i_host: bool, session):
        logger.info(f"[{self.room_id}] Host changed: hostUserID={host_user_id}, amIHost={am_i_host}")
        self.emit("OnHostChangedNotification", hostUserID=int(host_user_id), amIHost=am_i_host, session=_enum_name(session))

    def OnMeetingParticipantsChanged(self, session):
        logger.debug(f"[{self.room_id}] Participants changed (session={session})")
        self.emit("OnMeetingParticipantsChanged", session=_enum_name(session))


class MeetingControlHelperSink(_Broadcaster):
    """Callback sink for meeting-control events: AI Companion, meeting lock,
    focus mode, archiving, live stream, smart summary, side panel."""

    def __init__(self, room_id: str):
        self.room_id = room_id

    def OnReceiveAICompanionRequest(self, info):
        logger.info(f"[{self.room_id}] AI Companion request received")
        self.emit("OnReceiveAICompanionRequest", info=_pybind_to_jsonable(info))

    def OnAICompanionStatusNeedConfirm(self, info):
        logger.info(f"[{self.room_id}] AI Companion status needs confirm")
        self.emit("OnAICompanionStatusNeedConfirm", info=_pybind_to_jsonable(info))

    def OnUpdateMeetingLockStatus(self, meeting_locked: bool):
        self.emit("OnUpdateMeetingLockStatus", meetingLocked=meeting_locked)

    def OnUpdateFocusModeOptionsNotification(self, enable: bool, status):
        self.emit("OnUpdateFocusModeOptionsNotification", enable=enable, status=_enum_name(status))

    def OnUpdateLiveStreamStatus(self, status):
        self.emit("OnUpdateLiveStreamStatus", status=_pybind_to_jsonable(status))

    def OnArchivingStatusNotification(self, is_in_progress: bool):
        self.emit("OnArchivingStatusNotification", isInProgress=is_in_progress)

    def OnShowArchivingStatusFailNotification(self, show_archiving_fail: bool):
        self.emit("OnShowArchivingStatusFailNotification", showArchivingFail=show_archiving_fail)

    def OnSmartSummaryOn(self, summary_on: bool, has_set_email: bool):
        self.emit("OnSmartSummaryOn", summaryOn=summary_on, hasSetEmail=has_set_email)

    def OnShowSidePanel(self, is_show: bool, current_panel):
        self.emit("OnShowSidePanel", isShow=is_show, currentPanel=_enum_name(current_panel))


class WaitingRoomHelperSink(_Broadcaster):
    """Callback sink for waiting-room / meeting-admission events."""

    def __init__(self, room_id: str):
        self.room_id = room_id

    def OnInSilentModeNotification(self, info):
        self.emit("OnInSilentModeNotification", info=_pybind_to_jsonable(info))

    def OnEnableWaitingRoomOnEntryNotification(self, is_enable: bool):
        self.emit("OnEnableWaitingRoomOnEntryNotification", isEnable=is_enable)

    def OnUpdateAdmitGuestEnableNotification(self, is_enabled: bool):
        self.emit("OnUpdateAdmitGuestEnableNotification", isEnabled=is_enabled)


class RecordingHelperSink(_Broadcaster):
    """Callback sink for recording events: recording state, requests, permissions, disclaimers, CMR errors."""

    def __init__(self, room_id: str):
        self.room_id = room_id

    def OnUpdateMeetingRecordingInfo(self, recording_info):
        self.emit("OnUpdateMeetingRecordingInfo", recordingInfo=_pybind_to_jsonable(recording_info))

    def OnReceiveRecordingRequest(self, info):
        logger.info(f"[{self.room_id}] Recording request received")
        self.emit("OnReceiveRecordingRequest", info=_pybind_to_jsonable(info))

    def OnNeedPromptStartRecordingDisclaimerUpdate(self, need: bool):
        self.emit("OnNeedPromptStartRecordingDisclaimerUpdate", need=need)

    def OnQueryMeetingCloudRecordingNotification(self, error_code, has_cmr_edit: bool):
        self.emit("OnQueryMeetingCloudRecordingNotification", errorCode=_enum_name(error_code), hasCMREdit=has_cmr_edit)

    def OnUpdateMeetingUserRecordingStatus(self, user_id: int, can_record: bool, is_recording: bool, is_local_recording_disabled: bool):
        self.emit("OnUpdateMeetingUserRecordingStatus", userID=int(user_id), canRecord=can_record,
                  isRecording=is_recording, isLocalRecordingDisabled=is_local_recording_disabled)

    def OnSetRecordingNotificationEmailNotification(self, result: int):
        self.emit("OnSetRecordingNotificationEmailNotification", result=int(result))

    def OnSetMeetingRecordingResult(self, result: int, recording_notification_email: str, type):
        self.emit("OnSetMeetingRecordingResult", result=int(result),
                  recordingNotificationEmail=recording_notification_email, type=_enum_name(type))

    def OnUpdateRecordingPermission(self, info):
        self.emit("OnUpdateRecordingPermission", info=[_pybind_to_jsonable(i) for i in info])

    def OnMeetingCloudRecordingErrorNotification(self, show: bool, error_code, has_cmr_edit: bool, grace_period_date: int):
        self.emit("OnMeetingCloudRecordingErrorNotification", show=show, errorCode=_enum_name(error_code),
                  hasCMREdit=has_cmr_edit, gracePeriodDate=int(grace_period_date))

    # Second (2-arg) overload of the C++ callback, forwarded under a distinct name.
    def OnMeetingCloudRecordingErrorReason(self, result: bool, reason: str):
        self.emit("OnMeetingCloudRecordingErrorReason", result=result, reason=reason)


class MeetingAudioHelperSink(_Broadcaster):
    """Callback sink for meeting-audio host-control events (mute, ask-to-unmute, mute-on-entry)."""

    def __init__(self, room_id: str):
        self.room_id = room_id

    @_hot
    def OnUpdateMyAudioStatus(self, audio_status):
        self.emit("OnUpdateMyAudioStatus", audioStatus=_pybind_to_jsonable(audio_status))

    @_hot
    def OnMuteUserAudioNotification(self, user_id: int, audio_status):
        self.emit("OnMuteUserAudioNotification", userID=int(user_id), audioStatus=_pybind_to_jsonable(audio_status))

    def OnMuteOnEntryNotification(self, is_mute_on_entry: bool):
        self.emit("OnMuteOnEntryNotification", isMuteOnEntry=is_mute_on_entry)

    def OnAskUnmuteAudioByHostNotification(self, show: bool, type):
        self.emit("OnAskUnmuteAudioByHostNotification", show=show, type=_enum_name(type))

    def OnAllowAttendeesUnmuteThemselvesNotification(self, can_attendees_unmute_themselves: bool):
        self.emit("OnAllowAttendeesUnmuteThemselvesNotification", canAttendeesUnmuteThemselves=can_attendees_unmute_themselves)


class MeetingVideoHelperSink(_Broadcaster):
    """Callback sink for meeting-video host-control events (mute, ask-start, spotlight)."""

    def __init__(self, room_id: str):
        self.room_id = room_id

    @_hot
    def OnUpdateMyVideoNotification(self, video_status):
        self.emit("OnUpdateMyVideoNotification", videoStatus=_pybind_to_jsonable(video_status))

    @_hot
    def OnMuteUserVideoNotification(self, user_id: int, video_status):
        self.emit("OnMuteUserVideoNotification", userID=int(user_id), videoStatus=_pybind_to_jsonable(video_status))

    def OnAskStartVideoByHostNotification(self, user_id: int):
        self.emit("OnAskStartVideoByHostNotification", userID=int(user_id))

    def OnSpotlightStatusNotification(self, spotlight_status):
        self.emit("OnSpotlightStatusNotification", spotlightStatus=_pybind_to_jsonable(spotlight_status))

    def OnUpdateAllowAttendeesStartVideo(self, allow: bool):
        self.emit("OnUpdateAllowAttendeesStartVideo", allow=allow)


class MeetingShareHelperSink(_Broadcaster):
    """Callback sink for meeting-share / presentation events."""

    def __init__(self, room_id: str):
        self.room_id = room_id

    def OnSharingStatusNotification(self, status):
        self.emit("OnSharingStatusNotification", status=_pybind_to_jsonable(status))

    def OnShareSettingNotification(self, setting):
        self.emit("OnShareSettingNotification", setting=_pybind_to_jsonable(setting))

    def OnSharingSourceNotification(self, zr_share_sources, zrw_share_sources):
        self.emit("OnSharingSourceNotification",
                  zrShareSources=[_pybind_to_jsonable(s) for s in zr_share_sources],
                  zrwShareSources=[_pybind_to_jsonable(s) for s in zrw_share_sources])

    def OnIncomingMeetingShareNotification(self, noti):
        self.emit("OnIncomingMeetingShareNotification", noti=_pybind_to_jsonable(noti))

    def OnUpdateLocalViewStatus(self, is_on: bool):
        self.emit("OnUpdateLocalViewStatus", isOn=is_on)

    def OnStartLocalPresentResult(self, is_sharing_meeting: bool, display_state):
        self.emit("OnStartLocalPresentResult", isSharingMeeting=is_sharing_meeting, displayState=_enum_name(display_state))

    def OnUpdateAirPlayBlackMagicStatus(self, status):
        # Carries the wireless sharing key / direct-presentation pairing code
        # (status.directPresentationSharingKey) — push-only; the SDK has no getter.
        self.emit("OnUpdateAirPlayBlackMagicStatus", status=_pybind_to_jsonable(status))


class PhoneCallServiceSink(_Broadcaster):
    """Callback sink for SIP / phone-call events (incoming, status, transfer, upgrade-to-meeting)."""

    def __init__(self, room_id: str):
        self.room_id = room_id

    def OnReceiveIncomingSIPCallNotification(self, sip_call_info):
        logger.info(f"[{self.room_id}] Incoming SIP call")
        self.emit("OnReceiveIncomingSIPCallNotification", sipCallInfo=_pybind_to_jsonable(sip_call_info))

    def OnUpdateSIPCallStatusNotification(self, sip_call_info):
        self.emit("OnUpdateSIPCallStatusNotification", sipCallInfo=_pybind_to_jsonable(sip_call_info))

    def OnUpdateSIPServiceStatusNotification(self, sip_service):
        self.emit("OnUpdateSIPServiceStatusNotification", sipService=_pybind_to_jsonable(sip_service))

    def OnTerminateSIPCallNotification(self, reason, sip_call_info):
        self.emit("OnTerminateSIPCallNotification", reason=_enum_name(reason), sipCallInfo=_pybind_to_jsonable(sip_call_info))

    def OnUpdateSIPCallAudioStatusNotification(self, muted: bool):
        self.emit("OnUpdateSIPCallAudioStatusNotification", muted=muted)

    def OnAnswerSIPCallResult(self, succeeded: bool, sip_call_info, accepted: bool):
        self.emit("OnAnswerSIPCallResult", succeeded=succeeded, sipCallInfo=_pybind_to_jsonable(sip_call_info), accepted=accepted)

    def OnUpgradeSIPCallToMeetingResult(self, succeeded: bool, sip_call_info):
        self.emit("OnUpgradeSIPCallToMeetingResult", succeeded=succeeded, sipCallInfo=_pybind_to_jsonable(sip_call_info))

    def OnUpgradeSIPCallToMeetingNotification(self, succeeded: bool, sip_call_info):
        self.emit("OnUpgradeSIPCallToMeetingNotification", succeeded=succeeded, sipCallInfo=_pybind_to_jsonable(sip_call_info))

    def OnTransferSIPCallResult(self, succeeded: bool, sip_call_info, transfer_info):
        self.emit("OnTransferSIPCallResult", succeeded=succeeded, sipCallInfo=_pybind_to_jsonable(sip_call_info),
                  transferInfo=_pybind_to_jsonable(transfer_info))

    def OnTransferSIPCallNotification(self, succeeded: bool, sip_call_info):
        self.emit("OnTransferSIPCallNotification", succeeded=succeeded, sipCallInfo=_pybind_to_jsonable(sip_call_info))


class MeetingViewLayoutHelperSink(_Broadcaster):
    """Callback sink for meeting view / layout events (wall view, pages, screen layout, confidence monitor)."""

    def __init__(self, room_id: str):
        self.room_id = room_id

    def OnUpdateWallviewStyleNotification(self, status):
        self.emit("OnUpdateWallviewStyleNotification", status=_pybind_to_jsonable(status))

    def OnUpdateVideoThumbInfo(self, info):
        self.emit("OnUpdateVideoThumbInfo", info=_pybind_to_jsonable(info))

    def OnUpdateVideoPageStatusNotification(self, noti):
        self.emit("OnUpdateVideoPageStatusNotification", noti=_pybind_to_jsonable(noti))

    def OnUpdateIsNonVideoParticipantsShowedNotification(self, is_show: bool):
        self.emit("OnUpdateIsNonVideoParticipantsShowedNotification", isShowNonVideoParticipants=is_show)

    def OnUpdateScreenLayoutStatus(self, status):
        self.emit("OnUpdateScreenLayoutStatus", status=_pybind_to_jsonable(status))

    def OnConfidenceMonitorNotification(self, info):
        self.emit("OnConfidenceMonitorNotification", info=_pybind_to_jsonable(info))

    def OnDynamicLayoutOptionNotification(self, layout):
        self.emit("OnDynamicLayoutOptionNotification", layout=_enum_name(layout))

    def OnThumbnailsPositionNotification(self, type):
        self.emit("OnThumbnailsPositionNotification", type=_enum_name(type))

    def OnChangeAttendeeViewNotification(self, layout):
        self.emit("OnChangeAttendeeViewNotification", layout=_enum_name(layout))

    @_hot
    def OnVideoOrderNotification(self, video_order_info):
        self.emit("OnVideoOrderNotification", videoOrderInfo=_pybind_to_jsonable(video_order_info))


class SettingServiceSink(_Broadcaster):
    """Callback sink for device / settings events: mic/speaker/camera lists, current
    device, volume, mute state, network adapters."""

    def __init__(self, room_id: str):
        self.room_id = room_id

    def OnMicrophoneListChanged(self, microphones):
        self.emit("OnMicrophoneListChanged", microphones=[_pybind_to_jsonable(d) for d in microphones])

    def OnSpeakerListChanged(self, speakers):
        self.emit("OnSpeakerListChanged", speakers=[_pybind_to_jsonable(d) for d in speakers])

    def OnCameraListChanged(self, cameras):
        self.emit("OnCameraListChanged", cameras=[_pybind_to_jsonable(d) for d in cameras])

    def OnUpdateCOMList(self, com_list):
        self.emit("OnUpdateCOMList", comList=[_pybind_to_jsonable(d) for d in com_list])

    def OnCurrentMicrophoneChanged(self, exist: bool, microphone):
        self.emit("OnCurrentMicrophoneChanged", exist=exist, microphone=_pybind_to_jsonable(microphone))

    def OnCurrentSpeakerChanged(self, exist: bool, speaker):
        self.emit("OnCurrentSpeakerChanged", exist=exist, speaker=_pybind_to_jsonable(speaker))

    def OnCurrentCameraChanged(self, exist: bool, camera):
        self.emit("OnCurrentCameraChanged", exist=exist, camera=_pybind_to_jsonable(camera))

    def OnCurrentMicrophoneVolumeChanged(self, volume: float):
        self.emit("OnCurrentMicrophoneVolumeChanged", volume=volume)

    def OnCurrentSpeakerVolumeChanged(self, volume: float):
        self.emit("OnCurrentSpeakerVolumeChanged", volume=volume)

    def OnCurrentSelectedMicrophoneMuted(self, muted: bool):
        self.emit("OnCurrentSelectedMicrophoneMuted", muted=muted)

    def OnNetworkAdapterUpdateInfo(self, network_adapter_infos):
        self.emit("OnNetworkAdapterUpdateInfo", networkAdapterInfos=[_pybind_to_jsonable(n) for n in network_adapter_infos])


class ClosedCaptionHelperSink(_Broadcaster):
    """Callback sink for closed-caption / live-transcript events."""

    def __init__(self, room_id: str):
        self.room_id = room_id

    def OnUpdateClosedCaptionNotification(self, closed_caption_info):
        self.emit("OnUpdateClosedCaptionNotification", closedCaptionInfo=_pybind_to_jsonable(closed_caption_info))

    def OnNewLTTLanguageNotification(self, new_ltt_caption_info):
        self.emit("OnNewLTTLanguageNotification", newLttCaptionInfo=_pybind_to_jsonable(new_ltt_caption_info))

    def OnNewLTTCaptionNotification(self, type):
        self.emit("OnNewLTTCaptionNotification", type=_enum_name(type))

    @_hot
    def OnMessageAdd(self, message):
        self.emit("OnMessageAdd", message=_pybind_to_jsonable(message))

    @_hot
    def OnMessageUpdate(self, message):
        self.emit("OnMessageUpdate", message=_pybind_to_jsonable(message))

    def OnMessageLoad(self, messages, has_more_history: bool):
        self.emit("OnMessageLoad", messages=[_pybind_to_jsonable(m) for m in messages], hasMoreHistory=has_more_history)


class ProAVServiceSink(_Broadcaster):
    """Callback sink for Pro AV events (video overlay/loss/unassigned behavior, assigned-gallery seats)."""

    def __init__(self, room_id: str):
        self.room_id = room_id

    def OnProAVVideoOverlaySettingsNotification(self, settings):
        self.emit("OnProAVVideoOverlaySettingsNotification", settings=_pybind_to_jsonable(settings))

    def OnProAVUnassignedBehaviorNotification(self, behavior):
        self.emit("OnProAVUnassignedBehaviorNotification", behavior=_pybind_to_jsonable(behavior))

    def OnProAVVideoLossBehaviorNotification(self, behavior):
        self.emit("OnProAVVideoLossBehaviorNotification", behavior=_pybind_to_jsonable(behavior))

    def OnProAVNonPersistentAssignedGalleryUpdate(self, info):
        self.emit("OnProAVNonPersistentAssignedGalleryUpdate", info=_pybind_to_jsonable(info))

    def OnProAVPersistentAssignedGalleryUpdate(self, infos):
        self.emit("OnProAVPersistentAssignedGalleryUpdate", infos=[_pybind_to_jsonable(i) for i in infos])

    def OnProAVAssignedGalleryStatusUpdate(self, status, delete_indices):
        self.emit("OnProAVAssignedGalleryStatusUpdate", status=_pybind_to_jsonable(status),
                  deleteIndices=[int(i) for i in delete_indices])

    def OnProAVAssignedGalleryHideOptionsUpdate(self, options):
        self.emit("OnProAVAssignedGalleryHideOptionsUpdate", options=_pybind_to_jsonable(options))


class HWIOHelperSink(_Broadcaster):
    """Callback sink for hardware I/O events (service availability gate)."""

    def __init__(self, room_id: str):
        self.room_id = room_id

    def OnHWIOServiceStatusUpdated(self, is_service_available: bool, is_feature_allowed: bool, companion_zrid: str):
        self.emit("OnHWIOServiceStatusUpdated", isServiceAvailable=is_service_available,
                  isFeatureAllowed=is_feature_allowed, companionZRID=companion_zrid)


class DanteOutputHelperSink(_Broadcaster):
    """Callback sink for Dante / local-network audio device events."""

    def __init__(self, room_id: str):
        self.room_id = room_id

    def OnCreateLocalNetworkAudioDevice(self, result: int, info):
        self.emit("OnCreateLocalNetworkAudioDevice", result=int(result), info=_pybind_to_jsonable(info))

    def OnDestroyLocalNetworkAudioDevice(self, result: int):
        self.emit("OnDestroyLocalNetworkAudioDevice", result=int(result))

    def OnLocalNetworkAudioDeviceError(self, error):
        self.emit("OnLocalNetworkAudioDeviceError", error=_pybind_to_jsonable(error))

    def OnLocalNetworkAudioDeviceInfoNotification(self, info):
        self.emit("OnLocalNetworkAudioDeviceInfoNotification", info=_pybind_to_jsonable(info))


class NDIHelperSink(_Broadcaster):
    """Callback sink for NDI events (usage settings, device list)."""

    def __init__(self, room_id: str):
        self.room_id = room_id

    def OnNDIUsageSettingsNotification(self, settings):
        self.emit("OnNDIUsageSettingsNotification", settings=_pybind_to_jsonable(settings))

    def OnNDIDeviceListNotification(self, devices):
        self.emit("OnNDIDeviceListNotification", devices=[_pybind_to_jsonable(d) for d in devices])


class ControlSystemHelperSink(_Broadcaster):
    """Callback sink for control-system (ZRCS) events (enable state, scene list)."""

    def __init__(self, room_id: str):
        self.room_id = room_id

    def OnEnableZRCSNotification(self, enable: bool):
        self.emit("OnEnableZRCSNotification", enable=enable)

    def OnUpdateZRCSSceneList(self, scenes):
        self.emit("OnUpdateZRCSSceneList", scenes=[_pybind_to_jsonable(s) for s in scenes])


class BYODHelperSink(_Broadcaster):
    """Callback sink for BYOD (bring-your-own-device) events (emergency-call result)."""

    def __init__(self, room_id: str):
        self.room_id = room_id

    def OnMakeEmergencyCallInBYODModeNotification(self, succeed: bool):
        self.emit("OnMakeEmergencyCallInBYODModeNotification", succeed=succeed)


class CalibrationHelperSink(_Broadcaster):
    """Callback sink for camera-calibration events. Registered for completeness;
    calibration-wizard callbacks are not forwarded (deep/niche) — extend as needed."""

    def __init__(self, room_id: str):
        self.room_id = room_id


class _SubscriberQueue(asyncio.Queue):
    """Bounded per-subscriber event queue that surfaces overflow instead of hiding it.

    When the producer drops events (subscriber too slow), the next get() yields a
    single {"event": "EventsDropped", "count": N} marker before the surviving
    events — the gap chronologically precedes everything still queued — so the
    consumer knows its view of room state may be stale and it should resync.
    """

    def __init__(self, maxsize: int = 0):
        super().__init__(maxsize)
        self.dropped = 0

    async def get(self):
        if self.dropped:
            count, self.dropped = self.dropped, 0
            return {"event": "EventsDropped", "count": count}
        return await super().get()


# ===== Room Manager =====

class RoomManager:
    """Manages multiple Zoom Room connections"""

    def __init__(self):
        self.sdk = None
        self.rooms: Dict[str, any] = {}  # room_id -> IZoomRoomsService
        self.room_sinks: Dict[str, ZoomRoomsServiceSink] = {}
        self.premeeting_sinks: Dict[str, PreMeetingServiceSink] = {}
        self.meeting_list_sinks: Dict[str, MeetingListHelperSink] = {}
        self.meeting_reminder_sinks: Dict[str, MeetingReminderSink] = {}
        self.meeting_service_sinks: Dict[str, MeetingServiceSink] = {}
        self.participant_sinks: Dict[str, ParticipantHelperSink] = {}
        self.meeting_control_sinks: Dict[str, MeetingControlHelperSink] = {}
        self.waiting_room_sinks: Dict[str, WaitingRoomHelperSink] = {}
        self.recording_sinks: Dict[str, RecordingHelperSink] = {}
        self.meeting_audio_sinks: Dict[str, MeetingAudioHelperSink] = {}
        self.meeting_video_sinks: Dict[str, MeetingVideoHelperSink] = {}
        self.meeting_share_sinks: Dict[str, MeetingShareHelperSink] = {}
        self.meeting_viewlayout_sinks: Dict[str, MeetingViewLayoutHelperSink] = {}
        self.phone_call_sinks: Dict[str, PhoneCallServiceSink] = {}
        self.setting_sinks: Dict[str, SettingServiceSink] = {}
        self.closed_caption_sinks: Dict[str, ClosedCaptionHelperSink] = {}
        self.proav_sinks: Dict[str, ProAVServiceSink] = {}
        self.hwio_sinks: Dict[str, HWIOHelperSink] = {}
        self.dante_sinks: Dict[str, DanteOutputHelperSink] = {}
        self.ndi_sinks: Dict[str, NDIHelperSink] = {}
        self.control_system_sinks: Dict[str, ControlSystemHelperSink] = {}
        self.byod_sinks: Dict[str, BYODHelperSink] = {}
        self.calibration_sinks: Dict[str, CalibrationHelperSink] = {}
        self.heartbeat_task = None
        self.liveness_task = None
        self.sdk_sink = SDKSinkImpl()
        # Times synchronous SDK calls on the loop thread; flags any that stall it.
        self.sdk_monitor = SDKCallMonitor()
        # ===== Live event streaming (WebSocket) =====
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None
        # room_id -> set of per-subscriber queues; every subscriber receives every
        # event for its room (no per-session filtering exists).
        self._ws_subscribers: Dict[str, Set[asyncio.Queue]] = {}
        # ===== Auto-reconnect (self-healing paired rooms) =====
        # room_id -> asyncio.Task running the backoff retry loop while a room is offline.
        self._reconnect_tasks: Dict[str, asyncio.Task] = {}
        # rooms that were explicitly unpaired -> never auto-reconnect (retry can't recover them).
        self._unpaired_rooms: set = set()

    # ----- WebSocket event fan-out -----

    def bind_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Capture the running loop so sink callbacks (on SDK threads) can schedule delivery."""
        self._event_loop = loop

    def has_listeners(self, room_id: str) -> bool:
        """True when at least one WebSocket subscriber is attached to the room —
        the @_hot fast-path check that lets pure-emit callbacks skip payload
        serialization entirely (PRODUCTION-REVIEW.md 4a)."""
        return bool(self._ws_subscribers.get(room_id))

    def subscribe_events(self, room_id: str) -> asyncio.Queue:
        """Register a WebSocket subscriber for a room; returns its event queue."""
        queue = _SubscriberQueue(maxsize=1000)
        self._ws_subscribers.setdefault(room_id, set()).add(queue)
        return queue

    def unsubscribe_events(self, room_id: str, queue: asyncio.Queue) -> None:
        """Remove a WebSocket subscriber's queue."""
        subs = self._ws_subscribers.get(room_id)
        if subs:
            subs.discard(queue)
            if not subs:
                self._ws_subscribers.pop(room_id, None)

    def broadcast_event(self, room_id: str, payload: dict) -> None:
        """Fan a flat event out to a room's subscribers. Safe to call from any thread."""
        loop = self._event_loop
        if loop is None:
            return  # no loop bound yet (events before startup) -> nothing to deliver
        loop.call_soon_threadsafe(self._deliver_event, room_id, payload)

    def _deliver_event(self, room_id: str, payload: dict) -> None:
        """Runs on the event loop thread: enqueue to each subscriber (drop-oldest if
        full, counting the loss so the subscriber gets an EventsDropped marker)."""
        for queue in self._ws_subscribers.get(room_id, ()):
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                try:
                    queue.get_nowait()
                    queue.dropped += 1
                except asyncio.QueueEmpty:
                    pass
                try:
                    queue.put_nowait(payload)
                except asyncio.QueueFull:
                    pass

    # ----- Auto-reconnect (self-healing) -----
    # Backoff schedule (seconds) between reconnect attempts; holds at the final value.
    _RECONNECT_BACKOFF = (5, 10, 20, 30)
    _HEARTBEAT_ERROR_BACKOFF = 1.0  # pause after a HeartBeat raise before pumping again

    def schedule_reconnect(self, room_id: str) -> None:
        """Room went offline -> start a backoff retry loop. Safe to call from any thread."""
        loop = self._event_loop
        if loop is not None:
            loop.call_soon_threadsafe(self._start_reconnect, room_id)

    def cancel_reconnect(self, room_id: str) -> None:
        """Room reconnected (or is going away) -> stop retrying. Safe from any thread."""
        loop = self._event_loop
        if loop is not None:
            loop.call_soon_threadsafe(self._stop_reconnect, room_id)

    def mark_unpaired(self, room_id: str) -> None:
        """Room was unpaired -> stop retrying and don't restart (retry can't recover it)."""
        self._unpaired_rooms.add(room_id)
        self.cancel_reconnect(room_id)

    def _start_reconnect(self, room_id: str) -> None:
        """On the loop thread: launch one reconnect loop per room, if warranted."""
        if room_id in self._unpaired_rooms:
            return
        task = self._reconnect_tasks.get(room_id)
        if task and not task.done():
            return  # already retrying this room
        self._reconnect_tasks[room_id] = self._event_loop.create_task(self._reconnect_loop(room_id))

    def _stop_reconnect(self, room_id: str) -> None:
        """On the loop thread: cancel any running reconnect loop for a room."""
        task = self._reconnect_tasks.pop(room_id, None)
        if task and not task.done():
            task.cancel()

    async def _reconnect_loop(self, room_id: str) -> None:
        """Call the room's RetryToPairRoom() on a backoff until it reconnects.

        Cancelled by cancel_reconnect() when ConnectionStateConnected fires; self-exits
        if the room is unpaired or no longer managed. RetryToPairRoom only kicks off the
        reconnect - success arrives asynchronously via OnZRConnectionStateChanged.
        """
        attempt = 0
        try:
            while True:
                delay = self._RECONNECT_BACKOFF[min(attempt, len(self._RECONNECT_BACKOFF) - 1)]
                await asyncio.sleep(delay)
                if room_id in self._unpaired_rooms:
                    return
                room_service = self.rooms.get(room_id)
                if room_service is None:
                    return  # room no longer managed
                # Self-exit after a healed zombie: the SDK already believed the room
                # was Connected, so recovery may produce no fresh Connected callback
                # and cancel_reconnect never fires. If the cached state says
                # Connected AND commands work again, the room healed — stop retrying
                # (PRODUCTION-REVIEW.md 2.11). A real disconnect keeps looping:
                # its state is Disconnected until the callback flips it.
                sink = self.premeeting_sinks.get(room_id)
                state = getattr(sink, "connection_state", None)
                if state == zrc_sdk.ConnectionStateConnected and not self._probe_zombie(room_id):
                    logger.info(f"[{room_id}] auto-reconnect stopped (room healed while state stayed Connected)")
                    return
                attempt += 1
                try:
                    # The reconnect path is the prime blocking suspect — it runs
                    # exactly when the network is down. Time it so a real stall
                    # shows up in the logs / /health instead of staying hidden.
                    with self.sdk_monitor.measure(f"RetryToPairRoom[{room_id}]"):
                        result = room_service.RetryToPairRoom()
                    logger.info(f"[{room_id}] auto-reconnect attempt {attempt}: {result}")
                except Exception as e:
                    logger.error(f"[{room_id}] auto-reconnect attempt {attempt} raised: {e}")
        except asyncio.CancelledError:
            logger.info(f"[{room_id}] auto-reconnect stopped (reconnected or shutting down)")
            raise

    # ----- Liveness self-heal (the "zombie" state) -----
    # A room can report Connected (GetConnectionState) while its command channel is
    # dead — commands return NOT_CONNECT_TO_ZOOMROOM (11). The SDK never fires
    # Disconnected in this state, so auto-reconnect never triggers and the room
    # stays unusable, even while idle. This loop probes each room's REAL
    # reachability and reconnects the zombies. Interval is a balance: short enough
    # to recover promptly, long enough that per-room probes are negligible load.
    _LIVENESS_INTERVAL = 20  # seconds

    def _probe_zombie(self, room_id: str) -> bool:
        """True iff a command actually reaches the SDK but the room is unreachable
        (NOT_CONNECT_TO_ZOOMROOM) — the zombie state. Read-only, never raises."""
        room_service = self.rooms.get(room_id)
        if room_service is None:
            return False
        try:
            meeting_service = room_service.GetMeetingService()
            if not meeting_service:
                return False
            result, _status = meeting_service.GetMeetingStatus()
            return int(result) == NOT_CONNECT_TO_ZOOMROOM
        except Exception:
            return False  # can't confirm a zombie -> leave it to the next round

    def _liveness_check_once(self) -> None:
        """One probe pass over managed rooms; reconnect any confirmed zombie."""
        for room_id in list(self.rooms):
            if room_id in self._unpaired_rooms:
                continue
            task = self._reconnect_tasks.get(room_id)
            if task and not task.done():
                continue  # already reconnecting this room
            if self._probe_zombie(room_id):
                logger.warning(
                    f"[{room_id}] liveness: reports Connected but commands return "
                    f"NOT_CONNECT_TO_ZOOMROOM (11) — scheduling reconnect (zombie self-heal)"
                )
                self.schedule_reconnect(room_id)

    async def _liveness_loop(self) -> None:
        logger.info(f"Starting liveness self-heal loop ({self._LIVENESS_INTERVAL}s interval)...")
        while True:
            try:
                await asyncio.sleep(self._LIVENESS_INTERVAL)
                self._liveness_check_once()
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error(f"liveness loop error: {e}")

    def _restore_room(self, room_id: str, worker, can_retry: bool = True) -> bool:
        """Restore one previously-paired room at startup.

        A single room's failure must log and skip, never abort initialize() for
        the rest of the fleet (PRODUCTION-REVIEW.md 2.5b)."""
        try:
            self.rooms[room_id] = worker
            self.register_sinks_for_room(room_id, worker)
            if can_retry:
                logger.info(f"  Attempting to reconnect {room_id}...")
                retry_result = worker.RetryToPairRoom()
                logger.info(f"  RetryToPairRoom result: {retry_result}")
            logger.info(f"✓ Restored room service for: {room_id}")
            return True
        except Exception as e:
            logger.error(f"[{room_id}] restore failed — skipping this room: {e}")
            self.rooms.pop(room_id, None)
            return False

    def initialize(self):
        """Initialize the SDK"""
        logger.info("Initializing Zoom Rooms SDK...")
        # Create SDK instance with sink (new API in SDK 6.7+)
        self.sdk = zrc_sdk.CreateInstanceWithSink(self.sdk_sink)
        logger.info("SDK instance created with sink")

        # Initialize web domain (required for SDK to work properly)
        result = self.sdk.InitWebDomain("https://zoom.us")
        logger.info(f"InitWebDomain result: {result}")

        # Try QueryAllZoomRoomsServices first (should work according to docs)
        logger.info("Querying for previously paired rooms...")
        logger.info(f"Data directory: {self.sdk_sink.OnGetAppContentDirPath()}")

        room_infos = []
        result = self.sdk.QueryAllZoomRoomsServices(room_infos)

        logger.info(f"QueryAllZoomRoomsServices result: {result}")
        logger.info(f"Found {len(room_infos)} room(s) via QueryAllZoomRoomsServices")

        if result == zrc_sdk.ZRCSDKERR_SUCCESS and room_infos:
            # SDK successfully returned previously paired rooms
            for room_info in room_infos:
                logger.info(f"  - Room: {room_info.roomID}")
                logger.info(f"    Name: {room_info.roomName}")
                logger.info(f"    Display: {room_info.displayName}")
                logger.info(f"    Can retry: {room_info.canRetryToPair}")

                if room_info.worker:
                    self._restore_room(room_info.roomID, room_info.worker,
                                       can_retry=room_info.canRetryToPair)
        else:
            # QueryAllZoomRoomsServices returned empty - fallback to database query
            # This happens when rooms are paired but never fully connected
            logger.info("QueryAllZoomRoomsServices returned no rooms, querying database directly...")

            db_path = os.path.join(self.sdk_sink.OnGetAppContentDirPath(), "third_zrc_data.db")

            if os.path.exists(db_path):
                try:
                    # closing() so a raise mid-query (locked/corrupt db) can't
                    # leak the handle (PRODUCTION-REVIEW.md 4b)
                    with closing(sqlite3.connect(db_path)) as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT pk_id FROM ThirdRoomList")
                        room_ids = [row[0] for row in cursor.fetchall()]

                    if room_ids:
                        logger.info(f"Found {len(room_ids)} previously paired room(s) in database")
                        for room_id in room_ids:
                            logger.info(f"  - Restoring room: {room_id}")
                            # Create service for this room ID
                            room_service = self.sdk.CreateZoomRoomsService(room_id)
                            if room_service:
                                self._restore_room(room_id, room_service)
                    else:
                        logger.info("No previously paired rooms found in database")
                except Exception as e:
                    logger.error(f"Error querying database: {e}")
            else:
                logger.info(f"Database file not found: {db_path}")

        logger.info("✓ SDK initialized successfully")

    async def start_heartbeat(self):
        """Start the SDK HeartBeat timer (required on Linux)"""
        # Capture the running loop so sink callbacks (which fire on SDK threads) can
        # schedule WebSocket delivery via call_soon_threadsafe.
        self.bind_event_loop(asyncio.get_running_loop())

        async def heartbeat_loop():
            logger.info("Starting SDK HeartBeat loop (150ms interval)...")
            while True:
                try:
                    if self.sdk:
                        # HeartBeat runs every 150ms on the loop; if it ever spikes
                        # (e.g. with many connected rooms) the monitor surfaces it.
                        with self.sdk_monitor.measure("HeartBeat"):
                            self.sdk.HeartBeat()
                    await asyncio.sleep(0.15)  # 150ms interval
                except Exception as e:
                    # Never stop the pump on a transient error: the SDK services its
                    # queues/network/state machine from this call, so a permanent stop
                    # is a silent full outage that /health can't distinguish from
                    # healthy (PRODUCTION-REVIEW.md 1.1). CancelledError is a
                    # BaseException and still cancels the loop cleanly.
                    logger.error(f"HeartBeat error: {e} — continuing after backoff")
                    await asyncio.sleep(self._HEARTBEAT_ERROR_BACKOFF)

        self.heartbeat_task = asyncio.create_task(heartbeat_loop())
        self.liveness_task = asyncio.create_task(self._liveness_loop())

    async def stop_heartbeat(self):
        """Stop the HeartBeat + liveness timers"""
        for task in (self.heartbeat_task, getattr(self, "liveness_task", None)):
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    # One row per sink surface: (label, getter path from the room service, sink
    # class, per-room store attribute). register_sinks_for_room AND
    # _deregister_room_sinks both walk THIS table, so the two directions can no
    # longer drift (PRODUCTION-REVIEW.md 4d — the disjoint-static-map
    # deregistration bug hid in exactly that hand-mirrored drift).
    _SINK_SURFACES = (
        ("room service",     (),                                                  ZoomRoomsServiceSink,        "room_sinks"),
        ("pre-meeting",      ("GetPreMeetingService",),                           PreMeetingServiceSink,       "premeeting_sinks"),
        ("control system",   ("GetPreMeetingService", "GetControlSystemHelper"),  ControlSystemHelperSink,     "control_system_sinks"),
        ("BYOD",             ("GetPreMeetingService", "GetBYODHelper"),           BYODHelperSink,              "byod_sinks"),
        ("phone call",       ("GetPhoneCallService",),                            PhoneCallServiceSink,        "phone_call_sinks"),
        ("setting",          ("GetSettingService",),                              SettingServiceSink,          "setting_sinks"),
        ("calibration",      ("GetSettingService", "GetCalibrationHelper"),       CalibrationHelperSink,       "calibration_sinks"),
        ("pro AV",           ("GetProAVService",),                                ProAVServiceSink,            "proav_sinks"),
        ("HWIO",             ("GetProAVService", "GetHWIOHelper"),                HWIOHelperSink,              "hwio_sinks"),
        ("Dante output",     ("GetProAVService", "GetDanteOutputHelper"),         DanteOutputHelperSink,       "dante_sinks"),
        ("meeting service",  ("GetMeetingService",),                              MeetingServiceSink,          "meeting_service_sinks"),
        ("meeting list",     ("GetMeetingService", "GetMeetingListHelper"),       MeetingListHelperSink,       "meeting_list_sinks"),
        ("meeting reminder", ("GetMeetingService", "GetMeetingReminderHelper"),   MeetingReminderSink,         "meeting_reminder_sinks"),
        ("participant",      ("GetMeetingService", "GetParticipantHelper"),       ParticipantHelperSink,       "participant_sinks"),
        ("meeting control",  ("GetMeetingService", "GetMeetingControlHelper"),    MeetingControlHelperSink,    "meeting_control_sinks"),
        ("waiting room",     ("GetMeetingService", "GetWaitingRoomHelper"),       WaitingRoomHelperSink,       "waiting_room_sinks"),
        ("recording",        ("GetMeetingService", "GetRecordingHelper"),         RecordingHelperSink,         "recording_sinks"),
        ("meeting audio",    ("GetMeetingService", "GetMeetingAudioHelper"),      MeetingAudioHelperSink,      "meeting_audio_sinks"),
        ("meeting video",    ("GetMeetingService", "GetMeetingVideoHelper"),      MeetingVideoHelperSink,      "meeting_video_sinks"),
        ("meeting share",    ("GetMeetingService", "GetMeetingShareHelper"),      MeetingShareHelperSink,      "meeting_share_sinks"),
        ("view layout",      ("GetMeetingService", "GetMeetingViewLayoutHelper"), MeetingViewLayoutHelperSink, "meeting_viewlayout_sinks"),
        ("closed caption",   ("GetMeetingService", "GetClosedCaptionHelper"),     ClosedCaptionHelperSink,     "closed_caption_sinks"),
        ("NDI",              ("GetMeetingService", "GetNDIHelper"),               NDIHelperSink,               "ndi_sinks"),
    )

    def _resolve_surface(self, room_service, path, room_id, label):
        """Walk a _SINK_SURFACES getter path from the room service; None (with a
        log) if any hop is missing — a missing surface skips, never raises."""
        obj = room_service
        for getter in path:
            obj = getattr(obj, getter)()
            if not obj:
                logger.error(f"Failed to get {label} surface for room: {room_id}")
                return None
        return obj

    def register_sinks_for_room(self, room_id: str, room_service):
        """Register a sink on every surface in _SINK_SURFACES (the deregister
        mirror walks the same table)."""
        # (Re)pairing/restoring a room clears any prior unpaired flag so it can auto-reconnect again.
        self._unpaired_rooms.discard(room_id)
        for label, path, sink_cls, store_name in self._SINK_SURFACES:
            surface = self._resolve_surface(room_service, path, room_id, label)
            if surface is None:
                continue
            sink = sink_cls(room_id)
            sink.mgr = self
            result = surface.RegisterSink(sink)
            if result == zrc_sdk.ZRCSDKERR_SUCCESS:
                getattr(self, store_name)[room_id] = sink
                logger.info(f"✓ Registered {label} sink for: {room_id}")
            else:
                logger.error(f"Failed to register {label} sink: {result}")

    def create_room_service(self, room_id: str):
        """Create a new room service instance with callbacks"""
        # (Re)pairing always re-enables auto-reconnect — including a cached service
        # whose room was unpaired remotely and is now being re-paired.
        self._unpaired_rooms.discard(room_id)
        if room_id in self.rooms:
            return self.rooms[room_id]

        logger.info(f"Creating service for room: {room_id}")
        room_service = self.sdk.CreateZoomRoomsService(room_id)
        if not room_service:
            # Same guard the DB-restore path applies to this exact call — without
            # it the pair endpoint 500s with an opaque 'NoneType' AttributeError
            # (PRODUCTION-REVIEW.md 2.5c).
            logger.error(f"CreateZoomRoomsService returned no service for: {room_id}")
            return None

        # Register callback sinks
        self.register_sinks_for_room(room_id, room_service)

        self.rooms[room_id] = room_service
        return room_service

    def get_room_service(self, room_id: str):
        """Get existing room service or None"""
        return self.rooms.get(room_id)

    def get_meeting_list_sink(self, room_id: str) -> Optional[MeetingListHelperSink]:
        sink = self.meeting_list_sinks.get(room_id)
        if sink:
            return sink
        room_service = self.rooms.get(room_id)
        if not room_service:
            return None
        meeting_service = room_service.GetMeetingService()
        if not meeting_service:
            return None
        list_helper = meeting_service.GetMeetingListHelper()
        if not list_helper:
            return None
        meeting_list_sink = MeetingListHelperSink(room_id)
        meeting_list_sink.mgr = self
        result = list_helper.RegisterSink(meeting_list_sink)
        if result != zrc_sdk.ZRCSDKERR_SUCCESS:
            logger.error(f"Failed to register meeting list sink: {result}")
            return None
        self.meeting_list_sinks[room_id] = meeting_list_sink
        return meeting_list_sink

    def _sink_stores(self):
        """Every per-room sink registry (room_id -> sink instance) on this manager."""
        return [v for k, v in vars(self).items() if k.endswith("_sinks") and isinstance(v, dict)]

    def _deregister_room_sinks(self, room_id: str, room_service):
        """Deregister every surface in _SINK_SURFACES — the same table
        registration walks, so the mirror cannot drift."""
        for label, path, _sink_cls, _store_name in self._SINK_SURFACES:
            try:
                surface = self._resolve_surface(room_service, path, room_id, label)
                if surface:
                    surface.DeregisterSink()
            except Exception as e:
                logger.debug(f"[{room_id}] Failed to deregister {label} sink: {e}")

    def remove_room(self, room_id: str) -> None:
        """Fully forget a room: stop reconnecting, deregister every sink surface,
        and drop it from all per-room registries. Call on the event loop thread."""
        self._stop_reconnect(room_id)
        self._unpaired_rooms.discard(room_id)
        room_service = self.rooms.pop(room_id, None)
        if room_service is not None:
            self._deregister_room_sinks(room_id, room_service)
        for store in self._sink_stores():
            store.pop(room_id, None)

    def shutdown(self):
        """Clean up SDK resources"""
        logger.info("Shutting down SDK...")
        # Stop any in-flight auto-reconnect loops.
        for room_id in list(self._reconnect_tasks):
            self._stop_reconnect(room_id)
        for room_id in list(self.rooms):
            self.remove_room(room_id)
        # Belt and braces: clear any sink entries for rooms no longer in self.rooms.
        for store in self._sink_stores():
            store.clear()

        if self.sdk and hasattr(zrc_sdk, "ClearSDKSink"):
            try:
                zrc_sdk.ClearSDKSink(self.sdk)
            except Exception as e:
                logger.debug(f"Failed to clear SDK sink: {e}")

        # Don't call DestroyInstance - it can cause crashes
        # The SDK will clean up on process exit
        self.sdk = None
        logger.info("✓ SDK shutdown complete")
