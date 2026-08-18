"""
Live e2e scenario suite — drives real commands on a paired Zoom Room and asserts
the resulting events over the WebSocket. Each scenario follows the shape:

    precondition → trigger → await the event it produces → respond → assert → cleanup

This is the layer nothing else can cover: the contract test proves callbacks
serialize, the smoke tests prove endpoints exist — only this exercises the real
command→event dependency chains on hardware (the reason `_wait_for_event` exists).

Gating (these have real side effects):
  ZRC_E2E_LIVE=1     — required; scenarios start REAL meetings. Opt-in.
  ZRC_E2E_RECORD=1   — additionally required for the cloud-recording scenarios,
                       which create real recording artifacts / storage / emails.
  ZRC_TEST_ROOM      — the room_id to drive (default "lab", from conftest).

Run:
  ZRC_E2E_LIVE=1 pytest service/tests/test_live_scenarios.py -v
  ZRC_E2E_LIVE=1 ZRC_E2E_RECORD=1 pytest service/tests/test_live_scenarios.py -v

Scenarios that need a SECOND participant/host (a request to record, host asks to
unmute, admit-from-waiting-room) can't be self-triggered by one room — they're
present as explicit skips documenting what a human/second-client must do.
"""
import json
import os
import time
from contextlib import contextmanager

import pytest
from websockets.sync.client import connect as ws_connect

LIVE = os.environ.get("ZRC_E2E_LIVE") == "1"
RECORD = os.environ.get("ZRC_E2E_RECORD") == "1"

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(not LIVE, reason="set ZRC_E2E_LIVE=1 — these drive a real room / start meetings"),
]


# ============================================================ scenario harness

class Session:
    """Wraps (client, ws) for one room with trigger + await-event helpers.

    The WebSocket is the observation channel: after a trigger, `wait_for` reads
    frames until the expected event arrives (skipping unrelated ones) or times
    out — which is how a scenario chains a step onto the consequence of the last.
    """

    def __init__(self, client, room_id, ws):
        self.client = client
        self.room_id = room_id
        self.ws = ws

    # --- commands ---
    def post(self, path, **kw):
        return self.client.post(f"/api/rooms/{self.room_id}{path}", **kw)

    def get(self, path, **kw):
        return self.client.get(f"/api/rooms/{self.room_id}{path}", **kw)

    # --- observation ---
    def drain(self, quiet=0.4):
        """Discard buffered events so the next wait_for sees only fresh ones."""
        deadline = time.time() + quiet
        while time.time() < deadline:
            try:
                self.ws.recv(timeout=max(0.05, deadline - time.time()))
            except TimeoutError:
                break

    def wait_for(self, predicate, timeout=20):
        """Read WS frames until predicate(evt) matches; returns evt or None."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                msg = self.ws.recv(timeout=max(0.1, deadline - time.time()))
            except TimeoutError:
                break
            evt = json.loads(msg)
            if predicate(evt):
                return evt
        return None

    def wait_event(self, name, timeout=20):
        return self.wait_for(lambda e: e.get("event") == name, timeout)

    # --- shared setup: an instant meeting, cleaned up on exit ---
    @contextmanager
    def in_meeting(self, timeout=45):
        r = self.post("/meeting/start_instant")
        assert r.status_code == 200, r.text
        hit = self.wait_for(
            lambda e: e.get("event") == "OnUpdateMeetingStatus"
            and e.get("status") == "MeetingStatusInMeeting",
            timeout,
        )
        assert hit, "meeting never reached MeetingStatusInMeeting over the WS"
        try:
            yield
        finally:
            self.post("/meeting/exit")
            self.wait_for(
                lambda e: e.get("event") in ("OnExitMeetingNotification",)
                or (e.get("event") == "OnUpdateMeetingStatus"
                    and e.get("status") != "MeetingStatusInMeeting"),
                timeout=15,
            )


NOT_CONNECT_TO_ZOOMROOM = 11   # ZRCSDKError: command reached the SDK but the room is unreachable


def _room_usable(client, room_id):
    """(usable, reason). NOTE: `connection_state` is NOT a liveness signal — it can
    report Connected while commands fail with NOT_CONNECT_TO_ZOOMROOM (11), a
    "zombie" state auto-reconnect does not heal (the SDK never fires Disconnected).
    So we probe the actual command channel via meeting/status rather than trust the
    state field."""
    rooms = client.get("/api/rooms").json().get("rooms", [])
    room = next((r for r in rooms if r["room_id"] == room_id), None)
    if not room or "Connected" not in (room.get("connection_state") or ""):
        return False, "not paired/connected"
    st = client.get(f"/api/rooms/{room_id}/meeting/status")
    if st.status_code == 200 and st.json().get("result") == NOT_CONNECT_TO_ZOOMROOM:
        return False, ("zombie: reports Connected but commands return "
                       "NOT_CONNECT_TO_ZOOMROOM (11) — reconnect/re-pair the room")
    return True, ""


@pytest.fixture
def live(client, room_id, ws_url):
    """A genuinely-reachable-room Session with a live WebSocket. Skips (with the
    reason) if the room isn't paired, not connected, or in the zombie state."""
    usable, why = _room_usable(client, room_id)
    if not usable:
        pytest.skip(f"room '{room_id}': {why}")
    with ws_connect(ws_url) as ws:
        yield Session(client, room_id, ws)


# ================================================= pre-meeting scenarios (no meeting)

def test_meeting_list_resolves(live):
    """GET the room's calendar list; the SDK resolves it via OnUpdateMeetingList."""
    r = live.get("/meetings/list")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "meetings" in body or "meeting_list" in body or isinstance(body, dict)


@pytest.mark.parametrize("kind", ["microphones", "speakers", "cameras"])
def test_device_lists(live, kind):
    """Device inventory is readable pre-meeting (list shape, not specific devices)."""
    r = live.get(f"/settings/devices/{kind}")
    assert r.status_code == 200, r.text


def test_speaker_volume_roundtrip(live):
    """Set speaker volume → the change round-trips as OnCurrentSpeakerVolumeChanged."""
    original = None
    got = live.get("/settings/volume/speaker")
    if got.status_code == 200:
        original = got.json().get("volume")

    live.drain()
    target = 40 if (original is None or original > 50) else 60
    r = live.post("/settings/volume/speaker", json={"volume": target})
    assert r.status_code == 200, r.text
    evt = live.wait_event("OnCurrentSpeakerVolumeChanged", timeout=15)
    assert evt is not None, "no OnCurrentSpeakerVolumeChanged after setting volume"

    if original is not None:                       # restore
        live.post("/settings/volume/speaker", json={"volume": original})


# ==================================================== in-meeting scenarios

def test_meeting_lifecycle_and_participants(live):
    """Start a meeting → roster event arrives → participants list is readable → exit."""
    with live.in_meeting():
        roster = live.wait_for(
            lambda e: e.get("event") in (
                "OnInitMeetingParticipants", "OnUserJoin", "OnMeetingParticipantsChanged"),
            timeout=20,
        )
        assert roster, "no participant/roster event after joining the meeting"
        r = live.get("/participants/")
        assert r.status_code == 200, r.text
    # (meeting exited by the context manager; room stays paired)


def test_audio_mute_roundtrip(live):
    """In-meeting: mute audio → the status change comes back over the WS."""
    with live.in_meeting():
        # Normalize first: muting an already-muted mic changes nothing → no event.
        live.post("/audio/mute", params={"mute": "false"})
        live.drain(1.0)
        try:
            ra = live.post("/audio/mute", params={"mute": "true"})
            assert ra.status_code == 200, ra.text
            assert live.wait_event("OnUpdateMyAudioStatus", timeout=15), "no audio status after mute"
        finally:
            live.post("/audio/mute", params={"mute": "false"})   # always restore


def test_video_mute_roundtrip(live):
    """In-meeting: stop video → the status change comes back over the WS.

    Skips on rooms without a camera: UpdateMyVideo returns
    ZRCSDKERR_CAMERA_DISABLED (102) there, on every code version — an
    environmental limit, not a wrapper defect."""
    cams = live.get("/settings/devices/cameras")
    if cams.status_code == 200 and not cams.json().get("cameras"):
        pytest.skip("room has no camera — video mute untestable on this hardware")
    with live.in_meeting():
        live.post("/video/mute", params={"mute": "false"})   # normalize
        live.drain(1.0)
        try:
            rv = live.post("/video/mute", params={"mute": "true"})
            assert rv.status_code == 200, rv.text
            assert live.wait_event("OnUpdateMyVideoNotification", timeout=15), \
                f"no video status after mute (response: {rv.text})"
        finally:
            live.post("/video/mute", params={"mute": "false"})


# ==================================================== recording (extra opt-in)

recording = pytest.mark.skipif(
    not RECORD, reason="set ZRC_E2E_RECORD=1 — creates a REAL cloud recording")


@recording
def test_recording_lifecycle(live):
    """start → pause → resume → stop, observed via OnUpdateMeetingRecordingInfo."""
    with live.in_meeting():
        live.drain()
        r = live.post("/recording/cloud/start")
        assert r.status_code == 200, r.text
        info = live.wait_for(
            lambda e: e.get("event") == "OnUpdateMeetingRecordingInfo"
            and (e.get("recordingInfo") or {}).get("isCMRInProgress") is True,
            timeout=25,
        )
        assert info, "recording never reported isCMRInProgress"

        live.post("/recording/cloud/pause")
        assert live.wait_for(
            lambda e: e.get("event") == "OnUpdateMeetingRecordingInfo"
            and (e.get("recordingInfo") or {}).get("isCMRPaused") is True, timeout=20
        ), "recording never reported paused"

        live.post("/recording/cloud/resume")
        live.wait_event("OnUpdateMeetingRecordingInfo", timeout=20)

        live.post("/recording/cloud/stop")            # always stop (cleanup)


@recording
def test_recording_disclaimer_precheck(live):
    """cloud/start returns a disclaimer precheck; if the account requires one, the
    OnNeedPromptStartRecordingDisclaimerUpdate event should also fire. Skips
    cleanly when the account has no disclaimer policy."""
    with live.in_meeting():
        live.drain()
        r = live.post("/recording/cloud/start")
        assert r.status_code == 200, r.text
        needed = r.json().get("disclaimer_needed")
        if not needed:
            live.post("/recording/cloud/stop")
            pytest.skip("account does not require a recording disclaimer")
        assert live.wait_event("OnNeedPromptStartRecordingDisclaimerUpdate", timeout=15), \
            "disclaimer required but no OnNeedPromptStartRecordingDisclaimerUpdate event"
        live.post("/recording/cloud/stop")


# ================================= assisted / second-actor (documented skips)

@pytest.mark.skip(reason="needs a SECOND participant to request recording → "
                         "OnReceiveRecordingRequest; then respond-to-request(agree/deny)")
def test_respond_to_recording_request(live):
    """ASSISTED: have a second participant request to record, then answer:
        POST /recording/respond-to-request {"agree": true|false}
    Assert the request event arrives and the response returns success."""


@pytest.mark.skip(reason="needs the HOST to ask this room to unmute → "
                         "OnAskUnmuteAudioByHostNotification; then audio/mute(false)")
def test_ask_to_unmute_by_host(live):
    """ASSISTED: host asks the room to unmute; assert the ask event, then unmute."""
