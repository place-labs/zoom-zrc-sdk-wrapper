---
name: add-sink
description: Wire a new SDK sink surface (event callbacks) end-to-end. Use when adding a sink, helper sink, or new SDK callback interface — there are several hand-maintained mirrors that drift silently if any step is skipped.
---

# Add a sink surface

A sink surface = one SDK interface with `RegisterSink`/`DeregisterSink` plus a
Python sink class receiving its callbacks. Every step below is load-bearing; the
mirrors in steps 4–6 fail silently when skipped.

## Checklist

1. **Bindings — edit `generator/templates/zrc_bindings.cpp`** (source of truth):
   - Trampoline class holding the `py::object`, with `py::gil_scoped_acquire` in
     every callback before touching Python.
   - `RegisterSink`/`DeregisterSink` lambdas that share
     `auto& sinks = SinkRegistry<IFace, FaceTrampoline>();` — NEVER a
     `static std::map` inside a lambda body (per-lambda static = deregistration
     permanently broken; `test_bindings_source.py` rejects it).
   - Copy the file byte-identically to `bindings/zrc_bindings.cpp`.

2. **Python sink class** in `service/room_manager.py` — follow an existing sink:
   `__init__(self, room_id)`, callbacks that `self.emit(...)` flat JSON-able
   payloads (`_enum_name` for enums, `_pybind_to_jsonable` for structs).

3. **Store + registration**:
   - Sink store dict in `RoomManager.__init__` — name MUST end in `_sinks`
     (cleanup tests discover stores by that convention).
   - Register in `register_sinks_for_room` (set `sink.mgr = self`, check
     `ZRCSDKERR_SUCCESS`, store on success).

4. **Mirror: deregistration** — add the surface to
   `RoomManager._deregister_room_sinks` `surfaces()` generator.
   (Guarded: `test_remove_room_deregisters_every_registered_surface` fails if
   you forget.)

5. **Mirror: lifecycle test** — add the surface to `surfaces()` in
   `service/test_sink_lifecycle.py`.
   (Guarded: `test_lifecycle_test_covers_every_deregistered_surface` fails if
   this list drifts from `_deregister_room_sinks` — same label string required.)

6. **Contract test** — automatic: `test_sink_contracts.py` parses the
   trampolines, so the new callbacks are covered without edits. If a callback
   takes a struct the fabricator can't build, it reports ERROR — fix, don't skip.

7. **Verify** with `/run-tests` (contract count grows past 124, lifecycle past
   23 — update the baselines in the run-tests skill), then changelog the new
   events.
