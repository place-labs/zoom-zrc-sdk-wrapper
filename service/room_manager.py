"""
Room Manager - Manages multiple Zoom Room connections
"""

import asyncio
import logging
import sqlite3
import os
import threading
from collections import deque
from typing import Deque, Dict, Optional, Tuple

try:
    import zrc_sdk
except ImportError:
    print("ERROR: zrc_sdk module not found. Run '../build.sh' first.")
    raise

logger = logging.getLogger(__name__)


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
    out = {}
    for attr in dir(v):
        if attr.startswith("_"):
            continue
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
        self.pair_event.set()
        self.emit("OnPairRoomResult", result=int(result))

    def OnRoomUnpairedReason(self, reason: int):
        """Called when room is unpaired"""
        logger.warning(f"[{self.room_id}] Room unpaired, reason: {reason}")
        self.emit("OnRoomUnpairedReason", reason=_enum_name(reason))


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
            self.connected_event.set()
        self.emit("OnZRConnectionStateChanged", state=_enum_name(state))

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
        self.heartbeat_task = None
        self.sdk_sink = SDKSinkImpl()
        # ===== Live event streaming (WebSocket) =====
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None
        # room_id -> {per-subscriber asyncio.Queue: session filter or None}.
        # The filter is a ConfSessionType enum name (e.g. "CurrentSession"); when set,
        # the subscriber only receives session-tagged events for that session.
        self._ws_subscribers: Dict[str, Dict[asyncio.Queue, Optional[str]]] = {}

    # ----- WebSocket event fan-out -----

    def bind_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Capture the running loop so sink callbacks (on SDK threads) can schedule delivery."""
        self._event_loop = loop

    def subscribe_events(self, room_id: str) -> asyncio.Queue:
        """Register a WebSocket subscriber for a room; returns its event queue."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
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
        """Runs on the event loop thread: enqueue to each subscriber (drop-oldest if full)."""
        for queue in self._ws_subscribers.get(room_id, ()):
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                try:
                    queue.put_nowait(payload)
                except asyncio.QueueFull:
                    pass

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
                    self.rooms[room_info.roomID] = room_info.worker
                    self.register_sinks_for_room(room_info.roomID, room_info.worker)

                    if room_info.canRetryToPair:
                        logger.info(f"  Attempting to reconnect {room_info.roomID}...")
                        retry_result = room_info.worker.RetryToPairRoom()
                        logger.info(f"  RetryToPairRoom result: {retry_result}")

                    logger.info(f"✓ Restored room service for: {room_info.roomID}")
        else:
            # QueryAllZoomRoomsServices returned empty - fallback to database query
            # This happens when rooms are paired but never fully connected
            logger.info("QueryAllZoomRoomsServices returned no rooms, querying database directly...")

            db_path = os.path.join(self.sdk_sink.OnGetAppContentDirPath(), "third_zrc_data.db")

            if os.path.exists(db_path):
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT pk_id FROM ThirdRoomList")
                    room_ids = [row[0] for row in cursor.fetchall()]
                    conn.close()

                    if room_ids:
                        logger.info(f"Found {len(room_ids)} previously paired room(s) in database")
                        for room_id in room_ids:
                            logger.info(f"  - Restoring room: {room_id}")
                            # Create service for this room ID
                            room_service = self.sdk.CreateZoomRoomsService(room_id)
                            if room_service:
                                self.rooms[room_id] = room_service
                                self.register_sinks_for_room(room_id, room_service)

                                # Try to reconnect using stored credentials
                                logger.info(f"  Attempting to reconnect {room_id}...")
                                retry_result = room_service.RetryToPairRoom()
                                logger.info(f"  RetryToPairRoom result: {retry_result}")
                                logger.info(f"✓ Restored room service for: {room_id}")
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
                        self.sdk.HeartBeat()
                    await asyncio.sleep(0.15)  # 150ms interval
                except Exception as e:
                    logger.error(f"HeartBeat error: {e}")
                    break

        self.heartbeat_task = asyncio.create_task(heartbeat_loop())

    async def stop_heartbeat(self):
        """Stop the HeartBeat timer"""
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass

    def register_sinks_for_room(self, room_id: str, room_service):
        """Register callback sinks for a room service"""
        # Register room service callback sink
        room_sink = ZoomRoomsServiceSink(room_id)
        room_sink.mgr = self
        result = room_service.RegisterSink(room_sink)
        if result == zrc_sdk.ZRCSDKERR_SUCCESS:
            self.room_sinks[room_id] = room_sink
            logger.info(f"✓ Registered room service sink for: {room_id}")
        else:
            logger.error(f"Failed to register room service sink: {result}")

        # Register pre-meeting service callback sink
        premeeting = room_service.GetPreMeetingService()
        premeeting_sink = PreMeetingServiceSink(room_id)
        premeeting_sink.mgr = self
        result = premeeting.RegisterSink(premeeting_sink)
        if result == zrc_sdk.ZRCSDKERR_SUCCESS:
            self.premeeting_sinks[room_id] = premeeting_sink
            logger.info(f"✓ Registered pre-meeting sink for: {room_id}")
        else:
            logger.error(f"Failed to register pre-meeting sink: {result}")

        meeting_service = room_service.GetMeetingService()
        if meeting_service:
            list_helper = meeting_service.GetMeetingListHelper()
            if list_helper:
                meeting_list_sink = MeetingListHelperSink(room_id)
                meeting_list_sink.mgr = self
                result = list_helper.RegisterSink(meeting_list_sink)
                if result == zrc_sdk.ZRCSDKERR_SUCCESS:
                    self.meeting_list_sinks[room_id] = meeting_list_sink
                    logger.info(f"✓ Registered meeting list sink for: {room_id}")
                else:
                    logger.error(f"Failed to register meeting list sink: {result}")
            else:
                logger.error(f"Failed to get meeting list helper for room: {room_id}")
            reminder_helper = meeting_service.GetMeetingReminderHelper()
            if reminder_helper:
                reminder_sink = MeetingReminderSink(room_id)
                reminder_sink.mgr = self
                result = reminder_helper.RegisterSink(reminder_sink)
                if result == zrc_sdk.ZRCSDKERR_SUCCESS:
                    self.meeting_reminder_sinks[room_id] = reminder_sink
                    logger.info(f"✓ Registered meeting reminder sink for: {room_id}")
                else:
                    logger.error(f"Failed to register meeting reminder sink: {result}")
            else:
                logger.error(f"Failed to get meeting reminder helper for room: {room_id}")

            # Register meeting service sink (meeting status, start/exit, waiting for host)
            meeting_service_sink = MeetingServiceSink(room_id)
            meeting_service_sink.mgr = self
            result = meeting_service.RegisterSink(meeting_service_sink)
            if result == zrc_sdk.ZRCSDKERR_SUCCESS:
                self.meeting_service_sinks[room_id] = meeting_service_sink
                logger.info(f"✓ Registered meeting service sink for: {room_id}")
            else:
                logger.error(f"Failed to register meeting service sink: {result}")

            # Register participant helper sink (join/leave/update, host change)
            participant_helper = meeting_service.GetParticipantHelper()
            if participant_helper:
                participant_sink = ParticipantHelperSink(room_id)
                participant_sink.mgr = self
                result = participant_helper.RegisterSink(participant_sink)
                if result == zrc_sdk.ZRCSDKERR_SUCCESS:
                    self.participant_sinks[room_id] = participant_sink
                    logger.info(f"✓ Registered participant helper sink for: {room_id}")
                else:
                    logger.error(f"Failed to register participant helper sink: {result}")
            else:
                logger.error(f"Failed to get participant helper for room: {room_id}")

            # Register meeting control helper sink (AI Companion, lock, focus, archiving, live stream)
            control_helper = meeting_service.GetMeetingControlHelper()
            if control_helper:
                control_sink = MeetingControlHelperSink(room_id)
                control_sink.mgr = self
                result = control_helper.RegisterSink(control_sink)
                if result == zrc_sdk.ZRCSDKERR_SUCCESS:
                    self.meeting_control_sinks[room_id] = control_sink
                    logger.info(f"✓ Registered meeting control sink for: {room_id}")
                else:
                    logger.error(f"Failed to register meeting control sink: {result}")
            else:
                logger.error(f"Failed to get meeting control helper for room: {room_id}")

            # Register waiting room helper sink (meeting admission / silent mode)
            waiting_room_helper = meeting_service.GetWaitingRoomHelper()
            if waiting_room_helper:
                waiting_room_sink = WaitingRoomHelperSink(room_id)
                waiting_room_sink.mgr = self
                result = waiting_room_helper.RegisterSink(waiting_room_sink)
                if result == zrc_sdk.ZRCSDKERR_SUCCESS:
                    self.waiting_room_sinks[room_id] = waiting_room_sink
                    logger.info(f"✓ Registered waiting room sink for: {room_id}")
                else:
                    logger.error(f"Failed to register waiting room sink: {result}")
            else:
                logger.error(f"Failed to get waiting room helper for room: {room_id}")
        else:
            logger.error(f"Failed to get meeting service for room: {room_id}")

    def create_room_service(self, room_id: str):
        """Create a new room service instance with callbacks"""
        if room_id in self.rooms:
            return self.rooms[room_id]

        logger.info(f"Creating service for room: {room_id}")
        room_service = self.sdk.CreateZoomRoomsService(room_id)

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

    def shutdown(self):
        """Clean up SDK resources"""
        logger.info("Shutting down SDK...")
        for room_id, room_service in list(self.rooms.items()):
            try:
                room_service.DeregisterSink()
            except Exception as e:
                logger.debug(f"[{room_id}] Failed to deregister room sink: {e}")
            try:
                premeeting = room_service.GetPreMeetingService()
                if premeeting:
                    premeeting.DeregisterSink()
            except Exception as e:
                logger.debug(f"[{room_id}] Failed to deregister premeeting sink: {e}")
            try:
                meeting_service = room_service.GetMeetingService()
                if meeting_service:
                    list_helper = meeting_service.GetMeetingListHelper()
                    if list_helper:
                        list_helper.DeregisterSink()
                    meeting_service.DeregisterSink()
                    participant_helper = meeting_service.GetParticipantHelper()
                    if participant_helper:
                        participant_helper.DeregisterSink()
            except Exception as e:
                logger.debug(f"[{room_id}] Failed to deregister meeting/participant sink: {e}")

        self.room_sinks.clear()
        self.premeeting_sinks.clear()
        self.meeting_list_sinks.clear()
        self.meeting_service_sinks.clear()
        self.participant_sinks.clear()
        self.rooms.clear()

        if self.sdk and hasattr(zrc_sdk, "ClearSDKSink"):
            try:
                zrc_sdk.ClearSDKSink(self.sdk)
            except Exception as e:
                logger.debug(f"Failed to clear SDK sink: {e}")

        # Don't call DestroyInstance - it can cause crashes
        # The SDK will clean up on process exit
        self.sdk = None
        logger.info("✓ SDK shutdown complete")
