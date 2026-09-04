"""
Unit coverage for the waiting-room admission routes.

The SDK's IWaitingRoomHelper exposes PutUsersIntoMeeting (admit),
PutUsersIntoWaitingRoom (send back / hold), and PutAllUsersIntoMeeting
(admit all) — all bound in zrc_bindings.cpp and all returning a synchronous
ZRCSDKError command ack (actual roster convergence arrives via push events).
These tests pin the REST contract the PlaceOS driver implements against.
"""
import pytest

pytestmark = pytest.mark.unit

pytest.importorskip("fastapi")
from fastapi import FastAPI
from fastapi.testclient import TestClient

from _zrc_stub import FakeService

import room_manager as rm
from controllers import participant


def _make_app():
    mgr = rm.RoomManager()
    mgr.sdk = FakeService("sdk")
    room_service = mgr.create_room_service("r1")
    helper = room_service.GetMeetingService().GetWaitingRoomHelper()

    app = FastAPI()
    app.include_router(participant.router)
    participant.get_room_manager = lambda: mgr
    return app, helper


def test_admit_plumbs_user_ids_to_put_users_into_meeting():
    app, helper = _make_app()
    calls = []
    helper.PutUsersIntoMeeting = lambda user_ids: calls.append(list(user_ids)) or 0

    with TestClient(app) as client:
        single = client.post(
            "/api/rooms/r1/participants/waiting-room/admit",
            json={"user_ids": [16778240]},
        )
        multi = client.post(
            "/api/rooms/r1/participants/waiting-room/admit",
            json={"user_ids": [1, 2, 3]},
        )

    assert single.status_code == 200, single.text
    assert single.json() == {
        "room_id": "r1",
        "user_ids": [16778240],
        "count": 1,
        "result": 0,
        "success": True,
    }
    assert multi.status_code == 200, multi.text
    assert multi.json()["user_ids"] == [1, 2, 3]
    assert multi.json()["count"] == 3
    assert calls == [[16778240], [1, 2, 3]]


def test_hold_plumbs_user_ids_to_put_users_into_waiting_room():
    app, helper = _make_app()
    calls = []
    helper.PutUsersIntoWaitingRoom = lambda user_ids: calls.append(list(user_ids)) or 0

    with TestClient(app) as client:
        resp = client.post(
            "/api/rooms/r1/participants/waiting-room/hold",
            json={"user_ids": [7, 8]},
        )

    assert resp.status_code == 200, resp.text
    assert resp.json() == {
        "room_id": "r1",
        "user_ids": [7, 8],
        "count": 2,
        "result": 0,
        "success": True,
    }
    assert calls == [[7, 8]]


def test_admit_all_calls_put_all_users_into_meeting():
    app, helper = _make_app()
    calls = []
    helper.PutAllUsersIntoMeeting = lambda: calls.append("all") or 0

    with TestClient(app) as client:
        resp = client.post("/api/rooms/r1/participants/waiting-room/admit-all")

    assert resp.status_code == 200, resp.text
    assert resp.json() == {"room_id": "r1", "result": 0, "success": True}
    assert calls == ["all"]


def test_sdk_failure_ack_is_reported_not_fabricated():
    app, helper = _make_app()
    helper.PutUsersIntoMeeting = lambda user_ids: 7  # ZRCSDKERR_INTERNAL_ERROR

    with TestClient(app) as client:
        resp = client.post(
            "/api/rooms/r1/participants/waiting-room/admit",
            json={"user_ids": [1]},
        )

    assert resp.status_code == 200, resp.text
    assert resp.json()["result"] == 7
    assert resp.json()["success"] is False


def test_missing_or_invalid_body_is_4xx_not_5xx():
    app, _ = _make_app()

    with TestClient(app) as client:
        missing_admit = client.post("/api/rooms/r1/participants/waiting-room/admit")
        missing_hold = client.post("/api/rooms/r1/participants/waiting-room/hold")
        bad_type = client.post(
            "/api/rooms/r1/participants/waiting-room/admit",
            json={"user_ids": "not-a-list"},
        )
        wrong_key = client.post(
            "/api/rooms/r1/participants/waiting-room/hold",
            json={"users": [1]},
        )

    assert missing_admit.status_code == 422, missing_admit.text
    assert missing_hold.status_code == 422, missing_hold.text
    assert bad_type.status_code == 422, bad_type.text
    assert wrong_key.status_code == 422, wrong_key.text


def test_unknown_room_is_404():
    app, _ = _make_app()

    with TestClient(app) as client:
        resp = client.post(
            "/api/rooms/nope/participants/waiting-room/admit",
            json={"user_ids": [1]},
        )

    # Pin the room guard's body: FastAPI's unmatched-route 404 says "Not Found",
    # so status alone would pass vacuously without the route ever existing.
    assert resp.status_code == 404, resp.text
    assert resp.json() == {"detail": "Room nope not found"}


def test_helper_unavailable_is_500():
    app, _ = _make_app()
    mgr = participant.get_room_manager()
    meeting_service = mgr.get_room_service("r1").GetMeetingService()
    meeting_service.GetWaitingRoomHelper = lambda: None

    with TestClient(app) as client:
        resp = client.post(
            "/api/rooms/r1/participants/waiting-room/admit",
            json={"user_ids": [1]},
        )

    assert resp.status_code == 500, resp.text
    assert resp.json() == {"detail": "Waiting room helper not available"}
