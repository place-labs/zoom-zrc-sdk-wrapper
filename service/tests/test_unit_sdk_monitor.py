"""
Unit tests for SDKCallMonitor — the live instrumentation that times synchronous
SDK calls on the event-loop thread and flags any slow enough to stall the fleet.

A call that runs longer than the threshold on the single loop thread freezes
every room's REST + WS for that duration (see ARCHITECTURE.md → Threading
model), so the monitor's job is to make that visible in production.
"""
import logging
import time

import pytest

import _zrc_stub  # noqa: F401  (installs the fake zrc_sdk before room_manager import)
import room_manager as rm

pytestmark = pytest.mark.unit


def test_fast_call_is_not_flagged():
    mon = rm.SDKCallMonitor(slow_ms=50)
    with mon.measure("Fast"):
        pass
    s = mon.stats()
    assert s["calls"] == 1
    assert s["slow_calls"] == 0
    assert s["slowest"] == []


def test_slow_call_is_flagged_and_recorded(caplog):
    mon = rm.SDKCallMonitor(slow_ms=5)
    with caplog.at_level(logging.WARNING):
        with mon.measure("RetryToPairRoom[lab]"):
            time.sleep(0.02)          # 20 ms > 5 ms threshold
    s = mon.stats()
    assert s["calls"] == 1
    assert s["slow_calls"] == 1
    assert s["max_ms"] >= 20
    assert s["slowest"][-1]["call"] == "RetryToPairRoom[lab]"
    assert s["slowest"][-1]["ms"] >= 20
    assert any("RetryToPairRoom[lab]" in r.message and "SLOW" in r.message.upper()
               for r in caplog.records)


def test_timing_survives_an_exception():
    """A call that blocks then raises must still be timed (finally), and re-raise."""
    mon = rm.SDKCallMonitor(slow_ms=5)
    with pytest.raises(ValueError):
        with mon.measure("Boom"):
            time.sleep(0.02)
            raise ValueError("boom")
    s = mon.stats()
    assert s["calls"] == 1
    assert s["slow_calls"] == 1


def test_slowest_list_is_bounded():
    mon = rm.SDKCallMonitor(slow_ms=0)   # everything counts as slow
    for i in range(50):
        with mon.measure(f"call{i}"):
            pass
    s = mon.stats()
    assert s["slow_calls"] == 50
    assert len(s["slowest"]) <= 20        # only the most recent are retained
    assert s["slowest"][-1]["call"] == "call49"


def test_threshold_from_env(monkeypatch):
    monkeypatch.setenv("ZRC_SDK_SLOW_MS", "123")
    assert rm.SDKCallMonitor().slow_ms == 123.0


def test_manager_exposes_a_monitor():
    mgr = rm.RoomManager()
    assert isinstance(mgr.sdk_monitor, rm.SDKCallMonitor)
    assert mgr.sdk_monitor.stats()["calls"] == 0
