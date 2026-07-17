# Architecture — C++ SDK → Python → Clients

This service is a thin wrapper that exposes the native **Zoom Rooms C++ SDK** over
REST (commands) and WebSocket (live events). The key idea is that data flows in
**two directions** through the same layers:

- **Commands** travel *down*: client → REST → Python → pybind11 → C++ SDK → Zoom cloud → room.
- **Events** travel *up*: room → cloud → C++ SDK callback → pybind11 trampoline → Python sink → WebSocket → client.

## Layer stack

```
┌─────────────────────────────────────────────────────────────────────┐
│  CLIENTS                                                             │
│    REST consumer (PlaceOS driver, Postman)      WebSocket subscriber │
└───────────────┬─────────────────────────────────────────┬───────────┘
                │ HTTP  (commands / queries)               │ WS  (event stream)
                ▼                                          ▲
┌─────────────────────────────────────────────────────────────────────┐
│  FastAPI app  —  service/app.py                                     │
│    router wiring · lifespan (startup: init SDK + HeartBeat)         │
├─────────────────────────────────────────────────────────────────────┤
│  Controllers  —  service/controllers/*.py                           │
│    rooms · meetings · participant · settings · …   (REST endpoints) │
│    events.py  →  WS /api/rooms/{room_id}/events    (subscribe)      │
└───────────────┬─────────────────────────────────────────┬───────────┘
                │ calls                                     ▲ broadcast_event()
                ▼                                          │  (per-room queues)
┌─────────────────────────────────────────────────────────────────────┐
│  RoomManager  —  service/room_manager.py                            │
│    • holds SDK instance + HeartBeat loop (every 150 ms)            │
│    • Python sink classes  (On* handlers)   ◀── receive callbacks    │
│    • event broadcaster: subscribe / broadcast_event / queues        │
│    • per-room state (connection, meeting status)                    │
└───────────────┬─────────────────────────────────────────▲───────────┘
                │ import zrc_sdk                            │ Python callback
                ▼                                          │
┌─────────────────────────────────────────────────────────────────────┐
│  pybind11 module  —  zrc_sdk.*.so                                   │
│  (compiled from bindings/zrc_bindings.cpp)                         │
│    • Interfaces:  IZRCSDK · IZoomRoomsService · IMeetingService ·   │
│      IParticipantHelper · helpers…            (.def methods)        │
│    • Enums:  MeetingStatus · ConnectionState · ExitMeetingReason…  │
│    • Structs: MeetingParticipant · MeetingInfo…                    │
│    • Sink trampolines (duck-typed py::hasattr) ──► call into Python │
└───────────────┬─────────────────────────────────────────▲───────────┘
                │ C++ method call                          │ C++ virtual callback
                ▼                                          │
┌─────────────────────────────────────────────────────────────────────┐
│  Zoom Rooms C++ SDK  —  libZRCSdk.so   (include/, libs/)            │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │ HTTPS (cloud-mediated, not LAN)
                                  ▼
                        Zoom Cloud  ⇄  physical Zoom Room
```

## Command path (Python → C++ → room)

```
Client ──POST /api/rooms/{id}/pair──► controller (rooms.py)
      └─► RoomManager.get_room_service(id)
            └─► zrc_sdk.IZoomRoomsService.PairRoomWithActivationCode(code)   [pybind .def]
                  └─► C++ SDK  ──HTTPS──►  Zoom Cloud  ──►  Zoom Room
```

## Event path (room → C++ → Python → client)  ← what the WebSocket adds

```
Zoom Room ──► Zoom Cloud ──► C++ SDK fires virtual callback, e.g.
   IParticipantHelperSink::OnUserJoin(vector<MeetingParticipant>, ConfSessionType)
        │
        ▼   pybind11 trampoline  (ParticipantHelperSinkTrampoline)
   py::hasattr(py_sink,"OnUserJoin") ? py_sink.attr("OnUserJoin")(participants, session)
        │
        ▼   Python sink  (room_manager.py :: ParticipantHelperSink)
   def OnUserJoin(...):  self.emit("OnUserJoin", participants=[...], session=_enum_name(session))
        │
        ▼   RoomManager.broadcast_event(room_id, payload)
   loop.call_soon_threadsafe(_deliver_event)  →  per-subscriber asyncio.Queue
        │
        ▼   WS endpoint  (controllers/events.py)
   await websocket.send_json(payload)
        │
        ▼   Client receives:
   {"event":"OnUserJoin","session":"ConfSessionTypeGeneral","participants":[{"userID":…,"userName":…}]}
```

## The pybind11 bridge (the C++ ↔ Python seam)

Two mechanisms live in `bindings/zrc_bindings.cpp`:

| Direction | Mechanism | Example |
|---|---|---|
| **Python → C++** | `py::class_<Interface>().def("Method", &Interface::Method)` | `IMeetingService.StartInstantMeeting()` |
| **C++ → Python** | **Sink trampoline** — a C++ class implementing the SDK's `*Sink` interface that forwards each callback to a Python object via `py::hasattr` + `attr()` | `MeetingServiceSinkTrampoline::OnUpdateMeetingStatus` → Python `MeetingServiceSink.OnUpdateMeetingStatus` |

Callbacks can fire on an SDK thread, so trampolines take the GIL (`py::gil_scoped_acquire`)
before calling Python, and `broadcast_event` hops onto the event loop with
`call_soon_threadsafe` before touching subscriber queues.

**Enum encoding:** true SDK enums are emitted by **name** (`"MeetingStatusInMeeting"`),
derived from the pybind `py::enum_<>` registration; raw `int32_t` result/error codes
stay numeric (`0 = success`).

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
