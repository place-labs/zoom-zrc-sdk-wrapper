"""Notification-first contracts for the live ZRC verification matrix."""

from enum import Enum
from types import SimpleNamespace

import pytest

import _zrc_stub  # noqa: F401  (installs the fake SDK before room_manager)
import room_manager as rm

pytestmark = pytest.mark.unit


class _Capture:
    def __init__(self):
        self.events = []

    def broadcast_event(self, room_id, payload):
        self.events.append({"room_id": room_id, **payload})


class _NamedValue:
    def __init__(self, name):
        self.name = name


class _PayloadEnum(Enum):
    REMINDER_TYPE_RECORDING_DISCLAIMER = 1
    RecordingTypeCloud = 2
    AICompanionRequestSwitch = 3


def _capture(sink):
    sink.mgr = _Capture()
    return sink.mgr.events


def test_consolidated_customized_consent_preserves_prompt_payload():
    sink = rm.MeetingReminderSink("r1")
    events = _capture(sink)
    disclaimers = [
        SimpleNamespace(title="Recording", positiveActionText="Agree"),
        SimpleNamespace(title="AI Companion", negativeActionText="Decline"),
    ]

    sink.OnConsolidatedCustomizedConsentNotification(disclaimers, True)

    assert events == [
        {
            "room_id": "r1",
            "event": "OnConsolidatedCustomizedConsentNotification",
            "disclaimers": [
                {"positiveActionText": "Agree", "title": "Recording"},
                {"negativeActionText": "Decline", "title": "AI Companion"},
            ],
            "isAudioVideoBlocked": True,
        }
    ]


@pytest.mark.parametrize(
    ("sink", "callback", "args", "expected"),
    (
        (
            rm.MeetingReminderSink("r1"),
            "OnMeetingReminderNotification",
            (
                SimpleNamespace(
                    reminderType=(
                        _PayloadEnum.REMINDER_TYPE_RECORDING_DISCLAIMER
                    ),
                    disclaimerPrivacy=SimpleNamespace(title="Recording"),
                    isShowing=True,
                ),
            ),
            {
                "room_id": "r1",
                "event": "OnMeetingReminderNotification",
                "reminderContent": {
                    "reminderType": "REMINDER_TYPE_RECORDING_DISCLAIMER",
                    "disclaimerPrivacy": {"title": "Recording"},
                    "isShowing": True,
                },
            },
        ),
        (
            rm.RecordingHelperSink("r1"),
            "OnReceiveRecordingRequest",
            (
                SimpleNamespace(
                    recordingType=_PayloadEnum.RecordingTypeCloud,
                    senderName="Guest",
                ),
            ),
            {
                "room_id": "r1",
                "event": "OnReceiveRecordingRequest",
                "info": {
                    "recordingType": "RecordingTypeCloud",
                    "senderName": "Guest",
                },
            },
        ),
        (
            rm.MeetingControlHelperSink("r1"),
            "OnReceiveAICompanionRequest",
            (
                SimpleNamespace(
                    type=_PayloadEnum.AICompanionRequestSwitch,
                    senderNames=["Guest"],
                    AICFeatures=3,
                    switchAction=1,
                ),
            ),
            {
                "room_id": "r1",
                "event": "OnReceiveAICompanionRequest",
                "info": {
                    "type": "AICompanionRequestSwitch",
                    "senderNames": ["Guest"],
                    "AICFeatures": 3,
                    "switchAction": 1,
                },
            },
        ),
        (
            rm.WaitingRoomHelperSink("r1"),
            "OnEnableWaitingRoomOnEntryNotification",
            (True,),
            {
                "room_id": "r1",
                "event": "OnEnableWaitingRoomOnEntryNotification",
                "isEnable": True,
            },
        ),
        (
            rm.WaitingRoomHelperSink("r1"),
            "OnUpdateAdmitGuestEnableNotification",
            (False,),
            {
                "room_id": "r1",
                "event": "OnUpdateAdmitGuestEnableNotification",
                "isEnabled": False,
            },
        ),
        (
            rm.WaitingRoomHelperSink("r1"),
            "OnInSilentModeNotification",
            (
                SimpleNamespace(
                    isInSilentMode=True,
                    silentModeForNoHost=True,
                    isPutInByManual=False,
                ),
            ),
            {
                "room_id": "r1",
                "event": "OnInSilentModeNotification",
                "info": {
                    "isInSilentMode": True,
                    "silentModeForNoHost": True,
                    "isPutInByManual": False,
                },
            },
        ),
    ),
)
def test_additional_priority_notification_payload_contracts(
    sink, callback, args, expected
):
    events = _capture(sink)

    getattr(sink, callback)(*args)

    assert events == [expected]


def test_all_priority_notification_facades_emit_websocket_events():
    cases = (
        (
            rm.MeetingListHelperSink("r1"),
            "OnMeetingWillReleaseAutomatically",
            (SimpleNamespace(meetingNumber="123"),),
        ),
        (
            rm.MeetingReminderSink("r1"),
            "OnConsentNotification",
            (SimpleNamespace(isShowing=True, type=_NamedValue("CONSENT_TYPE_COMMON")),),
        ),
        (
            rm.MeetingReminderSink("r1"),
            "OnCustomizedReminderNotification",
            (SimpleNamespace(customizedDisclaimerType=1),),
        ),
        (
            rm.MeetingReminderSink("r1"),
            "OnCombinedConsentNotification",
            (SimpleNamespace(isShowing=True, type=7),),
        ),
        (
            rm.MeetingReminderSink("r1"),
            "OnPrivacyAlertNotification",
            (
                _NamedValue("PRIVACY_ALERT_ACTION_SHOW"),
                _NamedValue("PRIVACY_ALERT_TYPE_LIVE_TRANSCRIPTION"),
                SimpleNamespace(title="Privacy"),
            ),
        ),
        (
            rm.MeetingReminderSink("r1"),
            "OnInactiveDetectionNotification",
            (True, 123456),
        ),
        (
            rm.MeetingServiceSink("r1"),
            "OnJBHWaitingHostNotification",
            (True, _NamedValue("WaitingHostReasonJBH")),
        ),
        (rm.MeetingServiceSink("r1"), "OnMeetingWillStopAutomatically", ()),
        (
            rm.MeetingControlHelperSink("r1"),
            "OnAICompanionStatusNeedConfirm",
            (SimpleNamespace(summaryOn=True),),
        ),
        (
            rm.MeetingAudioHelperSink("r1"),
            "OnAskUnmuteAudioByHostNotification",
            (True, _NamedValue("AskUnmuteAudioByHostTypeUnmuteAudio")),
        ),
        (
            rm.MeetingVideoHelperSink("r1"),
            "OnAskStartVideoByHostNotification",
            (42,),
        ),
        (
            rm.MeetingShareHelperSink("r1"),
            "OnIncomingMeetingShareNotification",
            (SimpleNamespace(shareUserName="Guest"),),
        ),
    )

    for sink, callback, args in cases:
        events = _capture(sink)
        getattr(sink, callback)(*args)
        assert len(events) == 1, f"{callback} did not emit exactly one event"
        assert events[0]["room_id"] == "r1"
        assert events[0]["event"] == callback
