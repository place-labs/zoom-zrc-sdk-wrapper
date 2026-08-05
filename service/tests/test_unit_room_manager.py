"""
Unit tests for RoomManager connection-lifecycle logic (fake SDK, no server).

Covers:
  - re-pairing a remotely-unpaired room re-enables auto-reconnect
  - remove_room() purges every sink store and deregisters every SDK surface
  - WebSocket subscribers are told when events were dropped (queue overflow)
"""
import asyncio

import pytest

import _zrc_stub
from _zrc_stub import FakeService

import room_manager as rm

pytestmark = pytest.mark.unit


def make_mgr():
    mgr = rm.RoomManager()
    mgr.sdk = FakeService("sdk")
    return mgr


def sink_stores(mgr):
    """All per-room sink registries on the manager (any dict attr named *_sinks)."""
    return {k: v for k, v in vars(mgr).items() if k.endswith("_sinks") and isinstance(v, dict)}


# ----- Finding 4: unpaired flag must clear on re-pair of a cached room -----

def test_repair_of_cached_room_clears_unpaired_flag():
    mgr = make_mgr()
    mgr.create_room_service("r1")
    # Remote unpair: OnRoomUnpairedReason marks the room but it stays in mgr.rooms.
    mgr.mark_unpaired("r1")
    assert "r1" in mgr._unpaired_rooms
    # Operator re-pairs; create_room_service returns the cached service.
    mgr.create_room_service("r1")
    assert "r1" not in mgr._unpaired_rooms, (
        "re-pairing a cached room must re-enable auto-reconnect"
    )


# ----- Finding 5: full cleanup of a removed room -----

def test_registration_populates_every_sink_store():
    """Sanity for the tests below: pairing fills all the per-room stores."""
    mgr = make_mgr()
    mgr.create_room_service("r1")
    stores = sink_stores(mgr)
    populated = [name for name, store in stores.items() if "r1" in store]
    assert len(populated) == len(stores), (
        f"stores not populated by registration: {sorted(set(stores) - set(populated))}"
    )


def test_remove_room_purges_every_sink_store():
    mgr = make_mgr()
    mgr.create_room_service("r1")
    mgr._unpaired_rooms.add("r1")

    mgr.remove_room("r1")

    assert "r1" not in mgr.rooms
    assert "r1" not in mgr._unpaired_rooms
    leaked = [name for name, store in sink_stores(mgr).items() if "r1" in store]
    assert not leaked, f"sink stores still holding the removed room: {leaked}"


def test_remove_room_deregisters_every_registered_surface():
    mgr = make_mgr()
    service = mgr.create_room_service("r1")
    surfaces = [node for node in service.walk() if node.registered]
    assert len(surfaces) >= 20  # room + premeeting + meeting + helpers ...

    mgr.remove_room("r1")

    missed = [n._name for n in surfaces if n.deregistered == 0]
    assert not missed, f"surfaces never deregistered: {missed}"


def test_shutdown_purges_every_sink_store():
    mgr = make_mgr()
    service = mgr.create_room_service("r1")
    surfaces = [node for node in service.walk() if node.registered]

    mgr.shutdown()

    leaked = [name for name, store in sink_stores(mgr).items() if "r1" in store]
    assert not leaked, f"sink stores still populated after shutdown: {leaked}"
    missed = [n._name for n in surfaces if n.deregistered == 0]
    assert not missed, f"surfaces never deregistered on shutdown: {missed}"


# ----- Finding 7: slow subscribers must learn that events were dropped -----

def test_overflow_delivers_dropped_marker_before_next_event():
    mgr = rm.RoomManager()
    queue = mgr.subscribe_events("r1")
    capacity = queue.maxsize
    total = capacity + 5
    for i in range(total):
        mgr._deliver_event("r1", {"event": "E", "i": i})

    async def drain(n):
        return [await queue.get() for _ in range(n)]

    first, second = asyncio.run(drain(2))
    assert first["event"] == "EventsDropped", (
        "consumer got no signal that events were discarded"
    )
    assert first["count"] == 5
    # The oldest surviving event follows the marker: 0..4 were dropped.
    assert second == {"event": "E", "i": 5}


def test_no_marker_without_overflow():
    mgr = rm.RoomManager()
    queue = mgr.subscribe_events("r1")
    mgr._deliver_event("r1", {"event": "E", "i": 0})

    async def get_one():
        return await queue.get()

    assert asyncio.run(get_one()) == {"event": "E", "i": 0}
