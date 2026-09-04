"""Unit coverage for host audio/video prompt-response routes."""

import pytest

pytestmark = pytest.mark.unit

pytest.importorskip("fastapi")
from fastapi import FastAPI
from fastapi.testclient import TestClient

from _zrc_stub import FakeService

import room_manager as rm
from controllers import meeting_video, meetings


def _client_and_calls(results=(0, 0)):
    mgr = rm.RoomManager()
    mgr.sdk = FakeService("sdk")
    room_service = mgr.create_room_service("r1")
    meeting_service = room_service.GetMeetingService()
    calls = []

    meeting_service.GetMeetingAudioHelper().AnswerUnmuteAudioByHostRequest = (
        lambda accepted: calls.append(("audio", accepted)) or results[0]
    )
    meeting_service.GetMeetingVideoHelper().AnswerHostRequestUnmuteVideo = (
        lambda accepted: calls.append(("video", accepted)) or results[1]
    )

    app = FastAPI()
    app.include_router(meetings.router)
    app.include_router(meeting_video.router)
    meetings.get_room_manager = lambda: mgr
    meeting_video.get_room_manager = lambda: mgr
    return TestClient(app), calls


def test_host_prompt_response_routes_forward_accept_and_deny_to_sdk():
    client, calls = _client_and_calls()

    with client:
        audio_accept = client.post(
            "/api/rooms/r1/audio/answer-unmute-request",
            params={"accepted": True},
        )
        audio_deny = client.post(
            "/api/rooms/r1/audio/answer-unmute-request",
            params={"accepted": False},
        )
        video_accept = client.post(
            "/api/rooms/r1/video/answer-unmute-request",
            params={"accepted": True},
        )
        video_deny = client.post(
            "/api/rooms/r1/video/answer-unmute-request",
            params={"accepted": False},
        )

    for response in (audio_accept, audio_deny, video_accept, video_deny):
        assert response.status_code == 200, response.text
        assert response.json()["success"] is True
    assert calls == [
        ("audio", True),
        ("audio", False),
        ("video", True),
        ("video", False),
    ]


def test_host_prompt_response_routes_expose_sdk_failure_in_body():
    client, calls = _client_and_calls((14, 14))

    with client:
        audio = client.post(
            "/api/rooms/r1/audio/answer-unmute-request",
            params={"accepted": False},
        )
        video = client.post(
            "/api/rooms/r1/video/answer-unmute-request",
            params={"accepted": False},
        )

    assert audio.status_code == 200, audio.text
    assert video.status_code == 200, video.text
    assert audio.json()["result"] == 14
    assert video.json()["result"] == 14
    assert audio.json()["success"] is False
    assert video.json()["success"] is False
    assert calls == [("audio", False), ("video", False)]
