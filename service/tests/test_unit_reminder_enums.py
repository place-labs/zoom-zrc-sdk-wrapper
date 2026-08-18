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


def test_resolve_enum_numeric_string_coerces():
    """Pydantic v2 smart-union keeps a JSON '"3"' as str on int|str fields; on
    plain-int fields (pre-widening) it was coerced and worked. Restore that:
    digit strings resolve like their int (PRODUCTION-REVIEW.md 3.6)."""
    assert mr._resolve_enum(_Reminder, "3") is _Reminder.MeetingReminderTypeArchiving


def test_resolve_enum_bad_name_is_422():
    """Bad input is the CLIENT's error: 422 listing the allowed members, not an
    AttributeError that the blanket handler turns into an opaque 500."""
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as ei:
        mr._resolve_enum(_Reminder, "NoSuchMember")
    assert ei.value.status_code == 422
    assert "MeetingReminderTypeArchiving" in str(ei.value.detail)


def test_resolve_enum_bad_int_is_422():
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as ei:
        mr._resolve_enum(_Reminder, 999)
    assert ei.value.status_code == 422


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


def test_confirm_reminder_accepts_numeric_string(monkeypatch):
    """'"3"' (the enum's int as a JSON string) worked pre-widening via pydantic
    coercion — it must keep working, not 500."""
    client = _client(monkeypatch)
    r = client.post("/api/rooms/r1/meeting/reminder/confirm-reminder",
                    json={"is_agree": True, "notification_type": "3"})
    assert r.status_code == 200, r.text


def test_confirm_reminder_unknown_name_is_422_not_500(monkeypatch):
    client = _client(monkeypatch)
    r = client.post("/api/rooms/r1/meeting/reminder/confirm-reminder",
                    json={"is_agree": True, "notification_type": "BogusName"})
    assert r.status_code == 422, f"expected 422 for bad input, got {r.status_code}: {r.text}"


def test_customized_reminder_accepts_open_integer_and_known_name(monkeypatch):
    """customizedDisclaimerType is an open int32 compatibility field."""
    client = _client(monkeypatch)
    for val in (7, "7", "MeetingReminderTypeArchiving"):
        r = client.post(
            "/api/rooms/r1/meeting/reminder/confirm-custom-reminder",
            json={"is_agree": True, "notification_type": val},
        )
        assert r.status_code == 200, f"customized type {val!r} rejected: {r.text}"


def test_customized_reminder_rejects_unknown_non_numeric_name(monkeypatch):
    client = _client(monkeypatch)
    r = client.post(
        "/api/rooms/r1/meeting/reminder/confirm-custom-reminder",
        json={"is_agree": True, "notification_type": "NoSuchType"},
    )
    assert r.status_code == 422, r.text


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


# ----- combined consent: an OPEN int64, not an enum (PRODUCTION-REVIEW.md 3.7) -----

def test_combined_consent_echoes_int_and_digit_string(monkeypatch):
    """The SDK signature is ConfirmCombinedConsent(bool, int64_t) and the event
    carries CombinedConsent.type as a plain int — any echoed int must pass
    through, NOT be validated against MeetingReminderType (the wrong surface's
    table, which rejected legitimate values like 7)."""
    client = _client(monkeypatch)
    for val in (7, "7"):
        r = client.post("/api/rooms/r1/meeting/reminder/confirm-combined-consent",
                        json={"is_agree": True, "notification_type": val})
        assert r.status_code == 200, f"echoed open-int {val!r} rejected: {r.text}"


def test_combined_consent_non_numeric_is_422(monkeypatch):
    client = _client(monkeypatch)
    r = client.post("/api/rooms/r1/meeting/reminder/confirm-combined-consent",
                    json={"is_agree": True, "notification_type": "SomeName"})
    assert r.status_code == 422, r.text


# ----- SDK 7.1 consolidated customized consent -----

@pytest.mark.parametrize("is_agree", [False, True])
def test_consolidated_customized_consent_calls_sdk(monkeypatch, is_agree):
    client = _client(monkeypatch)
    mgr = mr.get_room_manager()
    helper = (
        mgr.get_room_service("r1")
        .GetMeetingService()
        .GetMeetingReminderHelper()
    )
    calls = []
    helper.AgreeConsolidatedCustomizedConsent = (
        lambda agree: calls.append(agree) or 0
    )

    r = client.post(
        "/api/rooms/r1/meeting/reminder/agree-consolidated-customized-consent",
        json={"is_agree": is_agree},
    )

    assert r.status_code == 200, r.text
    assert r.json() == {
        "room_id": "r1",
        "is_agree": is_agree,
        "result": 0,
        "success": True,
    }
    assert calls == [is_agree]


def test_consolidated_customized_consent_preserves_sdk_failure(monkeypatch):
    client = _client(monkeypatch)
    mgr = mr.get_room_manager()
    helper = (
        mgr.get_room_service("r1")
        .GetMeetingService()
        .GetMeetingReminderHelper()
    )
    helper.AgreeConsolidatedCustomizedConsent = lambda agree: 705

    r = client.post(
        "/api/rooms/r1/meeting/reminder/agree-consolidated-customized-consent",
        json={"is_agree": True},
    )

    assert r.status_code == 200, r.text
    assert r.json() == {
        "room_id": "r1",
        "is_agree": True,
        "result": 705,
        "success": False,
    }
