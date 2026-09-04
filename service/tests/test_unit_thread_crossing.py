"""
Unit tests for SDK-thread → event-loop signaling (PRODUCTION-REVIEW.md 2.4).

Sink callbacks fire on SDK C++ threads. asyncio objects are single-thread — the
only safe crossing is loop.call_soon_threadsafe (which locks AND wakes the
selector). Direct Event.set() from the SDK thread worked only by accident: the
GIL made the append atomic-ish and the 150ms heartbeat happened to pump the loop.
Under PYTHONASYNCIODEBUG=1 it raises on the SDK thread; with the heartbeat dead
the waiter never wakes.
"""
import pytest

import _zrc_stub  # noqa: F401  (installs the fake zrc_sdk before room_manager import)
from _zrc_stub import zrc_sdk
import room_manager as rm

pytestmark = pytest.mark.unit


class _SpyLoop:
    """Records call_soon_threadsafe callbacks without running them, so tests can
    assert the crossing is scheduled (not direct) and then run it explicitly."""

    def __init__(self):
        self.scheduled = []

    def call_soon_threadsafe(self, cb, *args):
        self.scheduled.append((cb, args))

    def run_all(self):
        for cb, args in self.scheduled:
            cb(*args)


def _mgr_with_spy():
    mgr = rm.RoomManager()
    spy = _SpyLoop()
    mgr._event_loop = spy
    return mgr, spy


def test_pair_result_crosses_via_call_soon_threadsafe():
    mgr, spy = _mgr_with_spy()
    sink = rm.ZoomRoomsServiceSink("r1")
    sink.mgr = mgr

    sink.OnPairRoomResult(0)

    assert not sink.pair_event.is_set(), (
        "pair_event was set directly from the (simulated) SDK thread — "
        "must be scheduled via call_soon_threadsafe"
    )
    spy.run_all()
    assert sink.pair_event.is_set(), "scheduled crossing never sets the event"
    assert sink.pair_result == 0


def test_connected_state_crosses_via_call_soon_threadsafe():
    mgr, spy = _mgr_with_spy()
    sink = rm.PreMeetingServiceSink("r1")
    sink.mgr = mgr

    sink.OnZRConnectionStateChanged(zrc_sdk.ConnectionStateConnected)

    assert not sink.connected_event.is_set(), (
        "connected_event was set directly from the (simulated) SDK thread"
    )
    spy.run_all()
    assert sink.connected_event.is_set()


def test_direct_set_fallback_without_bound_loop():
    """No loop bound (tests / pre-startup): fall back to a direct set so the
    contract test and early callbacks still work."""
    sink = rm.ZoomRoomsServiceSink("r1")   # no mgr at all
    sink.OnPairRoomResult(7)
    assert sink.pair_event.is_set()
    assert sink.pair_result == 7
