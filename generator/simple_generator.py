#!/usr/bin/env python3
"""
Simple Zoom Rooms SDK Binding Generator

Generates pybind11 bindings from a configuration file.
Much simpler than parsing headers, easier to maintain.
"""

from pathlib import Path
from jinja2 import Template


# Configuration: Define the API surface to expose
SDK_CONFIG = {
    # Core singleton SDK class
    'IZRCSDK': {
        'type': 'singleton',
        'methods': [
            'GetInstance() -> IZRCSDK*',
            'DestroyInstance() -> void',
            'RegisterSink(IZRCSDKSink*) -> void',
            'DeregisterSink(IZRCSDKSink*) -> void',
            'HeartBeat() -> void',
            'ForceFlushLog() -> void',
            'CreateZoomRoomsService(const std::string& roomID = "") -> IZoomRoomsService*',
            'QueryAllZoomRoomsServices(std::vector<ZoomRoomInfo>&) -> void',
        ],
    },

    # Per-room service
    'IZoomRoomsService': {
        'type': 'interface',
        'methods': [
            'GetSettingService() -> ISettingService*',
            'GetPreMeetingService() -> IPreMeetingService*',
            'GetMeetingService() -> IMeetingService*',
            'GetPhoneCallService() -> IPhoneCallService*',
            'GetProAVService() -> IProAVService*',
            'PairRoomWithActivationCode(const std::string&) -> ZRCSDKError',
            'UnpairRoom() -> ZRCSDKError',
            'RetryToPairRoom() -> ZRCSDKError',
            'CanRetryToPairLastRoom() -> bool',
            'RegisterSink(IZoomRoomsServiceSink*) -> void',
            'DeregisterSink(IZoomRoomsServiceSink*) -> void',
        ],
    },

    # Meeting service
    'IMeetingService': {
        'type': 'interface',
        'methods': [
            'RegisterSink(IMeetingServiceSink*) -> void',
            'DeregisterSink(IMeetingServiceSink*) -> void',
            'GetMeetingAudioHelper() -> IMeetingAudioHelper*',
            'GetMeetingVideoHelper() -> IMeetingVideoHelper*',
            'GetParticipantHelper() -> IParticipantHelper*',
            'GetMeetingControlHelper() -> IMeetingControlHelper*',
            'GetMeetingChatHelper() -> IMeetingChatHelper*',
            'GetCameraControlHelper() -> ICameraControlHelper*',
            'StartInstantMeeting() -> ZRCSDKError',
            'JoinMeeting(const std::string& meetingNumber, const std::string& password = "") -> ZRCSDKError',
            'ExitMeeting(ExitMeetingCmd) -> ZRCSDKError',
            'GetCurrentMeetingInfo() -> MeetingInfo',
        ],
    },

    # Pre-meeting service
    'IPreMeetingService': {
        'type': 'interface',
        'methods': [
            'RegisterSink(IPreMeetingServiceSink*) -> void',
            'DeregisterSink(IPreMeetingServiceSink*) -> void',
            'GetConnectionState() -> ConnectionState',
        ],
    },

    # Pro AV service
    'IProAVService': {
        'type': 'interface',
        'methods': [
            'RegisterSink(IProAVServiceSink*) -> void',
            'DeregisterSink(IProAVServiceSink*) -> void',
        ],
    },

    # Audio helper
    'IMeetingAudioHelper': {
        'type': 'interface',
        'methods': [
            'RegisterSink(IMeetingAudioHelperSink*) -> void',
            'DeregisterSink(IMeetingAudioHelperSink*) -> void',
            'MuteAudio(bool) -> ZRCSDKError',
            'MuteParticipantAudio(int32_t, bool) -> ZRCSDKError',
            'CanMuteUnmuteMyAudio() -> bool',
        ],
    },

    # Video helper
    'IMeetingVideoHelper': {
        'type': 'interface',
        'methods': [
            'RegisterSink(IMeetingVideoHelperSink*) -> void',
            'DeregisterSink(IMeetingVideoHelperSink*) -> void',
            'MuteVideo(bool) -> ZRCSDKError',
            'CanMuteUnmuteMyVideo() -> bool',
        ],
    },

    # Participant helper
    'IParticipantHelper': {
        'type': 'interface',
        'methods': [
            'RegisterSink(IParticipantHelperSink*) -> void',
            'DeregisterSink(IParticipantHelperSink*) -> void',
            'GetParticipantsList() -> std::vector<Participant>',
        ],
    },

    # Meeting control helper
    'IMeetingControlHelper': {
        'type': 'interface',
        'methods': [
            'RegisterSink(IMeetingControlHelperSink*) -> void',
            'DeregisterSink(IMeetingControlHelperSink*) -> void',
            'StartRecording() -> ZRCSDKError',
            'StopRecording() -> ZRCSDKError',
            'PauseRecording() -> ZRCSDKError',
            'ResumeRecording() -> ZRCSDKError',
        ],
    },

    # Camera control helper
    'ICameraControlHelper': {
        'type': 'interface',
        'methods': [
            'RegisterSink(ICameraControlHelperSink*) -> void',
            'DeregisterSink(ICameraControlHelperSink*) -> void',
        ],
    },

    # Callback sinks
    'IZRCSDKSink': {
        'type': 'sink',
        'methods': [
            'OnGetDeviceManufacturer() -> std::string',
            'OnGetDeviceModel() -> std::string',
            'OnGetDeviceSerialNumber() -> std::string',
            'OnGetDeviceMacAddress() -> std::string',
            'OnGetDeviceIP() -> std::string',
            'OnGetFirmwareVersion() -> std::string',
            'OnGetAppName() -> std::string',
            'OnGetAppVersion() -> std::string',
            'OnGetAppDeveloper() -> std::string',
            'OnGetAppContact() -> std::string',
            'OnGetAppContentDirPath() -> std::string',
        ],
    },

    'IZoomRoomsServiceSink': {
        'type': 'sink',
        'methods': [
            'OnPairRoomResult(int32_t) -> void',
            'OnRoomUnpairedReason(RoomUnpairedReason) -> void',
        ],
    },

    'IMeetingServiceSink': {
        'type': 'sink',
        'methods': [
            'OnUpdateMeetingStatus(MeetingStatus) -> void',
            'OnConfReadyNotification() -> void',
            'OnExitMeetingNotification() -> void',
        ],
    },

    'IPreMeetingServiceSink': {
        'type': 'sink',
        'methods': [
            'OnZRConnectionStateChanged(ConnectionState) -> void',
        ],
    },

    'IProAVServiceSink': {'type': 'sink', 'methods': []},
    'IMeetingAudioHelperSink': {'type': 'sink', 'methods': []},
    'IMeetingVideoHelperSink': {'type': 'sink', 'methods': []},
    'IParticipantHelperSink': {'type': 'sink', 'methods': []},
    'IMeetingControlHelperSink': {'type': 'sink', 'methods': []},
    'ICameraControlHelperSink': {'type': 'sink', 'methods': []},
    'IMeetingChatHelper': {'type': 'interface', 'methods': []},
}

# Key enums to expose
SDK_ENUMS = {
    'ZRCSDKError': [
        'ZRCSDKERR_SUCCESS',
        'ZRCSDKERR_WRONG_USAGE',
        'ZRCSDKERR_NOT_CONNECT_TO_ZOOMROOM',
        'ZRCSDKERR_ALREADY_IN_MEETING',
        'ZRCSDKERR_NOT_IN_MEETING',
    ],
    'MeetingStatus': [
        'Idle',
        'Connecting',
        'InMeeting',
        'Disconnecting',
    ],
    'ConnectionState': [
        'ConnectionStateNone',
        'ConnectionStateEstablished',
        'ConnectionStateConnected',
        'ConnectionStateDisconnected',
    ],
    'ExitMeetingCmd': [
        'Leave',
        'End',
    ],
    'RoomUnpairedReason': [
        'Unknown',
        'UserUnpair',
        'NetworkDisconnect',
    ],
}


BINDING_TEMPLATE = """// Auto-generated pybind11 bindings for Zoom Rooms SDK
// DO NOT EDIT MANUALLY - regenerate with simple_generator.py

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>

// SDK headers
#include "IZRCSDK.h"
#include "IZoomRoomsService.h"
#include "IMeetingService.h"
#include "IPreMeetingService.h"
#include "IProAVService.h"
#include "ISettingService.h"
#include "IPhoneCallService.h"
#include "ZRCSDKTypes.h"
#include "ServiceComponents/IMeetingAudioHelper.h"
#include "ServiceComponents/IMeetingVideoHelper.h"
#include "ServiceComponents/IParticipantHelper.h"
#include "ServiceComponents/IMeetingControlHelper.h"
#include "ServiceComponents/IMeetingChatHelper.h"
#include "ServiceComponents/ICameraControlHelper.h"

namespace py = pybind11;
using namespace ZRCSDK;

// Trampoline classes for Python to implement C++ interfaces
{% for class_name, class_info in classes.items() %}
{% if class_info.type == 'sink' %}
class Py{{ class_name }} : public {{ class_name }} {
public:
    using {{ class_name }}::{{ class_name }};

    {% for method_sig in class_info.methods %}
    {% set parts = method_sig.split('(') %}
    {% set name_and_ret = parts[0].split(' -> ') %}
    {% set method_name = name_and_ret[0].strip() %}
    {% set return_type = name_and_ret[1].strip() if name_and_ret|length > 1 else 'void' %}
    {% set params = parts[1].rstrip(')').strip() if parts|length > 1 else '' %}
    {{ return_type }} {{ method_name }}({{ params }}) override {
        PYBIND11_OVERRIDE({{ return_type }}, {{ class_name }}, {{ method_name }});
    }
    {% endfor %}
};
{% endif %}
{% endfor %}

PYBIND11_MODULE(zrc_sdk, m) {
    m.doc() = "Zoom Rooms Controller SDK Python Bindings";

    // ===== Enums =====
    {% for enum_name, enum_values in enums.items() %}
    py::enum_<{{ enum_name }}>(m, "{{ enum_name }}")
    {% for value in enum_values %}
        .value("{{ value }}", {{ enum_name }}::{{ value }})
    {% endfor %}
        .export_values();
    {% endfor %}

    // ===== Core Classes =====
    {% for class_name, class_info in classes.items() %}
    {% if class_info.type != 'sink' %}
    py::class_<{{ class_name }}>(m, "{{ class_name }}")
    {% for method_sig in class_info.methods %}
        {% set parts = method_sig.split('(') %}
        {% set name_and_ret = parts[0].split(' -> ') %}
        {% set method_name = name_and_ret[0].strip() %}
        .def("{{ method_name }}", &{{ class_name }}::{{ method_name }})
    {% endfor %}
        ;
    {% endif %}
    {% endfor %}

    // ===== Callback Interfaces (with trampolines) =====
    {% for class_name, class_info in classes.items() %}
    {% if class_info.type == 'sink' %}
    py::class_<{{ class_name }}, Py{{ class_name }}>(m, "{{ class_name }}")
    {% for method_sig in class_info.methods %}
        {% set parts = method_sig.split('(') %}
        {% set name_and_ret = parts[0].split(' -> ') %}
        {% set method_name = name_and_ret[0].strip() %}
        .def("{{ method_name }}", &{{ class_name }}::{{ method_name }})
    {% endfor %}
        ;
    {% endif %}
    {% endfor %}
}
"""


def generate_bindings(output_path: Path):
    """Generate the pybind11 C++ file"""
    print("Generating Zoom Rooms SDK bindings...")

    template = Template(BINDING_TEMPLATE)
    code = template.render(
        classes=SDK_CONFIG,
        enums=SDK_ENUMS,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(code)

    print(f"✓ Generated: {output_path}")
    print(f"  - {len(SDK_CONFIG)} classes/interfaces")
    print(f"  - {len(SDK_ENUMS)} enums")
    print(f"  - {sum(len(c['methods']) for c in SDK_CONFIG.values())} methods")


def main():
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    output_file = project_root / 'bindings' / 'zrc_bindings.cpp'

    print("=" * 60)
    print("Zoom Rooms SDK Binding Generator (Simple)")
    print("=" * 60)

    generate_bindings(output_file)

    print("\n" + "=" * 60)
    print("✓ Generation complete!")
    print("  Next: Run './build.sh' to compile")
    print("=" * 60)


if __name__ == '__main__':
    main()
