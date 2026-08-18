"""Unit coverage for AI Companion prompt-response routes (fake SDK)."""

import pytest

pytestmark = pytest.mark.unit

pytest.importorskip("fastapi")
from fastapi import FastAPI
from fastapi.testclient import TestClient

from _zrc_stub import FakeService

import room_manager as rm
from controllers import meeting_controls


def _client_and_calls():
    mgr = rm.RoomManager()
    mgr.sdk = FakeService("sdk")
    room_service = mgr.create_room_service("r1")
    control_helper = room_service.GetMeetingService().GetMeetingControlHelper()
    calls = []

    control_helper.RespondToTurnOnAICompanion = (
        lambda agree: calls.append(("respond_on", agree)) or 0
    )
    control_helper.RespondToTurnOffAICompanion = (
        lambda agree, delete_assets: calls.append(
            ("respond_off", agree, delete_assets)
        ) or 0
    )
    control_helper.ConfirmAICompanionStatusWhenJoin = (
        lambda agree: calls.append(("confirm_join", agree)) or 0
    )

    app = FastAPI()
    app.include_router(meeting_controls.router)
    meeting_controls.get_room_manager = lambda: mgr
    return TestClient(app), calls


def test_ai_companion_prompt_routes_call_the_matching_sdk_operations():
    client, calls = _client_and_calls()

    with client:
        turn_on = client.post(
            "/api/rooms/r1/ai-companion/respond-to-turn-on",
            params={"agree": False},
        )
        turn_off = client.post(
            "/api/rooms/r1/ai-companion/respond-to-turn-off",
            params={"agree": True, "delete_assets": True},
        )
        confirm = client.post(
            "/api/rooms/r1/ai-companion/confirm-status-when-join",
            params={"agree": False},
        )

    assert turn_on.status_code == 200, turn_on.text
    assert turn_off.status_code == 200, turn_off.text
    assert confirm.status_code == 200, confirm.text
    assert calls == [
        ("respond_on", False),
        ("respond_off", True, True),
        ("confirm_join", False),
    ]

