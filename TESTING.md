# Testing

Five suites, named by what they need to run — cheapest/most-portable first.

| Suite | File | Verifies | Needs | In CI? |
|-------|------|----------|-------|--------|
| **Unit** | `service/tests/` (`-m unit`) | service-layer lifecycle logic against a fake SDK: room removal/cleanup, re-pair flag, WS overflow marker, lifespan exit codes, bindings source contracts | nothing | ✅ |
| **Contract** | `service/test_sink_contracts.py` | every forwarded SDK callback serializes to a valid, once-only WS payload (125 callbacks) | compiled module (in image) | ✅ |
| **Lifecycle** | `service/test_sink_lifecycle.py` | RegisterSink/DeregisterSink work through the compiled bindings against the real SDK, for every sink surface | compiled module (in image) | ✅ |
| **Smoke** | `service/tests/test_api.py` (unmarked) | running service is up: health, room-list schema, OpenAPI surface, WS route, error handling | running container | ✅ |
| **Live e2e** | `service/tests/test_api.py` (`@pytest.mark.live`) | real pair → meeting → WS events → mute → exit | **paired Zoom Room** | ❌ (manual) |

## Unit tests

Pure-Python tests of the service layer with a stubbed `zrc_sdk`
(`service/tests/_zrc_stub.py` mimics the SDK object graph). No compiled module,
no server, no room — they run anywhere pytest runs and execute in under a second:

- **`test_unit_room_manager.py`** — `remove_room()` purges every sink store and
  deregisters every surface; re-pairing a remotely-unpaired room re-enables
  auto-reconnect; a slow WebSocket subscriber receives an `EventsDropped` marker
  after queue overflow; the `_SINK_SURFACES` table drives registration AND
  deregistration (23 surfaces, no drift).
- **`test_unit_rooms_endpoint.py`** — the unpair endpoint performs full cleanup
  (exercised in-process via FastAPI's TestClient).
- **`test_unit_lifespan.py`** — clean shutdown exits 0; a failed startup exits
  non-zero (run in a subprocess because the lifespan hard-exits).
- **`test_unit_heartbeat.py`** — the SDK pump survives a transient `HeartBeat()`
  exception (continue-with-backoff, not permanent stop); shutdown cancellation
  stays clean.
- **`test_unit_health.py`** — `/health` returns 503 when the heartbeat task has
  died or the SDK is missing (the k8s probes can only heal what it reports).
- **`test_unit_thread_crossing.py`** — SDK-thread callbacks signal asyncio
  events via `call_soon_threadsafe`, with a direct-set fallback when no loop is
  bound.
- **`test_unit_liveness.py`** — zombie detection (`Connected` but commands
  return 11), the liveness self-heal loop, and the reconnect loop's self-exit
  after a zombie heals without a fresh `Connected` callback.
- **`test_unit_startup_guards.py`** — a missing pre-meeting service or a falsy
  `CreateZoomRoomsService` skips/errors cleanly; one bad restored room can't
  abort startup for the fleet.
- **`test_unit_reminder_enums.py`** — reminder/consent endpoints accept enum
  names, ints, and digit-strings; unknown values 422 (never 500); combined
  consent passes the SDK's open int64 through.
- **`test_unit_sdk_monitor.py`** — SDK-call timing stats; malformed
  `ZRC_SDK_SLOW_MS` falls back to the default instead of crashing startup.
- **`test_unit_emit_gating.py`** — hot pure-emit callbacks skip payload
  serialization when a room has no WS listeners; per-type field lists are
  memoized for real pybind structs.
- **`test_unit_share_airplay.py`** — the share sink forwards
  `OnUpdateAirPlayBlackMagicStatus` (carries the wireless sharing key).
- **`test_unit_routes.py`** — no two endpoints share a `(method, path)`: FastAPI
  silently shadows duplicates by registration order (found live: a dead
  `/video/mute` twin whose callers got default-valued behavior).
- **`test_bindings_source.py`** — source contracts on the C++ bindings: every
  Register/Deregister pair uses the shared `SinkRegistry` (no lambda-local static
  maps), the `isMyself` alias exists, the generator template stays byte-identical
  to `bindings/zrc_bindings.cpp`, and the in-image lifecycle test's surface list
  matches the `_SINK_SURFACES` table.

```bash
pip install -r requirements-dev.txt
pytest -m unit -v
```

## Contract tests

Parses the trampolines in `bindings/zrc_bindings.cpp`, fabricates SDK arguments for
every forwarded callback, invokes the Python sink with a capturing manager, and
asserts the emitted WebSocket payload is produced exactly once, is JSON-serializable,
and carries an `event` key. No Zoom Room, no event loop, no network — it exercises
the payload-serialization layer for all events, including ones that only occur in a
live meeting.

```bash
# inside the built image (needs the compiled zrc_sdk module):
docker run --rm --entrypoint python <image> /app/service/test_sink_contracts.py
# or against the running container:
docker exec zrc-microservice python /app/service/test_sink_contracts.py
```

Exits 0 on all-pass and prints a PASS / FAIL / ERROR summary.

## Lifecycle tests

Exercises `RegisterSink`/`DeregisterSink` **through the compiled bindings** against
the real SDK — the layer the contract tests deliberately bypass (they invoke the
Python sink methods directly and never touch the C++ trampoline registry).
Registration is a local SDK operation, so no paired or reachable room is needed.

For each of the ~24 sink surfaces the service registers, it asserts the full cycle:
deregister-before-register fails → register succeeds → deregister succeeds →
double-deregister fails → a fresh register/deregister cycle succeeds. This is the
test that would have caught the disjoint-static-map bug (deregistration silently
never happening, trampolines leaking across pair/unpair cycles).

```bash
# inside the built image (needs the compiled zrc_sdk module):
docker run --rm --entrypoint python <image> /app/service/test_sink_lifecycle.py
```

## Smoke and live e2e tests (pytest)

Run against a **running service** (default `http://localhost:8000`).

```bash
pip install -r requirements-dev.txt

# smoke — safe, no side effects, no room needed (also runs the unit tests):
pytest -v

# live — drives a real paired room (STARTS + EXITS A MEETING):
ZRC_E2E_LIVE=1 ZRC_TEST_ROOM=lab pytest -v -m live
```

Configuration (environment variables):

| Var | Default | Meaning |
|-----|---------|---------|
| `ZRC_BASE_URL` | `http://localhost:8000` | service under test |
| `ZRC_TEST_ROOM` | `lab` | room_id used by the live tests |
| `ZRC_E2E_LIVE` | _(unset)_ | set to `1` to run the `@pytest.mark.live` tests |

**Smoke** is a fast liveness/surface gate: it proves the deployed service boots,
the SDK initializes, the documented routes exist, response shapes are correct,
the WebSocket route accepts a subscription, and bad input returns a clean 4xx (not 500).
It does **not** exercise real room behavior.

**Live e2e** is the real end-to-end. `test_meeting_flow_emits_ws_events`:
1. skips unless the room is paired + connected,
2. subscribes to `ws://…/api/rooms/{room}/events`,
3. `start_instant` → asserts `OnUpdateMeetingStatus → MeetingStatusInMeeting` on the WS,
4. asserts a participant roster event,
5. mutes audio + video → asserts an audio/video status event on the WS,
6. `exit` → asserts the room stays paired.

`test_ws_keepalive_when_idle` subscribes to a room_id that gets no events (a real
connected room is never quiet for 30s) and asserts the 30s keepalive frame fires.

The live suite **cannot run in CI** — it needs a physically paired Zoom Room and starts
a real meeting. Run it manually before a release against a lab room.

## What CI runs

`.github/workflows/dockerhub-build-push.yml` builds the image, then runs the
**contract** and **lifecycle** suites inside it, followed by **unit + smoke**
against the running container — a failing test blocks the push. Results appear in
the Actions run log, and the pytest results upload as a JUnit artifact
(`test-results`).

Live e2e coverage is a manual pre-release step against real hardware.

Measured baseline (Apple-Silicon dev box / emulated image, indicative only):
delivery ceiling ~150k events/s and sub-ms loop lag to 5k events/s; HeartBeat
~1.8 ms at 500 services (1.2 % of the 150 ms budget). Neither is the bottleneck —
a single 100 ms blocking SDK call stalling the loop ~100 ms fleet-wide is, which
is why offloading blocking calls (`asyncio.to_thread`) is the priority fix.
