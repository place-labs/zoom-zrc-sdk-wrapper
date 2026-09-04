"""
Unit tests for startup/pairing None-guards and per-room isolation
(PRODUCTION-REVIEW.md 2.5b / 2.5c).

At boot, initialize() restores every paired room; one bad room must log and skip,
not abort startup for the whole fleet. The premeeting service getter must be
guarded like its four siblings (phone/setting/proAV/...), and a falsy
CreateZoomRoomsService must surface as a clean error, not a 'NoneType' 500.
"""
import pytest

import _zrc_stub  # noqa: F401  (installs the fake zrc_sdk before room_manager import)
from _zrc_stub import FakeService
import room_manager as rm

pytestmark = pytest.mark.unit


class _NoPremeetingService(FakeService):
    def GetPreMeetingService(self):
        return None


def test_register_sinks_survives_missing_premeeting():
    """GetPreMeetingService() -> None must not raise; the other surfaces still
    register (the siblings are all guarded — this one wasn't)."""
    mgr = rm.RoomManager()
    svc = _NoPremeetingService("root")

    mgr.register_sinks_for_room("r1", svc)   # must not raise

    assert "r1" not in mgr.premeeting_sinks
    # the rest of the surfaces still registered on the fake graph
    assert any(node.registered for node in svc.walk()), "no sinks registered at all"


def test_restore_room_isolates_failure():
    """A raise while restoring one room is logged and skipped, and the room is
    not left half-tracked in mgr.rooms."""
    mgr = rm.RoomManager()

    def _boom(room_id, service):
        raise RuntimeError("bad room state")
    mgr.register_sinks_for_room = _boom

    ok = mgr._restore_room("bad", FakeService("bad"))

    assert ok is False
    assert "bad" not in mgr.rooms


def test_restore_room_happy_path():
    mgr = rm.RoomManager()
    svc = FakeService("root")

    ok = mgr._restore_room("good", svc, can_retry=True)

    assert ok is True
    assert mgr.rooms["good"] is svc


class _NoServiceSDK(FakeService):
    def CreateZoomRoomsService(self, room_id):
        return None


def test_create_room_service_returns_none_on_falsy_sdk_service():
    """CreateZoomRoomsService() -> falsy must yield None (for a clean endpoint
    error), not an AttributeError deep in sink registration (2.5c)."""
    mgr = rm.RoomManager()
    mgr.sdk = _NoServiceSDK("sdk")

    assert mgr.create_room_service("rX") is None
    assert "rX" not in mgr.rooms
