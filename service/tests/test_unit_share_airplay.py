"""
Unit test for the AirPlay / BlackMagic share-status callback that carries the
room's wireless **sharing key** (the code users enter at share.zoom.us / the Zoom
app to present to the room).

The SDK exposes it only via the push callback OnUpdateAirPlayBlackMagicStatus on
AirplayBlackMagicStatus — there is no getter. This asserts the Python share sink
forwards that callback as a flat WS event whose `status` carries the sharing key,
so subscribers get asynchronous updates whenever the code changes.
"""
import pytest

import _zrc_stub  # noqa: F401  (installs the fake zrc_sdk before room_manager import)
import room_manager as rm

pytestmark = pytest.mark.unit


class _FakeAirplayStatus:
    """Stand-in for the bound AirplayBlackMagicStatus struct (dir()-serializable)."""
    directPresentationSharingKey = "SHARE-KEY-123"
    directPresentationPairingCode = "PAIR-999"
    wifiName = "lab-wifi"
    isDirectPresentationConnected = False


class _CaptureMgr:
    def __init__(self):
        self.events = []

    def broadcast_event(self, room_id, payload):
        self.events.append((room_id, payload))


def test_airplay_status_forwards_sharing_key():
    sink = rm.MeetingShareHelperSink("r1")
    sink.mgr = _CaptureMgr()

    sink.OnUpdateAirPlayBlackMagicStatus(_FakeAirplayStatus())

    assert len(sink.mgr.events) == 1, "expected exactly one WS event"
    room_id, payload = sink.mgr.events[0]
    assert room_id == "r1"
    assert payload["event"] == "OnUpdateAirPlayBlackMagicStatus"
    assert payload["status"]["directPresentationSharingKey"] == "SHARE-KEY-123"
    assert payload["status"]["directPresentationPairingCode"] == "PAIR-999"
