// Minimal pybind11 bindings for Zoom Rooms SDK
// Only exposes core functionality without complex sink trampolines

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

// SDK headers
#include "IZRCSDK.h"
#include "IZoomRoomsService.h"
#include "IMeetingService.h"
#include "IPreMeetingService.h"
#include "ZRCSDKTypes.h"

namespace py = pybind11;
using namespace ZRCSDK;

// Simple concrete implementation of IZRCSDKSink for use from C++
// Python will not subclass this - we create it in C++
class SimpleSinkImpl : public IZRCSDKSink {
private:
    py::object py_sink;

public:
    SimpleSinkImpl(py::object obj) : py_sink(obj) {}

    std::string OnGetDeviceManufacturer() override {
        if (py::hasattr(py_sink, "OnGetDeviceManufacturer")) {
            return py_sink.attr("OnGetDeviceManufacturer")().cast<std::string>();
        }
        return "ZRC_Wrapper";
    }

    std::string OnGetDeviceModel() override {
        if (py::hasattr(py_sink, "OnGetDeviceModel")) {
            return py_sink.attr("OnGetDeviceModel")().cast<std::string>();
        }
        return "v1.0";
    }

    std::string OnGetDeviceSerialNumber() override {
        if (py::hasattr(py_sink, "OnGetDeviceSerialNumber")) {
            return py_sink.attr("OnGetDeviceSerialNumber")().cast<std::string>();
        }
        return "0000";
    }

    std::string OnGetDeviceMacAddress() override {
        if (py::hasattr(py_sink, "OnGetDeviceMacAddress")) {
            return py_sink.attr("OnGetDeviceMacAddress")().cast<std::string>();
        }
        return "00:00:00:00:00:00";
    }

    std::string OnGetDeviceIP() override {
        if (py::hasattr(py_sink, "OnGetDeviceIP")) {
            return py_sink.attr("OnGetDeviceIP")().cast<std::string>();
        }
        return "0.0.0.0";
    }

    std::string OnGetFirmwareVersion() override {
        if (py::hasattr(py_sink, "OnGetFirmwareVersion")) {
            return py_sink.attr("OnGetFirmwareVersion")().cast<std::string>();
        }
        return "1.0.0";
    }

    std::string OnGetAppName() override {
        if (py::hasattr(py_sink, "OnGetAppName")) {
            return py_sink.attr("OnGetAppName")().cast<std::string>();
        }
        return "ZRC_Wrapper";
    }

    std::string OnGetAppVersion() override {
        if (py::hasattr(py_sink, "OnGetAppVersion")) {
            return py_sink.attr("OnGetAppVersion")().cast<std::string>();
        }
        return "1.0.0";
    }

    std::string OnGetAppDeveloper() override {
        if (py::hasattr(py_sink, "OnGetAppDeveloper")) {
            return py_sink.attr("OnGetAppDeveloper")().cast<std::string>();
        }
        return "Custom";
    }

    std::string OnGetAppContact() override {
        if (py::hasattr(py_sink, "OnGetAppContact")) {
            return py_sink.attr("OnGetAppContact")().cast<std::string>();
        }
        return "support@example.com";
    }

    std::string OnGetAppContentDirPath() override {
        if (py::hasattr(py_sink, "OnGetAppContentDirPath")) {
            return py_sink.attr("OnGetAppContentDirPath")().cast<std::string>();
        }
        // Fallback: use /root/.zoom/data (contains third_zrc_data.db with room credentials)
        return "/root/.zoom/data";
    }

    bool OnPromptToInputUserNamePasswordForProxyServer(const std::string& proxyHost, uint32_t port, const std::string& description) override {
        return false;  // Don't prompt for proxy
    }
};

PYBIND11_MODULE(zrc_sdk, m) {
    m.doc() = "Zoom Rooms Controller SDK Python Bindings";

    // ===== Structs =====
    py::class_<ZoomRoomInfo>(m, "ZoomRoomInfo")
        .def(py::init<>())
        .def_readwrite("roomName", &ZoomRoomInfo::roomName)
        .def_readwrite("displayName", &ZoomRoomInfo::displayName)
        .def_readwrite("roomAddress", &ZoomRoomInfo::roomAddress)
        .def_readwrite("roomID", &ZoomRoomInfo::roomID)
        .def_readwrite("worker", &ZoomRoomInfo::worker)
        .def_readwrite("canRetryToPair", &ZoomRoomInfo::canRetryToPair);

    // ===== Enums =====
    py::enum_<ZRCSDKError>(m, "ZRCSDKError")
        .value("ZRCSDKERR_SUCCESS", ZRCSDKError::ZRCSDKERR_SUCCESS)
        .value("ZRCSDKERR_INTERNAL_ERROR", ZRCSDKError::ZRCSDKERR_INTERNAL_ERROR)
        .export_values();

    py::enum_<MeetingStatus>(m, "MeetingStatus")
        .value("MeetingStatusNotInMeeting", MeetingStatus::MeetingStatusNotInMeeting)
        .value("MeetingStatusConnectingToMeeting", MeetingStatus::MeetingStatusConnectingToMeeting)
        .value("MeetingStatusInMeeting", MeetingStatus::MeetingStatusInMeeting)
        .value("MeetingStatusLoggedOut", MeetingStatus::MeetingStatusLoggedOut)
        .export_values();

    py::enum_<ConnectionState>(m, "ConnectionState")
        .value("ConnectionStateNone", ConnectionState::ConnectionStateNone)
        .value("ConnectionStateEstablished", ConnectionState::ConnectionStateEstablished)
        .value("ConnectionStateConnected", ConnectionState::ConnectionStateConnected)
        .value("ConnectionStateDisconnected", ConnectionState::ConnectionStateDisconnected)
        .export_values();

    py::enum_<ExitMeetingCmd>(m, "ExitMeetingCmd")
        .value("ExitMeetingCmdLeave", ExitMeetingCmd::ExitMeetingCmdLeave)
        .value("ExitMeetingCmdEnd", ExitMeetingCmd::ExitMeetingCmdEnd)
        .export_values();

    py::enum_<RoomUnpairedReason>(m, "RoomUnpairedReason")
        .value("RoomUnpairedReason_TokenInvalid", RoomUnpairedReason::RoomUnpairedReason_TokenInvalid)
        .value("RoomUnpairedReason_RefreshTokenFail", RoomUnpairedReason::RoomUnpairedReason_RefreshTokenFail)
        .export_values();

    // ===== Core SDK =====
    py::class_<IZRCSDK>(m, "IZRCSDK")
        .def_static("GetInstance", &IZRCSDK::GetInstance, py::return_value_policy::reference)
        .def_static("DestroyInstance", &IZRCSDK::DestroyInstance)
        .def("HeartBeat", &IZRCSDK::HeartBeat)
        .def("ForceFlushLog", &IZRCSDK::ForceFlushLog)
        .def("CreateZoomRoomsService", &IZRCSDK::CreateZoomRoomsService,
             py::arg("roomID") = ZRCSDK_DEFAULT_ROOM_ID,
             py::return_value_policy::reference)
        .def("QueryAllZoomRoomsServices", &IZRCSDK::QueryAllZoomRoomsServices);

    // Helper to register SDK sink
    m.def("RegisterSDKSink", [](IZRCSDK* sdk, py::object py_sink) {
        static std::shared_ptr<SimpleSinkImpl> sink_impl;
        sink_impl = std::make_shared<SimpleSinkImpl>(py_sink);
        return sdk->RegisterSink(sink_impl.get());
    }, py::arg("sdk"), py::arg("sink"));

    // ===== ZoomRooms Service =====
    py::class_<IZoomRoomsService>(m, "IZoomRoomsService")
        .def("PairRoomWithActivationCode", &IZoomRoomsService::PairRoomWithActivationCode)
        .def("UnpairRoom", &IZoomRoomsService::UnpairRoom)
        .def("RetryToPairRoom", &IZoomRoomsService::RetryToPairRoom)
        .def("GetPreMeetingService", &IZoomRoomsService::GetPreMeetingService, py::return_value_policy::reference)
        .def("GetMeetingService", &IZoomRoomsService::GetMeetingService, py::return_value_policy::reference);

    // ===== Pre-Meeting Service =====
    py::class_<IPreMeetingService>(m, "IPreMeetingService")
        .def("GetConnectionState", &IPreMeetingService::GetConnectionState);

    // ===== Meeting Service =====
    py::class_<IMeetingService>(m, "IMeetingService")
        .def("StartInstantMeeting", &IMeetingService::StartInstantMeeting)
        .def("JoinMeeting", &IMeetingService::JoinMeeting)
        .def("ExitMeeting", &IMeetingService::ExitMeeting);
}
