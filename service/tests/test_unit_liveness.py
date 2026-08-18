"""
Unit tests for the proactive liveness loop — self-heals the "zombie" state where
a room reports Connected but commands return NOT_CONNECT_TO_ZOOMROOM (11).

Auto-reconnect can't catch this on its own: the SDK never fires Disconnected
(it believes it's connected), so schedule_reconnect is never triggered and the
room stays unusable — even while idle, with no command to reveal it. The loop
periodically probes each room's real reachability and reconnects the zombies.
"""
import asyncio

import pytest

import _zrc_stub  # noqa: F401  (installs the fake zrc_sdk before room_manager import)
import room_manager as rm

pytestmark = pytest.mark.unit


class _FakeMeetingService:
    def __init__(self, status_result):
        self._r = status_result

    def GetMeetingStatus(self):
        return (self._r, 0)          # (result, status) — result 11 == unreachable


class _FakeRoomService:
    def __init__(self, status_result):
        self._ms = _FakeMeetingService(status_result)

    def GetMeetingService(self):
        return self._ms


def _mgr_with(rooms):
    """RoomManager pre-populated with rooms → their GetMeetingStatus result code,
    with schedule_reconnect spied so no event loop is needed."""
    mgr = rm.RoomManager()
    for rid, result in rooms.items():
        mgr.rooms[rid] = _FakeRoomService(result)
    mgr.scheduled = []
    mgr.schedule_reconnect = lambda rid: mgr.scheduled.append(rid)
    return mgr


def test_probe_detects_zombie():
    mgr = _mgr_with({"z": rm.NOT_CONNECT_TO_ZOOMROOM})
    assert mgr._probe_zombie("z") is True


def test_probe_healthy_room():
    mgr = _mgr_with({"h": 0})
    assert mgr._probe_zombie("h") is False


def test_liveness_check_reconnects_zombie():
    mgr = _mgr_with({"z": rm.NOT_CONNECT_TO_ZOOMROOM})
    mgr._liveness_check_once()
    assert mgr.scheduled == ["z"]


def test_liveness_check_ignores_healthy_room():
    mgr = _mgr_with({"h": 0})
    mgr._liveness_check_once()
    assert mgr.scheduled == []


def test_liveness_check_skips_unpaired():
    mgr = _mgr_with({"z": rm.NOT_CONNECT_TO_ZOOMROOM})
    mgr._unpaired_rooms.add("z")
    mgr._liveness_check_once()
    assert mgr.scheduled == []


def test_liveness_check_skips_already_reconnecting():
    mgr = _mgr_with({"z": rm.NOT_CONNECT_TO_ZOOMROOM})

    class _RunningTask:
        def done(self):
            return False
    mgr._reconnect_tasks["z"] = _RunningTask()

    mgr._liveness_check_once()
    assert mgr.scheduled == []


def test_probe_survives_sdk_exception():
    """A raised probe (e.g. loop closing) must not crash the loop — treat as
    'not a confirmed zombie' and move on."""
    mgr = rm.RoomManager()

    class _Boom:
        def GetMeetingService(self):
            raise RuntimeError("boom")
    mgr.rooms["b"] = _Boom()
    assert mgr._probe_zombie("b") is False


# ===== reconnect loop self-exit after a healed zombie (PRODUCTION-REVIEW.md 2.11)

class _Reconnectable(_FakeRoomService):
    def __init__(self, status_result):
        super().__init__(status_result)
        self.retries = 0

    def RetryToPairRoom(self):
        self.retries += 1
        return 0


def _mgr_for_reconnect(status_result, connection_state):
    """Manager with one room, its meeting-status result, and a premeeting sink
    carrying the cached connection state the SDK last reported."""
    mgr = rm.RoomManager()
    mgr._RECONNECT_BACKOFF = (0.01,)
    mgr.rooms["r"] = _Reconnectable(status_result)
    sink = rm.PreMeetingServiceSink("r")
    sink.connection_state = connection_state
    mgr.premeeting_sinks["r"] = sink
    return mgr


def test_reconnect_loop_self_exits_after_zombie_heals():
    """Zombie heal produces no fresh Connected callback (the SDK already thought
    it was Connected), so cancel_reconnect never fires — the loop must notice
    'state says Connected and commands work again' and stop on its own."""
    import _zrc_stub
    healed = _mgr_for_reconnect(0, _zrc_stub.zrc_sdk.ConnectionStateConnected)

    async def run():
        task = asyncio.get_running_loop().create_task(healed._reconnect_loop("r"))
        await asyncio.wait_for(task, timeout=1.0)   # must finish by itself

    asyncio.run(run())


def test_reconnect_loop_keeps_retrying_while_disconnected():
    """A genuinely disconnected room (state=Disconnected, commands failing) must
    keep the retry loop alive — only the Connected callback stops it."""
    import _zrc_stub
    down = _mgr_for_reconnect(
        rm.NOT_CONNECT_TO_ZOOMROOM, _zrc_stub.zrc_sdk.ConnectionStateDisconnected)

    async def run():
        task = asyncio.get_running_loop().create_task(down._reconnect_loop("r"))
        await asyncio.sleep(0.2)
        assert not task.done(), "loop must keep retrying a disconnected room"
        assert down.rooms["r"].retries >= 2
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    asyncio.run(run())
