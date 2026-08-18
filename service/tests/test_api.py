"""
Smoke and live e2e tests — run against a RUNNING service.

Two groups:
  * Safe tests (no side effects) run always: health, root, room list, OpenAPI
    surface, unknown-room handling.
  * Live tests drive a real paired room (they START A MEETING). They are gated
    behind ZRC_E2E_LIVE=1 and skip unless the room is connected.

Run (from an env with pytest + httpx + websockets):
  ZRC_BASE_URL=http://localhost:8000 pytest service/tests -v            # safe only
  ZRC_E2E_LIVE=1 pytest service/tests -v -m live                        # + live flow
"""
import json
import os
import time

import pytest
from websockets.sync.client import connect as ws_connect

LIVE = os.environ.get("ZRC_E2E_LIVE") == "1"


# ----------------------------------------------------------------- Smoke: safe

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "healthy"
    assert body["sdk_initialized"] is True
    assert isinstance(body["active_rooms"], int)


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json().get("service")


def test_list_rooms_schema(client):
    r = client.get("/api/rooms")
    assert r.status_code == 200
    rooms = r.json()["rooms"]
    assert isinstance(rooms, list)
    for room in rooms:
        assert {"room_id", "paired", "connection_state"} <= room.keys()


def test_openapi_surface(client):
    """The documented REST surface must include the core routes.

    (WebSocket routes are not represented in openapi.json — see
    test_ws_endpoint_accepts_connection for the /events route.)
    """
    spec = client.get("/openapi.json").json()
    paths = set(spec["paths"])
    expected = {
        "/health",
        "/api/rooms",
        "/api/rooms/{room_id}/pair",
        "/api/rooms/{room_id}/unpair",
        "/api/rooms/{room_id}/status",
        "/api/rooms/{room_id}/meeting/start_instant",
        "/api/rooms/{room_id}/meeting/exit",
    }
    missing = expected - paths
    assert not missing, f"missing routes: {sorted(missing)}"


def test_ws_endpoint_accepts_connection(ws_url):
    """The WS events route exists and accepts a subscription (no room state needed)."""
    with ws_connect(ws_url) as ws:
        ws.close()


def test_unknown_room_status_is_error(client):
    r = client.get("/api/rooms/__does_not_exist__/status")
    assert r.status_code in (400, 404), r.text


# ---------------------------------------------------------------- Live e2e

def _room(client, room_id):
    rooms = client.get("/api/rooms").json()["rooms"]
    return next((r for r in rooms if r["room_id"] == room_id), None)


def _connected(client, room_id):
    room = _room(client, room_id)
    return bool(room) and "Connected" in room["connection_state"]


def _wait_for_event(ws, predicate, timeout):
    """Read WS frames until `predicate` matches or `timeout` elapses.

    Returns (matching_event | None, [all events seen]).
    """
    deadline = time.time() + timeout
    seen = []
    while time.time() < deadline:
        try:
            msg = ws.recv(timeout=max(0.1, deadline - time.time()))
        except TimeoutError:
            break
        evt = json.loads(msg)
        seen.append(evt)
        if predicate(evt):
            return evt, seen
    return None, seen


@pytest.mark.live
@pytest.mark.skipif(not LIVE, reason="set ZRC_E2E_LIVE=1 to run live room tests (starts a real meeting)")
def test_meeting_flow_emits_ws_events(client, room_id, ws_url):
    """Drive the paired room through a meeting and assert the WS mirrors it."""
    if not _connected(client, room_id):
        pytest.skip(f"room '{room_id}' is not paired/connected")

    with ws_connect(ws_url) as ws:
        # 1. start an instant meeting
        r = client.post(f"/api/rooms/{room_id}/meeting/start_instant")
        assert r.status_code == 200 and r.json().get("success"), r.text

        # 2. the meeting-status lifecycle must arrive over the WS
        hit, seen = _wait_for_event(
            ws,
            lambda e: e.get("event") == "OnUpdateMeetingStatus"
            and e.get("status") == "MeetingStatusInMeeting",
            timeout=45,
        )
        assert hit, f"no InMeeting status over WS; saw: {[e.get('event') for e in seen]}"

        # 3. a participant roster event should also appear
        hit_p, _ = _wait_for_event(
            ws,
            lambda e: e.get("event")
            in ("OnInitMeetingParticipants", "OnUserJoin", "OnMeetingParticipantsChanged"),
            timeout=20,
        )
        assert hit_p, "no participant event over WS"

        # 4. exercise in-meeting control endpoints
        rm_a = client.post(f"/api/rooms/{room_id}/audio/mute")
        assert rm_a.status_code == 200, rm_a.text
        rm_v = client.post(f"/api/rooms/{room_id}/video/mute")
        assert rm_v.status_code == 200, rm_v.text

        # 5. those controls should surface as audio/video status events on the WS
        hit_av, _ = _wait_for_event(
            ws,
            lambda e: e.get("event") in ("OnUpdateMyAudioStatus", "OnUpdateMyVideoNotification"),
            timeout=15,
        )
        assert hit_av, "no audio/video status event over WS after mute"

    # 6. clean up: exit the meeting (outside the WS context is fine)
    rx = client.post(f"/api/rooms/{room_id}/meeting/exit")
    assert rx.status_code == 200 and rx.json().get("success"), rx.text

    # 7. the room must remain paired and return to a connected/idle state
    room = _room(client, room_id)
    assert room and room["paired"] is True


@pytest.mark.live
@pytest.mark.skipif(not LIVE, reason="set ZRC_E2E_LIVE=1 to run this ~35s slow test")
def test_ws_keepalive_when_idle(base_url):
    """A subscription with no room activity receives the 30s keepalive frame.

    Subscribes to a room_id that gets no SDK events (a real connected room is
    never quiet for 30s), so the socket is genuinely idle and the keepalive fires.
    Gated because it necessarily waits ~30s.
    """
    idle_url = (
        base_url.replace("https://", "wss://").replace("http://", "ws://")
        + "/api/rooms/__idle_keepalive__/events"
    )
    with ws_connect(idle_url) as ws:
        hit, seen = _wait_for_event(ws, lambda e: e.get("event") == "keepalive", timeout=35)
        assert hit, f"no keepalive within 35s; saw: {[e.get('event') for e in seen]}"
