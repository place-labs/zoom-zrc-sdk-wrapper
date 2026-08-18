"""Unit coverage for SDK 7.1 participant assignment signatures."""

import pytest

pytestmark = pytest.mark.unit

pytest.importorskip("fastapi")
from fastapi import FastAPI
from fastapi.testclient import TestClient

from _zrc_stub import FakeService

import room_manager as rm
from controllers import participant


def test_assign_host_and_cohost_pass_empty_assets_privilege():
    mgr = rm.RoomManager()
    mgr.sdk = FakeService("sdk")
    room_service = mgr.create_room_service("r1")
    helper = room_service.GetMeetingService().GetParticipantHelper()
    calls = []

    helper.AssignHost = (
        lambda user_id, assets_privilege: calls.append(
            ("host", user_id, assets_privilege)
        )
        or 0
    )
    helper.AssignCohost = (
        lambda user_id, assign, assets_privilege: calls.append(
            ("cohost", user_id, assign, assets_privilege)
        )
        or 0
    )

    app = FastAPI()
    app.include_router(participant.router)
    participant.get_room_manager = lambda: mgr

    with TestClient(app) as client:
        host = client.post(
            "/api/rooms/r1/participants/assign-host", params={"user_id": 42}
        )
        cohost = client.post(
            "/api/rooms/r1/participants/assign-cohost",
            json={"user_id": 43, "assign": True},
        )

    assert host.status_code == 200, host.text
    assert host.json() == {
        "room_id": "r1",
        "user_id": 42,
        "result": 0,
        "success": True,
    }
    assert cohost.status_code == 200, cohost.text
    assert cohost.json() == {
        "room_id": "r1",
        "user_id": 43,
        "assign": True,
        "result": 0,
        "success": True,
    }
    assert calls == [
        ("host", 42, None),
        ("cohost", 43, True, None),
    ]
