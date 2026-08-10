 # Changelog

## [Unreleased]

### Added
- **Wireless sharing key over the WebSocket** — the meeting-share sink now forwards `OnUpdateAirPlayBlackMagicStatus`, giving subscribers asynchronous updates whenever the room's AirPlay / direct-presentation status changes. The event's `status` carries `directPresentationSharingKey` (the code users enter at share.zoom.us / the Zoom app to present to the room) and `directPresentationPairingCode`. The SDK exposes this **push-only** (no getter), and the C++ trampoline previously stubbed the callback as a no-op (`override {}`), so the key never reached the API. Now the template + bindings forward it (GIL-guarded, byte-identical); the `AirplayBlackMagicStatus` struct was already bound. Contract coverage 124 → 125 callbacks; new unit test `test_unit_share_airplay.py`

## [1.4.0] - 2026-08-05 - Code-Review Hardening, Test Suites & CI Gating

### Major Changes

#### 🐞 Code-Review Fixes
- **Sink deregistration actually works now** — each `RegisterSink`/`DeregisterSink` binding pair declared its own lambda-local `static std::map`, so deregistration always consulted an empty map, returned `ZRCSDKERR_INTERNAL_ERROR`, and left the trampoline registered with the SDK forever (events kept flowing after unpair; trampolines stacked up across pair/unpair cycles). Both lambdas now share one `SinkRegistry<Iface, Trampoline>()` map
- **Full cleanup on unpair/shutdown** — new `RoomManager.remove_room()` stops the reconnect loop, deregisters **all 23** sink surfaces (mirroring registration), and purges every per-room sink store. Previously the unpair endpoint cleaned only 3 legacy stores and left the rest live; `shutdown()` covered only 5 surfaces
- **Startup failures exit non-zero** — the lifespan's `os._exit(0)` also ran when startup raised, logging `✓ Microservice stopped` and exiting 0 (so `restart: on-failure` never restarted the container). Startup errors now propagate; only a clean shutdown reaches the hard exit
- **Auto-reconnect survives remote unpair → re-pair** — re-pairing a room whose service was still cached returned early without clearing the unpaired flag, permanently disabling self-healing for that room
- **Slow WebSocket consumers learn about dropped events** — on queue overflow the subscriber now receives one `{"event": "EventsDropped", "count": N}` marker before the surviving events (the gap precedes everything still queued) instead of silently losing state
- **`isMyself` restored** — the backwards-compat alias on `MeetingParticipant` had been dropped, an `AttributeError` for external consumers of the compiled module
- **Reminder/consent handlers accept enum names, not just ints** — the event stream emits SDK enums by name, so a client echoing a captured value back sends the name; the four reminder/consent endpoints (`confirm-reminder`, `confirm-custom-reminder`, `confirm-consent`, `confirm-combined-consent`) now resolve `int | str` against the wrapper's own bound enums via `_resolve_enum`, closing the round-trip so nothing outside the wrapper needs the integer mapping. Consent now passes a real `ConsentType` enum (was a raw int). Ints still accepted — non-breaking
- **`handle-privacy` no longer 500s** — the handler read `request.notification_type`, a field `PrivacyRequest` never had (dead + crashing line); removed. Its enums resolve `int | str` too, and the duplicated `handle_privacy_alert` function name (continue-on-inactivity route) was renamed `continue_on_inactivity`

#### 🧪 Test Suites (see `TESTING.md`)
- **Unit** (`pytest -m unit`, `service/tests/`) — hermetic suite against a fake SDK (`_zrc_stub.py`), no compiled module / server / room: connection lifecycle (`remove_room`, re-pair flag, overflow marker), unpair endpoint via in-process FastAPI, lifespan exit codes via subprocess, and bindings source contracts (shared sink registry, `isMyself` alias, generator template byte-identical to bindings)
- **Contract** (`service/test_sink_contracts.py`, in-image) — every forwarded SDK callback serializes to a valid, once-only WS payload (124 callbacks)
- **Lifecycle** (`service/test_sink_lifecycle.py`, in-image) — RegisterSink/DeregisterSink cycle through the compiled bindings on every sink surface, against the real SDK (the layer where the disjoint-static-map bug lived)
- **Smoke / live e2e** (`service/tests/test_api.py`) — safe API checks against a running service; `@live`-marked meeting-flow tests for a real paired room (manual, pre-release)

#### 🐳 CI Pipeline (test-gated publishing)
- `dockerhub-build-push.yml` now builds the image once, runs **contract → lifecycle → unit + smoke** against it, and only pushes to Docker Hub if everything passes; pytest results upload as a JUnit artifact

### Modified Files

#### Bindings
- **`bindings/zrc_bindings.cpp`** — shared `SinkRegistry` for all Register/Deregister pairs; `isMyself` alias restored
- **`generator/templates/zrc_bindings.cpp`** — mirrored _(source of truth)_

#### Service
- **`service/room_manager.py`** — `remove_room()` full-cleanup path; `_SubscriberQueue` with `EventsDropped` overflow marker; re-pair clears the unpaired flag; `SDKCallMonitor` times loop-thread SDK calls (`RetryToPairRoom`/`HeartBeat`/pairing) and flags any slow enough to stall the fleet, threshold via `ZRC_SDK_SLOW_MS` (default 50 ms)
- **`service/controllers/rooms.py`** — unpair now delegates to `remove_room()`; pairing call timed via `sdk_monitor`
- **`service/app.py`** — `/health` now includes `sdk_call_timing` (calls, slow_calls, max_ms, recent slowest) — live SDK-call latency, readable without grepping logs
- **`service/controllers/meeting_reminder.py`** — `_resolve_enum` (int-or-name); widened request models to `int | str`; consent passes a real `ConsentType`; removed the crashing `handle-privacy` line; renamed the duplicate `handle_privacy_alert`
- **`service/app.py`** — `os._exit(0)` only on clean shutdown; startup failures propagate

#### Tests & CI
- **`service/tests/`**, **`service/test_sink_lifecycle.py`**, **`pytest.ini`**, **`requirements-dev.txt`** _(new)_
- **`service/test_sink_contracts.py`** — capture manager grew reconnect-hook no-ops
- **`.github/workflows/dockerhub-build-push.yml`** — build → test → push gating

#### Documentation
- **`TESTING.md`** _(new)_ — the five suites, what each needs, and what CI runs
- **`ARCHITECTURE.md`** — reworked the diagram set to favor structure over redundant linear traces: added the **SDK service & sink object graph** (the 23-node domain tree that `register_sinks_for_room`/`remove_room` walk), the **threading model** (SDK callback threads vs the single asyncio loop, and the `call_soon_threadsafe`/GIL boundary where the timing bugs live), and a **bindings source-of-truth** codegen flow; kept the layer stack, deployment topology, lifecycle state machine, and CI/CD pipeline; dropped the command-path and event-path box-chains (folded into a worked JSON example) and the flat event-delivery sequence (subsumed by the threading model). A **consistent, light/dark-safe colour language** (blue = our Python · amber = the C++ seam · grey = external · violet = infra; green/amber/red = healthy/transient/broken states) now encodes ownership and health across every diagram; deployment annotated with the live node/ENI MAC. All diagrams verified by rendering in both light and dark backgrounds.
- **`CHANGELOG.md`** — this entry

#### Deployment
- **`deploy/k8s/zoom-zrc.yaml`** _(new)_ — stable-MAC EKS deployment: `hostNetwork` StatefulSet pinned to the dedicated self-managed node whose retained primary ENI supplies the SDK-visible MAC, with PVC for the pairing DB and a pre-pairing verification runbook. Replaces the pod-network StatefulSet whose per-recreation MAC invalidated stored room credentials (FINDINGS.md §2–4)

#### Claude Code Project Config
- **`CLAUDE.md`** _(new)_ — repo invariants (template/bindings sync, `os._exit` rule, pinned MAC, amd64-only SDK) and workflow rules, loaded into every session
- **`.claude/skills/`** _(new)_ — `run-tests` (suite sequence + expected counts), `add-sink` (the five hand-maintained mirrors), `release` (changelog/version/tag ritual), `sdk-upgrade` (pin bump → stub → verify)
- **`.claude/workflows/sink-audit.js`** _(new)_ — per-surface multi-agent drift audit across bindings, registration, cleanup, and test coverage
- **`.claude/agents/bindings-auditor.md`** _(new)_ — read-only reviewer for the pybind11 layer (registry sharing, template sync, GIL, exception containment, API stability, static teardown)
- **`.claude/settings.json`** _(new)_ — shared permission allowlist (docker/pytest/git read-ops); `settings.local.json` gitignored

## [1.3.0] - 2026-07-23 - Live WebSocket Streaming & Connection Resilience

### Major Changes

#### 📡 Live WebSocket Event Streaming
- New endpoint **`GET /api/rooms/{room_id}/events`** — per-room live stream of SDK callbacks as flat JSON, delivered as they fire
- Enums emitted **name-only** (e.g. `MeetingStatusInMeeting`); raw `int32_t` result/error codes stay numeric; struct payloads pass through in full, curation left to the consumer
- Idle **keepalive** frame every 30s; per-room subscriber registry with a bounded, drop-oldest queue; SDK-thread callbacks marshalled to the event loop via `call_soon_threadsafe`

#### 🔔 New Event Sinks
- Meeting lifecycle & participants — **`MeetingServiceSink`** (`OnUpdateMeetingStatus`, meeting info) and **`ParticipantHelperSink`** (roster init, join / leave / update)
- Resolves the four sinks left **Pending** in 1.2.0 — **`RecordingHelperSink`**, **`MeetingAudioHelperSink`**, **`MeetingVideoHelperSink`**, **`MeetingShareHelperSink`**
- Calls & devices — **`PhoneCallServiceSink`**, **`SettingServiceSink`**
- Layout & captions — **`MeetingViewLayoutHelperSink`**, **`ClosedCaptionHelperSink`**
- Pro AV & infrastructure — **`ProAVServiceSink`**, **`HWIOHelperSink`**, **`DanteOutputHelperSink`**, **`NDIHelperSink`**, **`ControlSystemHelperSink`**, **`BYODHelperSink`**, **`CalibrationHelperSink`**
- All stream over the WebSocket and register per room; high-value/state callbacks forwarded, deep-nested-struct callbacks stubbed

#### ♻️ Auto-Reconnect
- On `OnZRConnectionStateChanged` → `Disconnected`, a per-room backoff loop (5s → 10s → 20s → cap 30s) calls `RetryToPairRoom()` until reconnected, then stops on `Connected`
- Gives up (and does not restart) on `OnRoomUnpairedReason`; re-pairing clears the flag. Connection lifecycle is owned by the wrapper — consumers just observe state over the WebSocket

#### 🔐 Paired-Credential Persistence
- `docker-compose.yml` pins a fixed **`mac_address`** — the SDK keys its `ZRCSDK.conf` credential encryption off the NIC MAC, and Docker's per-start random MAC made stored credentials undecryptable (`sqlcipher … hmac check failed` → `RetryToPairRoom` returns `ZRCSDKERR_INTERNAL_ERROR`). A stable MAC keeps pairings across restarts and rebuilds
- **Never change the pinned MAC once set** — it orphans the encrypted credentials and forces re-pairing

#### 🩹 Stability Fixes
- **GIL guards** — `SimpleSinkImpl`'s 11 device-info callbacks now `py::gil_scoped_acquire` before touching Python, matching every other trampoline
- **Clean shutdown** — `app.py` hard-exits with `os._exit(0)`; the SDK's static `RegisterSink` registries hold `py::object`s destroyed after `Py_Finalize` (`thread state is NULL`, `signal 6`), so skipping finalization eliminates the shutdown/restart crash

#### 🐳 Build
- **`docker-compose.yml`** — added `platform: linux/amd64` (the SDK ships x86_64-only; matches prod, emulates on Apple Silicon)

#### 📝 Documentation
- **`DOCKER.md`** — pinned-MAC requirement and `platform: linux/amd64` configuration
- **`README.md`** — pinned-MAC persistence note; auto-reconnect / connection-lifecycle behavior

### Modified Files

#### Bindings
- **`bindings/zrc_bindings.cpp`** — `MeetingServiceSink` + `ParticipantHelperSink` trampolines; GIL guards on `SimpleSinkImpl`
- **`generator/templates/zrc_bindings.cpp`** — mirrored _(source of truth)_

#### Service
- **`service/room_manager.py`** — WebSocket subscriber registry & broadcast, meeting/participant sink classes, per-room auto-reconnect
- **`service/controllers/events.py`** — WebSocket `/api/rooms/{room_id}/events` endpoint _(new)_
- **`service/app.py`** — event-router wiring; `os._exit(0)` shutdown fix

#### Docker
- **`docker-compose.yml`** — pinned `mac_address`, `platform: linux/amd64`

#### Documentation
- **`DOCKER.md`** — pinned-MAC + platform configuration
- **`README.md`** — pinned-MAC note; auto-reconnect / connection-lifecycle

## [1.2.0] - 2026-07-16 - SDK 7.1 Upgrade & Call-Control Sinks

### Major Changes

#### ⬆️ Zoom Rooms SDK `6.7.0.1264` → `7.1.0.523`
- Docker build pulls the new version automatically via `sdk-version.lock`
- **Requires C++17** — 7.1.0 adds `std::optional` params (`AssignHost` / `AssignCohost`)

#### 🔔 New Event Sinks
- **`MeetingControlHelperSink`** — AI Companion prompts, meeting lock, focus mode, live stream, archiving, smart summary, side panel
- **`WaitingRoomHelperSink`** — admission & silent-mode events, plus admit / admit-all / put-back actions
- Both stream over the existing WebSocket and register per room

#### 🩹 SDK 7.0+ Compatibility
- No-op trampoline stubs for new callbacks so existing sinks stay concrete — `OnZRWarningNotification`, `OnConsolidatedCustomizedConsentNotification`, `OnShowParticipantLocalTimeNotification`

#### 📝 Documentation
- Troubleshooting for pairing **error 100** and the Docker `172.17.0.0/16` subnet collision

### Modified Files

#### SDK & Build
- **`sdk-version.lock`** — pin → `7.1.0.523`
- **`CMakeLists.txt`, `CMakeLists.docker.txt`** — `CMAKE_CXX_STANDARD` 14 → 17

#### Bindings
- **`generator/templates/zrc_bindings.cpp`** — trampolines, `RegisterSink`, structs/enums, compat stubs _(source of truth)_
- **`bindings/zrc_bindings.cpp`** — regenerated from template

#### Service
- **`service/room_manager.py`** — new sink classes + per-room registration

#### Documentation
- **`DOCKER.md`** — error-100 / subnet-collision troubleshooting
- **`README.md`** — build requirement C++14 → C++17

### Pending

Not yet wired: `IRecordingHelper`, `IMeetingAudioHelper`, `IMeetingVideoHelper`, `IMeetingShareHelper`.

## [1.1.0] - 2025-10-16 - Self-Contained Setup

### Major Changes

#### ✨ Fully Self-Contained Wrapper
- SDK is now automatically downloaded during build process
- No external dependencies - everything contained in wrapper/ directory
- Downloads SDK from: https://nws.zoom.us/nws/pkg/1.0/package/download?identifier=us.zoom.ZRC.SDK.LINUX&arch=x86_64

#### 📦 Git-Friendly Structure
- Added comprehensive .gitignore
- Excludes SDK binaries (Demo/, include/, libs/)
- Excludes build artifacts (build/, *.so)
- Only source code committed to version control

#### 🐳 Docker Improvements
- Dockerfile now downloads SDK automatically
- No need for parent directory context
- Self-contained build process
- Fixed LD_LIBRARY_PATH configuration

#### 📝 Documentation
- Added SELF_CONTAINED_SETUP.md - Complete setup guide
- Updated README.md with Docker-first approach
- Updated STATUS.md to reflect self-contained nature
- All docs emphasize automatic SDK download

### Modified Files

#### Build Scripts
- `build.sh` - Added automatic SDK download and extraction
- `run_service.sh` - Updated library paths to use local SDK
- `CMakeLists.txt` - Changed SDK paths from parent to local directory

#### Docker Configuration
- `Dockerfile` - Now downloads and extracts SDK during build
- `docker-compose.yml` - Updated context and library paths
- Fixed environment variable: `LD_LIBRARY_PATH=/app/libs`

#### Version Control
- `.gitignore` - Comprehensive exclusions for SDK and binaries

### Technical Details

#### SDK Download Process
```bash
# In build.sh
SDK_URL="https://nws.zoom.us/nws/pkg/1.0/package/download?identifier=us.zoom.ZRC.SDK.LINUX&arch=x86_64"
curl -L "$SDK_URL" -o zrc_sdk.zip
unzip -q -o zrc_sdk.zip
```

#### Directory Structure Changes
**Before:**
```
zoom/
├── include/          # SDK headers (manual)
├── libs/             # SDK libraries (manual)
└── wrapper/          # Wrapper code
```

**After:**
```
zoom/wrapper/         # Self-contained
├── include/          # Downloaded automatically
├── libs/             # Downloaded automatically
├── Demo/             # Downloaded automatically
└── [source files]    # Committed to git
```

### Testing

All functionality verified:
- ✅ Local build with automatic SDK download
- ✅ Docker build with automatic SDK download
- ✅ Service startup and API endpoints
- ✅ SDK initialization and room restoration
- ✅ Health checks passing

### Performance

- SDK download: 30.9 MB, 4-6 seconds
- Local build time: 10-15 seconds (after download)
- Docker build time: 60-90 seconds (including download)
- No performance degradation from previous version

### Migration Guide

If you have the old setup with SDK in parent directory:

```bash
# 1. Pull latest changes
cd /home/steve/projects/zoom/wrapper
git pull

# 2. Clean old build artifacts
rm -rf build service/*.so

# 3. Rebuild (automatically downloads SDK)
./build.sh

# 4. Run service
./run_service.sh
```

For Docker:
```bash
# 1. Pull latest changes
git pull

# 2. Rebuild with new Dockerfile
docker-compose build --no-cache

# 3. Start service
docker-compose up -d
```

### Known Issues

None. All previous functionality maintained.

### Breaking Changes

None. API remains unchanged. Only build process updated.

---

## [1.0.0] - 2025-10-16 - Initial Release

### Features

- ✅ pybind11 C++ bindings for Zoom Rooms SDK
- ✅ FastAPI REST API microservice
- ✅ Docker and docker-compose support
- ✅ Automatic room restoration on startup
- ✅ Multi-room support
- ✅ Health check endpoints
- ✅ SDK HeartBeat loop (150ms)

### SDK Methods Exposed

**Core SDK (IZRCSDK)**
- GetInstance()
- HeartBeat()
- CreateZoomRoomsService()
- RegisterSDKSink()
- QueryAllZoomRoomsServices()

**Room Service (IZoomRoomsService)**
- PairRoomWithActivationCode()
- UnpairRoom()
- RetryToPairRoom()
- GetMeetingService()
- GetPreMeetingService()

**Meeting Service (IMeetingService)**
- StartInstantMeeting()
- JoinMeeting()
- ExitMeeting()

**Pre-Meeting Service (IPreMeetingService)**
- GetConnectionState()

### Documentation

- README.md - Quick start and API usage
- STATUS.md - Build status and features
- DOCKER.md - Docker deployment guide
- DOCKER_DEPLOYMENT_SUMMARY.md - Docker technical details
