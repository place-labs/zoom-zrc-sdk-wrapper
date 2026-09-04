"""Unit coverage for structured recording SDK failures."""

import pytest

pytestmark = pytest.mark.unit

pytest.importorskip("fastapi")
from fastapi import FastAPI
from fastapi.testclient import TestClient

from _zrc_stub import FakeService

import room_manager as rm
from controllers import recording


def _client_with_recording_helper():
    mgr = rm.RoomManager()
    mgr.sdk = FakeService("sdk")
    room_service = mgr.create_room_service("r1")
    helper = room_service.GetMeetingService().GetRecordingHelper()

    app = FastAPI()
    app.include_router(recording.router)
    recording.get_room_manager = lambda: mgr
    return TestClient(app), helper


def test_duplicate_recording_stop_returns_structured_sdk_error():
    client, helper = _client_with_recording_helper()
    helper.StopMeetingCloudRecording = lambda: 10

    with client:
        response = client.post("/api/rooms/r1/recording/cloud/stop")

    assert response.status_code == 500, response.text
    assert response.json() == {
        "detail": {
            "message": "Failed to stop cloud recording",
            "error_code": 10,
            "error_name": "ZRCSDKERR_ALREADY_IN_THIS_STATE",
        }
    }


def test_recording_email_precondition_error_has_stable_name():
    assert recording.zrcsdk_error_name(352) == (
        "ZRCSDKERR_NOT_SET_RECORDING_NOTIFICATION_EMAIL"
    )


@pytest.mark.parametrize(
    ("result", "error_name"),
    [
        (16, "ZRCSDKERR_REQUEST_HAS_BEEN_RESPONSED"),
        (999, "Unknown(999)"),
    ],
)
def test_recording_request_failure_is_structured(result, error_name):
    client, helper = _client_with_recording_helper()
    calls = []
    helper.ResponseToRecordingRequest = (
        lambda agree, persist: calls.append((agree, persist)) or result
    )

    with client:
        response = client.post(
            "/api/rooms/r1/recording/respond-to-request",
            json={"agree": False, "is_persist": False},
        )

    assert response.status_code == 502, response.text
    assert response.json() == {
        "detail": {
            "message": "Failed to respond to recording request",
            "error_code": result,
            "error_name": error_name,
        }
    }
    assert calls == [(False, False)]


def test_recording_notification_email_failure_is_structured():
    client, helper = _client_with_recording_helper()
    emails = []
    helper.SetMeetingRecordingNotificationEmail = (
        lambda email: emails.append(email) or 221
    )

    with client:
        response = client.post(
            "/api/rooms/r1/recording/notification-email",
            json={"email": "reserved@example.com"},
        )

    assert response.status_code == 500, response.text
    assert response.json() == {
        "detail": {
            "message": "Failed to set notification email",
            "error_code": 221,
            "error_name": "ZRCSDKERR_NOT_IN_MEETING",
        }
    }
    assert emails == ["reserved@example.com"]
