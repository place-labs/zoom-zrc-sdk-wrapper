#!/usr/bin/env python3
"""
Sink registration lifecycle test (runs in the built image).

Exercises RegisterSink/DeregisterSink THROUGH the compiled bindings against the
real SDK — the layer the contract test bypasses (it calls the Python sink
methods directly and never touches the C++ registry). Registration and
deregistration are local SDK operations, so no paired or even reachable Zoom
Room is required.

For every sink surface the service registers (mirrors
room_manager.register_sinks_for_room):
  1. DeregisterSink before any registration fails (registry starts empty),
  2. RegisterSink succeeds,
  3. DeregisterSink then succeeds  <-- the disjoint-static-map bug made this
     return ZRCSDKERR_INTERNAL_ERROR forever, leaving trampolines registered,
  4. a second DeregisterSink fails (entry really removed),
  5. a fresh register/deregister cycle succeeds (registry is reusable).

Run inside the built image:
  docker run --rm --entrypoint python <image> /app/service/test_sink_lifecycle.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zrc_sdk               # noqa: E402
from room_manager import SDKSinkImpl  # noqa: E402

SUCCESS = zrc_sdk.ZRCSDKERR_SUCCESS


class DummySink:
    """Trampolines hold the py::object and only look up attributes when a
    callback fires; no callbacks fire in this test, so no methods are needed."""


def surfaces(room_service):
    """Every sink surface the service registers, mirroring register_sinks_for_room."""
    yield "room service", room_service
    premeeting = room_service.GetPreMeetingService()
    if premeeting:
        yield "pre-meeting", premeeting
        yield "control system", premeeting.GetControlSystemHelper()
        yield "BYOD", premeeting.GetBYODHelper()
    yield "phone call", room_service.GetPhoneCallService()
    setting_service = room_service.GetSettingService()
    if setting_service:
        yield "setting", setting_service
        yield "calibration", setting_service.GetCalibrationHelper()
    proav_service = room_service.GetProAVService()
    if proav_service:
        yield "pro AV", proav_service
        yield "HWIO", proav_service.GetHWIOHelper()
        yield "Dante output", proav_service.GetDanteOutputHelper()
    meeting_service = room_service.GetMeetingService()
    if meeting_service:
        yield "meeting service", meeting_service
        yield "meeting list", meeting_service.GetMeetingListHelper()
        yield "meeting reminder", meeting_service.GetMeetingReminderHelper()
        yield "participant", meeting_service.GetParticipantHelper()
        yield "meeting control", meeting_service.GetMeetingControlHelper()
        yield "waiting room", meeting_service.GetWaitingRoomHelper()
        yield "recording", meeting_service.GetRecordingHelper()
        yield "meeting audio", meeting_service.GetMeetingAudioHelper()
        yield "meeting video", meeting_service.GetMeetingVideoHelper()
        yield "meeting share", meeting_service.GetMeetingShareHelper()
        yield "view layout", meeting_service.GetMeetingViewLayoutHelper()
        yield "closed caption", meeting_service.GetClosedCaptionHelper()
        yield "NDI", meeting_service.GetNDIHelper()


def check_lifecycle(label, surface):
    """Run the register/deregister cycle on one surface; returns a list of problems."""
    problems = []

    pre = surface.DeregisterSink()
    if pre == SUCCESS:
        problems.append("deregister BEFORE register unexpectedly succeeded")

    if surface.RegisterSink(DummySink()) != SUCCESS:
        problems.append("RegisterSink failed")
        return problems  # nothing to deregister

    first = surface.DeregisterSink()
    if first != SUCCESS:
        problems.append(f"DeregisterSink after register failed ({first})")

    second = surface.DeregisterSink()
    if second == SUCCESS:
        problems.append("second DeregisterSink unexpectedly succeeded (entry not removed)")

    if surface.RegisterSink(DummySink()) != SUCCESS:
        problems.append("re-register after deregister failed")
    elif surface.DeregisterSink() != SUCCESS:
        problems.append("deregister of re-registered sink failed")

    return problems


def main():
    sdk = zrc_sdk.CreateInstanceWithSink(SDKSinkImpl())
    sdk.InitWebDomain("https://zoom.us")
    room_service = sdk.CreateZoomRoomsService("ci-lifecycle-test")
    if not room_service:
        print("FATAL: CreateZoomRoomsService returned no service")
        return 1

    passed, failed, skipped = 0, 0, 0
    for label, surface in surfaces(room_service):
        if not surface:
            print(f"SKIP  {label}: surface not available")
            skipped += 1
            continue
        try:
            problems = check_lifecycle(label, surface)
        except Exception as e:
            problems = [f"raised {type(e).__name__}: {e}"]
        if problems:
            failed += 1
            for p in problems:
                print(f"FAIL  {label}: {p}")
        else:
            passed += 1
            print(f"PASS  {label}")

    print(f"\n{passed} passed, {failed} failed, {skipped} skipped")
    return 1 if failed else 0


if __name__ == "__main__":
    rc = main()
    # Hard-exit like service/app.py: the SDK instance holds py::objects in C++
    # statics whose teardown after Py_Finalize aborts. Flush first — os._exit
    # skips stdio flushing.
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(rc)
