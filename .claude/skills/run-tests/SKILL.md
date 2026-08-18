---
name: run-tests
description: Run this repo's test suites in order — unit locally, contract and lifecycle inside the Docker image, smoke against the running container. Use before committing, before a release, or whenever asked to verify the code works.
---

# Run the test suites

Run in this order (cheapest first); stop and report on the first failure.
Expected pass counts are the current baselines — report any deviation.

## 1. Unit (hermetic — no SDK, no server)

```bash
pytest -m unit -v
```

Expected: **64 passed**. Needs only `pip install -r requirements-dev.txt`.

## 2. Build the image

```bash
docker build --platform linux/amd64 -t zrc-ci:test .
```

The SDK is x86_64-only; on Apple Silicon this emulates and the
`zrc_bindings.cpp` compile is the slow step (minutes). If the Docker daemon is
down on macOS: `open -a Docker` and poll `docker info`.

## 3. Contract (in image)

```bash
docker run --rm --entrypoint python zrc-ci:test /app/service/test_sink_contracts.py
```

Expected: **125 PASS, 0 FAIL, 0 ERROR**.

## 4. Lifecycle (in image)

```bash
docker run --rm --entrypoint python zrc-ci:test /app/service/test_sink_lifecycle.py
```

Expected: **23 passed, 0 failed, 0 skipped**.

## 5. Smoke (against the running container)

```bash
docker rm -f zrc-ci 2>/dev/null
docker run -d --name zrc-ci -p 8000:8000 zrc-ci:test
# poll http://localhost:8000/health until 200 (up to ~60s)
ZRC_BASE_URL=http://localhost:8000 pytest -v -m "not live"
docker rm -f zrc-ci
```

Expected: **70 passed** (64 unit + 6 smoke), 14 deselected (live).

## Reporting

Give the actual pass counts for every suite — never summarize as "tests pass"
without the numbers. This mirrors CI (`dockerhub-build-push.yml`), so a clean
local run predicts a green pipeline.

The expected counts above are the baselines as of 1.5.0. If a change
legitimately alters them (new sink, new test), update the numbers **in this
file** in the same commit.

## Live e2e (manual, NOT part of this skill's automatic run)

Drives a real paired room and **starts a real meeting** — only when the user
explicitly asks, and confirm the room id with them first:

```bash
ZRC_E2E_LIVE=1 ZRC_TEST_ROOM=<room> pytest -v -m live
```
