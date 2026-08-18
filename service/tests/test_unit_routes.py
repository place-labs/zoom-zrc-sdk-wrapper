"""
Route-table integrity: no two endpoints may register the same (method, path).

FastAPI resolves duplicates by registration order — the first wins and the
second becomes silently unreachable dead code, while callers using the shadowed
route's parameter names get 200s with default-valued behavior (unknown query
params are dropped). Found live: /video/mute was defined by both meetings.py
(param `mute`, wins) and meeting_video.py (param `stop`, shadowed), so
`?stop=false` silently STOPPED video via the winner's `mute=True` default.
"""
import pytest

pytestmark = pytest.mark.unit

pytest.importorskip("fastapi")

import _zrc_stub  # noqa: F401  (installs the fake zrc_sdk before app import)
import app as service_app


def _leaf_routes(routes):
    for r in routes:
        orig = getattr(r, "original_router", None)   # starlette _IncludedRouter
        if orig is not None:
            yield from _leaf_routes(orig.routes)
        else:
            yield r


def test_no_duplicate_method_path_pairs():
    seen, dupes = {}, []
    for r in _leaf_routes(service_app.app.routes):
        path = getattr(r, "path", None)
        methods = getattr(r, "methods", None) or (
            ["WS"] if "WebSocket" in type(r).__name__ else [])
        ep = getattr(r, "endpoint", None)
        name = f"{ep.__module__}.{ep.__name__}" if ep else "?"
        for m in methods:
            if m == "HEAD":
                continue
            key = (m, path)
            if key in seen:
                dupes.append(f"{m} {path}: {seen[key]} shadows {name}")
            else:
                seen[key] = name
    assert len(seen) > 200, f"route walk looks broken (only {len(seen)} routes found)"
    assert not dupes, "shadowed duplicate routes:\n  " + "\n  ".join(dupes)


def test_join_url_does_not_advertise_removed_bring_share_parameter():
    route = next(
        r for r in _leaf_routes(service_app.app.routes)
        if getattr(r, "path", None) == "/api/rooms/{room_id}/meeting/join-url"
        and "POST" in (getattr(r, "methods", None) or ())
    )
    query_params = {param.name for param in route.dependant.query_params}
    assert "url" in query_params
    assert "bring_share" not in query_params
