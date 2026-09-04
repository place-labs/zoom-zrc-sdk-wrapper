"""Unit coverage for the callback-driven meeting password flow."""

from types import SimpleNamespace

import pytest

pytestmark = pytest.mark.unit

import _zrc_stub  # noqa: F401
import room_manager as rm


class _CaptureManager:
    def __init__(self):
        self.events = []

    def broadcast_event(self, room_id, payload):
        self.events.append((room_id, payload))


def test_meeting_password_notification_serializes_lock_status():
    manager = _CaptureManager()
    sink = rm.MeetingServiceSink("r1")
    sink.mgr = manager
    lock_status = SimpleNamespace(
        isLocked=True,
        remainTimeSec=45,
        wrongPwdInputCount=3,
    )

    sink.OnMeetingNeedsPasswordNotification(True, True, lock_status)

    assert manager.events == [
        (
            "r1",
            {
                "event": "OnMeetingNeedsPasswordNotification",
                "showPasswordDialog": True,
                "wrongAndRetry": True,
                "lockStatus": {
                    "isLocked": True,
                    "remainTimeSec": 45,
                    "wrongPwdInputCount": 3,
                },
            },
        )
    ]


def test_meeting_password_lock_status_notification_is_forwarded():
    manager = _CaptureManager()
    sink = rm.MeetingServiceSink("r1")
    sink.mgr = manager
    lock_status = SimpleNamespace(
        isLocked=False,
        remainTimeSec=0,
        wrongPwdInputCount=1,
    )

    sink.OnConfDeviceLockStatusNotification(lock_status)

    assert manager.events == [
        (
            "r1",
            {
                "event": "OnConfDeviceLockStatusNotification",
                "lockStatus": {
                    "isLocked": False,
                    "remainTimeSec": 0,
                    "wrongPwdInputCount": 1,
                },
            },
        )
    ]


@pytest.mark.parametrize(
    ("callback", "event_name"),
    [
        ("OnMeetingErrorNotification", "OnMeetingErrorNotification"),
        ("OnMeetingEndedNotification", "OnMeetingEndedNotification"),
    ],
)
def test_meeting_failure_diagnostics_are_forwarded(callback, event_name):
    manager = _CaptureManager()
    sink = rm.MeetingServiceSink("r1")
    sink.mgr = manager
    error_info = SimpleNamespace(
        errorCode=300,
        errorInfo="The meeting passcode is incorrect.",
        errorTitle="Unable to join",
        errorDescLink="https://support.zoom.us/example",
    )

    getattr(sink, callback)(error_info)

    assert manager.events == [
        (
            "r1",
            {
                "event": event_name,
                "errorInfo": {
                    "errorCode": 300,
                    "errorInfo": "The meeting passcode is incorrect.",
                    "errorTitle": "Unable to join",
                    "errorDescLink": "https://support.zoom.us/example",
                },
            },
        )
    ]
