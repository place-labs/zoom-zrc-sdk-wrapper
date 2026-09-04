# Zoom ZRC SDK Wrapper

FastAPI microservice wrapping the Zoom Rooms C++ SDK (pybind11 bindings), deployed
as a Docker image. REST + WebSocket API for pairing rooms, driving meetings, and
streaming SDK events.

## Invariants — never violate these

- **`generator/templates/zrc_bindings.cpp` is the source of truth** for
  `bindings/zrc_bindings.cpp`; the two files must stay **byte-identical**
  (`test_bindings_source.py` enforces this). Edit the template, copy to bindings —
  or edit bindings and copy back — never let them diverge.
- **Sink Register/Deregister pairs must use the shared `SinkRegistry<Iface, Trampoline>()`**
  — a `static std::map` declared inside a lambda body is per-lambda and breaks
  deregistration silently.
- **Any script that instantiates the SDK must exit via `os._exit()`** (see
  `service/app.py` lifespan): the SDK holds `py::object`s in C++ statics whose
  teardown after `Py_Finalize` aborts the process.
- **Never change the pinned `mac_address` in `docker-compose.yml`** — the SDK
  encrypts stored room credentials with a key derived from the NIC MAC; changing it
  orphans all pairings.
- The SDK ships **x86_64-only**: always build/run Docker with `--platform linux/amd64`.

## Workflow rules

- Run `pytest -m unit` before every commit (hermetic, <1s, needs only
  `requirements-dev.txt`). Full verification: `/run-tests`.
- Adding a sink surface touches multiple hand-maintained mirrors — use `/add-sink`.
- Releases follow the changelog/version/tag ritual — use `/release`. Never edit a
  released CHANGELOG.md section; new work gets a new version section.
- Test suites and what each one needs: see `TESTING.md`.
