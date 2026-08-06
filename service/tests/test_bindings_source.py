"""
Source contracts for the pybind11 bindings (no compiler needed).

  - RegisterSink/DeregisterSink lambda pairs must share ONE trampoline registry.
    A `static std::map` declared inside a lambda body is a distinct object per
    lambda (each lambda is its own closure type), so a deregister lambda with its
    own map can never find what the register lambda stored — DeregisterSink would
    always return ZRCSDKERR_INTERNAL_ERROR and the sink would stay registered
    with the SDK forever (use-after-free / events after unpair).
  - The public `isMyself` alias on MeetingParticipant is part of the module API
    and must not disappear.
  - The generator template must stay byte-identical to the bindings, or the next
    regeneration silently reverts fixes.
"""
import os
import re

import pytest

pytestmark = pytest.mark.unit

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BINDINGS = os.path.join(REPO_ROOT, "bindings", "zrc_bindings.cpp")
TEMPLATE = os.path.join(REPO_ROOT, "generator", "templates", "zrc_bindings.cpp")

with open(BINDINGS) as f:
    SRC = f.read()


def _lambda_bodies(method):
    """Bodies of every `.def("<method>", [](...){ ... })` lambda in the bindings."""
    return re.findall(r'\.def\("%s",\s*\[\]\((.*?)\}\)' % method, SRC, re.S)


def test_deregister_lambdas_do_not_declare_their_own_registry():
    bodies = _lambda_bodies("DeregisterSink")
    assert len(bodies) >= 20, "expected a DeregisterSink binding per sink surface"
    offenders = [b.split(")")[0] for b in bodies if "static std::map" in b]
    assert not offenders, (
        "DeregisterSink lambdas with a lambda-local static registry (invisible "
        f"to the matching RegisterSink lambda): {offenders}"
    )


def test_register_and_deregister_use_the_shared_registry():
    for method in ("RegisterSink", "DeregisterSink"):
        bodies = _lambda_bodies(method)
        assert len(bodies) >= 20
        offenders = [b.split(")")[0] for b in bodies if "SinkRegistry<" not in b]
        assert not offenders, f"{method} lambdas not using SinkRegistry: {offenders}"


def test_meeting_participant_keeps_isMyself_alias():
    assert '.def_readwrite("isMyself", &MeetingParticipant::isMySelf)' in SRC, (
        "backwards-compat alias 'isMyself' was removed from MeetingParticipant"
    )


def test_generator_template_matches_bindings():
    with open(TEMPLATE) as f:
        assert f.read() == SRC, (
            "generator/templates/zrc_bindings.cpp differs from "
            "bindings/zrc_bindings.cpp — regeneration would revert fixes"
        )


def _yielded_labels(source, func_name):
    """Labels from `yield "<label>", ...` lines inside one function body."""
    body = re.search(rf"def {func_name}\(.*?(?=\n    def |\ndef |\Z)", source, re.S)
    assert body, f"function {func_name} not found"
    return set(re.findall(r'yield "([^"]+)",', body.group(0)))


def test_lifecycle_test_covers_every_deregistered_surface():
    """The in-image lifecycle test's surface list is hand-maintained; keep it in
    lockstep with _deregister_room_sinks (which the unit tests keep in lockstep
    with registration) so a new sink surface can't be silently untested."""
    with open(os.path.join(REPO_ROOT, "service", "room_manager.py")) as f:
        deregistered = _yielded_labels(f.read(), "surfaces")
    with open(os.path.join(REPO_ROOT, "service", "test_sink_lifecycle.py")) as f:
        lifecycle = _yielded_labels(f.read(), "surfaces")
    assert deregistered, "no surfaces found in room_manager surfaces()"
    missing = deregistered - lifecycle
    extra = lifecycle - deregistered
    assert not missing, f"surfaces missing from test_sink_lifecycle.surfaces(): {sorted(missing)}"
    assert not extra, f"test_sink_lifecycle.surfaces() lists unknown surfaces: {sorted(extra)}"
