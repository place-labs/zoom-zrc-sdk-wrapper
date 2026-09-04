"""
Unit tests for participant_to_dict silent-mode / waiting-room derivation.

The SDK's MeetingParticipant struct has no `isInWaitingRoom` attribute — the
bound flags are `isInSilentMode` and `isLeavingSilentMode` (silent mode covers
waiting room and put-on-hold, per IWaitingRoomHelper.h). The serializer must
derive `is_in_waiting_room` from `isInSilentMode` (contract field consumers
already bind to), expose the honest `is_in_silent_mode` / `is_leaving_silent_mode`
fields, and never read the nonexistent `isInWaitingRoom` attribute.
"""
import pytest

from _zrc_stub import FakeService  # noqa: F401  (installs fake zrc_sdk, fixes sys.path)

from controllers.participant import participant_to_dict

pytestmark = pytest.mark.unit


class _FakeParticipant:
    """Stand-in for the bound MeetingParticipant struct."""

    def __init__(self, **attrs):
        self.userID = 16778240
        self.userName = "Alice"
        for name, value in attrs.items():
            setattr(self, name, value)


def test_silent_mode_flags_flow_through():
    d = participant_to_dict(
        _FakeParticipant(isInSilentMode=True, isLeavingSilentMode=False)
    )
    assert d["is_in_waiting_room"] is True
    assert d["is_in_silent_mode"] is True
    assert d["is_leaving_silent_mode"] is False

    d = participant_to_dict(
        _FakeParticipant(isInSilentMode=False, isLeavingSilentMode=True)
    )
    assert d["is_in_waiting_room"] is False
    assert d["is_in_silent_mode"] is False
    assert d["is_leaving_silent_mode"] is True


def test_missing_silent_mode_attrs_degrade_to_none():
    # Older SDK builds without the silent-mode fields must not crash or invent values.
    d = participant_to_dict(_FakeParticipant())
    assert d["is_in_waiting_room"] is None
    assert d["is_in_silent_mode"] is None
    assert d["is_leaving_silent_mode"] is None


def test_serializer_ignores_nonexistent_isInWaitingRoom_attr():
    # A stray isInWaitingRoom attribute must not feed the output — the field
    # derives from isInSilentMode only.
    d = participant_to_dict(_FakeParticipant(isInWaitingRoom=True))
    assert d["is_in_waiting_room"] is None


def test_no_production_source_reads_dead_isInWaitingRoom_attr():
    # AST scan of every production module under service/ (tests excluded):
    # ban getattr(..., "isInWaitingRoom", ...) in any quote style and direct
    # .isInWaitingRoom attribute access. Comments/docstrings naturally don't
    # trip an AST walk of Call/Attribute nodes.
    import ast
    import pathlib

    from _zrc_stub import SERVICE_DIR

    dead = "isInWaitingRoom"
    offenders = []
    for path in sorted(pathlib.Path(SERVICE_DIR).rglob("*.py")):
        if "tests" in path.relative_to(SERVICE_DIR).parts:
            continue
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            is_dead_getattr = (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "getattr"
                and any(
                    isinstance(arg, ast.Constant) and arg.value == dead
                    for arg in node.args
                )
            )
            is_dead_attribute = isinstance(node, ast.Attribute) and node.attr == dead
            if is_dead_getattr or is_dead_attribute:
                offenders.append(f"{path}:{node.lineno}")

    assert not offenders, f"dead {dead} reads in production code: {offenders}"
