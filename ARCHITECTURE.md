# Architecture — C++ SDK → Python → Clients

This service is a thin wrapper that exposes the native **Zoom Rooms C++ SDK** over
REST (commands) and WebSocket (live events). The key idea is that data flows in
**two directions** through the same layers:

- **Commands** travel *down*: client → REST → Python → pybind11 → C++ SDK → Zoom cloud → room.
- **Events** travel *up*: room → cloud → C++ SDK callback → pybind11 trampoline → Python sink → WebSocket → client.

## Layer stack

The same layers, traversed in opposite directions: each edge label reads
**⬇ command / ⬆ event**. One node per layer keeps the stack a clean vertical
spine — this is the orientation map; the diagrams further down zoom into the
parts that aren't a straight line.

```mermaid
flowchart TB
    clients["CLIENTS<br/>REST consumer (PlaceOS driver, Postman) · WebSocket subscriber"]
    app["FastAPI app — service/app.py<br/>router wiring · lifespan (startup: init SDK + HeartBeat)"]
    ctrl["Controllers — service/controllers/*.py<br/>rooms · meetings · participant · settings · … (REST)<br/>events.py → WS /api/rooms/{room_id}/events"]
    rm["RoomManager — service/room_manager.py<br/>SDK instance + HeartBeat (150 ms) · Python sinks (On* handlers)<br/>broadcaster: subscribe / broadcast_event / queues · per-room state"]
    bind["pybind11 module — zrc_sdk.*.so (from bindings/zrc_bindings.cpp)<br/>Interfaces · Enums · Structs · Sink trampolines (py::hasattr)"]
    sdk["Zoom Rooms C++ SDK — libZRCSdk.so (include/, libs/)"]
    zoom["Zoom Cloud ⇄ physical Zoom Room"]

    clients <-->|"⬇ HTTP command / ⬆ WS event stream"| app
    app <-->|"⬇ route / ⬆ broadcast_event()"| ctrl
    ctrl <-->|"⬇ call / ⬆ per-room queue"| rm
    rm <-->|"⬇ zrc_sdk method / ⬆ Python callback"| bind
    bind <-->|"⬇ C++ method call / ⬆ virtual callback"| sdk
    sdk <-->|"HTTPS (cloud-mediated, not LAN)"| zoom

    classDef ours fill:#dbeafe,stroke:#3b82f6,color:#12325a
    classDef seam fill:#fed7aa,stroke:#ea580c,color:#7c2d12
    classDef ext fill:#e5e7eb,stroke:#9ca3af,color:#374151
    class app,ctrl,rm ours
    class bind seam
    class clients,sdk,zoom ext
```

_Blue is our code, amber the C++ seam, grey what we don't own — the boundary
between "our Python" and "the closed SDK + Zoom" is the amber node._

## The C++ ↔ Python seam (pybind11 bridge)

Two mechanisms live in `bindings/zrc_bindings.cpp`:

| Direction | Mechanism | Example |
|---|---|---|
| **Python → C++** | `py::class_<Interface>().def("Method", &Interface::Method)` | `IMeetingService.StartInstantMeeting()` |
| **C++ → Python** | **Sink trampoline** — a C++ class implementing the SDK's `*Sink` interface that forwards each callback to a Python object via `py::hasattr` + `attr()` | `MeetingServiceSinkTrampoline::OnUpdateMeetingStatus` → Python `MeetingServiceSink.OnUpdateMeetingStatus` |

Callbacks can fire on an SDK-owned thread, so trampolines take the GIL
(`py::gil_scoped_acquire`) before calling Python, and `broadcast_event` hops onto
the event loop with `call_soon_threadsafe` before touching subscriber queues (see
the [threading model](#threading-model)).

**Enum encoding:** true SDK enums are emitted by **name** (`"MeetingStatusInMeeting"`),
derived from the pybind `py::enum_<>` registration; raw `int32_t` result/error codes
stay numeric (`0 = success`). The inbound path is symmetric — handlers accept an
enum name or int and resolve it against the same bound enum (`_resolve_enum`), so a
client can echo a captured name straight back without knowing the integer.

### A worked event

What actually crosses the wire when a participant joins — the SDK's typed C++
callback becomes a flat JSON event (this is the payload shape a consumer binds to,
which the box-by-box path can't show):

```jsonc
// SDK fires on an SDK thread:
//   IParticipantHelperSink::OnUserJoin(vector<MeetingParticipant>, ConfSessionType)
// → trampoline (GIL) → ParticipantHelperSink.OnUserJoin → emit() → WS client receives:
{
  "event": "OnUserJoin",
  "session": "ConfSessionTypeGeneral",          // enum → name
  "participants": [                              // struct vector → list of flat dicts
    { "userID": 16778240, "userName": "Alice", "isHost": true, "isMySelf": false }
  ]
}
```

## Key files

| Layer | File |
|---|---|
| C++ SDK | `include/`, `libs/libZRCSdk.so` |
| Bindings (source of truth) | `generator/templates/zrc_bindings.cpp` → copied to `bindings/zrc_bindings.cpp` |
| Compiled module | `service/zrc_sdk.*.so` (built by `build.sh` / Dockerfile) |
| SDK lifecycle + sinks + broadcaster | `service/room_manager.py` |
| REST endpoints | `service/controllers/*.py` |
| WebSocket endpoint | `service/controllers/events.py` |
| App wiring | `service/app.py` |
| K8s deployment (stable-MAC node) | `deploy/k8s/zoom-zrc.yaml` |

## Diagrams

Rendered natively by GitHub and most IDEs (Mermaid). Ordered as a reading path:
the domain map, how it's concurrent, how it's built, where it runs, its runtime
states, and how it ships.

**Colour language** (consistent across diagrams, and legible in light or dark):
🟦 **blue** = our Python · 🟧 **amber** = the C++/pybind seam · ⬜ **grey** =
external (closed SDK, Zoom cloud, rooms) · 🟪 **violet** = infra. In the lifecycle
diagram, 🟩/🟨/🟥 green·amber·red = healthy·transient·broken. Colour only
reinforces the labels — the text alone still carries the meaning.

### SDK service & sink object graph

The domain is a **tree**, not a line: from a paired room you reach every
capability by walking `Get*Service()` → `Get*Helper()`. `register_sinks_for_room`
walks exactly this tree and registers **one Python sink per node (23 total)**;
`remove_room` / the lifecycle test walk the same tree in reverse. This is the map
to consult when adding a sink or chasing "where does event X come from."

```mermaid
flowchart LR
    root["IZoomRoomsService<br/>· ZoomRoomsServiceSink"]

    root --> pre["IPreMeetingService<br/>· PreMeetingServiceSink"]
    root --> phone["IPhoneCallService<br/>· PhoneCallServiceSink"]
    root --> setting["ISettingService<br/>· SettingServiceSink"]
    root --> proav["IProAVService<br/>· ProAVServiceSink"]
    root --> meeting["IMeetingService<br/>· MeetingServiceSink"]

    pre --> cs["IControlSystemHelper"]
    pre --> byod["IBYODHelper"]

    setting --> cal["ICalibrationHelper"]

    proav --> hwio["IHWIOHelper"]
    proav --> dante["IDanteOutputHelper"]

    meeting --> mlist["IMeetingListHelper"]
    meeting --> mrem["IMeetingReminderHelper"]
    meeting --> part["IParticipantHelper"]
    meeting --> mctrl["IMeetingControlHelper"]
    meeting --> wait["IWaitingRoomHelper"]
    meeting --> rec["IRecordingHelper"]
    meeting --> audio["IMeetingAudioHelper"]
    meeting --> video["IMeetingVideoHelper"]
    meeting --> share["IMeetingShareHelper"]
    meeting --> layout["IMeetingViewLayoutHelper"]
    meeting --> cc["IClosedCaptionHelper"]
    meeting --> ndi["INDIHelper"]
```

_Every leaf also has its own `*Sink` (e.g. `IParticipantHelper` →
`ParticipantHelperSink`); omitted on the helpers to keep the tree legible._

### Threading model

The subtle part of the runtime: **two kinds of thread**, and one narrow bridge
between them. Everything Python-async lives on a **single event-loop thread**;
SDK callbacks arrive on **SDK-owned threads** you don't control. The only safe
crossing is `loop.call_soon_threadsafe`, and Python may only run on an SDK thread
while holding the GIL. Most timing bugs live at this boundary.

```mermaid
flowchart TB
    subgraph sdk["SDK-owned callback threads (many, not ours)"]
        cb["sink callback fires<br/>OnUserJoin · OnUpdateMeetingStatus · OnZRConnectionStateChanged"]
        gil["trampoline: py::gil_scoped_acquire"]
        emit["Python sink runs here, holding the GIL<br/>emit() · mark_unpaired() · schedule_reconnect()"]
        dev["device-info callbacks<br/>OnGetDeviceMacAddress → returns a value inline"]
        cb --> gil --> emit
    end

    subgraph loop["asyncio event loop — ONE thread"]
        heartbeat["HeartBeat: sdk.HeartBeat() every 150 ms"]
        handlers["REST handlers: await SDK calls"]
        reconnect["reconnect loop: RetryToPairRoom()"]
        sdkcall["⚠ all issue blocking C++ SDK calls on this one thread —<br/>a slow call stalls every room's REST + WS"]
        deliver["_deliver_event → per-subscriber asyncio.Queue<br/>drop-oldest + EventsDropped marker on overflow"]
        wsend["WS endpoint: await queue.get() → websocket.send_json"]
        heartbeat --> sdkcall
        handlers --> sdkcall
        reconnect --> sdkcall
        deliver --> wsend
    end

    emit ==>|"loop.call_soon_threadsafe()<br/><b>the only safe crossing</b>"| deliver

    classDef ours fill:#dbeafe,stroke:#3b82f6,color:#12325a
    classDef ext fill:#e5e7eb,stroke:#9ca3af,color:#374151
    classDef seam fill:#fed7aa,stroke:#ea580c,color:#7c2d12
    classDef bad fill:#fecaca,stroke:#dc2626,color:#7f1d1d
    class cb,dev ext
    class gil,emit seam
    class heartbeat,handlers,reconnect,deliver,wsend ours
    class sdkcall bad
```

_Two aspects share the single loop thread: the **command side** (HeartBeat,
handlers, reconnect all issue SDK calls) and the **delivery side** (queue →
WebSocket). A blocking SDK call on any of them stalls all of it — which is why
`RetryToPairRoom()` on the loop is a known sharp edge._

### Bindings: source of truth → compiled module

The C++ layer is **generated**, so there's a rule that's easy to break: edit the
template, never the copy. A test asserts the two stay byte-identical.

```mermaid
flowchart LR
    tmpl["generator/templates/<br/>zrc_bindings.cpp<br/>(SOURCE OF TRUTH)"]
    bind["bindings/<br/>zrc_bindings.cpp<br/>(byte-identical copy)"]
    so["service/zrc_sdk.*.so<br/>(compiled module)"]
    svc["service imports<br/>zrc_sdk"]

    tmpl -->|"copy · test_bindings_source<br/>enforces identical"| bind
    bind -->|"CMake + pybind11<br/>build.sh / Dockerfile"| so
    so --> svc

    classDef seam fill:#fed7aa,stroke:#ea580c,color:#7c2d12
    classDef ours fill:#dbeafe,stroke:#3b82f6,color:#12325a
    class tmpl,bind,so seam
    class svc ours
```

### System context & deployment topology

Where the service runs and who talks to whom. The SDK-visible MAC comes from the
dedicated node's retained ENI (`hostNetwork`), which is what makes pairing
credentials survive pod recreation (see FINDINGS.md §2–4).

```mermaid
flowchart TB
    subgraph clients["Clients"]
        rest["REST consumer<br/>(PlaceOS driver)"]
        ws["WebSocket subscriber<br/>(live events)"]
    end

    subgraph cluster["EKS cluster (namespace placeos)"]
        svc["Service zoom-zrc<br/>(ClusterIP :8000)"]
        subgraph node["Dedicated node ip-10-80-24-89 · us-west-2a"]
            pod["Pod zoom-zrc-0 (hostNetwork)<br/>FastAPI + RoomManager + zrc_sdk.so<br/>reads retained ENI eth0 = 02:ff:cb:fe:09:a3<br/>SDK keys creds off it → survives recreation"]
            pvc[("PVC data<br/>/root/.zoom/data<br/>pairing DB")]
        end
    end

    zoom["Zoom Cloud"]
    room1["Zoom Room A"]
    room2["Zoom Room B"]

    rest -->|HTTP commands| svc
    ws -->|WS event stream| svc
    svc --> pod
    pod --- pvc
    pod <-->|HTTPS - cloud-mediated, not LAN| zoom
    zoom <--> room1
    zoom <--> room2

    classDef infra fill:#ede9fe,stroke:#8b5cf6,color:#4c1d95
    classDef ext fill:#e5e7eb,stroke:#9ca3af,color:#374151
    class svc,pod,pvc infra
    class rest,ws,zoom,room1,room2 ext
```

### Room connection lifecycle

The `RetryToPairRoom` result discriminates the two failure modes: `SUCCESS` =
transient (auto-reconnect handles it), `INTERNAL_ERROR` = credentials dead
(MAC changed — needs a fresh activation code).

```mermaid
stateDiagram-v2
    direction TB
    [*] --> Unpaired
    Unpaired --> Pairing: POST /pair (code)
    Pairing --> Unpaired: failed / timeout
    Pairing --> Connected: paired
    Connected --> Disconnected: connection lost
    Disconnected --> Reconnecting: schedule_reconnect()
    Reconnecting --> Reconnecting: backoff 5→10→20→30s
    Reconnecting --> Connected: RetryToPairRoom SUCCESS
    Reconnecting --> CredsDead: RetryToPairRoom INTERNAL_ERROR
    Connected --> RemoteUnpaired: OnRoomUnpairedReason (ZR side)
    Connected --> Unpaired: POST /unpair (remove_room, deregister all sinks)
    RemoteUnpaired --> Unpaired: re-pair (clears flag)
    CredsDead --> Unpaired: re-pair (fresh code)

    classDef good fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef warn fill:#fef08a,stroke:#ca8a04,color:#713f12
    classDef bad fill:#fecaca,stroke:#dc2626,color:#7f1d1d
    class Connected good
    class Reconnecting warn
    class RemoteUnpaired warn
    class CredsDead bad
```

_`CredsDead` = credentials can't decrypt (MAC changed); the `RetryToPairRoom`
result is the discriminator between a transient drop and dead credentials._

### Build & deploy pipeline

Immutable image tags derived from the commit; tests gate the registry push;
deploys are a manual `set image` with the minted tag.

```mermaid
flowchart LR
    dev["git push<br/>(feat/ws)"] --> gha["GitHub Actions"]
    subgraph gha_steps["CI (blocks on any failure)"]
        build["docker build<br/>linux/amd64"] --> t1["contract tests<br/>(124 callbacks)"]
        t1 --> t2["lifecycle tests<br/>(23 sink surfaces)"]
        t2 --> t3["unit + smoke<br/>(pytest, live container)"]
    end
    gha --> gha_steps
    t3 -->|all green| hub[("Docker Hub<br/>placeos/zoom-zrc:branch-sha")]
    hub -.->|operator:<br/>kubectl set image| sts["StatefulSet zoom-zrc"]
    sts -->|recreates pod,<br/>node pulls image| pod2["zoom-zrc-0"]
```
