/reus# Production-Readiness Review — Findings Reference

_Max-effort multi-agent review of `feat/ws`, 2026-08-10. 32 agents; 25 candidate
findings, each independently verified; 2 refuted; 23 kept, deduping to 15 distinct
issues. This doc is the durable reference: mechanism, concrete failure story, fix,
status._

**Verdict at review time: not production-ready — but the gaps are targeted fixes,
not an architectural rewrite.** The serious issues cluster in the resilience
machinery: the service could die silently and *stay* dead because the health check
couldn't see it, and an unguarded exception could abort the whole process.

| # | Where | One-liner | Severity | Status |
|---|-------|-----------|----------|--------|
| 1.1 | `room_manager.py` heartbeat_loop | one exception silently kills the SDK pump forever | Critical | ✅ fixed |
| 1.2 | `app.py` /health | health check physically can't fail → k8s never heals | Critical | ✅ fixed |
| 1.3 | all C++ trampolines | any callback raise can abort the whole process | Critical | ✅ fixed |
| 2.4 | pair/connection sinks | asyncio `Event.set()` from SDK thread; heartbeat masks it | High | ✅ fixed |
| 2.5a | `SDKCallMonitor.__init__` | bad `ZRC_SDK_SLOW_MS` env = boot crash-loop | High | ✅ fixed |
| 2.5b | `register_sinks_for_room` | premeeting sink unguarded; one bad room bricks startup | High | ✅ fixed |
| 2.5c | `create_room_service` | unguarded SDK call → opaque `NoneType` 500 on pair | High | ✅ fixed |
| 2.11 | `_reconnect_loop` | loop can spin forever after a zombie heals | High | ✅ fixed |
| 2.3 | reconnect/liveness loops | blocking SDK calls on the shared event loop | — | 🟡 accepted risk (monitored) |
| 3.6 | `meeting_reminder.py` | numeric strings & typos now 500 instead of 422/success | Medium | ✅ fixed |
| 3.7 | combined-consent route | resolves against the wrong enum table | Medium | ✅ fixed (int contract) |
| 4a | `_Broadcaster.emit` path | full JSON serialization even with zero WS listeners | Low | ✅ fixed |
| 4b | `initialize()` DB fallback | sqlite handle leaks if the query raises | Low | ✅ fixed |
| 4c | `_ws_subscribers` | annotation promises a session filter that was never built | Low | ✅ fixed |
| 4d | sink registration | ~150 lines of copy-paste that must mirror deregistration | Low | ✅ fixed (single table) |

---

## Tier 1 — Critical (silent or total outage)

### 1.1 Heartbeat loop dies permanently on one exception

**Was:** `heartbeat_loop` wrapped `sdk.HeartBeat()` in `try/except Exception:
logger.error(...); break`. The SDK is a reactor — `HeartBeat()` (150 ms, required
on Linux) is the pump that services its queues, network I/O, timers, and state
machine. One transient raise → `break` → the pump stops forever, with one log line,
while the process keeps serving HTTP.

**Failure story:** heartbeat dies at 3 AM → keepalives stop → ZR drops the TCP
session underneath the SDK → `GetConnectionState()` keeps reporting the *cached*
`Connected` (state transitions need the pump that's dead) → commands return
`NOT_CONNECT_TO_ZOOMROOM (11)` → no `Disconnected` callback ever fires → auto-
reconnect never triggers → `/health` still 200 → k8s never restarts. Fleet dead
until a human notices.

**Zombie connection (Connected + 11):** this is one of exactly two credible causes
of the zombie state observed live on 2026-08-04 — the other being an SDK-internal
state-machine wedge with a live heartbeat. The incident logs are gone, so it can't
be settled retroactively. Counter-evidence for the incident specifically: a full
re-pair *succeeded* without a restart, proving SDK network threads + callback
dispatch were alive (whether that also proves the heartbeat was alive depends on
undocumented SDK internals). Going forward the logs distinguish the two in seconds:
`HeartBeat error` in the log = this bug; liveness-loop zombie warnings with a
clean heartbeat log = SDK-internal wedge. The fix set covers both branches:
1.1-fix keeps the pump alive; the liveness loop heals SDK-internal zombies;
1.2-fix makes k8s restart anything neither can heal.

**Fix:** `continue` with a 1 s backoff instead of `break`. `CancelledError` is a
`BaseException`, so shutdown cancellation stays clean.

### 1.2 `/health` cannot say "unhealthy"

**Was:** the handler unconditionally returned a dict (FastAPI → HTTP 200) with a
hardcoded `"status": "healthy"`. Both the k8s `livenessProbe` and `readinessProbe`
point at it — a probe that can only return 200 is a smoke detector with no
battery; every failure it should auto-remediate becomes a human-paged incident.

**Fix:** returns **503** when the heartbeat task has exited (a completed
run-forever task = it crashed) or the SDK is gone after startup. The existing k8s
manifest starts working as designed with zero manifest changes; a pod restart is
a *correct* remediation here (creds persist in the volume, rooms re-pair
automatically — proven live).

### 1.3 Unguarded exceptions could abort the whole process

Two stacked gaps:

- **Python:** `emit()`'s try/except guards only `broadcast_event`. But kwargs are
  evaluated **in the sink method's frame before `emit()` is entered** — an
  expression like `count=len(meeting_list)` raising on an unexpected SDK shape was
  outside every guard.
- **C++:** all 136 trampolines called `py_sink.attr("OnX")(args)` with zero
  `try/catch` (grep: 0 `try`, 0 `error_already_set` in the file). A Python raise
  becomes `py::error_already_set` unwinding through the SDK's closed-source C++
  callback dispatcher → realistic outcome `std::terminate` → **all rooms die
  mid-callback**.

Low probability per event, total cost when it hits, 125 forwarded callbacks ×
every event of every meeting compounding the odds.

**Fix:** every trampoline forward is wrapped in
`try/catch (py::error_already_set) → discard_as_unraisable` (logged via
`sys.unraisablehook`, never crosses into the SDK). Value-returning sink methods
(`OnGetDeviceMacAddress` etc.) return safe fallbacks on error. Applied in the
generator template and mirrored byte-identical to `bindings/zrc_bindings.cpp`.

---

## Tier 2 — High (bad failure modes, startup crashes)

### 2.4 `asyncio.Event.set()` from the SDK callback thread

**Was:** `OnPairRoomResult` / `OnZRConnectionStateChanged` called
`pair_event.set()` / `connected_event.set()` directly from SDK C++ threads.
asyncio objects are single-thread; cross-thread signaling must use
`loop.call_soon_threadsafe` (which locks **and wakes the selector**). It worked by
accident: CPython's GIL makes the append atomic-ish, and the 150 ms heartbeat
guaranteed the loop ticked soon enough to notice. Two sharp edges: (a)
`PYTHONASYNCIODEBUG=1` makes `call_soon` raise on a foreign thread → crash through
the (then-guardless) trampoline on every pairing; (b) with the heartbeat dead
(1.1), `await pair_event.wait()` never wakes even though the callback fired.
`MeetingListHelperSink` did it correctly 85 lines away.

**Fix:** `_Broadcaster._set_threadsafe(event)` routes through the bound loop's
`call_soon_threadsafe`, falling back to a direct `set()` when no loop is bound
(tests, pre-startup). Audited the neighboring cross-thread entry points
(`schedule_reconnect` / `cancel_reconnect` / `mark_unpaired`) — already safe
(marshaled via `call_soon_threadsafe` internally).

### 2.5 Startup / pairing crashes on bad input

- **a — `ZRC_SDK_SLOW_MS`:** `float(env)` ran at module import (`app.py` builds
  `RoomManager()` at import). `ZRC_SDK_SLOW_MS: ""` or `"50ms"` → `ValueError` →
  uvicorn can't import the app → `CrashLoopBackOff` before any useful log. A
  tuning knob whose only failure mode is "service won't boot."
  **Fix:** parse guarded; warns and falls back to 50.
- **b — premeeting sink:** `GetPreMeetingService()` was dereferenced unguarded
  while all four sibling services (phone/setting/proAV/…) check `if service:`.
  At boot, `initialize()` restores every paired room with no per-room isolation —
  one bad room = `AttributeError` = the whole service fails startup, for all
  rooms, in a restart loop.
  **Fix:** guarded like the siblings; per-room restore wrapped so one room's
  failure logs and skips.
- **c — `create_room_service`:** dereferenced `CreateZoomRoomsService(room_id)`
  unguarded; the DB-restore path guards the identical call. A falsy return
  (malformed room_id, degraded SDK) surfaced as an opaque
  `'NoneType' object has no attribute 'RegisterSink'` 500 on the pair endpoint.
  **Fix:** returns None → pair endpoint raises a clear 502-style error naming the
  room.

### 2.11 Reconnect loop never exits after healing a zombie

**Was:** `_reconnect_loop`'s only exits: room unpaired, room removed, or
`cancel_reconnect()` — which fires in exactly one place:
`OnZRConnectionStateChanged(Connected)`. A zombie room's SDK *already believes*
it's Connected, so after `RetryToPairRoom` heals the transport the SDK plausibly
never re-fires `Connected` → the loop retries every 30 s **forever** — log spam,
monitor noise, misleading "reconnecting" about a healthy room.

**Fix:** at the top of each iteration: cached connection state is `Connected`
**and** `_probe_zombie()` says healthy → the room healed without a state change →
self-exit. Normal disconnects (state = `Disconnected`) keep looping as before.

### 2.3 Blocking SDK calls on the shared event loop — 🟡 accepted risk

The reconnect + liveness loops call `RetryToPairRoom()` / `GetMeetingStatus()`
synchronously on the single loop serving WS, heartbeat, and REST. The review
flagged the structure; live measurement says the calls are reactor-style enqueues
returning in ~ms even when the room is unreachable. The obvious fix
(`asyncio.to_thread`) is **wrong for this SDK** — the bindings never release the
GIL and the SDK is main-thread-affine. Decision: **keep on-loop, keep monitored**
— `SDKCallMonitor` wraps exactly these calls and `/health.sdk_call_timing`
surfaces any call over `ZRC_SDK_SLOW_MS` (50 ms). Revisit only if `slow_calls`
climbs in production.

---

## Tier 3 — Medium (API regressions from the enum-name work)

### 3.6 Reminder/consent endpoints: 500 instead of 422

**Was:** widening request fields to `int | str` (so clients can echo enum *names*
from events) changed pydantic v2 behavior for numeric strings: `"3"` used to
coerce to `3` on an `int` field (and succeed); on `int | str` it stays a string,
`getattr(Enum, "3")` → `AttributeError` → blanket handler → **HTTP 500**. Typo'd
names also 500'd. Bad input should be 4xx; a 500 misleads callers and trips
error-rate alerting. Applied to all 5 routes (confirm-reminder,
confirm-custom-reminder, confirm-consent, confirm-combined-consent,
handle-privacy).

**Fix:** `_resolve_enum` coerces digit-strings to int (restores the old
behavior), and unknown names/values raise **HTTP 422** listing the allowed enum
members. Routes re-raise `HTTPException` before their generic 500 handler.

### 3.7 Combined consent resolved against the wrong enum

**Was:** `confirm-combined-consent` resolved `notification_type` against
`MeetingReminderType` — a different surface's enum. A verifier traced the SDK
signature: `ConfirmCombinedConsent(bool, int64_t consentType)` where the value is
the **open int** carried in `OnCombinedConsentNotification.type` (serialized as a
plain int in our WS event — there are no names to echo).

**Contract decision (made 2026-08-10):** the field is the echoed
`CombinedConsent.type` integer. Accept ints and digit-strings; non-numeric
strings → 422 explaining the contract. No enum table involved — matches the SDK's
own "open int" design. (Same pattern as custom-reminder's
`customizedDisclaimerType`, which the SDK documents as deliberately open — the
review's refuted finding #2 confirmed that passthrough design.)

---

## Tier 4 — Low (efficiency / maintainability)

### 4a Serialization ran even with zero listeners
Kwargs-evaluate-first (see 1.3) meant every event was fully serialized —
recursive `dir()` reflection per struct — on SDK threads holding the GIL, then
dropped if no WS client was connected (the REST-only common case).
**Fix:** hot pure-emit callbacks check `mgr.has_listeners(room_id)` first
(defensive `getattr` so the contract test's capture manager still exercises
them); `_pybind_to_jsonable` memoizes the per-type field list instead of
re-running `dir()` per event.

### 4b sqlite handle leak in the startup DB fallback
`conn.close()` was skipped if `execute`/`fetchall` raised on a locked/corrupt
`third_zrc_data.db`. **Fix:** `contextlib.closing`.

### 4c `_ws_subscribers` annotation promised an unbuilt feature
Annotated `Dict[str, Dict[Queue, Optional[str]]]` with a documented per-subscriber
session filter; actual storage is a plain `set` and no filter code exists. A
maintainer trusting the annotation ships an `AttributeError`; a consumer trusting
the docs silently receives every session's events.
**Fix:** annotation + comment now tell the truth (`Dict[str, Set[asyncio.Queue]]`).

### 4d Sink registration copy-paste (~150 lines, hand-mirrored)
`register_sinks_for_room` hand-inlined the identical
get-helper→guard→create→RegisterSink→store→log block ~11 times — while the same
function already contained a data-driven loop for 4 other groups. The mirror that
must stay in lockstep (`_deregister_room_sinks`) is exactly the drift terrain
where the disjoint-static-map deregistration bug hid.
**Fix:** one `_SINK_SURFACES` table drives **both** registration and
deregistration — they can no longer drift. The in-image lifecycle test (23
surfaces) is the behavioral net.

---

## Refuted findings (the adversarial pass working)

1. *"`MeetingReminderType(bad_int)` raises ValueError"* — refuted: pybind's
   `py::enum_` is not a Python `IntEnum`; its constructor semantics differ.
2. *"custom-reminder wraps a type the SDK wants raw"* — refuted: the SDK header
   documents `customizedDisclaimerType` as a deliberately open `int32_t`; the
   int-passthrough design is correct (and 3.7 now follows the same pattern).

---

## Addendum (2026-08-12): found by the live e2e suite, not the review

### A16 Shadowed duplicate route: `POST /api/rooms/{room_id}/video/mute` — ✅ fixed

Defined twice: `meetings.py` (param `mute: bool = True`, registered first → wins)
and `meeting_video.py` (param `stop: bool` — **silently unreachable**). FastAPI
resolves duplicates by registration order and drops unknown query params, so a
caller sending `stop=false` (start video) hit the winner, lost the param, took
the `mute=True` default, and got a 200 that silently *stopped* video.

**Why the review missed it:** each route is locally correct; the defect only
exists in the *combination* across two files, and no finder angle diffed the
assembled route table. The live suite caught it because the scenario used the
shadowed route's parameter spelling and the expected event never came.

**Fix:** dead route removed; `mute` is now required (missing/wrong params 422
loudly instead of silently acting); `test_unit_routes.py` walks the assembled
app and rejects any `(method, path)` collision — this class of bug can't recur
silently.

**Also from the same investigation:** the live audio/video scenario is split so
the video half skips with a clear reason on camera-less rooms — the lab ZR has
no camera, and `UpdateMyVideo` there returns `ZRCSDKERR_CAMERA_DISABLED (102)`
on every code version (environmental, not a wrapper defect). Pre-release live
run: **9 passed, 5 documented skips, 0 failed**.

---

## The failure web (why Tier 1 mattered beyond its own bugs)

1.1, 1.2, 2.4, and 2.11 formed one interlocking web: the heartbeat accidentally
masked the thread bug (2.4), the health check masked the heartbeat dying (1.2),
and the reconnect loop depended on a callback the zombie case never fires (2.11).
Fixing 1.1 + 1.2 made the entire self-healing story — auto-reconnect, liveness
loop, k8s restarts — actually load-bearing instead of best-effort.
