"""
Shared fixtures for the smoke / live e2e suite (and unit tests alongside).

Targets a RUNNING service (default http://localhost:8000). Override with:
  ZRC_BASE_URL   - service base URL           (default http://localhost:8000)
  ZRC_TEST_ROOM  - room_id used by live tests (default "lab")
  ZRC_E2E_LIVE=1 - opt in to live room tests that start a real meeting
"""
import os
import pytest
import httpx

BASE_URL = os.environ.get("ZRC_BASE_URL", "http://localhost:8000")
ROOM_ID = os.environ.get("ZRC_TEST_ROOM", "lab")


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture()
def client(base_url):
    with httpx.Client(base_url=base_url, timeout=30.0) as c:
        yield c


@pytest.fixture(scope="session")
def room_id():
    return ROOM_ID


@pytest.fixture(scope="session")
def ws_url(room_id):
    base = BASE_URL.replace("https://", "wss://").replace("http://", "ws://")
    return f"{base}/api/rooms/{room_id}/events"
