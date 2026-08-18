"""Unit coverage for structured recording SDK failures."""

import pytest

pytestmark = pytest.mark.unit

pytest.importorskip("fastapi")
from fastapi import FastAPI
from fastapi.testclient import TestClient

from _zrc_stub import FakeService

import room_manager as rm
from controllers import recording


def test_duplicate_recording_stop_returns_structured_sdk_error():
    mgr = rm.RoomManager()
    mgr.sdk = FakeService("sdk")
    room_service = mgr.create_room_service("r1")
    helper = room_service.GetMeetingService().GetRecordingHelper()
    helper.StopMeetingCloudRecording = lambda: 10

    app = FastAPI()
    app.include_router(recording.router)
    recording.get_room_manager = lambda: mgr

    with TestClient(app) as client:
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
