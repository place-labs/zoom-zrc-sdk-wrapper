"""Unit coverage for the strict mute/unmute verb contract."""

import pytest

pytestmark = pytest.mark.unit

pytest.importorskip("fastapi")
from fastapi import FastAPI
from fastapi.testclient import TestClient

from _zrc_stub import FakeService

import room_manager as rm
from controllers import meetings


def _client_and_calls():
    mgr = rm.RoomManager()
    mgr.sdk = FakeService("sdk")
    room_service = mgr.create_room_service("r1")
    meeting_service = room_service.GetMeetingService()
    calls = []

    meeting_service.GetMeetingAudioHelper().UpdateMyAudioStatus = (
        lambda muted: calls.append(("audio", muted)) or 0
    )
    meeting_service.GetMeetingVideoHelper().UpdateMyVideo = (
        lambda stopped: calls.append(("video", stopped)) or 0
    )

    app = FastAPI()
    app.include_router(meetings.router)
    meetings.get_room_manager = lambda: mgr
    return TestClient(app), calls


def test_mute_and_unmute_verb_endpoints_set_explicit_state():
    client, calls = _client_and_calls()

    with client:
        assert client.post("/api/rooms/r1/audio/mute").status_code == 200
        assert client.post("/api/rooms/r1/audio/unmute").status_code == 200
        assert client.post("/api/rooms/r1/video/mute").status_code == 200
        assert client.post("/api/rooms/r1/video/unmute").status_code == 200

    assert calls == [
        ("audio", True),
        ("audio", False),
        ("video", True),
        ("video", False),
    ]


def test_legacy_mute_queries_are_rejected_instead_of_silently_ignored():
    client, calls = _client_and_calls()

    with client:
        audio = client.post("/api/rooms/r1/audio/mute", params={"mute": False})
        video = client.post(
            "/api/rooms/r1/video/mute", params={"mute": False}
        )

    assert audio.status_code == 422, audio.text
    assert video.status_code == 422, video.text
    assert calls == []


def test_legacy_stop_query_is_not_a_supported_video_alias():
    client, calls = _client_and_calls()

    with client:
        response = client.post(
            "/api/rooms/r1/video/mute",
            params={"stop": False},
        )

    assert response.status_code == 422, response.text
    assert calls == []
