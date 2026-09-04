"""
Unit test for the unpair endpoint (fake SDK, router exercised in-process): it
must fully clean up the room via RoomManager.remove_room, not just the legacy
sink dicts.
"""
import pytest

pytestmark = pytest.mark.unit

pytest.importorskip("fastapi")
from fastapi import FastAPI
from fastapi.testclient import TestClient

import _zrc_stub
from _zrc_stub import FakeService

import room_manager as rm
from controllers import rooms as rooms_ctrl


def test_unpair_endpoint_purges_all_sink_stores():
    mgr = rm.RoomManager()
    mgr.sdk = FakeService("sdk")
    service = mgr.create_room_service("r1")
    surfaces = [node for node in service.walk() if node.registered]

    app = FastAPI()
    app.include_router(rooms_ctrl.router)
    rooms_ctrl.get_room_manager = lambda: mgr

    with TestClient(app) as client:
        resp = client.post("/api/rooms/r1/unpair")

    assert resp.status_code == 200
    assert resp.json()["unpaired"] is True
    assert "r1" not in mgr.rooms
    stores = {k: v for k, v in vars(mgr).items() if k.endswith("_sinks") and isinstance(v, dict)}
    leaked = [name for name, store in stores.items() if "r1" in store]
    assert not leaked, f"unpair left sinks behind: {leaked}"
    missed = [n._name for n in surfaces if n.deregistered == 0]
    assert not missed, f"unpair never deregistered: {missed}"
