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
