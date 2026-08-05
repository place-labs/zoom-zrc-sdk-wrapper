"""
Unit tests for the app lifespan exit behavior (fake SDK, subprocess-isolated).

The lifespan hard-exits with os._exit(0) after a CLEAN shutdown (deliberate: it
skips Python finalization that would abort in the SDK's static teardown). But a
FAILED startup must NOT be converted into a silent exit code 0 — the exception
has to propagate so the process exits non-zero and the error gets logged.

Runs the lifespan in a subprocess because os._exit would kill the test runner.
"""
import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.unit

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_DIR = os.path.dirname(TESTS_DIR)

_SCRIPT_PREAMBLE = f"""
import asyncio, sys
sys.path.insert(0, {TESTS_DIR!r})
sys.path.insert(0, {SERVICE_DIR!r})
import _zrc_stub  # installs the fake zrc_sdk before app imports it
import app

async def main():
    async with app.lifespan(app.app):
        pass
"""


def _run(script, tmp_path):
    env = dict(os.environ, HOME=str(tmp_path))  # hermetic ~/.zoom/data
    return subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True, text=True, timeout=60, env=env,
    )


def test_clean_shutdown_exits_zero(tmp_path):
    proc = _run(_SCRIPT_PREAMBLE + "asyncio.run(main())\n", tmp_path)
    assert proc.returncode == 0, proc.stderr


def test_startup_failure_exits_nonzero(tmp_path):
    script = _SCRIPT_PREAMBLE + """
def boom():
    raise RuntimeError("startup boom")
app.room_manager.initialize = boom
asyncio.run(main())
"""
    proc = _run(script, tmp_path)
    assert proc.returncode != 0, (
        "startup failure was masked as a clean exit 0:\n" + proc.stderr
    )
    assert "startup boom" in proc.stderr
