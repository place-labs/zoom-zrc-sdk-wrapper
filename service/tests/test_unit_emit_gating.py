"""
Unit tests for no-listener emit gating + serialization memoization
(PRODUCTION-REVIEW.md 4a).

Python evaluates emit()'s kwargs before the call, so every SDK event was fully
serialized (recursive dir() reflection, on the SDK thread, holding the GIL) even
with zero WebSocket subscribers — the REST-only common case. Hot pure-emit
callbacks now skip entirely when nobody is listening; the per-type field list is
memoized for real pybind structs.
"""
import pytest

import _zrc_stub  # noqa: F401  (installs the fake zrc_sdk before room_manager import)
import room_manager as rm

pytestmark = pytest.mark.unit


_reads = {"n": 0}


class _SpyStatus:
    """Counts field reads — a read means serialization ran."""
    @property
    def isMuted(self):
        _reads["n"] += 1
        return True


def test_hot_callback_skips_serialization_with_no_listeners():
    _reads["n"] = 0
    mgr = rm.RoomManager()                     # real manager: has_listeners, no subs
    sink = rm.MeetingAudioHelperSink("r1")
    sink.mgr = mgr

    sink.OnUpdateMyAudioStatus(_SpyStatus())

    assert _reads["n"] == 0, "payload was serialized despite zero WS listeners"


def test_hot_callback_runs_with_a_listener():
    _reads["n"] = 0
    mgr = rm.RoomManager()
    mgr.subscribe_events("r1")
    sink = rm.MeetingAudioHelperSink("r1")
    sink.mgr = mgr

    sink.OnUpdateMyAudioStatus(_SpyStatus())

    assert _reads["n"] > 0, "with a listener the payload must be built"


def test_hot_callback_runs_under_capture_managers():
    """The contract test injects a bare capture manager with no has_listeners —
    hot callbacks must still execute there (coverage depends on it)."""
    _reads["n"] = 0

    class _Capture:
        def __init__(self):
            self.events = []

        def broadcast_event(self, room_id, payload):
            self.events.append(payload)

    sink = rm.MeetingAudioHelperSink("r1")
    sink.mgr = _Capture()

    sink.OnUpdateMyAudioStatus(_SpyStatus())

    assert len(sink.mgr.events) == 1
    assert _reads["n"] > 0


def test_field_names_memoized_for_sdk_types():
    """Real pybind structs (module 'zrc_sdk') get their field list cached per
    type; other objects keep exact per-instance dir() semantics."""
    FakeStruct = type("FakeStruct", (), {"__module__": "zrc_sdk", "x": 1, "y": 2})
    out1 = rm._pybind_to_jsonable(FakeStruct())
    out2 = rm._pybind_to_jsonable(FakeStruct())
    assert out1 == out2 == {"x": 1, "y": 2}
    assert FakeStruct in rm._FIELD_NAMES_CACHE, "sdk-type field list not cached"

    plain = type("Plain", (), {"a": 5})
    assert rm._pybind_to_jsonable(plain()) == {"a": 5}
    assert plain not in rm._FIELD_NAMES_CACHE, "non-sdk types must not be cached"
