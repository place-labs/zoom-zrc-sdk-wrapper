"""
Unit tests for the reminder/consent enum-resolution contract (fake SDK).

The event stream emits SDK enums by NAME; the driver echoes the name back on the
REST response path. These handlers must therefore accept either an int value or
an enum member name and resolve it against the wrapper's own bound enums —
closing the loop so nothing outside the wrapper needs the integer mapping.
"""
import enum

import pytest

pytest.importorskip("fastapi")
from fastapi import FastAPI
from fastapi.testclient import TestClient

import _zrc_stub
from _zrc_stub import FakeService

import room_manager as rm
from controllers import meeting_reminder as mr

pytestmark = pytest.mark.unit


class _Reminder(enum.IntEnum):
    MeetingReminderTypeDisclaimer = 0
    MeetingReminderTypeArchiving = 3


class _Consent(enum.IntEnum):
    CONSENT_TYPE_NONE = 0
    CONSENT_TYPE_ARCHIVING = 3


# ----- _resolve_enum: the core logic -----

def test_resolve_enum_by_int():
    assert mr._resolve_enum(_Reminder, 3) is _Reminder.MeetingReminderTypeArchiving


def test_resolve_enum_by_name():
    assert mr._resolve_enum(_Reminder, "MeetingReminderTypeArchiving") is _Reminder.MeetingReminderTypeArchiving


def test_resolve_enum_bad_name_raises():
    with pytest.raises((AttributeError, ValueError, KeyError)):
        mr._resolve_enum(_Reminder, "NoSuchMember")


def test_resolve_enum_bad_int_raises():
    with pytest.raises(ValueError):
        mr._resolve_enum(_Reminder, 999)


# ----- request models accept both int and name -----

def test_models_accept_name_and_int():
    assert mr.NotificationRequest(notification_type="MeetingReminderTypeArchiving").notification_type == "MeetingReminderTypeArchiving"
    assert mr.NotificationRequest(notification_type=3).notification_type == 3
    assert mr.ConfirmConsentRequest(consent_type="CONSENT_TYPE_ARCHIVING").consent_type == "CONSENT_TYPE_ARCHIVING"
    assert mr.PrivacyRequest(privacy_alert_action="A", privacy_alert_type=1)


# ----- end-to-end through the router (fake SDK) -----

def _client(monkeypatch):
    monkeypatch.setattr(_zrc_stub.zrc_sdk, "MeetingReminderType", _Reminder, raising=False)
    monkeypatch.setattr(_zrc_stub.zrc_sdk, "CustomizedMeetingReminderType", _Reminder, raising=False)
    monkeypatch.setattr(_zrc_stub.zrc_sdk, "ConsentType", _Consent, raising=False)
    monkeypatch.setattr(_zrc_stub.zrc_sdk, "PrivacyAlertAction", _Reminder, raising=False)
    monkeypatch.setattr(_zrc_stub.zrc_sdk, "PrivacyAlertType", _Reminder, raising=False)
    mgr = rm.RoomManager()
    mgr.sdk = FakeService("sdk")
    mgr.create_room_service("r1")
    app = FastAPI()
    app.include_router(mr.router)
    mr.get_room_manager = lambda: mgr
    return TestClient(app)


def test_confirm_reminder_accepts_enum_name(monkeypatch):
    client = _client(monkeypatch)
    r = client.post("/api/rooms/r1/meeting/reminder/confirm-reminder",
                    json={"is_agree": True, "notification_type": "MeetingReminderTypeArchiving"})
    assert r.status_code == 200, r.text
    assert r.json()["success"] is True


def test_confirm_reminder_still_accepts_int(monkeypatch):
    client = _client(monkeypatch)
    r = client.post("/api/rooms/r1/meeting/reminder/confirm-reminder",
                    json={"is_agree": True, "notification_type": 3})
    assert r.status_code == 200, r.text


def test_confirm_consent_accepts_enum_name(monkeypatch):
    client = _client(monkeypatch)
    r = client.post("/api/rooms/r1/meeting/reminder/confirm-consent",
                    json={"is_agree": True, "consent_type": "CONSENT_TYPE_ARCHIVING", "consent_id": "x"})
    assert r.status_code == 200, r.text


def test_handle_privacy_alert_does_not_crash(monkeypatch):
    """Regression: the handler read request.notification_type, absent on
    PrivacyRequest, so it 500'd on every call."""
    client = _client(monkeypatch)
    r = client.post("/api/rooms/r1/meeting/reminder/handle-privacy",
                    json={"privacy_alert_action": "MeetingReminderTypeArchiving",
                          "privacy_alert_type": 3})
    assert r.status_code == 200, r.text
