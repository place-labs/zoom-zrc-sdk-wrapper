---
name: sdk-upgrade
description: Upgrade the pinned Zoom Rooms SDK version and absorb its API changes. Use when bumping sdk-version.lock, moving to a new ZRC SDK release, or diagnosing build breaks after an SDK change.
---

# SDK upgrade ritual

The SDK is closed-source, x86_64-only, and downloaded at image build time from
the pin in `sdk-version.lock`. Upgrades break in two ways: compile errors (new
pure-virtual callbacks make existing trampolines abstract) and runtime/ABI
drift (struct fields renamed or retyped). The suites catch both — in the image.

## 1. Bump the pin

Update `sdk-version.lock` to the new version string.

## 2. Build — expect trampoline breaks

```bash
docker build --platform linux/amd64 -t zrc-ci:test .
```

New pure-virtual sink callbacks fail the compile. For each: add a **no-op
trampoline stub** in `generator/templates/zrc_bindings.cpp` (see the 7.0
compat stubs, e.g. `OnZRWarningNotification`, for the pattern) unless the
callback is worth forwarding — then wire it fully via `/add-sink`. Copy the
template to `bindings/` byte-identically. Language-standard bumps go in BOTH
`CMakeLists.txt` and `CMakeLists.docker.txt` (7.1 needed C++14 → 17).

## 3. Catch runtime drift

```bash
docker run --rm --entrypoint python zrc-ci:test /app/service/test_sink_contracts.py
docker run --rm --entrypoint python zrc-ci:test /app/service/test_sink_lifecycle.py
```

Contract failures = renamed/retyped struct fields — fix the bindings AND any
`service/` code reading those fields. Then finish with the full `/run-tests`.

## 4. Document

Changelog entry (`#### ⬆️` subsection) with old → new SDK version, new
callbacks stubbed vs. forwarded, and any build-requirement changes. An SDK bump
is at least a minor version of this wrapper.

## Gotchas

- Never hand-edit only `bindings/zrc_bindings.cpp` — the template is the
  source of truth and the sync test will fail.
- Deprecation/renames on the Python-visible API (e.g. struct field spellings)
  break external consumers — keep backwards-compat aliases (see `isMyself`).
- The paired-credential DB survives SDK upgrades but NOT MAC changes; don't
  touch `docker-compose.yml`'s `mac_address` while upgrading.
