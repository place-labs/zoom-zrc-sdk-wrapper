#!/usr/bin/env python3
"""
Simple Zoom Rooms SDK Binding Generator

Generates pybind11 bindings from a configuration file.
"""

from pathlib import Path
from typing import List, Dict


# Simplified configuration - just list methods, we'll manually write the bindings
SDK_CONFIG = {
    'core_classes': [
        'IZRCSDK',
        'IZoomRoomsService',
        'IMeetingService',
        'IPreMeetingService',
        'IProAVService',
        'ISettingService',
        'IPhoneCallService',
        'IMeetingAudioHelper',
        'IMeetingVideoHelper',
        'IParticipantHelper',
        'IMeetingControlHelper',
        'IMeetingChatHelper',
        'ICameraControlHelper',
    ],

    'sink_classes': [
        'IZRCSDKSink',
        'IZoomRoomsServiceSink',
        'IMeetingServiceSink',
        'IPreMeetingServiceSink',
        'IProAVServiceSink',
        'IMeetingAudioHelperSink',
        'IMeetingVideoHelperSink',
        'IParticipantHelperSink',
        'IMeetingControlHelperSink',
        'ICameraControlHelperSink',
    ],

    'enums': [
        'ZRCSDKError',
        'MeetingStatus',
        'ConnectionState',
        'ExitMeetingCmd',
        'RoomUnpairedReason',
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

// Trampoline class for IZRCSDKSink to allow Python override
class PyIZRCSDKSink : public IZRCSDKSink {
public:
    using IZRCSDKSink::IZRCSDKSink;

    std::string OnGetDeviceManufacturer() override {
        PYBIND11_OVERRIDE_PURE(std::string, IZRCSDKSink, OnGetDeviceManufacturer);
    }
    std::string OnGetDeviceModel() override {
        PYBIND11_OVERRIDE_PURE(std::string, IZRCSDKSink, OnGetDeviceModel);
    }
    std::string OnGetDeviceSerialNumber() override {
        PYBIND11_OVERRIDE_PURE(std::string, IZRCSDKSink, OnGetDeviceSerialNumber);
    }
    std::string OnGetDeviceMacAddress() override {
        PYBIND11_OVERRIDE_PURE(std::string, IZRCSDKSink, OnGetDeviceMacAddress);
    }
    std::string OnGetDeviceIP() override {
        PYBIND11_OVERRIDE_PURE(std::string, IZRCSDKSink, OnGetDeviceIP);
    }
    std::string OnGetFirmwareVersion() override {
        PYBIND11_OVERRIDE_PURE(std::string, IZRCSDKSink, OnGetFirmwareVersion);
    }
    std::string OnGetAppName() override {
        PYBIND11_OVERRIDE_PURE(std::string, IZRCSDKSink, OnGetAppName);
    }
    std::string OnGetAppVersion() override {
        PYBIND11_OVERRIDE_PURE(std::string, IZRCSDKSink, OnGetAppVersion);
    }
    std::string OnGetAppDeveloper() override {
        PYBIND11_OVERRIDE_PURE(std::string, IZRCSDKSink, OnGetAppDeveloper);
    }
    std::string OnGetAppContact() override {
        PYBIND11_OVERRIDE_PURE(std::string, IZRCSDKSink, OnGetAppContact);
    }
    std::string OnGetAppContentDirPath() override {
        PYBIND11_OVERRIDE_PURE(std::string, IZRCSDKSink, OnGetAppContentDirPath);
    }
    bool OnPromptToInputUserNamePasswordForProxyServer(const std::string& proxyHost, uint32_t port, const std::string& description) override {
        PYBIND11_OVERRIDE_PURE(bool, IZRCSDKSink, OnPromptToInputUserNamePasswordForProxyServer, proxyHost, port, description);
    }
};

// Trampoline for IZoomRoomsServiceSink
class PyIZoomRoomsServiceSink : public IZoomRoomsServiceSink {
public:
    using IZoomRoomsServiceSink::IZoomRoomsServiceSink;

    void OnPairRoomResult(int32_t result) override {
        PYBIND11_OVERRIDE_PURE(void, IZoomRoomsServiceSink, OnPairRoomResult, result);
    }
    void OnRoomUnpairedReason(RoomUnpairedReason reason) override {
        PYBIND11_OVERRIDE_PURE(void, IZoomRoomsServiceSink, OnRoomUnpairedReason, reason);
    }
};

// Trampoline for IMeetingServiceSink
class PyIMeetingServiceSink : public IMeetingServiceSink {
public:
    using IMeetingServiceSink::IMeetingServiceSink;

    void OnUpdateMeetingStatus(MeetingStatus status) override {
        PYBIND11_OVERRIDE(void, IMeetingServiceSink, OnUpdateMeetingStatus, status);
    }
    void OnConfReadyNotification() override {
        PYBIND11_OVERRIDE(void, IMeetingServiceSink, OnConfReadyNotification);
    }
    void OnExitMeetingNotification() override {
        PYBIND11_OVERRIDE(void, IMeetingServiceSink, OnExitMeetingNotification);
    }
};

// Trampoline for IPreMeetingServiceSink
class PyIPreMeetingServiceSink : public IPreMeetingServiceSink {
public:
    using IPreMeetingServiceSink::IPreMeetingServiceSink;

    void OnZRConnectionStateChanged(ConnectionState state) override {
        PYBIND11_OVERRIDE(void, IPreMeetingServiceSink, OnZRConnectionStateChanged, state);
    }
};

PYBIND11_MODULE(zrc_sdk, m) {
    m.doc() = "Zoom Rooms Controller SDK Python Bindings";

    // ===== Key Enums =====
    py::enum_<ZRCSDKError>(m, "ZRCSDKError")
        .value("ZRCSDKERR_SUCCESS", ZRCSDKError::ZRCSDKERR_SUCCESS)
        .value("ZRCSDKERR_WRONG_USAGE", ZRCSDKError::ZRCSDKERR_WRONG_USAGE)
        .export_values();

    py::enum_<MeetingStatus>(m, "MeetingStatus")
        .value("Idle", MeetingStatus::Idle)
        .value("Connecting", MeetingStatus::Connecting)
        .value("InMeeting", MeetingStatus::InMeeting)
        .value("Disconnecting", MeetingStatus::Disconnecting)
        .export_values();

    py::enum_<ConnectionState>(m, "ConnectionState")
        .value("ConnectionStateNone", ConnectionState::ConnectionStateNone)
        .value("ConnectionStateEstablished", ConnectionState::ConnectionStateEstablished)
        .value("ConnectionStateConnected", ConnectionState::ConnectionStateConnected)
        .value("ConnectionStateDisconnected", ConnectionState::ConnectionStateDisconnected)
        .export_values();

    py::enum_<ExitMeetingCmd>(m, "ExitMeetingCmd")
        .value("Leave", ExitMeetingCmd::Leave)
        .value("End", ExitMeetingCmd::End)
        .export_values();

    py::enum_<RoomUnpairedReason>(m, "RoomUnpairedReason")
        .value("RoomUnpairedReason_TokenInvalid", RoomUnpairedReason::RoomUnpairedReason_TokenInvalid)
        .value("RoomUnpairedReason_RefreshTokenFail", RoomUnpairedReason::RoomUnpairedReason_RefreshTokenFail)
        .export_values();

    // ===== SDK Sinks (Callbacks) =====
    py::class_<IZRCSDKSink, PyIZRCSDKSink>(m, "IZRCSDKSink")
        .def(py::init<>())
        .def("OnGetDeviceManufacturer", &IZRCSDKSink::OnGetDeviceManufacturer)
        .def("OnGetDeviceModel", &IZRCSDKSink::OnGetDeviceModel)
        .def("OnGetDeviceSerialNumber", &IZRCSDKSink::OnGetDeviceSerialNumber)
        .def("OnGetDeviceMacAddress", &IZRCSDKSink::OnGetDeviceMacAddress)
        .def("OnGetDeviceIP", &IZRCSDKSink::OnGetDeviceIP)
        .def("OnGetFirmwareVersion", &IZRCSDKSink::OnGetFirmwareVersion)
        .def("OnGetAppName", &IZRCSDKSink::OnGetAppName)
        .def("OnGetAppVersion", &IZRCSDKSink::OnGetAppVersion)
        .def("OnGetAppDeveloper", &IZRCSDKSink::OnGetAppDeveloper)
        .def("OnGetAppContact", &IZRCSDKSink::OnGetAppContact)
        .def("OnGetAppContentDirPath", &IZRCSDKSink::OnGetAppContentDirPath);

    py::class_<IZoomRoomsServiceSink, PyIZoomRoomsServiceSink>(m, "IZoomRoomsServiceSink")
        .def(py::init<>())
        .def("OnPairRoomResult", &IZoomRoomsServiceSink::OnPairRoomResult)
        .def("OnRoomUnpairedReason", &IZoomRoomsServiceSink::OnRoomUnpairedReason);

    py::class_<IMeetingServiceSink, PyIMeetingServiceSink>(m, "IMeetingServiceSink")
        .def(py::init<>())
        .def("OnUpdateMeetingStatus", &IMeetingServiceSink::OnUpdateMeetingStatus)
        .def("OnConfReadyNotification", &IMeetingServiceSink::OnConfReadyNotification)
        .def("OnExitMeetingNotification", &IMeetingServiceSink::OnExitMeetingNotification);

    py::class_<IPreMeetingServiceSink, PyIPreMeetingServiceSink>(m, "IPreMeetingServiceSink")
        .def(py::init<>())
        .def("OnZRConnectionStateChanged", &IPreMeetingServiceSink::OnZRConnectionStateChanged);

    // Simple sinks without trampolines (no methods to override)
    py::class_<IProAVServiceSink>(m, "IProAVServiceSink")
        .def(py::init<>());

    py::class_<IMeetingAudioHelperSink>(m, "IMeetingAudioHelperSink")
        .def(py::init<>());

    py::class_<IMeetingVideoHelperSink>(m, "IMeetingVideoHelperSink")
        .def(py::init<>());

    py::class_<IParticipantHelperSink>(m, "IParticipantHelperSink")
        .def(py::init<>());

    py::class_<IMeetingControlHelperSink>(m, "IMeetingControlHelperSink")
        .def(py::init<>());

    py::class_<ICameraControlHelperSink>(m, "ICameraControlHelperSink")
        .def(py::init<>());

    // ===== Core SDK Class =====
    py::class_<IZRCSDK>(m, "IZRCSDK")
        .def_static("GetInstance", &IZRCSDK::GetInstance, py::return_value_policy::reference)
        .def_static("DestroyInstance", &IZRCSDK::DestroyInstance)
        .def("RegisterSink", &IZRCSDK::RegisterSink)
        .def("HeartBeat", &IZRCSDK::HeartBeat)
        .def("ForceFlushLog", &IZRCSDK::ForceFlushLog)
        .def("CreateZoomRoomsService", &IZRCSDK::CreateZoomRoomsService,
             py::arg("roomID") = ZRCSDK_DEFAULT_ROOM_ID,
             py::return_value_policy::reference)
        .def("QueryAllZoomRoomsServices", &IZRCSDK::QueryAllZoomRoomsServices);

    // ===== ZoomRooms Service =====
    py::class_<IZoomRoomsService>(m, "IZoomRoomsService")
        .def("RegisterSink", &IZoomRoomsService::RegisterSink)
        .def("DeregisterSink", &IZoomRoomsService::DeregisterSink)
        .def("PairRoomWithActivationCode", &IZoomRoomsService::PairRoomWithActivationCode)
        .def("UnpairRoom", &IZoomRoomsService::UnpairRoom)
        .def("RetryToPairRoom", &IZoomRoomsService::RetryToPairRoom)
        .def("GetSettingService", &IZoomRoomsService::GetSettingService, py::return_value_policy::reference)
        .def("GetPreMeetingService", &IZoomRoomsService::GetPreMeetingService, py::return_value_policy::reference)
        .def("GetMeetingService", &IZoomRoomsService::GetMeetingService, py::return_value_policy::reference)
        .def("GetPhoneCallService", &IZoomRoomsService::GetPhoneCallService, py::return_value_policy::reference)
        .def("GetProAVService", &IZoomRoomsService::GetProAVService, py::return_value_policy::reference);

    // ===== Pre-Meeting Service =====
    py::class_<IPreMeetingService>(m, "IPreMeetingService")
        .def("RegisterSink", &IPreMeetingService::RegisterSink)
        .def("DeregisterSink", &IPreMeetingService::DeregisterSink)
        .def("GetConnectionState", &IPreMeetingService::GetConnectionState);

    // ===== Meeting Service =====
    py::class_<IMeetingService>(m, "IMeetingService")
        .def("RegisterSink", &IMeetingService::RegisterSink)
        .def("DeregisterSink", &IMeetingService::DeregisterSink)
        .def("GetMeetingAudioHelper", &IMeetingService::GetMeetingAudioHelper, py::return_value_policy::reference)
        .def("GetMeetingVideoHelper", &IMeetingService::GetMeetingVideoHelper, py::return_value_policy::reference)
        .def("GetParticipantHelper", &IMeetingService::GetParticipantHelper, py::return_value_policy::reference)
        .def("GetMeetingControlHelper", &IMeetingService::GetMeetingControlHelper, py::return_value_policy::reference)
        .def("GetMeetingChatHelper", &IMeetingService::GetMeetingChatHelper, py::return_value_policy::reference)
        .def("GetCameraControlHelper", &IMeetingService::GetCameraControlHelper, py::return_value_policy::reference)
        .def("StartInstantMeeting", &IMeetingService::StartInstantMeeting)
        .def("JoinMeeting", &IMeetingService::JoinMeeting)
        .def("ExitMeeting", &IMeetingService::ExitMeeting);

    // ===== Pro AV Service =====
    py::class_<IProAVService>(m, "IProAVService")
        .def("RegisterSink", &IProAVService::RegisterSink)
        .def("DeregisterSink", &IProAVService::DeregisterSink);

    // ===== Setting Service =====
    py::class_<ISettingService>(m, "ISettingService");

    // ===== Phone Call Service =====
    py::class_<IPhoneCallService>(m, "IPhoneCallService");

    // ===== Helper Classes =====
    py::class_<IMeetingAudioHelper>(m, "IMeetingAudioHelper")
        .def("RegisterSink", &IMeetingAudioHelper::RegisterSink)
        .def("DeregisterSink", &IMeetingAudioHelper::DeregisterSink);

    py::class_<IMeetingVideoHelper>(m, "IMeetingVideoHelper")
        .def("RegisterSink", &IMeetingVideoHelper::RegisterSink)
        .def("DeregisterSink", &IMeetingVideoHelper::DeregisterSink);

    py::class_<IParticipantHelper>(m, "IParticipantHelper")
        .def("RegisterSink", &IParticipantHelper::RegisterSink)
        .def("DeregisterSink", &IParticipantHelper::DeregisterSink);

    py::class_<IMeetingControlHelper>(m, "IMeetingControlHelper")
        .def("RegisterSink", &IMeetingControlHelper::RegisterSink)
        .def("DeregisterSink", &IMeetingControlHelper::DeregisterSink);

    py::class_<ICameraControlHelper>(m, "ICameraControlHelper")
        .def("RegisterSink", &ICameraControlHelper::RegisterSink)
        .def("DeregisterSink", &ICameraControlHelper::DeregisterSink);

    py::class_<IMeetingChatHelper>(m, "IMeetingChatHelper")
        .def("RegisterSink", &IMeetingChatHelper::RegisterSink)
        .def("DeregisterSink", &IMeetingChatHelper::DeregisterSink);
}
"""


def generate_bindings(output_path: Path):
    """Generate the pybind11 C++ file"""
    print("Generating Zoom Rooms SDK bindings...")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(BINDING_TEMPLATE)

    print(f"✓ Generated: {output_path}")
    print(f"  - {len(SDK_CONFIG['core_classes'])} core classes")
    print(f"  - {len(SDK_CONFIG['sink_classes'])} sink classes")
    print(f"  - {len(SDK_CONFIG['enums'])} enums")


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
