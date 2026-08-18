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
