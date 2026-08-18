"""
Unit tests for heartbeat-loop resilience (PRODUCTION-REVIEW.md 1.1).

The SDK is a reactor: HeartBeat() is the pump that services its queues, network
I/O, and state machine on Linux. A single transient exception must never stop the
pump permanently — that failure mode is silent (process keeps serving HTTP,
connection state stays cached at Connected) and unrecoverable without a restart.
"""
import asyncio

import pytest

import _zrc_stub  # noqa: F401  (installs the fake zrc_sdk before room_manager import)
import room_manager as rm

pytestmark = pytest.mark.unit


class _FlakySDK:
    """HeartBeat raises on the first call, then works — a transient fault."""

    def __init__(self):
        self.calls = 0

    def HeartBeat(self):
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("transient SDK hiccup")


def test_heartbeat_survives_one_exception():
    mgr = rm.RoomManager()
    mgr.sdk = _FlakySDK()
    mgr._HEARTBEAT_ERROR_BACKOFF = 0.01  # fast backoff for the test

    async def run():
        await mgr.start_heartbeat()
        await asyncio.sleep(0.5)
        await mgr.stop_heartbeat()

    asyncio.run(run())
    assert mgr.sdk.calls >= 2, (
        f"heartbeat stopped after the first exception (calls={mgr.sdk.calls}) — "
        "the pump must continue past transient errors"
    )


def test_heartbeat_cancellation_still_clean():
    """Shutdown cancellation must still stop the loop (CancelledError is a
    BaseException — the continue-on-Exception fix must not swallow it)."""
    mgr = rm.RoomManager()
    mgr.sdk = _FlakySDK()

    async def run():
        await mgr.start_heartbeat()
        await asyncio.sleep(0.05)
        await mgr.stop_heartbeat()
        assert mgr.heartbeat_task.cancelled() or mgr.heartbeat_task.done()

    asyncio.run(run())
