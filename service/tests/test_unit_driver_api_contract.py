"""REST/WebSocket route parity with the PlaceOS Zoom ZRC driver."""

import pytest

pytestmark = pytest.mark.unit

pytest.importorskip("fastapi")

import _zrc_stub  # noqa: F401
import app as service_app


# query fields, JSON body fields; room_id is the common path parameter.
DRIVER_ROUTES = {
    ("GET", "/health"): ((), ()),
    ("GET", "/api/rooms"): ((), ()),
    ("POST", "/api/rooms/{room_id}/pair"): ((), ("activation_code",)),
    ("POST", "/api/rooms/{room_id}/unpair"): ((), ()),
    ("GET", "/api/rooms/{room_id}/status"): ((), ()),
    ("GET", "/api/rooms/{room_id}/pre-meeting/connection-state"): ((), ()),
    ("POST", "/api/rooms/{room_id}/pre-meeting/wake-up"): ((), ()),
    ("GET", "/api/rooms/{room_id}/meeting/status"): ((), ()),
    ("POST", "/api/rooms/{room_id}/meeting/start_instant"): ((), ()),
    ("POST", "/api/rooms/{room_id}/meeting/join"): (
        (),
        ("meeting_number", "password", "bring_share"),
    ),
    ("POST", "/api/rooms/{room_id}/meeting/join-url"): (("url",), ()),
    ("POST", "/api/rooms/{room_id}/meeting/password/send"): (
        ("password",),
        (),
    ),
    ("POST", "/api/rooms/{room_id}/meeting/start"): (
        (),
        (
            "meeting_number",
            "meeting_name",
            "host_name",
            "start_time",
            "end_time",
            "bring_share",
        ),
    ),
    ("POST", "/api/rooms/{room_id}/meeting/exit"): ((), ()),
    ("POST", "/api/rooms/{room_id}/meeting/cancel-waiting-host"): ((), ()),
    ("GET", "/api/rooms/{room_id}/meetings/list"): (("timeout",), ()),
    ("POST", "/api/rooms/{room_id}/meeting/reminder/confirm-reminder"): (
        (),
        ("is_agree", "notification_type"),
    ),
    ("POST", "/api/rooms/{room_id}/meeting/reminder/confirm-custom-reminder"): (
        (),
        ("is_agree", "notification_type"),
    ),
    ("POST", "/api/rooms/{room_id}/meeting/reminder/confirm-consent"): (
        (),
        ("is_agree", "consent_type", "consent_id"),
    ),
    ("POST", "/api/rooms/{room_id}/meeting/reminder/confirm-combined-consent"): (
        (),
        ("is_agree", "notification_type"),
    ),
    (
        "POST",
        "/api/rooms/{room_id}/meeting/reminder/agree-consolidated-customized-consent",
    ): ((), ("is_agree",)),
    ("POST", "/api/rooms/{room_id}/meeting/reminder/handle-privacy"): (
        (),
        ("privacy_alert_action", "privacy_alert_type"),
    ),
    ("POST", "/api/rooms/{room_id}/meeting/reminder/continue-on-inactivity"): (
        (),
        (),
    ),
    ("POST", "/api/rooms/{room_id}/recording/respond-to-request"): (
        (),
        ("agree", "is_persist"),
    ),
    ("GET", "/api/rooms/{room_id}/recording/disclaimer-needed"): ((), ()),
    ("POST", "/api/rooms/{room_id}/recording/prompt-disclaimer"): ((), ()),
    ("POST", "/api/rooms/{room_id}/recording/cloud/start"): ((), ()),
    ("POST", "/api/rooms/{room_id}/recording/notification-email"): (
        (),
        ("email",),
    ),
    ("POST", "/api/rooms/{room_id}/recording/cloud/stop"): ((), ()),
    ("POST", "/api/rooms/{room_id}/recording/cloud/pause"): ((), ()),
    ("POST", "/api/rooms/{room_id}/recording/cloud/resume"): ((), ()),
    ("POST", "/api/rooms/{room_id}/ai-companion/turn-on"): (
        ("features",),
        (),
    ),
    ("POST", "/api/rooms/{room_id}/ai-companion/turn-off"): (
        ("features", "delete_assets"),
        (),
    ),
    ("POST", "/api/rooms/{room_id}/ai-companion/respond-to-turn-on"): (
        ("agree",),
        (),
    ),
    ("POST", "/api/rooms/{room_id}/ai-companion/respond-to-turn-off"): (
        ("agree", "delete_assets"),
        (),
    ),
    ("POST", "/api/rooms/{room_id}/ai-companion/confirm-status-when-join"): (
        ("agree",),
        (),
    ),
    ("POST", "/api/rooms/{room_id}/audio/mute"): ((), ()),
    ("POST", "/api/rooms/{room_id}/audio/unmute"): ((), ()),
    ("POST", "/api/rooms/{room_id}/audio/answer-unmute-request"): (
        ("accepted",),
        (),
    ),
    ("POST", "/api/rooms/{room_id}/video/mute"): ((), ()),
    ("POST", "/api/rooms/{room_id}/video/unmute"): ((), ()),
    ("POST", "/api/rooms/{room_id}/video/answer-unmute-request"): (
        ("accepted",),
        (),
    ),
    ("GET", "/api/rooms/{room_id}/settings/volume/speaker"): ((), ()),
    ("POST", "/api/rooms/{room_id}/settings/volume/speaker"): (
        (),
        ("volume",),
    ),
    ("GET", "/api/rooms/{room_id}/settings/volume/microphone"): ((), ()),
    ("POST", "/api/rooms/{room_id}/settings/volume/microphone"): (
        (),
        ("volume",),
    ),
    ("GET", "/api/rooms/{room_id}/participants/"): (("session",), ()),
}


def _leaf_routes(routes):
    for route in routes:
        original = getattr(route, "original_router", None)
        if original is not None:
            yield from _leaf_routes(original.routes)
        else:
            yield route


def _body_fields(route):
    fields = []
    for param in route.dependant.body_params:
        annotation = param.field_info.annotation
        model_fields = getattr(annotation, "model_fields", None)
        if model_fields:
            fields.extend(model_fields)
        else:
            fields.append(param.name)
    return tuple(fields)


def test_all_driver_rest_calls_match_route_and_parameter_locations():
    actual = {}
    for route in _leaf_routes(service_app.app.routes):
        path = getattr(route, "path", None)
        for method in getattr(route, "methods", None) or ():
            key = (method, path)
            if key in DRIVER_ROUTES:
                actual[key] = (
                    tuple(param.name for param in route.dependant.query_params),
                    _body_fields(route),
                )

    assert actual == DRIVER_ROUTES


def test_driver_event_websocket_route_exists():
    routes = list(_leaf_routes(service_app.app.routes))
    assert any(
        getattr(route, "path", None) == "/api/rooms/{room_id}/events"
        and "WebSocket" in type(route).__name__
        for route in routes
    )
