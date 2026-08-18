"""Unit coverage for AI Companion prompt-response routes (fake SDK)."""

import pytest

pytestmark = pytest.mark.unit

pytest.importorskip("fastapi")
from fastapi import FastAPI
from fastapi.testclient import TestClient

from _zrc_stub import FakeService

import room_manager as rm
from controllers import meeting_controls


def _client_and_calls(results=(0, 0, 0)):
    mgr = rm.RoomManager()
    mgr.sdk = FakeService("sdk")
    room_service = mgr.create_room_service("r1")
    control_helper = room_service.GetMeetingService().GetMeetingControlHelper()
    calls = []

    control_helper.RespondToTurnOnAICompanion = (
        lambda agree: calls.append(("respond_on", agree)) or results[0]
    )
    control_helper.RespondToTurnOffAICompanion = (
        lambda agree, delete_assets: calls.append(
            ("respond_off", agree, delete_assets)
        ) or results[1]
    )
    control_helper.ConfirmAICompanionStatusWhenJoin = (
        lambda agree: calls.append(("confirm_join", agree)) or results[2]
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
    assert turn_on.json()["success"] is True
    assert turn_off.json()["success"] is True
    assert confirm.json()["success"] is True
    assert calls == [
        ("respond_on", False),
        ("respond_off", True, True),
        ("confirm_join", False),
    ]


@pytest.mark.parametrize(
    ("path", "params", "results", "message"),
    [
        (
            "/api/rooms/r1/ai-companion/respond-to-turn-on",
            {"agree": False},
            (705, 0, 0),
            "Failed to respond to AI Companion turn-on request",
        ),
        (
            "/api/rooms/r1/ai-companion/respond-to-turn-off",
            {"agree": True, "delete_assets": True},
            (0, 705, 0),
            "Failed to respond to AI Companion turn-off request",
        ),
        (
            "/api/rooms/r1/ai-companion/confirm-status-when-join",
            {"agree": False},
            (0, 0, 705),
            "Failed to confirm AI Companion status",
        ),
    ],
)
def test_ai_companion_prompt_routes_return_structured_sdk_failures(
    path, params, results, message
):
    client, _ = _client_and_calls(results)

    with client:
        response = client.post(path, params=params)

    assert response.status_code == 502, response.text
    assert response.json() == {
        "detail": {
            "message": message,
            "error_code": 705,
            "error_name": "ZRCSDKERR_AIC_NOT_SET_MEETING_SUMMARY_NOTIFY_EMAIL",
        }
    }


def test_ai_companion_prompt_route_has_stable_unknown_error_name():
    client, _ = _client_and_calls((999, 0, 0))

    with client:
        response = client.post(
            "/api/rooms/r1/ai-companion/respond-to-turn-on",
            params={"agree": False},
        )

    assert response.status_code == 502, response.text
    assert response.json()["detail"] == {
        "message": "Failed to respond to AI Companion turn-on request",
        "error_code": 999,
        "error_name": "Unknown(999)",
    }
