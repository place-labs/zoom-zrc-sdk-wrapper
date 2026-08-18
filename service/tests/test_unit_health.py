"""
Unit tests for /health truthfulness (PRODUCTION-REVIEW.md 1.2).

The k8s liveness/readiness probes point at /health; a handler that can only
return 200 disables the cluster's self-healing entirely. It must go 503 when the
heartbeat pump has died (a completed run-forever task = it crashed) or the SDK is
missing — the two states where a pod restart is the correct remediation.

The handler is mounted on a bare FastAPI app: TestClient against the real app
would run its lifespan, which hard-exits the process (see test_unit_lifespan).
"""
import pytest

pytestmark = pytest.mark.unit

pytest.importorskip("fastapi")
from fastapi import FastAPI
from fastapi.testclient import TestClient

import _zrc_stub  # noqa: F401  (installs the fake zrc_sdk before app import)
import app as service_app


class _Task:
    def __init__(self, dead):
        self._dead = dead

    def done(self):
        return self._dead


def _client():
    t = FastAPI()
    t.get("/health")(service_app.health)
    return TestClient(t)


def test_health_200_while_running():
    mgr = service_app.room_manager
    mgr.sdk = object()
    mgr.heartbeat_task = _Task(dead=False)
    r = _client().get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"
    assert "sdk_call_timing" in r.json()


def test_health_503_when_heartbeat_dead():
    mgr = service_app.room_manager
    mgr.sdk = object()
    mgr.heartbeat_task = _Task(dead=True)   # loop exited = pump crashed
    r = _client().get("/health")
    assert r.status_code == 503, "a dead heartbeat must fail the k8s probes"
    body = r.json()
    assert body["status"] == "unhealthy"
    assert "heartbeat" in body["reason"].lower()


def test_health_503_when_sdk_missing():
    mgr = service_app.room_manager
    mgr.sdk = None
    mgr.heartbeat_task = None
    r = _client().get("/health")
    assert r.status_code == 503
    assert "sdk" in r.json()["reason"].lower()
