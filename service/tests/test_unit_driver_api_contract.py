"""REST/WebSocket route parity with the PlaceOS Zoom ZRC driver."""

import pytest

pytestmark = pytest.mark.unit

pytest.importorskip("fastapi")

from fastapi import FastAPI
from fastapi.testclient import TestClient

from _zrc_stub import FakeService

import app as service_app
import room_manager as rm
from controllers import participant


# query fields, JSON body fields; room_id is the common path parameter.
DRIVER_ROUTES = {
    ("GET", "/health"): ((), ()),
    ("GET", "/api/rooms"): ((), ()),
    ("POST", "/api/rooms/{room_id}/pair"): ((), ("activation_code",)),
    ("POST", "/api/rooms/{room_id}/unpair"): ((), ()),
    ("GET", "/api/rooms/{room_id}/status"): ((), ()),
    ("GET", "/api/rooms/{room_id}/pre-meeting/connection-state"): ((), ()),
    ("POST", "/api/rooms/{room_id}/pre-meeting/wake-up"): ((), ()),
    ("GET", "/api/rooms/{room_id}/meeting/status"): ((), ()),
    ("POST", "/api/rooms/{room_id}/meeting/start_instant"): ((), ()),
    ("POST", "/api/rooms/{room_id}/meeting/join"): (
        (),
        ("meeting_number", "password", "bring_share"),
    ),
    ("POST", "/api/rooms/{room_id}/meeting/join-url"): (("url",), ()),
    ("POST", "/api/rooms/{room_id}/meeting/password/send"): (
        ("password",),
        (),
    ),
    ("POST", "/api/rooms/{room_id}/meeting/start"): (
        (),
        (
            "meeting_number",
            "meeting_name",
            "host_name",
            "start_time",
            "end_time",
            "bring_share",
        ),
    ),
    ("POST", "/api/rooms/{room_id}/meeting/exit"): ((), ()),
    ("POST", "/api/rooms/{room_id}/meeting/cancel-waiting-host"): ((), ()),
    ("GET", "/api/rooms/{room_id}/meetings/list"): (("timeout",), ()),
    ("POST", "/api/rooms/{room_id}/meeting/reminder/confirm-reminder"): (
        (),
        ("is_agree", "notification_type"),
    ),
    ("POST", "/api/rooms/{room_id}/meeting/reminder/confirm-custom-reminder"): (
        (),
        ("is_agree", "notification_type"),
    ),
    ("POST", "/api/rooms/{room_id}/meeting/reminder/confirm-consent"): (
        (),
        ("is_agree", "consent_type", "consent_id"),
    ),
    ("POST", "/api/rooms/{room_id}/meeting/reminder/confirm-combined-consent"): (
        (),
        ("is_agree", "notification_type"),
    ),
    (
        "POST",
        "/api/rooms/{room_id}/meeting/reminder/agree-consolidated-customized-consent",
    ): ((), ("is_agree",)),
    ("POST", "/api/rooms/{room_id}/meeting/reminder/handle-privacy"): (
        (),
        ("privacy_alert_action", "privacy_alert_type"),
    ),
    ("POST", "/api/rooms/{room_id}/meeting/reminder/continue-on-inactivity"): (
        (),
        (),
    ),
    ("POST", "/api/rooms/{room_id}/recording/respond-to-request"): (
        (),
        ("agree", "is_persist"),
    ),
    ("GET", "/api/rooms/{room_id}/recording/disclaimer-needed"): ((), ()),
    ("POST", "/api/rooms/{room_id}/recording/prompt-disclaimer"): ((), ()),
    ("POST", "/api/rooms/{room_id}/recording/cloud/start"): ((), ()),
    ("POST", "/api/rooms/{room_id}/recording/notification-email"): (
        (),
        ("email",),
    ),
    ("POST", "/api/rooms/{room_id}/recording/cloud/stop"): ((), ()),
    ("POST", "/api/rooms/{room_id}/recording/cloud/pause"): ((), ()),
    ("POST", "/api/rooms/{room_id}/recording/cloud/resume"): ((), ()),
    ("POST", "/api/rooms/{room_id}/ai-companion/turn-on"): (
        ("features",),
        (),
    ),
    ("POST", "/api/rooms/{room_id}/ai-companion/turn-off"): (
        ("features", "delete_assets"),
        (),
    ),
    ("POST", "/api/rooms/{room_id}/ai-companion/respond-to-turn-on"): (
        ("agree",),
        (),
    ),
    ("POST", "/api/rooms/{room_id}/ai-companion/respond-to-turn-off"): (
        ("agree", "delete_assets"),
        (),
    ),
    ("POST", "/api/rooms/{room_id}/ai-companion/confirm-status-when-join"): (
        ("agree",),
        (),
    ),
    ("POST", "/api/rooms/{room_id}/audio/mute"): ((), ()),
    ("POST", "/api/rooms/{room_id}/audio/unmute"): ((), ()),
    ("POST", "/api/rooms/{room_id}/audio/answer-unmute-request"): (
        ("accepted",),
        (),
    ),
    ("POST", "/api/rooms/{room_id}/video/mute"): ((), ()),
    ("POST", "/api/rooms/{room_id}/video/unmute"): ((), ()),
    ("POST", "/api/rooms/{room_id}/video/answer-unmute-request"): (
        ("accepted",),
        (),
    ),
    ("GET", "/api/rooms/{room_id}/settings/volume/speaker"): ((), ()),
    ("POST", "/api/rooms/{room_id}/settings/volume/speaker"): (
        (),
        ("volume",),
    ),
    ("GET", "/api/rooms/{room_id}/settings/volume/microphone"): ((), ()),
    ("POST", "/api/rooms/{room_id}/settings/volume/microphone"): (
        (),
        ("volume",),
    ),
    ("GET", "/api/rooms/{room_id}/participants/"): (("session",), ()),
    ("GET", "/api/rooms/{room_id}/participants/silent-mode"): ((), ()),
    ("DELETE", "/api/rooms/{room_id}/participants/{user_id}"): ((), ()),
    ("POST", "/api/rooms/{room_id}/participants/expel-multiple"): (
        (),
        ("user_ids",),
    ),
    ("POST", "/api/rooms/{room_id}/participants/waiting-room/admit"): (
        (),
        ("user_ids",),
    ),
    ("POST", "/api/rooms/{room_id}/participants/waiting-room/admit-all"): ((), ()),
}


def _leaf_routes(routes):
    for route in routes:
        original = getattr(route, "original_router", None)
        if original is not None:
            yield from _leaf_routes(original.routes)
        else:
            yield route


def _body_fields(route):
    fields = []
    for param in route.dependant.body_params:
        annotation = param.field_info.annotation
        model_fields = getattr(annotation, "model_fields", None)
        if model_fields:
            fields.extend(model_fields)
        else:
            fields.append(param.name)
    return tuple(fields)


def test_all_driver_rest_calls_match_route_and_parameter_locations():
    actual = {}
    for route in _leaf_routes(service_app.app.routes):
        path = getattr(route, "path", None)
        for method in getattr(route, "methods", None) or ():
            key = (method, path)
            if key in DRIVER_ROUTES:
                actual[key] = (
                    tuple(param.name for param in route.dependant.query_params),
                    _body_fields(route),
                )

    assert actual == DRIVER_ROUTES


def _participant_test_client():
    mgr = rm.RoomManager()
    mgr.sdk = FakeService("sdk")
    room_service = mgr.create_room_service("r1")
    helper = room_service.GetMeetingService().GetParticipantHelper()

    app = FastAPI()
    app.include_router(participant.router)
    participant.get_room_manager = lambda: mgr
    return helper, TestClient(app)


def test_waiting_room_deny_maps_to_sdk_expel():
    """Waiting-room DENY has no dedicated SDK API; the driver denies via expel.

    The ZRC SDK's IWaitingRoomHelper only offers admit-direction operations, so
    the deny contract is: DELETE /participants/{user_id} -> ExpelUser(userID)
    and POST /participants/expel-multiple -> ExpelUsers(userIDs), using the
    userIDs reported for silent-mode (waiting room) participants.
    """
    helper, client = _participant_test_client()
    calls = []
    helper.ExpelUser = lambda user_id: calls.append(("expel", user_id)) or 0
    helper.ExpelUsers = (
        lambda user_ids: calls.append(("expel_multiple", tuple(user_ids))) or 0
    )

    with client:
        single = client.delete("/api/rooms/r1/participants/16778240")
        multiple = client.post(
            "/api/rooms/r1/participants/expel-multiple",
            json={"user_ids": [16778240, 16779264]},
        )

    assert single.status_code == 200, single.text
    assert single.json() == {
        "room_id": "r1",
        "user_id": 16778240,
        "result": 0,
        "success": True,
    }
    assert multiple.status_code == 200, multiple.text
    assert multiple.json() == {
        "room_id": "r1",
        "user_ids": [16778240, 16779264],
        "count": 2,
        "result": 0,
        "success": True,
    }
    assert calls == [
        ("expel", 16778240),
        ("expel_multiple", (16778240, 16779264)),
    ]


def test_waiting_room_admit_maps_to_sdk_put_users_into_meeting():
    """Admit routes drive IWaitingRoomHelper's admit-direction operations."""
    helper, client = _participant_test_client()
    del helper  # admit uses the waiting-room helper, not the participant helper
    mgr = participant.get_room_manager()
    wr_helper = mgr.get_room_service("r1").GetMeetingService().GetWaitingRoomHelper()
    calls = []
    wr_helper.PutUsersIntoMeeting = (
        lambda user_ids: calls.append(("admit", tuple(user_ids))) or 0
    )
    wr_helper.PutAllUsersIntoMeeting = lambda: calls.append(("admit_all",)) or 0

    with client:
        admit = client.post(
            "/api/rooms/r1/participants/waiting-room/admit",
            json={"user_ids": [16778240, 16779264]},
        )
        admit_all = client.post("/api/rooms/r1/participants/waiting-room/admit-all")

    assert admit.status_code == 200, admit.text
    assert admit.json() == {
        "room_id": "r1",
        "user_ids": [16778240, 16779264],
        "count": 2,
        "result": 0,
        "success": True,
    }
    assert admit_all.status_code == 200, admit_all.text
    assert admit_all.json() == {
        "room_id": "r1",
        "result": 0,
        "success": True,
    }
    assert calls == [
        ("admit", (16778240, 16779264)),
        ("admit_all",),
    ]


def test_expel_multiple_sdk_failure_is_200_success_false():
    """A nonzero ExpelUsers ack surfaces as HTTP 200 with success:false."""
    helper, client = _participant_test_client()
    helper.ExpelUsers = lambda user_ids: 7  # ZRCSDKERR_INTERNAL_ERROR

    with client:
        resp = client.post(
            "/api/rooms/r1/participants/expel-multiple",
            json={"user_ids": [16778240]},
        )

    assert resp.status_code == 200, resp.text
    assert resp.json()["result"] == 7
    assert resp.json()["success"] is False


def test_silent_mode_listing_flags_waiting_room_guests():
    """GET /participants/silent-mode exposes deniable waiting-room guests."""
    helper, client = _participant_test_client()

    class Guest:
        userID = 16778240
        userName = "Waiting Guest"
        isInSilentMode = True

    helper.GetParticipantsInSilentMode = lambda: (0, [Guest()])

    with client:
        response = client.get("/api/rooms/r1/participants/silent-mode")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is True
    assert body["count"] == 1
    assert body["participants"][0]["user_id"] == 16778240
    assert body["participants"][0]["is_in_waiting_room"] is True


def test_driver_event_websocket_route_exists():
    routes = list(_leaf_routes(service_app.app.routes))
    assert any(
        getattr(route, "path", None) == "/api/rooms/{room_id}/events"
        and "WebSocket" in type(route).__name__
        for route in routes
    )
