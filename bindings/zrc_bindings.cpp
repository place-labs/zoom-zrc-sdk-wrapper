// Minimal pybind11 bindings for Zoom Rooms SDK
// Only exposes core functionality without complex sink trampolines

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <map>
#include <memory>

// SDK headers
#include "IZRCSDK.h"
#include "IZoomRoomsService.h"
#include "IMeetingService.h"
#include "IPreMeetingService.h"
#include "IPhoneCallService.h"
#include "IProAVService.h"
#include "ISettingService.h"
#include "ServiceComponents/IMeetingAudioHelper.h"
#include "ServiceComponents/IMeetingVideoHelper.h"
#include "ServiceComponents/IMeetingControlHelper.h"
#include "ServiceComponents/IMeetingListHelper.h"
#include "ServiceComponents/IMeetingReminderHelper.h"
#include "ServiceComponents/IMeetingShareHelper.h"
#include "ServiceComponents/IMeetingViewLayoutHelper.h"
#include "ServiceComponents/INDIHelper.h"
#include "ServiceComponents/IParticipantHelper.h"
#include "ServiceComponents/IRecordingHelper.h"
#include "ServiceComponents/IThirdPartyMeetingHelper.h"
#include "ServiceComponents/ICalibrationHelper.h"
#include "ServiceComponents/IContactHelper.h"
#include "ServiceComponents/IBYODHelper.h"
#include "ServiceComponents/IControlSystemHelper.h"
#include "ServiceComponents/IDanteOutputHelper.h"
#include "ServiceComponents/IHWIOHelper.h"
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

// No-op SDK sink for shutdown to avoid Python callbacks during interpreter teardown.
class NoopSinkImpl : public IZRCSDKSink {
public:
    std::string OnGetDeviceManufacturer() override { return "ZRC_Wrapper"; }
    std::string OnGetDeviceModel() override { return "v1.0"; }
    std::string OnGetDeviceSerialNumber() override { return "0000"; }
    std::string OnGetDeviceMacAddress() override { return "00:00:00:00:00:00"; }
    std::string OnGetDeviceIP() override { return "0.0.0.0"; }
    std::string OnGetFirmwareVersion() override { return "1.0.0"; }
    std::string OnGetAppName() override { return "ZRC_Wrapper"; }
    std::string OnGetAppVersion() override { return "1.0.0"; }
    std::string OnGetAppDeveloper() override { return "Custom"; }
    std::string OnGetAppContact() override { return "support@example.com"; }
    std::string OnGetAppContentDirPath() override { return "/root/.zoom/data"; }
    bool OnPromptToInputUserNamePasswordForProxyServer(const std::string&, uint32_t, const std::string&) override {
        return false;
    }
};

namespace {
    std::shared_ptr<SimpleSinkImpl> g_sdk_sink_impl;
    NoopSinkImpl g_noop_sdk_sink;
}

// Trampoline for IZoomRoomsServiceSink
class ZoomRoomsServiceSinkTrampoline : public IZoomRoomsServiceSink {
private:
    py::object py_sink;

public:
    ZoomRoomsServiceSinkTrampoline(py::object obj) : py_sink(obj) {}

    void OnPairRoomResult(int32_t result) override {
        // Acquire GIL before calling Python
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnPairRoomResult")) {
            py_sink.attr("OnPairRoomResult")(result);
        }
    }

    void OnRoomUnpairedReason(RoomUnpairedReason reason) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnRoomUnpairedReason")) {
            py_sink.attr("OnRoomUnpairedReason")(reason);
        }
    }
};

// Trampoline for IPreMeetingServiceSink
class PreMeetingServiceSinkTrampoline : public IPreMeetingServiceSink {
private:
    py::object py_sink;

public:
    PreMeetingServiceSinkTrampoline(py::object obj) : py_sink(obj) {}

    void OnZRConnectionStateChanged(ConnectionState connectionState) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnZRConnectionStateChanged")) {
            py_sink.attr("OnZRConnectionStateChanged")(connectionState);
        }
    }

    void OnShutdownOSNot(bool restartOS) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnShutdownOSNot")) {
            py_sink.attr("OnShutdownOSNot")(restartOS);
        }
    }
};

// Trampoline for IMeetingListHelperSink
class MeetingListHelperSinkTrampoline : public IMeetingListHelperSink {
private:
    py::object py_sink;

public:
    MeetingListHelperSinkTrampoline(py::object obj) : py_sink(obj) {}

    void OnUpdateMeetingList(ListMeetingResult result, const std::vector<MeetingItem>& meetingList) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnUpdateMeetingList")) {
            py_sink.attr("OnUpdateMeetingList")(result, meetingList);
        }
    }

    void OnUpdatedScheduleCalendarEventNotification(ScheduleCalendarEventResult scheduleResult) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnUpdatedScheduleCalendarEventNotification")) {
            py_sink.attr("OnUpdatedScheduleCalendarEventNotification")(scheduleResult);
        }
    }

    void OnUpdatedDeleteCalendarEventNotification(DeleteCalendarEventResult deleteResult) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnUpdatedDeleteCalendarEventNotification")) {
            py_sink.attr("OnUpdatedDeleteCalendarEventNotification")(deleteResult);
        }
    }

    void OnShowUpcomingMeetingAlertResult(int32_t result, const MeetingItem& meetingItem) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnShowUpcomingMeetingAlertResult")) {
            py_sink.attr("OnShowUpcomingMeetingAlertResult")(result, meetingItem);
        }
    }

    void OnCloseUpcomingMeetingAlertResult(int32_t result) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnCloseUpcomingMeetingAlertResult")) {
            py_sink.attr("OnCloseUpcomingMeetingAlertResult")(result);
        }
    }

    void OnMeetingWillReleaseAutomatically(const MeetingItem& meetingItem) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnMeetingWillReleaseAutomatically")) {
            py_sink.attr("OnMeetingWillReleaseAutomatically")(meetingItem);
        }
    }
};

// Trampoline for IMeetingReminderHelperSink
class MeetingReminderHelperSinkTrampoline : public IMeetingReminderHelperSink {
private:
    py::object py_sink;

public:
    MeetingReminderHelperSinkTrampoline(py::object obj) : py_sink(obj) {}

    void OnConsentNotification(const ConsentInfo& info) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnConsentNotification")) {
            py_sink.attr("OnConsentNotification")(info);
        } 
    }
        
    void OnMeetingReminderNotification(const MeetingReminderContent& reminderContent) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnMeetingReminderNotification")) {
            py_sink.attr("OnMeetingReminderNotification")(reminderContent);
        }
    }
    
    void OnCustomizedReminderNotification(const CustomizedMeetingReminderContent& customizedContent) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnCustomizedReminderNotification")) {
            py_sink.attr("OnCustomizedReminderNotification")(customizedContent);
        }
    }
    
    void OnCombinedConsentNotification(const CombinedConsent& combinedConsent) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnCombinedConsentNotification")) {
            py_sink.attr("OnCombinedConsentNotification")(combinedConsent);
        }
    }
    
    void OnPrivacyAlertNotification(PrivacyAlertAction action, PrivacyAlertType type, const DisclaimerPrivacy& message) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnPrivacyAlertNotification")) {
            py_sink.attr("OnPrivacyAlertNotification")(action, type, message);
        }
    }
    
    void OnMessageEventNotification(MessageEvent messageEvent) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnMessageEventNotification")) {
            py_sink.attr("OnMessageEventNotification")(messageEvent);
        }
    }
    
    void OnInactiveDetectionNotification(bool isShowPrompt, time_t autoEndTime) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnInactiveDetectionNotification")) {
            py_sink.attr("OnInactiveDetectionNotification")(isShowPrompt, autoEndTime);
        }
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

    py::enum_<ConnectionState>(m, "ConnectionState")
        .value("ConnectionStateNone", ConnectionState::ConnectionStateNone)
        .value("ConnectionStateEstablished", ConnectionState::ConnectionStateEstablished)
        .value("ConnectionStateConnected", ConnectionState::ConnectionStateConnected)
        .value("ConnectionStateDisconnected", ConnectionState::ConnectionStateDisconnected)
        .export_values();

    py::enum_<RoomUnpairedReason>(m, "RoomUnpairedReason")
        .value("RoomUnpairedReason_TokenInvalid", RoomUnpairedReason::RoomUnpairedReason_TokenInvalid)
        .value("RoomUnpairedReason_RefreshTokenFail", RoomUnpairedReason::RoomUnpairedReason_RefreshTokenFail)
        .export_values();

    py::enum_<CameraBoundaryAdjustField>(m, "CameraBoundaryAdjustField")
        .value("CameraBoundaryAdjustFieldUnknown", CameraBoundaryAdjustField::CameraBoundaryAdjustFieldUnknown)
        .value("CameraBoundaryAdjustFieldLeft", CameraBoundaryAdjustField::CameraBoundaryAdjustFieldLeft)
        .value("CameraBoundaryAdjustFieldRight", CameraBoundaryAdjustField::CameraBoundaryAdjustFieldRight)
        .value("CameraBoundaryAdjustFieldDepth", CameraBoundaryAdjustField::CameraBoundaryAdjustFieldDepth)
        .export_values();

    py::enum_<VirtualAudioDeviceType>(m, "VirtualAudioDeviceType")
        .value("VirtualAudioDeviceTypeUnknown", VirtualAudioDeviceType::VirtualAudioDeviceTypeUnknown)
        .value("VirtualAudioDeviceTypeMicrophone", VirtualAudioDeviceType::VirtualAudioDeviceTypeMicrophone)
        .value("VirtualAudioDeviceTypeSpeaker", VirtualAudioDeviceType::VirtualAudioDeviceTypeSpeaker)
        .export_values();

    py::enum_<PSTNCallOutStatus>(m, "PSTNCallOutStatus")
        .value("PSTNCallOutStatusUnknown", PSTNCallOutStatus::PSTNCallOutStatusUnknown)
        .value("PSTNCallOutStatusCalling", PSTNCallOutStatus::PSTNCallOutStatusCalling)
        .value("PSTNCallOutStatusRinging", PSTNCallOutStatus::PSTNCallOutStatusRinging)
        .value("PSTNCallOutStatusAccepted", PSTNCallOutStatus::PSTNCallOutStatusAccepted)
        .value("PSTNCallOutStatusBusy", PSTNCallOutStatus::PSTNCallOutStatusBusy)
        .value("PSTNCallOutStatusNotAvailable", PSTNCallOutStatus::PSTNCallOutStatusNotAvailable)
        .value("PSTNCallOutStatusUserHangUp", PSTNCallOutStatus::PSTNCallOutStatusUserHangUp)
        .value("PSTNCallOutStatusOtherFail", PSTNCallOutStatus::PSTNCallOutStatusOtherFail)
        .value("PSTNCallOutStatusJoinSuc", PSTNCallOutStatus::PSTNCallOutStatusJoinSuc)
        .export_values();

    // ===== Core SDK =====
    py::class_<IZRCSDK>(m, "IZRCSDK")
        .def_static("CreateInstance", [](py::object py_sink) {
            g_sdk_sink_impl = std::make_shared<SimpleSinkImpl>(py_sink);
            return IZRCSDK::CreateInstance(g_sdk_sink_impl.get());
        }, py::arg("sink"), py::return_value_policy::reference)
        .def_static("GetInstance", &IZRCSDK::GetInstance, py::return_value_policy::reference)
        .def_static("DestroyInstance", &IZRCSDK::DestroyInstance)
        .def("InitWebDomain", &IZRCSDK::InitWebDomain)
        .def("HeartBeat", &IZRCSDK::HeartBeat)
        .def("ForceFlushLog", &IZRCSDK::ForceFlushLog)
        .def("CreateZoomRoomsService", &IZRCSDK::CreateZoomRoomsService,
             py::arg("roomID") = ZRCSDK_DEFAULT_ROOM_ID,
             py::return_value_policy::reference)
        .def("QueryAllZoomRoomsServices", &IZRCSDK::QueryAllZoomRoomsServices);

    // Module-level helper to create SDK instance with sink (for backwards compatibility)
    m.def("CreateInstanceWithSink", [](py::object py_sink) {
        g_sdk_sink_impl = std::make_shared<SimpleSinkImpl>(py_sink);
        return IZRCSDK::CreateInstance(g_sdk_sink_impl.get());
    }, py::arg("sink"), py::return_value_policy::reference);

    // ===== ZoomRooms Service =====
    py::class_<IZoomRoomsService>(m, "IZoomRoomsService")
        .def("PairRoomWithActivationCode", &IZoomRoomsService::PairRoomWithActivationCode)
        .def("UnpairRoom", &IZoomRoomsService::UnpairRoom)
        .def("RetryToPairRoom", &IZoomRoomsService::RetryToPairRoom)
        .def("GetPreMeetingService", &IZoomRoomsService::GetPreMeetingService, py::return_value_policy::reference)
        .def("GetMeetingService", &IZoomRoomsService::GetMeetingService, py::return_value_policy::reference)
        .def("GetPhoneCallService", &IZoomRoomsService::GetPhoneCallService, py::return_value_policy::reference)
        .def("GetProAVService", &IZoomRoomsService::GetProAVService, py::return_value_policy::reference)
        .def("GetSettingService", &IZoomRoomsService::GetSettingService, py::return_value_policy::reference)
        .def("RegisterSink", [](IZoomRoomsService* self, py::object py_sink) {
            // Create a trampoline and keep it alive in a static map
            static std::map<IZoomRoomsService*, std::shared_ptr<ZoomRoomsServiceSinkTrampoline>> sinks;
            auto trampoline = std::make_shared<ZoomRoomsServiceSinkTrampoline>(py_sink);
            sinks[self] = trampoline;
            return self->RegisterSink(trampoline.get());
        })
        .def("DeregisterSink", [](IZoomRoomsService* self) {
            static std::map<IZoomRoomsService*, std::shared_ptr<ZoomRoomsServiceSinkTrampoline>> sinks;
            auto it = sinks.find(self);
            if (it != sinks.end()) {
                auto result = self->DeregisterSink(it->second.get());
                sinks.erase(it);
                return result;
            }
            return ZRCSDKERR_INTERNAL_ERROR;
        });

    // ===== Pre-Meeting Service Enums =====
    py::enum_<LogType>(m, "LogType")
        .value("LogTypeBasic", LogType::LogTypeBasic)
        .value("LogTypeAudio", LogType::LogTypeAudio)
        .value("LogTypeContentSharing", LogType::LogTypeContentSharing)
        .value("LogTypeCrashDump", LogType::LogTypeCrashDump)
        .export_values();

    // ===== Pre-Meeting Helper Classes (opaque for now) =====
    py::class_<IContactHelper>(m, "IContactHelper");
    py::class_<IBYODHelper>(m, "IBYODHelper");
    py::class_<IControlSystemHelper>(m, "IControlSystemHelper");

    // ===== Pre-Meeting Service =====
    py::class_<IPreMeetingService>(m, "IPreMeetingService")
        .def("GetConnectionState", [](IPreMeetingService* self) {
            ConnectionState state;
            ZRCSDKError result = self->GetConnectionState(state);
            return py::make_tuple(result, state);
        })
        .def("RegisterSink", [](IPreMeetingService* self, py::object py_sink) {
            // Create a trampoline and keep it alive in a static map
            static std::map<IPreMeetingService*, std::shared_ptr<PreMeetingServiceSinkTrampoline>> sinks;
            auto trampoline = std::make_shared<PreMeetingServiceSinkTrampoline>(py_sink);
            sinks[self] = trampoline;
            return self->RegisterSink(trampoline.get());
        })
        .def("DeregisterSink", [](IPreMeetingService* self) {
            static std::map<IPreMeetingService*, std::shared_ptr<PreMeetingServiceSinkTrampoline>> sinks;
            auto it = sinks.find(self);
            if (it != sinks.end()) {
                auto result = self->DeregisterSink(it->second.get());
                sinks.erase(it);
                return result;
            }
            return ZRCSDKERR_INTERNAL_ERROR;
        })
        .def("NotifyZoomRoomsSendProblemReport", &IPreMeetingService::NotifyZoomRoomsSendProblemReport)
        .def("IsZoomRoomSupportRestartOS", [](IPreMeetingService* self) {
            bool support;
            ZRCSDKError result = self->IsZoomRoomSupportRestartOS(support);
            return py::make_tuple(result, support);
        })
        .def("RestartZoomRoomOS", &IPreMeetingService::RestartZoomRoomOS)
        .def("LogoutZoomRoomDevice", &IPreMeetingService::LogoutZoomRoomDevice)
        .def("WakeZoomRoomUp", &IPreMeetingService::WakeZoomRoomUp)
        .def("GetContactHelper", &IPreMeetingService::GetContactHelper, py::return_value_policy::reference)
        .def("GetBYODHelper", &IPreMeetingService::GetBYODHelper, py::return_value_policy::reference)
        .def("GetControlSystemHelper", &IPreMeetingService::GetControlSystemHelper, py::return_value_policy::reference);

    // ===== Meeting Service Enums =====
    py::enum_<ExitMeetingCmd>(m, "ExitMeetingCmd")
        .value("ExitMeetingCmdLeave", ExitMeetingCmd::ExitMeetingCmdLeave)
        .value("ExitMeetingCmdEnd", ExitMeetingCmd::ExitMeetingCmdEnd)
        .export_values();

    py::enum_<MeetingStatus>(m, "MeetingStatus")
        .value("MeetingStatusNotInMeeting", MeetingStatus::MeetingStatusNotInMeeting)
        .value("MeetingStatusConnectingToMeeting", MeetingStatus::MeetingStatusConnectingToMeeting)
        .value("MeetingStatusInMeeting", MeetingStatus::MeetingStatusInMeeting)
        .value("MeetingStatusLoggedOut", MeetingStatus::MeetingStatusLoggedOut)
        .export_values();

    py::enum_<RoomSystemProtocolType>(m, "RoomSystemProtocolType")
        .value("RoomSystemProtocolTypeUnknown", RoomSystemProtocolType::RoomSystemProtocolTypeUnknown)
        .value("RoomSystemProtocolTypeH323", RoomSystemProtocolType::RoomSystemProtocolTypeH323)
        .value("RoomSystemProtocolTypeSIP", RoomSystemProtocolType::RoomSystemProtocolTypeSIP)
        .export_values();

    // ===== Meeting Service Structs =====
    py::class_<LegacyRoomSystem>(m, "LegacyRoomSystem")
        .def(py::init<>())
        .def_readwrite("name", &LegacyRoomSystem::name)
        .def_readwrite("ip", &LegacyRoomSystem::ip)
        .def_readwrite("e164Num", &LegacyRoomSystem::e164Num)
        .def_readwrite("roomSystemType", &LegacyRoomSystem::roomSystemType)
        .def_readwrite("encryptType", &LegacyRoomSystem::encryptType)
        .def_readwrite("isPexipCVI", &LegacyRoomSystem::isPexipCVI);

    py::class_<MeetingInfo>(m, "MeetingInfo")
        .def(py::init<>())
        .def_readwrite("meetingID", &MeetingInfo::meetingID)
        .def_readwrite("meetingNumber", &MeetingInfo::meetingNumber)
        .def_readwrite("meetingName", &MeetingInfo::meetingName)
        .def_readwrite("meetingType", &MeetingInfo::meetingType)
        .def_readwrite("meetingPassword", &MeetingInfo::meetingPassword)
        .def_readwrite("numericPassword", &MeetingInfo::numericPassword)
        .def_readwrite("inviteEmailTitle", &MeetingInfo::inviteEmailTitle)
        .def_readwrite("inviteEmailContent", &MeetingInfo::inviteEmailContent)
        .def_readwrite("joinMeetingUrl", &MeetingInfo::joinMeetingUrl)
        .def_readwrite("isWebinar", &MeetingInfo::isWebinar)
        .def_readwrite("isWaitingRoom", &MeetingInfo::isWaitingRoom)
        .def_readwrite("encryptionAlgorithm", &MeetingInfo::encryptionAlgorithm)
        .def_readwrite("myUserId", &MeetingInfo::myUserId)
        .def_readwrite("isWebinarAttendee", &MeetingInfo::isWebinarAttendee)
        .def_readwrite("isWebinarAttendeeCanTalk", &MeetingInfo::isWebinarAttendeeCanTalk)
        .def_readwrite("amIOriginalHost", &MeetingInfo::amIOriginalHost)
        .def_readwrite("canPutOnHold", &MeetingInfo::canPutOnHold)
        .def_readwrite("isAllowHostAssignCCEditor", &MeetingInfo::isAllowHostAssignCCEditor)
        .def_readwrite("isPAC", &MeetingInfo::isPAC)
        .def_readwrite("isPACVideoForbidden", &MeetingInfo::isPACVideoForbidden)
        .def_readwrite("isPACShareForbidden", &MeetingInfo::isPACShareForbidden)
        .def_readwrite("isGreenRoomEnabled", &MeetingInfo::isGreenRoomEnabled)
        .def_readwrite("isDebriefSessionEnabled", &MeetingInfo::isDebriefSessionEnabled)
        .def_readwrite("isPrivateModeMeeting", &MeetingInfo::isPrivateModeMeeting);

    py::class_<MeetingInvitationInfo>(m, "MeetingInvitationInfo")
        .def(py::init<>())
        .def_readwrite("callerContactID", &MeetingInvitationInfo::callerContactID)
        .def_readwrite("callerName", &MeetingInvitationInfo::callerName)
        .def_readwrite("callerAvatarUrl", &MeetingInvitationInfo::callerAvatarUrl)
        .def_readwrite("calleeContactID", &MeetingInvitationInfo::calleeContactID)
        .def_readwrite("meetingID", &MeetingInvitationInfo::meetingID)
        .def_readwrite("password", &MeetingInvitationInfo::password)
        .def_readwrite("meetingOptions", &MeetingInvitationInfo::meetingOptions)
        .def_readwrite("meetingNumber", &MeetingInvitationInfo::meetingNumber)
        .def_readwrite("expireTime", &MeetingInvitationInfo::expireTime);

    // ===== Meeting Service =====
    py::class_<IMeetingService>(m, "IMeetingService")
        .def("StartInstantMeeting", &IMeetingService::StartInstantMeeting)
        .def("MeetWithIMUsers", &IMeetingService::MeetWithIMUsers)
        .def("StartMeeting", &IMeetingService::StartMeeting, py::arg("meeting"), py::arg("bringShareToMeeting") = false)
        .def("StartMeetingWithHostKey", &IMeetingService::StartMeetingWithHostKey)
        .def("JoinMeetingWithMeetingNumber", &IMeetingService::JoinMeetingWithMeetingNumber,
            py::arg("meetingNumber"), py::arg("bringShareToMeeting") = false)
        .def("JoinMeetingWithURL", &IMeetingService::JoinMeetingWithURL, py::arg("url"))
        .def("JoinMeetingWithContactID", &IMeetingService::JoinMeetingWithContactID, py::arg("contactID"))
        .def("JoinMeetingWithPersonalLinkName", &IMeetingService::JoinMeetingWithPersonalLinkName,
            py::arg("personalLinkName"), py::arg("bringShareToMeeting") = false)
        .def("JoinMeetingWithPersonalLink", &IMeetingService::JoinMeetingWithPersonalLink, py::arg("personalLink"))
        .def("CancelConfirmPersonalLink", &IMeetingService::CancelConfirmPersonalLink)
        .def("ExitMeeting", &IMeetingService::ExitMeeting)
        .def("SetRoomTempDisplayNameForMeeting", &IMeetingService::SetRoomTempDisplayNameForMeeting)
        .def("SendMeetingPassword", &IMeetingService::SendMeetingPassword)
        .def("CancelEnteringMeetingPassword", &IMeetingService::CancelEnteringMeetingPassword)
        .def("CancelWaitingForHost", &IMeetingService::CancelWaitingForHost)
        .def("AnswerMeetingInvite", &IMeetingService::AnswerMeetingInvite)
        .def("InviteAttendees", &IMeetingService::InviteAttendees)
        .def("InviteLegacyRoomSystems", &IMeetingService::InviteLegacyRoomSystems)
        .def("InviteLegacyRoomSystemWithIpOrE164Number", &IMeetingService::InviteLegacyRoomSystemWithIpOrE164Number)
        .def("SendMeetingInviteEmail", &IMeetingService::SendMeetingInviteEmail)
        .def("RequestE2ESecurityCode", &IMeetingService::RequestE2ESecurityCode)
        .def("SendDTMF", &IMeetingService::SendDTMF)
        .def("GetMeetingStatus", [](IMeetingService* self) {
            MeetingStatus status;
            ZRCSDKError result = self->GetMeetingStatus(status);
            return py::make_tuple(result, status);
        })
        .def("GetMeetingInfo", [](IMeetingService* self) {
            MeetingInfo info;
            ZRCSDKError result = self->GetMeetingInfo(info);
            return py::make_tuple(result, info);
        })
        .def("ExtendMeeting", &IMeetingService::ExtendMeeting)
        .def("GetMeetingAudioHelper", &IMeetingService::GetMeetingAudioHelper, py::return_value_policy::reference)
        .def("GetMeetingVideoHelper", &IMeetingService::GetMeetingVideoHelper, py::return_value_policy::reference)
        .def("GetMeetingControlHelper", &IMeetingService::GetMeetingControlHelper, py::return_value_policy::reference)
        .def("GetMeetingListHelper", &IMeetingService::GetMeetingListHelper, py::return_value_policy::reference)
        .def("GetMeetingReminderHelper", &IMeetingService::GetMeetingReminderHelper, py::return_value_policy::reference)
        .def("GetMeetingShareHelper", &IMeetingService::GetMeetingShareHelper, py::return_value_policy::reference)
        .def("GetMeetingViewLayoutHelper", &IMeetingService::GetMeetingViewLayoutHelper, py::return_value_policy::reference)
        .def("GetNDIHelper", &IMeetingService::GetNDIHelper, py::return_value_policy::reference)
        .def("GetParticipantHelper", &IMeetingService::GetParticipantHelper, py::return_value_policy::reference)
        .def("GetRecordingHelper", &IMeetingService::GetRecordingHelper, py::return_value_policy::reference)
        .def("GetThirdPartyMeetingHelper", &IMeetingService::GetThirdPartyMeetingHelper, py::return_value_policy::reference);

    // ===== Meeting Audio Helper =====
    py::class_<IMeetingAudioHelper>(m, "IMeetingAudioHelper")
        .def("UpdateMyAudioStatus", &IMeetingAudioHelper::UpdateMyAudioStatus);

    // ===== Meeting Video Helper =====
    py::class_<IMeetingVideoHelper>(m, "IMeetingVideoHelper")
        .def("UpdateMyVideo", &IMeetingVideoHelper::UpdateMyVideo)
        .def("MuteUserVideo", &IMeetingVideoHelper::MuteUserVideo)
        .def("AnswerHostRequestUnmuteVideo", &IMeetingVideoHelper::AnswerHostRequestUnmuteVideo)
        .def("AllowAttendeesStartVideo", &IMeetingVideoHelper::AllowAttendeesStartVideo)
        .def("ShowPinUserInstruction", &IMeetingVideoHelper::ShowPinUserInstruction)
        .def("AllowUserMultiPin", &IMeetingVideoHelper::AllowUserMultiPin)
        .def("PinUserOnScreen", &IMeetingVideoHelper::PinUserOnScreen)
        .def("AddPinUserOnScreen", &IMeetingVideoHelper::AddPinUserOnScreen)
        .def("UnpinUserFromScreen", &IMeetingVideoHelper::UnpinUserFromScreen)
        .def("UnpinUserFromAllScreens", &IMeetingVideoHelper::UnpinUserFromAllScreens)
        .def("PinSmartNameTagStreamOnScreen", &IMeetingVideoHelper::PinSmartNameTagStreamOnScreen)
        .def("AddPinSmartNameTagStreamOnScreen", &IMeetingVideoHelper::AddPinSmartNameTagStreamOnScreen)
        .def("UnpinSmartNameTagStreamFromScreen", &IMeetingVideoHelper::UnpinSmartNameTagStreamFromScreen)
        .def("UnpinSmartNameTagStreamFromAllScreens", &IMeetingVideoHelper::UnpinSmartNameTagStreamFromAllScreens)
        .def("RemoveAllPinUsers", &IMeetingVideoHelper::RemoveAllPinUsers)
        .def("SpotlightUser", &IMeetingVideoHelper::SpotlightUser)
        .def("AddSpotlightUser", &IMeetingVideoHelper::AddSpotlightUser)
        .def("CancelSpotlightUser", &IMeetingVideoHelper::CancelSpotlightUser)
        .def("RemoveAllSpotlightUsers", &IMeetingVideoHelper::RemoveAllSpotlightUsers)
        .def("IsSupportSetMyVideoHidden", [](IMeetingVideoHelper* self) {
            bool support;
            ZRCSDKError result = self->IsSupportSetMyVideoHidden(support);
            return py::make_tuple(result, support);
        })
        .def("SetMyVideoHidden", &IMeetingVideoHelper::SetMyVideoHidden)
        .def("SetMyVideoTouchUp", &IMeetingVideoHelper::SetMyVideoTouchUp)
        .def("SetMyVideoLowLight", &IMeetingVideoHelper::SetMyVideoLowLight)
        .def("FetchMyMeetingVideoSettings", &IMeetingVideoHelper::FetchMyMeetingVideoSettings)
        .def("SetMyMeetingVideoTouchUp", &IMeetingVideoHelper::SetMyMeetingVideoTouchUp)
        .def("SetMyMeetingVideoLowLight", &IMeetingVideoHelper::SetMyMeetingVideoLowLight)
        .def("ShowVideoPreview",
            static_cast<ZRCSDKError(IMeetingVideoHelper::*)(bool, PreviewVideoType, const MeetingItem&)>(&IMeetingVideoHelper::ShowVideoPreview));

    // ===== Meeting Control Helper Enums =====
    py::enum_<FocusModeStatus>(m, "FocusModeStatus")
        .value("FocusModeStatusOff", FocusModeStatus::FocusModeStatusOff)
        .value("FocusModeStatusEnding", FocusModeStatus::FocusModeStatusEnding)
        .value("FocusModeStatusOn", FocusModeStatus::FocusModeStatusOn)
        .export_values();

    py::enum_<AICompanionOption>(m, "AICompanionOption")
        .value("AICompanionOptionSmartSummary", AICompanionOption::AICompanionOptionSmartSummary)
        .value("AICompanionOptionSmartQuestion", AICompanionOption::AICompanionOptionSmartQuestion)
        .value("AICompanionOptionSmartRecording", AICompanionOption::AICompanionOptionSmartRecording)
        .export_values();

    py::enum_<PanelType>(m, "PanelType")
        .value("PanelTypeNone", PanelType::PanelTypeNone)
        .value("PanelTypePList", PanelType::PanelTypePList)
        .export_values();

    py::enum_<PanelAction>(m, "PanelAction")
        .value("PanelActionShow", PanelAction::PanelActionShow)
        .value("PanelActionHide", PanelAction::PanelActionHide)
        .value("PanelActionSwitchTab", PanelAction::PanelActionSwitchTab)
        .value("PanelActionScrollUp", PanelAction::PanelActionScrollUp)
        .value("PanelActionScrollDown", PanelAction::PanelActionScrollDown)
        .export_values();

    // ===== Meeting Control Helper =====
    py::class_<IMeetingControlHelper>(m, "IMeetingControlHelper")
        .def("ShowTopBanner", &IMeetingControlHelper::ShowTopBanner)
        .def("LockMeeting", &IMeetingControlHelper::LockMeeting)
        .def("StartFocusMode", &IMeetingControlHelper::StartFocusMode)
        .def("EnableHiFiMusicMode", &IMeetingControlHelper::EnableHiFiMusicMode)
        .def("HasNewAppSignaling", &IMeetingControlHelper::HasNewAppSignaling)
        .def("ListSignalingApps", &IMeetingControlHelper::ListSignalingApps)
        .def("ListSignalingAppAccessedUsers", &IMeetingControlHelper::ListSignalingAppAccessedUsers)
        .def("GetSignalingAppPermissionLink", &IMeetingControlHelper::GetSignalingAppPermissionLink)
        .def("StartMeetingSummary", &IMeetingControlHelper::StartMeetingSummary)
        .def("StartMeetingQuery", &IMeetingControlHelper::StartMeetingQuery)
        .def("ChangeMeetingQueryPrivilegeSetting", &IMeetingControlHelper::ChangeMeetingQueryPrivilegeSetting)
        .def("SetMeetingSummaryNotificationEmail", &IMeetingControlHelper::SetMeetingSummaryNotificationEmail)
        .def("TurnOnAICompanion", &IMeetingControlHelper::TurnOnAICompanion)
        .def("TurnOffAICompanion", &IMeetingControlHelper::TurnOffAICompanion)
        .def("RespondToTurnOnAICompanion", &IMeetingControlHelper::RespondToTurnOnAICompanion)
        .def("RespondToTurnOffAICompanion", &IMeetingControlHelper::RespondToTurnOffAICompanion)
        .def("AskHostToTurnOnAICompanion", &IMeetingControlHelper::AskHostToTurnOnAICompanion)
        .def("AskHostToTurnOffAllAICompanion", &IMeetingControlHelper::AskHostToTurnOffAllAICompanion)
        .def("ConfirmAICompanionStatusWhenJoin", &IMeetingControlHelper::ConfirmAICompanionStatusWhenJoin)
        .def("AskToEnableAICompanion", &IMeetingControlHelper::AskToEnableAICompanion)
        .def("ControlSidePanel", &IMeetingControlHelper::ControlSidePanel);

    // ===== Meeting Share Helper Enums =====
    py::enum_<ConfInstType>(m, "ConfInstType")
        .value("ConfInstTypeUnknown", ConfInstType::ConfInstTypeUnknown)
        .value("ConfInstTypeCurrentConf", ConfInstType::ConfInstTypeCurrentConf)
        .value("ConfInstTypeMasterConf", ConfInstType::ConfInstTypeMasterConf)
        .value("ConfInstTypeBackstage", ConfInstType::ConfInstTypeBackstage)
        .value("ConfInstTypeNewBO", ConfInstType::ConfInstTypeNewBO)
        .export_values();

    py::enum_<ShareSourceType>(m, "ShareSourceType")
        .value("ShareSourceTypeUnknown", ShareSourceType::ShareSourceTypeUnknown)
        .value("ShareSourceTypeNormal", ShareSourceType::ShareSourceTypeNormal)
        .value("ShareSourceTypeCloudWB", ShareSourceType::ShareSourceTypeCloudWB)
        .value("ShareSourceTypeCollaborationZapps", ShareSourceType::ShareSourceTypeCollaborationZapps)
        .export_values();

    py::enum_<SharingInstructionDisplayState>(m, "SharingInstructionDisplayState")
        .value("SharingInstructionDisplayStateNone", SharingInstructionDisplayState::SharingInstructionDisplayStateNone)
        .value("SharingInstructionDisplayStateDesktop", SharingInstructionDisplayState::SharingInstructionDisplayStateDesktop)
        .value("SharingInstructionDisplayStateIOS", SharingInstructionDisplayState::SharingInstructionDisplayStateIOS)
        .value("SharingInstructionDisplayStateWhiteboardCamera", SharingInstructionDisplayState::SharingInstructionDisplayStateWhiteboardCamera)
        .export_values();

    py::enum_<SharingState>(m, "SharingState")
        .value("SharingStateNone", SharingState::SharingStateNone)
        .value("SharingStateConnecting", SharingState::SharingStateConnecting)
        .value("SharingStateSending", SharingState::SharingStateSending)
        .value("SharingStateReceiving", SharingState::SharingStateReceiving)
        .value("SharingStateSendingAndReceiving", SharingState::SharingStateSendingAndReceiving)
        .export_values();

    py::enum_<ZRSharePrivilegeType>(m, "ZRSharePrivilegeType")
        .value("ZRSharePrivilegeTypeEnabled", ZRSharePrivilegeType::ZRSharePrivilegeTypeEnabled)
        .value("ZRSharePrivilegeTypeDisabled", ZRSharePrivilegeType::ZRSharePrivilegeTypeDisabled)
        .value("ZRSharePrivilegeTypeDisabledParticipant", ZRSharePrivilegeType::ZRSharePrivilegeTypeDisabledParticipant)
        .value("ZRSharePrivilegeTypeDisabledWhileOthersSharing", ZRSharePrivilegeType::ZRSharePrivilegeTypeDisabledWhileOthersSharing)
        .value("ZRSharePrivilegeTypeDisabledWhileGuestsInMeeting", ZRSharePrivilegeType::ZRSharePrivilegeTypeDisabledWhileGuestsInMeeting)
        .value("ZRSharePrivilegeTypeDisabledWhileCloudWhiteboard", ZRSharePrivilegeType::ZRSharePrivilegeTypeDisabledWhileCloudWhiteboard)
        .value("ZRSharePrivilegeTypeDisabledInBOWhileMainSessionSharing", ZRSharePrivilegeType::ZRSharePrivilegeTypeDisabledInBOWhileMainSessionSharing)
        .value("ZRSharePrivilegeTypeDisabledStartShareForSimulive", ZRSharePrivilegeType::ZRSharePrivilegeTypeDisabledStartShareForSimulive)
        .value("ZRSharePrivilegeTypeDisabledStartShareForDSOnly", ZRSharePrivilegeType::ZRSharePrivilegeTypeDisabledStartShareForDSOnly)
        .export_values();

    py::enum_<MeetingSharePrivilegeType>(m, "MeetingSharePrivilegeType")
        .value("MeetingSharePrivilegeTypeUnknown", MeetingSharePrivilegeType::MeetingSharePrivilegeTypeUnknown)
        .value("MeetingSharePrivilegeTypeHostGrab", MeetingSharePrivilegeType::MeetingSharePrivilegeTypeHostGrab)
        .value("MeetingSharePrivilegeTypeLockShare", MeetingSharePrivilegeType::MeetingSharePrivilegeTypeLockShare)
        .value("MeetingSharePrivilegeTypeAnyoneGrab", MeetingSharePrivilegeType::MeetingSharePrivilegeTypeAnyoneGrab)
        .value("MeetingSharePrivilegeTypeMultiShare", MeetingSharePrivilegeType::MeetingSharePrivilegeTypeMultiShare)
        .export_values();

    py::enum_<MeetingShareViewPrivilege>(m, "MeetingShareViewPrivilege")
        .value("MeetingShareViewPrivilege_FocusModeOff", MeetingShareViewPrivilege::MeetingShareViewPrivilege_FocusModeOff)
        .value("MeetingShareViewPrivilege_FocusModeHostOnly", MeetingShareViewPrivilege::MeetingShareViewPrivilege_FocusModeHostOnly)
        .value("MeetingShareViewPrivilege_FocusModeAllParticipants", MeetingShareViewPrivilege::MeetingShareViewPrivilege_FocusModeAllParticipants)
        .export_values();

    py::enum_<HDMI60FPSShareDisableReason>(m, "HDMI60FPSShareDisableReason")
        .value("HDMI60FPSShareDisableReasonUnknown", HDMI60FPSShareDisableReason::HDMI60FPSShareDisableReasonUnknown)
        .value("HDMI60FPSShareDisableReasonNotDisable", HDMI60FPSShareDisableReason::HDMI60FPSShareDisableReasonNotDisable)
        .value("HDMI60FPSShareDisableReasonCaptureCardNotSupport", HDMI60FPSShareDisableReason::HDMI60FPSShareDisableReasonCaptureCardNotSupport)
        .value("HDMI60FPSShareDisableReasonZRNotSupport", HDMI60FPSShareDisableReason::HDMI60FPSShareDisableReasonZRNotSupport)
        .value("HDMI60FPSShareDisableReasonCaptureCardAndZRNotSupport", HDMI60FPSShareDisableReason::HDMI60FPSShareDisableReasonCaptureCardAndZRNotSupport)
        .value("HDMI60FPSShareDisableReasonOptimizeVideoShareIsOff", HDMI60FPSShareDisableReason::HDMI60FPSShareDisableReasonOptimizeVideoShareIsOff)
        .value("HDMI60FPSShareDisableReasonMultiShareIsOn", HDMI60FPSShareDisableReason::HDMI60FPSShareDisableReasonMultiShareIsOn)
        .export_values();

    py::enum_<CurrentShareType>(m, "CurrentShareType")
        .value("CurrentShareTypeUnknown", CurrentShareType::CurrentShareTypeUnknown)
        .value("CurrentShareTypeNormal", CurrentShareType::CurrentShareTypeNormal)
        .value("CurrentShareTypeCamera", CurrentShareType::CurrentShareTypeCamera)
        .value("CurrentShareTypeAnnotated", CurrentShareType::CurrentShareTypeAnnotated)
        .value("CurrentShareTypeZoomApp", CurrentShareType::CurrentShareTypeZoomApp)
        .value("CurrentShareTypeWhiteboard", CurrentShareType::CurrentShareTypeWhiteboard)
        .value("CurrentShareTypeLocalHDMI", CurrentShareType::CurrentShareTypeLocalHDMI)
        .value("CurrentShareTypeAnnotatedLocalHDMI", CurrentShareType::CurrentShareTypeAnnotatedLocalHDMI)
        .export_values();

    py::enum_<SlideOperationType>(m, "SlideOperationType")
        .value("SlideOperationTypeLeft", SlideOperationType::SlideOperationTypeLeft)
        .value("SlideOperationTypeRight", SlideOperationType::SlideOperationTypeRight)
        .export_values();

    py::enum_<DocsSharePrivilegeType>(m, "DocsSharePrivilegeType")
        .value("DocsSharePrivilegeTypeUnknown", DocsSharePrivilegeType::DocsSharePrivilegeTypeUnknown)
        .value("DocsSharePrivilegeTypeHostGrab", DocsSharePrivilegeType::DocsSharePrivilegeTypeHostGrab)
        .value("DocsSharePrivilegeTypeAnyoneGrab", DocsSharePrivilegeType::DocsSharePrivilegeTypeAnyoneGrab)
        .export_values();

    py::enum_<DocsInitiatePrivilegeType>(m, "DocsInitiatePrivilegeType")
        .value("DocsInitiatePrivilegeTypeUnknown", DocsInitiatePrivilegeType::DocsInitiatePrivilegeTypeUnknown)
        .value("DocsInitiatePrivilegeTypeHostOnly", DocsInitiatePrivilegeType::DocsInitiatePrivilegeTypeHostOnly)
        .value("DocsInitiatePrivilegeTypeInternalUsers", DocsInitiatePrivilegeType::DocsInitiatePrivilegeTypeInternalUsers)
        .value("DocsInitiatePrivilegeTypeAllParticipants", DocsInitiatePrivilegeType::DocsInitiatePrivilegeTypeAllParticipants)
        .export_values();

    // ===== Meeting Share Helper Structs =====
    py::class_<ShareSource>(m, "ShareSource")
        .def(py::init<>())
        .def_readwrite("userID", &ShareSource::userID)
        .def_readwrite("shareSourceID", &ShareSource::shareSourceID)
        .def_readwrite("shareSourceType", &ShareSource::shareSourceType)
        .def_readwrite("isSharingAudio", &ShareSource::isSharingAudio)
        .def_readwrite("isAudioMuted", &ShareSource::isAudioMuted)
        .def_readwrite("fromType", &ShareSource::fromType);

    py::class_<LocalPresentationInfo>(m, "LocalPresentationInfo")
        .def(py::init<>())
        .def_readwrite("success", &LocalPresentationInfo::success)
        .def_readwrite("meetingNumber", &LocalPresentationInfo::meetingNumber)
        .def_readwrite("meetingPassword", &LocalPresentationInfo::meetingPassword);

    py::class_<SharingStatus>(m, "SharingStatus")
        .def(py::init<>())
        .def_readwrite("sharingState", &SharingStatus::sharingState)
        .def_readwrite("canShareToBO", &SharingStatus::canShareToBO)
        .def_readwrite("isSharingToBO", &SharingStatus::isSharingToBO);

    py::class_<ZRWSharingStatus>(m, "ZRWSharingStatus")
        .def(py::init<>())
        .def_readwrite("isSharing", &ZRWSharingStatus::isSharing)
        .def_readwrite("canShareToBO", &ZRWSharingStatus::canShareToBO)
        .def_readwrite("isSharingToBO", &ZRWSharingStatus::isSharingToBO);

    py::class_<ShareSetting>(m, "ShareSetting")
        .def(py::init<>())
        .def_readwrite("isMultiShareOn", &ShareSetting::isMultiShareOn)
        .def_readwrite("isMultiShareDisabled", &ShareSetting::isMultiShareDisabled)
        .def_readwrite("zrSharePrivilegeType", &ShareSetting::zrSharePrivilegeType)
        .def_readwrite("meetingSharePrivilegeType", &ShareSetting::meetingSharePrivilegeType)
        .def_readwrite("isSharePrivilegeSettingLocked", &ShareSetting::isSharePrivilegeSettingLocked);

    py::class_<AirplayBlackMagicStatus>(m, "AirplayBlackMagicStatus")
        .def(py::init<>())
        .def_readwrite("instructionDisplayState", &AirplayBlackMagicStatus::instructionDisplayState)
        .def_readwrite("wifiName", &AirplayBlackMagicStatus::wifiName)
        .def_readwrite("serverName", &AirplayBlackMagicStatus::serverName)
        .def_readwrite("password", &AirplayBlackMagicStatus::password)
        .def_readwrite("directPresentationPairingCode", &AirplayBlackMagicStatus::directPresentationPairingCode)
        .def_readwrite("directPresentationSharingKey", &AirplayBlackMagicStatus::directPresentationSharingKey)
        .def_readwrite("isAirHostClientConnected", &AirplayBlackMagicStatus::isAirHostClientConnected)
        .def_readwrite("isBlackMagicConnected", &AirplayBlackMagicStatus::isBlackMagicConnected)
        .def_readwrite("isBlackMagicDataAvailable", &AirplayBlackMagicStatus::isBlackMagicDataAvailable)
        .def_readwrite("isSharingBlackMagic", &AirplayBlackMagicStatus::isSharingBlackMagic)
        .def_readwrite("isDirectPresentationConnected", &AirplayBlackMagicStatus::isDirectPresentationConnected)
        .def_readwrite("isBlackMagicSharingLocallyAvailable", &AirplayBlackMagicStatus::isBlackMagicSharingLocallyAvailable)
        .def_readwrite("isBlackMagicSharingLocally", &AirplayBlackMagicStatus::isBlackMagicSharingLocally);

    py::class_<CameraSharingStatus>(m, "CameraSharingStatus")
        .def(py::init<>())
        .def_readwrite("deviceID", &CameraSharingStatus::deviceID)
        .def_readwrite("isSharing", &CameraSharingStatus::isSharing)
        .def_readwrite("isMirrored", &CameraSharingStatus::isMirrored)
        .def_readwrite("canBeControlled", &CameraSharingStatus::canBeControlled)
        .def_readwrite("panTiltSpeedPercentage", &CameraSharingStatus::panTiltSpeedPercentage);

    py::class_<SlideControlInfo>(m, "SlideControlInfo")
        .def(py::init<>())
        .def_readwrite("userID", &SlideControlInfo::userID)
        .def_readwrite("userName", &SlideControlInfo::userName)
        .def_readwrite("shareSourceID", &SlideControlInfo::shareSourceID);

    py::class_<DocsShareSettingsInfo>(m, "DocsShareSettingsInfo")
        .def(py::init<>())
        .def_readwrite("isSupported", &DocsShareSettingsInfo::isSupported)
        .def_readwrite("isAllowParticipantsToShare", &DocsShareSettingsInfo::isAllowParticipantsToShare)
        .def_readwrite("sharePrivilege", &DocsShareSettingsInfo::sharePrivilege)
        .def_readwrite("initiatePrivilege", &DocsShareSettingsInfo::initiatePrivilege)
        .def_readwrite("isLocked", &DocsShareSettingsInfo::isLocked);

    py::class_<IncomingMeetingShareNot>(m, "IncomingMeetingShareNot")
        .def(py::init<>())
        .def_readwrite("incomingSource", &IncomingMeetingShareNot::incomingSource)
        .def_readwrite("shareUserName", &IncomingMeetingShareNot::shareUserName)
        .def_readwrite("currentShareType", &IncomingMeetingShareNot::currentShareType);

    // ===== Meeting Video Helper Enums =====
    py::enum_<PinShareWarningType>(m, "PinShareWarningType")
        .value("PinShareWarningTypeNone", PinShareWarningType::PinShareWarningTypeNone)
        .value("PinShareWarningTypeNoAnnotationForSelf", PinShareWarningType::PinShareWarningTypeNoAnnotationForSelf)
        .value("PinShareWarningTypeStopSelfShare", PinShareWarningType::PinShareWarningTypeStopSelfShare)
        .value("PinShareWarningTypeStopCameraShare", PinShareWarningType::PinShareWarningTypeStopCameraShare)
        .value("PinShareWarningTypeStopWhiteboard", PinShareWarningType::PinShareWarningTypeStopWhiteboard)
        .export_values();

    py::enum_<CanNotPinShareReason>(m, "CanNotPinShareReason")
        .value("CanNotPinShareReasonUnknown", CanNotPinShareReason::CanNotPinShareReasonUnknown)
        .value("CanNotPinShareReasonContentOnly", CanNotPinShareReason::CanNotPinShareReasonContentOnly)
        .export_values();

    py::enum_<PreviewVideoType>(m, "PreviewVideoType")
        .value("PreviewVideoTypeCameraSettings", PreviewVideoType::PreviewVideoTypeCameraSettings)
        .value("PreviewVideoTypeVirtualBackground", PreviewVideoType::PreviewVideoTypeVirtualBackground)
        .value("PreviewVideoTypeMeetingAlert", PreviewVideoType::PreviewVideoTypeMeetingAlert)
        .export_values();

    py::enum_<ScreenLayoutSourceType>(m, "ScreenLayoutSourceType")
        .value("ScreenLayoutSourceTypeNone", ScreenLayoutSourceType::ScreenLayoutSourceTypeNone)
        .value("ScreenLayoutSourceTypeActiveVideo", ScreenLayoutSourceType::ScreenLayoutSourceTypeActiveVideo)
        .value("ScreenLayoutSourceTypeSelfVideo", ScreenLayoutSourceType::ScreenLayoutSourceTypeSelfVideo)
        .value("ScreenLayoutSourceTypePinnedVideo", ScreenLayoutSourceType::ScreenLayoutSourceTypePinnedVideo)
        .value("ScreenLayoutSourceTypeSharedContent", ScreenLayoutSourceType::ScreenLayoutSourceTypeSharedContent)
        .value("ScreenLayoutSourceTypeThumbnailShareView", ScreenLayoutSourceType::ScreenLayoutSourceTypeThumbnailShareView)
        .export_values();

    // ===== Meeting Video Helper Structs =====
    py::class_<AudioStatus>(m, "AudioStatus")
        .def(py::init<>())
        .def_readwrite("audioType", &AudioStatus::audioType)
        .def_readwrite("isMuted", &AudioStatus::isMuted);

    py::class_<VideoStatus>(m, "VideoStatus")
        .def(py::init<>())
        .def_readwrite("hasSource", &VideoStatus::hasSource)
        .def_readwrite("receiving", &VideoStatus::receiving)
        .def_readwrite("sending", &VideoStatus::sending)
        .def_readwrite("canControl", &VideoStatus::canControl);

    py::class_<HandStatus>(m, "HandStatus")
        .def(py::init<>())
        .def_readwrite("handRaised", &HandStatus::handRaised)
        .def_readwrite("timeStamp", &HandStatus::timeStamp);

    py::class_<ScreenStatusForPin>(m, "ScreenStatusForPin")
        .def(py::init<>())
        .def_readwrite("screenIndex", &ScreenStatusForPin::screenIndex)
        .def_readwrite("canPinVideo", &ScreenStatusForPin::canPinVideo)
        .def_readwrite("pinnedUserIDs", &ScreenStatusForPin::pinnedUserIDs)
        .def_readwrite("screenLayout", &ScreenStatusForPin::screenLayout)
        .def_readwrite("pinnedShareSourceID", &ScreenStatusForPin::pinnedShareSourceID)
        .def_readwrite("pinnedShareSourceType", &ScreenStatusForPin::pinnedShareSourceType)
        .def_readwrite("pinnableShareTypes", &ScreenStatusForPin::pinnableShareTypes)
        .def_readwrite("canPinShare", &ScreenStatusForPin::canPinShare)
        .def_readwrite("canNotPinShareReason", &ScreenStatusForPin::canNotPinShareReason)
        .def_readwrite("isZRWScreen", &ScreenStatusForPin::isZRWScreen)
        .def_readwrite("isThumbnailScreen", &ScreenStatusForPin::isThumbnailScreen)
        .def_readwrite("pinnedShareUserID", &ScreenStatusForPin::pinnedShareUserID);

    py::class_<SpotlightStatus>(m, "SpotlightStatus")
        .def(py::init<>())
        .def_readwrite("present", &SpotlightStatus::present)
        .def_readwrite("userIDs", &SpotlightStatus::userIDs);

    py::class_<MyVideoTouchUpSettings>(m, "MyVideoTouchUpSettings")
        .def(py::init<>())
        .def_readwrite("isFaceBeautyEnabled", &MyVideoTouchUpSettings::isFaceBeautyEnabled)
        .def_readwrite("faceBeautyStrength", &MyVideoTouchUpSettings::faceBeautyStrength);

    py::class_<MyVideoLowLightSettings>(m, "MyVideoLowLightSettings")
        .def(py::init<>())
        .def_readwrite("isAdjustLowLightEnabled", &MyVideoLowLightSettings::isAdjustLowLightEnabled)
        .def_readwrite("isAutoAdjustLowLight", &MyVideoLowLightSettings::isAutoAdjustLowLight)
        .def_readwrite("adjustLowLightValue", &MyVideoLowLightSettings::adjustLowLightValue);

    py::class_<MyVideoSettings>(m, "MyVideoSettings")
        .def(py::init<>())
        .def_readwrite("touchUpSettings", &MyVideoSettings::touchUpSettings)
        .def_readwrite("lowLightSettings", &MyVideoSettings::lowLightSettings)
        .def_readwrite("allowUserEnhanceAppearance", &MyVideoSettings::allowUserEnhanceAppearance)
        .def_readwrite("canPresetSettingsForMeeting", &MyVideoSettings::canPresetSettingsForMeeting)
        .def_readwrite("isLocked", &MyVideoSettings::isLocked);

    py::class_<MyMeetingVideoSettings>(m, "MyMeetingVideoSettings")
        .def(py::init<>())
        .def_readwrite("setting", &MyMeetingVideoSettings::setting)
        .def_readwrite("meeting", &MyMeetingVideoSettings::meeting);

    // ===== Meeting View Layout Helper Enums =====
    py::enum_<VideoLayoutStyle>(m, "VideoLayoutStyle")
        .value("VideoLayoutStyleUnknown", VideoLayoutStyle::VideoLayoutStyleUnknown)
        .value("VideoLayoutStyleGallery", VideoLayoutStyle::VideoLayoutStyleGallery)
        .value("VideoLayoutStyleSpeaker", VideoLayoutStyle::VideoLayoutStyleSpeaker)
        .value("VideoLayoutStyleThumbnail", VideoLayoutStyle::VideoLayoutStyleThumbnail)
        .value("VideoLayoutStyleContentOnly", VideoLayoutStyle::VideoLayoutStyleContentOnly)
        .value("VideoLayoutStyleCancelContentOnly", VideoLayoutStyle::VideoLayoutStyleCancelContentOnly)
        .value("VideoLayoutStyleDynamicLayout", VideoLayoutStyle::VideoLayoutStyleDynamicLayout)
        .export_values();

    py::enum_<VideoThumbPosition>(m, "VideoThumbPosition")
        .value("VideoThumbPositionCenter", VideoThumbPosition::VideoThumbPositionCenter)
        .value("VideoThumbPositionUp", VideoThumbPosition::VideoThumbPositionUp)
        .value("VideoThumbPositionRight", VideoThumbPosition::VideoThumbPositionRight)
        .value("VideoThumbPositionUpRight", VideoThumbPosition::VideoThumbPositionUpRight)
        .value("VideoThumbPositionDown", VideoThumbPosition::VideoThumbPositionDown)
        .value("VideoThumbPositionDownRight", VideoThumbPosition::VideoThumbPositionDownRight)
        .value("VideoThumbPositionLeft", VideoThumbPosition::VideoThumbPositionLeft)
        .value("VideoThumbPositionUpLeft", VideoThumbPosition::VideoThumbPositionUpLeft)
        .value("VideoThumbPositionDownLeft", VideoThumbPosition::VideoThumbPositionDownLeft)
        .export_values();

    py::enum_<VideoThumbSize>(m, "VideoThumbSize")
        .value("VideoThumbSizeOff", VideoThumbSize::VideoThumbSizeOff)
        .value("VideoThumbSize1x", VideoThumbSize::VideoThumbSize1x)
        .value("VideoThumbSize2x", VideoThumbSize::VideoThumbSize2x)
        .value("VideoThumbSize3x", VideoThumbSize::VideoThumbSize3x)
        .value("VideoThumbSizeVideoStripe", VideoThumbSize::VideoThumbSizeVideoStripe)
        .export_values();

    py::enum_<PageVideoType>(m, "PageVideoType")
        .value("PageVideoTypeUnknown", PageVideoType::PageVideoTypeUnknown)
        .value("PageVideoTypeGalleryView", PageVideoType::PageVideoTypeGalleryView)
        .value("PageVideoTypeThumbnailView", PageVideoType::PageVideoTypeThumbnailView)
        .value("PageVideoTypeDynamicLayoutView", PageVideoType::PageVideoTypeDynamicLayoutView)
        .export_values();

    py::enum_<VideoOrderType>(m, "VideoOrderType")
        .value("VideoOrderTypeUnknown", VideoOrderType::VideoOrderTypeUnknown)
        .value("VideoOrderTypeDefault", VideoOrderType::VideoOrderTypeDefault)
        .value("VideoOrderTypeAlphabetical", VideoOrderType::VideoOrderTypeAlphabetical)
        .value("VideoOrderTypeReverseAlphabetical", VideoOrderType::VideoOrderTypeReverseAlphabetical)
        .value("VideoOrderTypeSavedOrder", VideoOrderType::VideoOrderTypeSavedOrder)
        .export_values();

    py::enum_<DynamicLayoutType>(m, "DynamicLayoutType")
        .value("DynamicLayoutTypeSpeakersOnUnknown", DynamicLayoutType::DynamicLayoutTypeSpeakersOnUnknown)
        .value("DynamicLayoutTypeSpeakersOnBottom", DynamicLayoutType::DynamicLayoutTypeSpeakersOnBottom)
        .value("DynamicLayoutTypeSpeakersOnMiddle", DynamicLayoutType::DynamicLayoutTypeSpeakersOnMiddle)
        .value("DynamicLayoutTypeSpeakersOnTop", DynamicLayoutType::DynamicLayoutTypeSpeakersOnTop)
        .export_values();

    py::enum_<ConfidenceMonitorLayoutType>(m, "ConfidenceMonitorLayoutType")
        .value("ConfidenceMonitorLayoutTypeUnknown", ConfidenceMonitorLayoutType::ConfidenceMonitorLayoutTypeUnknown)
        .value("ConfidenceMonitorLayoutTypeSelf", ConfidenceMonitorLayoutType::ConfidenceMonitorLayoutTypeSelf)
        .value("ConfidenceMonitorLayoutTypeActive", ConfidenceMonitorLayoutType::ConfidenceMonitorLayoutTypeActive)
        .value("ConfidenceMonitorLayoutTypeShareContent", ConfidenceMonitorLayoutType::ConfidenceMonitorLayoutTypeShareContent)
        .export_values();

    py::enum_<AttendeeViewLayoutType>(m, "AttendeeViewLayoutType")
        .value("AttendeeViewLayoutTypeNone", AttendeeViewLayoutType::AttendeeViewLayoutTypeNone)
        .value("AttendeeViewLayoutTypeStandard", AttendeeViewLayoutType::AttendeeViewLayoutTypeStandard)
        .value("AttendeeViewLayoutTypeSpeaker", AttendeeViewLayoutType::AttendeeViewLayoutTypeSpeaker)
        .value("AttendeeViewLayoutTypeGallery", AttendeeViewLayoutType::AttendeeViewLayoutTypeGallery)
        .value("AttendeeViewLayoutTypeFollow", AttendeeViewLayoutType::AttendeeViewLayoutTypeFollow)
        .value("AttendeeViewLayoutTypeShareContentOnly", AttendeeViewLayoutType::AttendeeViewLayoutTypeShareContentOnly)
        .export_values();

    py::enum_<ThumbnailsPositionType>(m, "ThumbnailsPositionType")
        .value("ThumbnailsPositionTypeNone", ThumbnailsPositionType::ThumbnailsPositionTypeNone)
        .value("ThumbnailsPositionTypeBottom", ThumbnailsPositionType::ThumbnailsPositionTypeBottom)
        .value("ThumbnailsPositionTypeTop", ThumbnailsPositionType::ThumbnailsPositionTypeTop)
        .value("ThumbnailsPositionTypeUnknown", ThumbnailsPositionType::ThumbnailsPositionTypeUnknown)
        .export_values();

    // ===== Meeting View Layout Helper Structs =====
    py::class_<VideoPageStatus>(m, "VideoPageStatus")
        .def(py::init<>())
        .def_readwrite("isInFirstPage", &VideoPageStatus::isInFirstPage)
        .def_readwrite("isInLastPage", &VideoPageStatus::isInLastPage)
        .def_readwrite("pageVideoType", &VideoPageStatus::pageVideoType)
        .def_readwrite("videoCountInCurrentPage", &VideoPageStatus::videoCountInCurrentPage);

    py::class_<VideoThumbInfo>(m, "VideoThumbInfo")
        .def(py::init<>())
        .def_readwrite("isSupported", &VideoThumbInfo::isSupported)
        .def_readwrite("position", &VideoThumbInfo::position)
        .def_readwrite("size", &VideoThumbInfo::size)
        .def_readwrite("videoPageStatus", &VideoThumbInfo::videoPageStatus)
        .def_readwrite("isThumbnailOnTop", &VideoThumbInfo::isThumbnailOnTop);

    py::class_<VideoLayoutStatus>(m, "VideoLayoutStatus")
        .def(py::init<>())
        .def_readwrite("canSwitchSpeakerView", &VideoLayoutStatus::canSwitchSpeakerView)
        .def_readwrite("canSwitchThumbnailView", &VideoLayoutStatus::canSwitchThumbnailView)
        .def_readwrite("canSwitchGalleryView", &VideoLayoutStatus::canSwitchGalleryView)
        .def_readwrite("canSwitchContentOnly", &VideoLayoutStatus::canSwitchContentOnly)
        .def_readwrite("canSwitchDynamicLayout", &VideoLayoutStatus::canSwitchDynamicLayout)
        .def_readwrite("isInThumbnail", &VideoLayoutStatus::isInThumbnail)
        .def_readwrite("isInGalleryView", &VideoLayoutStatus::isInGalleryView)
        .def_readwrite("isInContentOnly", &VideoLayoutStatus::isInContentOnly)
        .def_readwrite("isInImmersive", &VideoLayoutStatus::isInImmersive)
        .def_readwrite("isInDynamicLayout", &VideoLayoutStatus::isInDynamicLayout)
        .def_readwrite("canAdjustFloatingVideo", &VideoLayoutStatus::canAdjustFloatingVideo)
        .def_readwrite("canSwitchFloatingShareContent", &VideoLayoutStatus::canSwitchFloatingShareContent)
        .def_readwrite("isInFloatingShareContent", &VideoLayoutStatus::isInFloatingShareContent);

    py::class_<WallViewStyleStatus>(m, "WallViewStyleStatus")
        .def(py::init<>())
        .def_readwrite("videoLayoutStatus", &WallViewStyleStatus::videoLayoutStatus)
        .def_readwrite("videoPageStatus", &WallViewStyleStatus::videoPageStatus)
        .def_readwrite("videoThumbInfo", &WallViewStyleStatus::videoThumbInfo);

    py::class_<VideoOrderInfo>(m, "VideoOrderInfo")
        .def(py::init<>())
        .def_readwrite("type", &VideoOrderInfo::type)
        .def_readwrite("hasSavedOrder", &VideoOrderInfo::hasSavedOrder)
        .def_readwrite("isFollowHostOrder", &VideoOrderInfo::isFollowHostOrder)
        .def_readwrite("isSavedOrderEnabled", &VideoOrderInfo::isSavedOrderEnabled);

    py::class_<ConfidenceMonitorInfo>(m, "ConfidenceMonitorInfo")
        .def(py::init<>())
        .def_readwrite("layout", &ConfidenceMonitorInfo::layout)
        .def_readwrite("isSharedContentAvailable", &ConfidenceMonitorInfo::isSharedContentAvailable);

    py::class_<ScreenLayoutCtrlInfo>(m, "ScreenLayoutCtrlInfo")
        .def(py::init<>())
        .def_readwrite("layout", &ScreenLayoutCtrlInfo::layout)
        .def_readwrite("enable", &ScreenLayoutCtrlInfo::enable)
        .def_readwrite("visible", &ScreenLayoutCtrlInfo::visible);

    py::class_<ScreenLayoutInfo>(m, "ScreenLayoutInfo")
        .def(py::init<>())
        .def_readwrite("screen", &ScreenLayoutInfo::screen)
        .def_readwrite("layout", &ScreenLayoutInfo::layout)
        .def_readwrite("layoutCtrlInfos", &ScreenLayoutInfo::layoutCtrlInfos);

    py::class_<ScreenLayoutStatus>(m, "ScreenLayoutStatus")
        .def(py::init<>())
        .def_readwrite("canShowContentOnly", &ScreenLayoutStatus::canShowContentOnly)
        .def_readwrite("isInContentOnly", &ScreenLayoutStatus::isInContentOnly)
        .def_readwrite("canAdjustFloatingVideo", &ScreenLayoutStatus::canAdjustFloatingVideo)
        .def_readwrite("canSwitchFloatingShareContent", &ScreenLayoutStatus::canSwitchFloatingShareContent)
        .def_readwrite("isInFloatingShareContent", &ScreenLayoutStatus::isInFloatingShareContent)
        .def_readwrite("canAdjustMyAutoGeneratedVideoStreamsVisibility", &ScreenLayoutStatus::canAdjustMyAutoGeneratedVideoStreamsVisibility)
        .def_readwrite("isShowMyAutoGeneratedVideoStreams", &ScreenLayoutStatus::isShowMyAutoGeneratedVideoStreams)
        .def_readwrite("layoutInfos", &ScreenLayoutStatus::layoutInfos);

    // ===== NDI Helper Enums =====
    py::enum_<NDIResolution>(m, "NDIResolution")
        .value("NDIResolutionUnknown", NDIResolution::NDIResolutionUnknown)
        .value("NDIResolution360p", NDIResolution::NDIResolution360p)
        .value("NDIResolution720p", NDIResolution::NDIResolution720p)
        .value("NDIResolution1080p", NDIResolution::NDIResolution1080p)
        .export_values();

    py::enum_<NDIFrameRate>(m, "NDIFrameRate")
        .value("NDIFrameRateUnknown", NDIFrameRate::NDIFrameRateUnknown)
        .value("NDIFrameRate25fps", NDIFrameRate::NDIFrameRate25fps)
        .value("NDIFrameRate29_97fps", NDIFrameRate::NDIFrameRate29_97fps)
        .value("NDIFrameRate30fps", NDIFrameRate::NDIFrameRate30fps)
        .value("NDIFrameRate50fps", NDIFrameRate::NDIFrameRate50fps)
        .value("NDIFrameRate59_94fps", NDIFrameRate::NDIFrameRate59_94fps)
        .value("NDIFrameRate60fps", NDIFrameRate::NDIFrameRate60fps)
        .export_values();

    py::enum_<NDISourceType>(m, "NDISourceType")
        .value("NDISourceTypeNone", NDISourceType::NDISourceTypeNone)
        .value("NDISourceTypeActiveSpeaker", NDISourceType::NDISourceTypeActiveSpeaker)
        .value("NDISourceTypeUser", NDISourceType::NDISourceTypeUser)
        .value("NDISourceTypeShare", NDISourceType::NDISourceTypeShare)
        .value("NDISourceTypePinGroup", NDISourceType::NDISourceTypePinGroup)
        .value("NDISourceTypeSpotlightGroup", NDISourceType::NDISourceTypeSpotlightGroup)
        .value("NDISourceTypeGallery", NDISourceType::NDISourceTypeGallery)
        .export_values();

    // ===== Participant Helper Enums =====
    py::enum_<ZRWUserChangeType>(m, "ZRWUserChangeType")
        .value("ZRW_JOIN", ZRWUserChangeType::ZRW_JOIN)
        .value("ZRW_LEAVE", ZRWUserChangeType::ZRW_LEAVE)
        .export_values();

    py::enum_<ClaimHostResult>(m, "ClaimHostResult")
        .value("ClaimHostResultSuccess", ClaimHostResult::ClaimHostResultSuccess)
        .value("ClaimHostResultInvalidHostKey", ClaimHostResult::ClaimHostResultInvalidHostKey)
        .value("ClaimHostResultUnknownError", ClaimHostResult::ClaimHostResultUnknownError)
        .export_values();

    py::enum_<ReportIssueType>(m, "ReportIssueType")
        .value("ISSUE_TYPE_OFFENSIVE_ILLEGAL_ABUSIVE", ReportIssueType::ISSUE_TYPE_OFFENSIVE_ILLEGAL_ABUSIVE)
        .value("ISSUE_TYPE_SUICIDE_SELF_HARM", ReportIssueType::ISSUE_TYPE_SUICIDE_SELF_HARM)
        .value("ISSUE_TYPE_PRIVATE_INFORMATION", ReportIssueType::ISSUE_TYPE_PRIVATE_INFORMATION)
        .value("ISSUE_TYPE_SPAM", ReportIssueType::ISSUE_TYPE_SPAM)
        .value("ISSUE_TYPE_COPYRIGHT_TRADEMARK_INFRINGEMENT", ReportIssueType::ISSUE_TYPE_COPYRIGHT_TRADEMARK_INFRINGEMENT)
        .value("ISSUE_TYPE_IMPERSONATION", ReportIssueType::ISSUE_TYPE_IMPERSONATION)
        .value("ISSUE_TYPE_ILL_TELL_YOU_LATER", ReportIssueType::ISSUE_TYPE_ILL_TELL_YOU_LATER)
        .export_values();

    py::enum_<ConfSessionType>(m, "ConfSessionType")
        .value("CurrentSession", ConfSessionType::CurrentSession)
        .value("MasterSession", ConfSessionType::MasterSession)
        .export_values();

    py::enum_<AudioType>(m, "AudioType", py::arithmetic())
        .value("AudioTypeNone", AudioType::AudioTypeNone)
        .value("AudioTypeVoIP", AudioType::AudioTypeVoIP)
        .value("AudioTypePhone", AudioType::AudioTypePhone)
        .export_values();

    // ===== Phone Call Service Enums =====
    py::enum_<SIPCallStatus>(m, "SIPCallStatus")
        .value("SIPCallStatusInit", SIPCallStatus::SIPCallStatusInit)
        .value("SIPCallStatusCallOutFailed", SIPCallStatus::SIPCallStatusCallOutFailed)
        .value("SIPCallStatusIncoming", SIPCallStatus::SIPCallStatusIncoming)
        .value("SIPCallStatusRinging", SIPCallStatus::SIPCallStatusRinging)
        .value("SIPCallStatusNotFound", SIPCallStatus::SIPCallStatusNotFound)
        .value("SIPCallStatusBusy", SIPCallStatus::SIPCallStatusBusy)
        .value("SIPCallStatusDeclined", SIPCallStatus::SIPCallStatusDeclined)
        .value("SIPCallStatusNotAvailable", SIPCallStatus::SIPCallStatusNotAvailable)
        .value("SIPCallStatusTimeout", SIPCallStatus::SIPCallStatusTimeout)
        .value("SIPCallStatusAccepted", SIPCallStatus::SIPCallStatusAccepted)
        .value("SIPCallStatusHold", SIPCallStatus::SIPCallStatusHold)
        .value("SIPCallStatusInCall", SIPCallStatus::SIPCallStatusInCall)
        .value("SIPCallStatusTerminated", SIPCallStatus::SIPCallStatusTerminated)
        .value("SIPCallStatusRemoteHold", SIPCallStatus::SIPCallStatusRemoteHold)
        .value("SIPCallStatusBothHold", SIPCallStatus::SIPCallStatusBothHold)
        .value("SIPCallStatusSessionInProgress", SIPCallStatus::SIPCallStatusSessionInProgress)
        .value("SIPCallStatusStayOnPhone", SIPCallStatus::SIPCallStatusStayOnPhone)
        .export_values();

    py::enum_<SIPCallConferenceRole>(m, "SIPCallConferenceRole")
        .value("SIPCallConferenceRoleUnknown", SIPCallConferenceRole::SIPCallConferenceRoleUnknown)
        .value("SIPCallConferenceRoleHost", SIPCallConferenceRole::SIPCallConferenceRoleHost)
        .value("SIPCallConferenceRoleParticipant", SIPCallConferenceRole::SIPCallConferenceRoleParticipant)
        .export_values();

    py::enum_<SIPCallSpamType>(m, "SIPCallSpamType")
        .value("SIPCallSpamTypeNone", SIPCallSpamType::SIPCallSpamTypeNone)
        .value("SIPCallSpamTypeNotSpam", SIPCallSpamType::SIPCallSpamTypeNotSpam)
        .value("SIPCallSpamTypeSpam", SIPCallSpamType::SIPCallSpamTypeSpam)
        .value("SIPCallSpamTypeMaybeSpam", SIPCallSpamType::SIPCallSpamTypeMaybeSpam)
        .export_values();

    py::enum_<SIPCallAttestLevel>(m, "SIPCallAttestLevel")
        .value("SIPCallAttestLevelUndefined", SIPCallAttestLevel::SIPCallAttestLevelUndefined)
        .value("SIPCallAttestLevelA", SIPCallAttestLevel::SIPCallAttestLevelA)
        .value("SIPCallAttestLevelB", SIPCallAttestLevel::SIPCallAttestLevelB)
        .value("SIPCallAttestLevelC", SIPCallAttestLevel::SIPCallAttestLevelC)
        .export_values();

    py::enum_<SIPCallThirdPartyType>(m, "SIPCallThirdPartyType")
        .value("SIPCallThirdPartyTypeDefault", SIPCallThirdPartyType::SIPCallThirdPartyTypeDefault)
        .value("SIPCallThirdPartyTypeTransfer", SIPCallThirdPartyType::SIPCallThirdPartyTypeTransfer)
        .export_values();

    py::enum_<EmergencyAddressType>(m, "EmergencyAddressType")
        .value("EmergencyAddressTypeUnknown", EmergencyAddressType::EmergencyAddressTypeUnknown)
        .value("EmergencyAddressTypeStatic", EmergencyAddressType::EmergencyAddressTypeStatic)
        .value("EmergencyAddressTypeDetect", EmergencyAddressType::EmergencyAddressTypeDetect)
        .export_values();

    py::enum_<SIPCallTransferInfoType>(m, "SIPCallTransferInfoType")
        .value("SIPCallTransferInfoTypeUnknown", SIPCallTransferInfoType::SIPCallTransferInfoTypeUnknown)
        .value("SIPCallTransferInfoTypeBlind", SIPCallTransferInfoType::SIPCallTransferInfoTypeBlind)
        .value("SIPCallTransferInfoTypeWarm", SIPCallTransferInfoType::SIPCallTransferInfoTypeWarm)
        .value("SIPCallTransferInfoTypeWarmComplete", SIPCallTransferInfoType::SIPCallTransferInfoTypeWarmComplete)
        .value("SIPCallTransferInfoTypeVoicemail", SIPCallTransferInfoType::SIPCallTransferInfoTypeVoicemail)
        .export_values();

    py::enum_<SIPServiceStatus>(m, "SIPServiceStatus")
        .value("SIPServiceStatusIdle", SIPServiceStatus::SIPServiceStatusIdle)
        .value("SIPServiceStatusRegistering", SIPServiceStatus::SIPServiceStatusRegistering)
        .value("SIPServiceStatusRegFailed", SIPServiceStatus::SIPServiceStatusRegFailed)
        .value("SIPServiceStatusRegistered", SIPServiceStatus::SIPServiceStatusRegistered)
        .value("SIPServiceStatusRinging", SIPServiceStatus::SIPServiceStatusRinging)
        .value("SIPServiceStatusCallingOut", SIPServiceStatus::SIPServiceStatusCallingOut)
        .value("SIPServiceStatusInCall", SIPServiceStatus::SIPServiceStatusInCall)
        .export_values();

    py::enum_<SIPCallTerminateReason>(m, "SIPCallTerminateReason")
        .value("SIPCallTerminateReasonUnknown", SIPCallTerminateReason::SIPCallTerminateReasonUnknown)
        .value("SIPCallTerminateReasonByLocal", SIPCallTerminateReason::SIPCallTerminateReasonByLocal)
        .value("SIPCallTerminateReasonByRemote", SIPCallTerminateReason::SIPCallTerminateReasonByRemote)
        .value("SIPCallTerminateReasonByNetworkBreak", SIPCallTerminateReason::SIPCallTerminateReasonByNetworkBreak)
        .value("SIPCallTerminateReasonByInitAudioDeviceFailed", SIPCallTerminateReason::SIPCallTerminateReasonByInitAudioDeviceFailed)
        .value("SIPCallTerminateReasonBySipServiceStopped", SIPCallTerminateReason::SIPCallTerminateReasonBySipServiceStopped)
        .export_values();

    // ===== Phone Call Service Structs =====
    py::class_<SIPCallMemberInfo>(m, "SIPCallMemberInfo")
        .def(py::init<>())
        .def_readwrite("name", &SIPCallMemberInfo::name)
        .def_readwrite("number", &SIPCallMemberInfo::number)
        .def_readwrite("attestLevel", &SIPCallMemberInfo::attestLevel);

    py::class_<SIPCallConferenceInfo>(m, "SIPCallConferenceInfo")
        .def(py::init<>())
        .def_readwrite("role", &SIPCallConferenceInfo::role)
        .def_readwrite("hostCallID", &SIPCallConferenceInfo::hostCallID);

    py::class_<SIPCallRedirectInfo>(m, "SIPCallRedirectInfo")
        .def(py::init<>())
        .def_readwrite("endType", &SIPCallRedirectInfo::endType)
        .def_readwrite("endName", &SIPCallRedirectInfo::endName)
        .def_readwrite("endNumber", &SIPCallRedirectInfo::endNumber);

    py::class_<EmergencyCallAddress>(m, "EmergencyCallAddress")
        .def(py::init<>())
        .def_readwrite("addressType", &EmergencyCallAddress::addressType)
        .def_readwrite("address", &EmergencyCallAddress::address);

    py::class_<EmergencyCall>(m, "EmergencyCall")
        .def(py::init<>())
        .def_readwrite("emergencyCallAddress", &EmergencyCall::emergencyCallAddress)
        .def_readwrite("locationPermissionEnabled", &EmergencyCall::locationPermissionEnabled)
        .def_readwrite("customEmergencyNumbers", &EmergencyCall::customEmergencyNumbers);

    py::class_<SIPCallInfo>(m, "SIPCallInfo")
        .def(py::init<>())
        .def_readwrite("status", &SIPCallInfo::status)
        .def_readwrite("callID", &SIPCallInfo::callID)
        .def_readwrite("peerDisplayName", &SIPCallInfo::peerDisplayName)
        .def_readwrite("peerNumber", &SIPCallInfo::peerNumber)
        .def_readwrite("peerURI", &SIPCallInfo::peerURI)
        .def_readwrite("isIncomingCall", &SIPCallInfo::isIncomingCall)
        .def_readwrite("selfInfo", &SIPCallInfo::selfInfo)
        .def_readwrite("conferenceInfo", &SIPCallInfo::conferenceInfo)
        .def_readwrite("remoteMembers", &SIPCallInfo::remoteMembers)
        .def_readwrite("elapsedCallTime", &SIPCallInfo::elapsedCallTime)
        .def_readwrite("relatedCallID", &SIPCallInfo::relatedCallID)
        .def_readwrite("blindDisplayName", &SIPCallInfo::blindDisplayName)
        .def_readwrite("originalPeerURI", &SIPCallInfo::originalPeerURI)
        .def_readwrite("peerSpamType", &SIPCallInfo::peerSpamType)
        .def_readwrite("peerAttestLevel", &SIPCallInfo::peerAttestLevel)
        .def_readwrite("redirectInfo", &SIPCallInfo::redirectInfo)
        .def_readwrite("isEmergencyCall", &SIPCallInfo::isEmergencyCall)
        .def_readwrite("emergencyCallAddress", &SIPCallInfo::emergencyCallAddress);

    py::class_<SIPCallTransferInfo>(m, "SIPCallTransferInfo")
        .def(py::init<>())
        .def_readwrite("type", &SIPCallTransferInfo::type)
        .def_readwrite("peerURI", &SIPCallTransferInfo::peerURI);

    py::class_<SIPCallerID>(m, "SIPCallerID")
        .def(py::init<>())
        .def_readwrite("name", &SIPCallerID::name)
        .def_readwrite("number", &SIPCallerID::number)
        .def_readwrite("extensionID", &SIPCallerID::extensionID);

    py::class_<CloudPBXServiceInfo>(m, "CloudPBXServiceInfo")
        .def(py::init<>())
        .def_readwrite("extension", &CloudPBXServiceInfo::extension)
        .def_readwrite("companyNumber", &CloudPBXServiceInfo::companyNumber)
        .def_readwrite("directNumbers", &CloudPBXServiceInfo::directNumbers)
        .def_readwrite("countryCode", &CloudPBXServiceInfo::countryCode)
        .def_readwrite("countryName", &CloudPBXServiceInfo::countryName)
        .def_readwrite("areaCode", &CloudPBXServiceInfo::areaCode)
        .def_readwrite("callerIDs", &CloudPBXServiceInfo::callerIDs)
        .def_readwrite("formattedCompanyNumber", &CloudPBXServiceInfo::formattedCompanyNumber)
        .def_readwrite("formattedDirectNumbers", &CloudPBXServiceInfo::formattedDirectNumbers)
        .def_readwrite("isEnabledMakeOutBoundPSTNCall", &CloudPBXServiceInfo::isEnabledMakeOutBoundPSTNCall)
        .def_readwrite("isEnabledHaveADID", &CloudPBXServiceInfo::isEnabledHaveADID)
        .def_readwrite("isEnable911Call", &CloudPBXServiceInfo::isEnable911Call)
        .def_readwrite("emergencyCall", &CloudPBXServiceInfo::emergencyCall);

    py::class_<SIPService>(m, "SIPService")
        .def(py::init<>())
        .def_readwrite("status", &SIPService::status)
        .def_readwrite("userName", &SIPService::userName)
        .def_readwrite("displayName", &SIPService::displayName)
        .def_readwrite("responseCode", &SIPService::responseCode)
        .def_readwrite("responseDescription", &SIPService::responseDescription)
        .def_readwrite("isZoomPhoneAvailable", &SIPService::isZoomPhoneAvailable)
        .def_readwrite("cloudPBXServiceInfo", &SIPService::cloudPBXServiceInfo);

    // ===== NDI Helper Structs =====
    py::class_<NDIUsageSettings>(m, "NDIUsageSettings")
        .def(py::init<>())
        .def_readwrite("isPersistentNDIEnabled", &NDIUsageSettings::isPersistentNDIEnabled)
        .def_readwrite("isPersistentNDILocked", &NDIUsageSettings::isPersistentNDILocked)
        .def_readwrite("isNDIEnabledForPreMeeting", &NDIUsageSettings::isNDIEnabledForPreMeeting)
        .def_readwrite("resolution", &NDIUsageSettings::resolution)
        .def_readwrite("frameRate", &NDIUsageSettings::frameRate)
        .def_readwrite("supportedResolutionList", &NDIUsageSettings::supportedResolutionList)
        .def_readwrite("supportedFrameRateList", &NDIUsageSettings::supportedFrameRateList)
        .def_readwrite("outputCount", &NDIUsageSettings::outputCount)
        .def_readwrite("maxOutputCount", &NDIUsageSettings::maxOutputCount);

    py::class_<NDISource>(m, "NDISource")
        .def(py::init<>())
        .def_readwrite("type", &NDISource::type)
        .def_readwrite("sourceID", &NDISource::sourceID)
        .def_readwrite("fromType", &NDISource::fromType)
        .def_readwrite("sourceTypeIndex", &NDISource::sourceTypeIndex)
        .def_readwrite("shareSourceID", &NDISource::shareSourceID)
        .def_readwrite("gridSize", &NDISource::gridSize);

    py::class_<NDIPinnedSource>(m, "NDIPinnedSource")
        .def(py::init<>())
        .def_readwrite("source", &NDIPinnedSource::source)
        .def_readwrite("index", &NDIPinnedSource::index);

    py::class_<NDIUsageInfo>(m, "NDIUsageInfo")
        .def(py::init<>())
        .def_readwrite("ndiEnabled", &NDIUsageInfo::ndiEnabled)
        .def_readwrite("supportedCount", &NDIUsageInfo::supportedCount)
        .def_readwrite("sources", &NDIUsageInfo::sources)
        .def_readwrite("galleryPageCount", &NDIUsageInfo::galleryPageCount);

    // ===== Meeting List Helper Enums =====
    py::enum_<ListMeetingResult>(m, "ListMeetingResult")
        .value("LIST_MEETING_SUCCESS", ListMeetingResult::LIST_MEETING_SUCCESS)
        .value("LIST_MEETING_ERROR_UNKNOWN", ListMeetingResult::LIST_MEETING_ERROR_UNKNOWN)
        .value("LIST_MEETING_ERROR_GOOGLE_CALENDAR_INVALID_CREDENTIAL", ListMeetingResult::LIST_MEETING_ERROR_GOOGLE_CALENDAR_INVALID_CREDENTIAL)
        .value("LIST_MEETING_ERROR_GOOGLE_CALENDAR_DAILY_LIMIT_EXCEEDED", ListMeetingResult::LIST_MEETING_ERROR_GOOGLE_CALENDAR_DAILY_LIMIT_EXCEEDED)
        .value("LIST_MEETING_ERROR_EWS_INVALID_CREDENTIAL", ListMeetingResult::LIST_MEETING_ERROR_EWS_INVALID_CREDENTIAL)
        .value("LIST_MEETING_ERROR_EWS_AUTH_METHOD_UNSUPPORTED", ListMeetingResult::LIST_MEETING_ERROR_EWS_AUTH_METHOD_UNSUPPORTED)
        .value("LIST_MEETING_ERROR_EWS_FOLDER_NOT_FOUND", ListMeetingResult::LIST_MEETING_ERROR_EWS_FOLDER_NOT_FOUND)
        .value("LIST_MEETING_ERROR_EWS_IMPERSONATE_USER_DENIED", ListMeetingResult::LIST_MEETING_ERROR_EWS_IMPERSONATE_USER_DENIED)
        .value("LIST_MEETING_ERROR_EWS_NON_EXISTENT_MAILBOX", ListMeetingResult::LIST_MEETING_ERROR_EWS_NON_EXISTENT_MAILBOX)
        .value("LIST_MEETING_ERROR_CALENDAR_SERVICE_DISCONNECTED", ListMeetingResult::LIST_MEETING_ERROR_CALENDAR_SERVICE_DISCONNECTED)
        .export_values();

    py::enum_<ScheduleCalendarEventResult>(m, "ScheduleCalendarEventResult")
        .value("ScheduleCalendarEventResultSuccess", ScheduleCalendarEventResult::ScheduleCalendarEventResultSuccess)
        .value("ScheduleCalendarEventResultFailUnknown", ScheduleCalendarEventResult::ScheduleCalendarEventResultFailUnknown)
        .value("ScheduleCalendarEventResultFailWeakPWD", ScheduleCalendarEventResult::ScheduleCalendarEventResultFailWeakPWD)
        .export_values();

    py::enum_<DeleteCalendarEventResult>(m, "DeleteCalendarEventResult")
        .value("DeleteCalendarEventResultSuccess", DeleteCalendarEventResult::DeleteCalendarEventResultSuccess)
        .value("DeleteCalendarEventResultFailByDeleteCalendar", DeleteCalendarEventResult::DeleteCalendarEventResultFailByDeleteCalendar)
        .value("DeleteCalendarEventResultFailByZRInMeeting", DeleteCalendarEventResult::DeleteCalendarEventResultFailByZRInMeeting)
        .value("DeleteCalendarEventResultFailUnknown", DeleteCalendarEventResult::DeleteCalendarEventResultFailUnknown)
        .export_values();

    py::enum_<ZoomMeetingItemType>(m, "ZoomMeetingItemType")
        .value("ZoomMeetingItemTypeDefault", ZoomMeetingItemType::ZoomMeetingItemTypeDefault)
        .value("ZoomMeetingItemTypeZESingleSession", ZoomMeetingItemType::ZoomMeetingItemTypeZESingleSession)
        .value("ZoomMeetingItemTypeZEMultiSession", ZoomMeetingItemType::ZoomMeetingItemTypeZEMultiSession)
        .value("ZoomMeetingItemTypeZESubSession", ZoomMeetingItemType::ZoomMeetingItemTypeZESubSession)
        .export_values();

    py::enum_<ThirdPartyMeetingServiceProvider>(m, "ThirdPartyMeetingServiceProvider")
        .value("ThirdPartyMeetingServiceProviderInvalid", ThirdPartyMeetingServiceProvider::ThirdPartyMeetingServiceProviderInvalid)
        .value("ThirdPartyMeetingServiceProviderWebex", ThirdPartyMeetingServiceProvider::ThirdPartyMeetingServiceProviderWebex)
        .value("ThirdPartyMeetingServiceProviderSkype", ThirdPartyMeetingServiceProvider::ThirdPartyMeetingServiceProviderSkype)
        .value("ThirdPartyMeetingServiceProviderGoToMeeting", ThirdPartyMeetingServiceProvider::ThirdPartyMeetingServiceProviderGoToMeeting)
        .value("ThirdPartyMeetingServiceProviderTeams", ThirdPartyMeetingServiceProvider::ThirdPartyMeetingServiceProviderTeams)
        .export_values();

    // ===== Meeting List Helper Structs =====
    py::class_<DialNumber>(m, "DialNumber")
        .def(py::init<>())
        .def_readwrite("countryCode", &DialNumber::countryCode)
        .def_readwrite("phoneNumber", &DialNumber::phoneNumber);

    py::class_<ThirdPartyMeeting>(m, "ThirdPartyMeeting")
        .def(py::init<>())
        .def_readwrite("serviceProvider", &ThirdPartyMeeting::serviceProvider)
        .def_readwrite("meetingNumber", &ThirdPartyMeeting::meetingNumber)
        .def_readwrite("sipAddress", &ThirdPartyMeeting::sipAddress)
        .def_readwrite("h323Address", &ThirdPartyMeeting::h323Address)
        .def_readwrite("joinMeetingURL", &ThirdPartyMeeting::joinMeetingURL)
        .def_readwrite("dialNumbers", &ThirdPartyMeeting::dialNumbers);

    py::class_<EventScheduledByUserInfo>(m, "EventScheduledByUserInfo")
        .def(py::init<>())
        .def_readwrite("userID", &EventScheduledByUserInfo::userID)
        .def_readwrite("userName", &EventScheduledByUserInfo::userName)
        .def_readwrite("userAvatarURL", &EventScheduledByUserInfo::userAvatarURL);

    py::class_<MeetingItem>(m, "MeetingItem")
        .def(py::init<>())
        .def_readwrite("zoomMeetingItemType", &MeetingItem::zoomMeetingItemType)
        .def_readwrite("meetingNumber", &MeetingItem::meetingNumber)
        .def_readwrite("meetingName", &MeetingItem::meetingName)
        .def_readwrite("hostName", &MeetingItem::hostName)
        .def_readwrite("startTime", &MeetingItem::startTime)
        .def_readwrite("endTime", &MeetingItem::endTime)
        .def_readwrite("scheduledFrom", &MeetingItem::scheduledFrom)
        .def_readwrite("isPrivate", &MeetingItem::isPrivate)
        .def_readwrite("isAllDayEvent", &MeetingItem::isAllDayEvent)
        .def_readwrite("isCheckedIn", &MeetingItem::isCheckedIn)
        .def_readwrite("meetingDomain", &MeetingItem::meetingDomain)
        .def_readwrite("isInstantMeeting", &MeetingItem::isInstantMeeting)
        .def_readwrite("thirdPartyMeetingInfo", &MeetingItem::thirdPartyMeetingInfo)
        .def_readwrite("scheduledByInfo", &MeetingItem::scheduledByInfo);

    py::class_<ScheduleCalendarEventParam>(m, "ScheduleCalendarEventParam")
        .def(py::init<>())
        .def_readwrite("topic", &ScheduleCalendarEventParam::topic)
        .def_readwrite("password", &ScheduleCalendarEventParam::password)
        .def_readwrite("startTime", &ScheduleCalendarEventParam::startTime)
        .def_readwrite("endTime", &ScheduleCalendarEventParam::endTime)
        .def_readwrite("attendees", &ScheduleCalendarEventParam::attendees)
        .def_readwrite("enableWaitingRoom", &ScheduleCalendarEventParam::enableWaitingRoom);

    // ===== Meeting List Helper =====
    py::class_<IMeetingListHelper>(m, "IMeetingListHelper")
        .def("RegisterSink", [](IMeetingListHelper* self, py::object py_sink) {
            static std::map<IMeetingListHelper*, std::shared_ptr<MeetingListHelperSinkTrampoline>> sinks;
            auto trampoline = std::make_shared<MeetingListHelperSinkTrampoline>(py_sink);
            sinks[self] = trampoline;
            return self->RegisterSink(trampoline.get());
        })
        .def("DeregisterSink", [](IMeetingListHelper* self) {
            static std::map<IMeetingListHelper*, std::shared_ptr<MeetingListHelperSinkTrampoline>> sinks;
            auto it = sinks.find(self);
            if (it != sinks.end()) {
                auto result = self->DeregisterSink(it->second.get());
                sinks.erase(it);
                return result;
            }
            return ZRCSDKERR_INTERNAL_ERROR;
        })
        .def("ListMeeting", &IMeetingListHelper::ListMeeting)
        .def("ScheduleCalendarEvent", &IMeetingListHelper::ScheduleCalendarEvent)
        .def("DeleteCalendarEvent", &IMeetingListHelper::DeleteCalendarEvent)
        .def("CheckInCalendarEvent", &IMeetingListHelper::CheckInCalendarEvent)
        .def("CheckOutCalendarEvent", &IMeetingListHelper::CheckOutCalendarEvent)
        .def("ShowUpcomingMeetingAlert", &IMeetingListHelper::ShowUpcomingMeetingAlert)
        .def("CloseUpcomingMeetingAlert", &IMeetingListHelper::CloseUpcomingMeetingAlert)
        .def("CloseAutoReleaseMeetingAlert", &IMeetingListHelper::CloseAutoReleaseMeetingAlert);

    // ===== Meeting Share Helper =====
    py::class_<IMeetingShareHelper>(m, "IMeetingShareHelper")
        .def("LaunchSharingMeeting", &IMeetingShareHelper::LaunchSharingMeeting)
        .def("SwitchFromLocalPresentationToNormalMeeting", &IMeetingShareHelper::SwitchFromLocalPresentationToNormalMeeting)
        .def("ShowSharingInstruction", &IMeetingShareHelper::ShowSharingInstruction)
        .def("ShareBlackMagic", &IMeetingShareHelper::ShareBlackMagic)
        .def("ShareCamera", &IMeetingShareHelper::ShareCamera)
        .def("ShareToBreakoutRooms", &IMeetingShareHelper::ShareToBreakoutRooms)
        .def("StopShareToBreakoutRooms", &IMeetingShareHelper::StopShareToBreakoutRooms)
        .def("StopSharing", &IMeetingShareHelper::StopSharing)
        .def("StopZRWSharing", &IMeetingShareHelper::StopZRWSharing)
        .def("EnableMultiShare", &IMeetingShareHelper::EnableMultiShare)
        .def("ShowPinShareInstruction", &IMeetingShareHelper::ShowPinShareInstruction)
        .def("PinShareOnZRScreen", &IMeetingShareHelper::PinShareOnZRScreen)
        .def("PinShareOnZRWScreen", &IMeetingShareHelper::PinShareOnZRWScreen)
        .def("PinIncomingMeetingShare", &IMeetingShareHelper::PinIncomingMeetingShare)
        .def("ControlSlide", &IMeetingShareHelper::ControlSlide)
        .def("MuteShareAudio", &IMeetingShareHelper::MuteShareAudio)
        .def("EnableHDMI60FPSShare", &IMeetingShareHelper::EnableHDMI60FPSShare)
        .def("GetLocalHDMIShareAudioPlaybackStatus", [](IMeetingShareHelper* self) {
            bool isSupport, isEnabled;
            ZRCSDKError result = self->GetLocalHDMIShareAudioPlaybackStatus(isSupport, isEnabled);
            return py::make_tuple(result, isSupport, isEnabled);
        })
        .def("EnableLocalHDMIShareAudioPlayback", &IMeetingShareHelper::EnableLocalHDMIShareAudioPlayback)
        .def("SetMeetingShareSetting", &IMeetingShareHelper::SetMeetingShareSetting)
        .def("SetMeetingShareViewPrivilege", &IMeetingShareHelper::SetMeetingShareViewPrivilege)
        .def("OptimizeVideoSharing", &IMeetingShareHelper::OptimizeVideoSharing)
        .def("AllowParticipantsShareDocs", &IMeetingShareHelper::AllowParticipantsShareDocs)
        .def("ChangeDocsSharePrivilege", &IMeetingShareHelper::ChangeDocsSharePrivilege)
        .def("ChangeDocsInitiatePrivilege", &IMeetingShareHelper::ChangeDocsInitiatePrivilege)
        .def("GetDocsShareSettingsInfo", [](IMeetingShareHelper* self) {
            DocsShareSettingsInfo info;
            ZRCSDKError result = self->GetDocsShareSettingsInfo(info);
            return py::make_tuple(result, info);
        })
        .def("EnableAnnotationOverHDMI", &IMeetingShareHelper::EnableAnnotationOverHDMI);

    // ===== Meeting View Layout Helper =====
    py::class_<IMeetingViewLayoutHelper>(m, "IMeetingViewLayoutHelper")
        .def("UpdateVideoLayoutStyle", &IMeetingViewLayoutHelper::UpdateVideoLayoutStyle)
        .def("ControlVideoPosition", &IMeetingViewLayoutHelper::ControlVideoPosition)
        .def("TurnVideoPage", &IMeetingViewLayoutHelper::TurnVideoPage)
        .def("SwitchToFloatingShareForSingleScreen", &IMeetingViewLayoutHelper::SwitchToFloatingShareForSingleScreen)
        .def("IsSupportShowNonVideoParticipants", [](IMeetingViewLayoutHelper* self) {
            bool support;
            ZRCSDKError result = self->IsSupportShowNonVideoParticipants(support);
            return py::make_tuple(result, support);
        })
        .def("ShowNonVideoParticipants", &IMeetingViewLayoutHelper::ShowNonVideoParticipants)
        .def("EnableShowUpTo49PerPageInGallery", &IMeetingViewLayoutHelper::EnableShowUpTo49PerPageInGallery)
        .def("EnableAutoSwitchSpeaker", &IMeetingViewLayoutHelper::EnableAutoSwitchSpeaker)
        .def("SelectVideoOrder", &IMeetingViewLayoutHelper::SelectVideoOrder)
        .def("SetDynamicLayoutOption", &IMeetingViewLayoutHelper::SetDynamicLayoutOption)
        .def("SetConfidenceMonitorLayout", &IMeetingViewLayoutHelper::SetConfidenceMonitorLayout)
        .def("ChangeAttendeeView", &IMeetingViewLayoutHelper::ChangeAttendeeView)
        .def("SelectGalleryGrid", &IMeetingViewLayoutHelper::SelectGalleryGrid)
        .def("ExpandConfSelfVideo", &IMeetingViewLayoutHelper::ExpandConfSelfVideo)
        .def("SetScreenLayout", &IMeetingViewLayoutHelper::SetScreenLayout)
        .def("SetShareContentOnly", &IMeetingViewLayoutHelper::SetShareContentOnly)
        .def("ShowScreenIndex", &IMeetingViewLayoutHelper::ShowScreenIndex)
        .def("GetThumbnailsPosition", [](IMeetingViewLayoutHelper* self) {
            ThumbnailsPositionType type;
            ZRCSDKError result = self->GetThumbnailsPosition(type);
            return py::make_tuple(result, type);
        })
        .def("ChangeThumbnailsPosition", &IMeetingViewLayoutHelper::ChangeThumbnailsPosition)
        .def("ShowMyAutoGeneratedVideoStreams", &IMeetingViewLayoutHelper::ShowMyAutoGeneratedVideoStreams);

    // ===== NDI Helper =====
    py::class_<INDIHelper>(m, "INDIHelper")
        .def("SetNDIResolution", &INDIHelper::SetNDIResolution)
        .def("SetNDIFrameRate", &INDIHelper::SetNDIFrameRate)
        .def("SetNDIEnableInPreMeeting", &INDIHelper::SetNDIEnableInPreMeeting)
        .def("SetNDIOutputCount", &INDIHelper::SetNDIOutputCount)
        .def("GetAvailableNDISources", [](INDIHelper* self) {
            std::vector<NDISource> sources;
            ZRCSDKError result = self->GetAvailableNDISources(sources);
            return py::make_tuple(result, sources);
        })
        .def("GetNDIPinnedSources", [](INDIHelper* self) {
            std::vector<NDIPinnedSource> sources;
            ZRCSDKError result = self->GetNDIPinnedSources(sources);
            return py::make_tuple(result, sources);
        })
        .def("PinNDI", &INDIHelper::PinNDI)
        .def("UnpinNDI", &INDIHelper::UnpinNDI)
        .def("GetNDIDeviceList", [](INDIHelper* self) {
            std::vector<Device> devices;
            ZRCSDKError result = self->GetNDIDeviceList(devices);
            return py::make_tuple(result, devices);
        })
        .def("AddPersistentNDISource", &INDIHelper::AddPersistentNDISource)
        .def("RemovePersistentNDISource", &INDIHelper::RemovePersistentNDISource)
        .def("ListPersistentNDISources", &INDIHelper::ListPersistentNDISources);

    py::class_<MeetingParticipant>(m, "MeetingParticipant")
        .def(py::init<>())
        .def_readwrite("userID", &MeetingParticipant::userID)
        .def_readwrite("parentUserID", &MeetingParticipant::parentUserID)
        .def_readwrite("userGUID", &MeetingParticipant::userGUID)
        .def_readwrite("userName", &MeetingParticipant::userName)
        .def_readwrite("pronouns", &MeetingParticipant::pronouns)
        .def_readwrite("avatarUrl", &MeetingParticipant::avatarUrl)
        .def_readwrite("isMySelf", &MeetingParticipant::isMySelf)
        .def_readwrite("isMyself", &MeetingParticipant::isMySelf)
        .def_readwrite("isHost", &MeetingParticipant::isHost)
        .def_readwrite("isCohost", &MeetingParticipant::isCohost)
        .def_readwrite("isGuest", &MeetingParticipant::isGuest)
        .def_readwrite("isViewOnlyUser", &MeetingParticipant::isViewOnlyUser)
        .def_readwrite("isViewOnlyUserCanTalk", &MeetingParticipant::isViewOnlyUserCanTalk)
        .def_readwrite("canRecord", &MeetingParticipant::canRecord)
        .def_readwrite("isRecording", &MeetingParticipant::isRecording)
        .def_readwrite("recordingDisabled", &MeetingParticipant::recordingDisabled)
        .def_readwrite("isInSilentMode", &MeetingParticipant::isInSilentMode)
        .def_readwrite("isLeavingSilentMode", &MeetingParticipant::isLeavingSilentMode)
        .def_readwrite("audioStatus", &MeetingParticipant::audioStatus)
        .def_readwrite("videoStatus", &MeetingParticipant::videoStatus)
        .def_readwrite("handStatus", &MeetingParticipant::handStatus)
        .def_readwrite("reactionEmoji", &MeetingParticipant::reactionEmoji)
        .def_readwrite("isInterpreter", &MeetingParticipant::isInterpreter)
        .def_readwrite("isRemoteControlAdmin", &MeetingParticipant::isRemoteControlAdmin)
        .def_readwrite("isVirtualAssistant", &MeetingParticipant::isVirtualAssistant)
        .def_readwrite("isCompanionModeUser", &MeetingParticipant::isCompanionModeUser)
        .def_readwrite("isCompanionZRUser", &MeetingParticipant::isCompanionZRUser)
        .def_readwrite("attendeeJid", &MeetingParticipant::attendeeJid);

    // ===== Participant Helper =====
    py::class_<IParticipantHelper>(m, "IParticipantHelper")
        .def("GetParticipantsInMeeting", [](IParticipantHelper* self, ConfSessionType session) {
            std::vector<MeetingParticipant> participants;
            ZRCSDKError result = self->GetParticipantsInMeeting(participants, session);
            return py::make_tuple(result, participants);
        })
        .def("GetVirtualParticipantsInMeeting", [](IParticipantHelper* self, ConfSessionType session) {
            std::vector<MeetingParticipant> participants;
            ZRCSDKError result = self->GetVirtualParticipantsInMeeting(participants, session);
            return py::make_tuple(result, participants);
        })
        .def("GetParticipantsInSilentMode", [](IParticipantHelper* self) {
            std::vector<MeetingParticipant> participants;
            ZRCSDKError result = self->GetParticipantsInSilentMode(participants);
            return py::make_tuple(result, participants);
        })
        .def("GetParticipantsLeftMeeting", [](IParticipantHelper* self) {
            std::vector<MeetingParticipant> participants;
            ZRCSDKError result = self->GetParticipantsLeftMeeting(participants);
            return py::make_tuple(result, participants);
        })
        .def("AssignHost", &IParticipantHelper::AssignHost)
        .def("AssignCohost", &IParticipantHelper::AssignCohost)
        .def("ClaimHost", &IParticipantHelper::ClaimHost)
        .def("EnableAttendeesAnnotateOnShare", &IParticipantHelper::EnableAttendeesAnnotateOnShare)
        .def("RenameUser", &IParticipantHelper::RenameUser)
        .def("AllowAttendeesRenameThemselves", &IParticipantHelper::AllowAttendeesRenameThemselves)
        .def("IsAttendeesRenameThemselvesEnabled", [](IParticipantHelper* self) {
            bool enable;
            ZRCSDKError result = self->IsAttendeesRenameThemselvesEnabled(enable);
            return py::make_tuple(result, enable);
        })
        .def("IsAttendeesRenameThemselvesLocked", [](IParticipantHelper* self) {
            bool locked;
            ZRCSDKError result = self->IsAttendeesRenameThemselvesLocked(locked);
            return py::make_tuple(result, locked);
        })
        .def("IsAttendeesRenameThemselvesAllowed", [](IParticipantHelper* self) {
            bool allow;
            ZRCSDKError result = self->IsAttendeesRenameThemselvesAllowed(allow);
            return py::make_tuple(result, allow);
        })
        .def("AllowWebinarAttendeeRaiseHand", &IParticipantHelper::AllowWebinarAttendeeRaiseHand)
        .def("RaiseHand", &IParticipantHelper::RaiseHand)
        .def("LowerUserHand", &IParticipantHelper::LowerUserHand)
        .def("LowerAllHands", &IParticipantHelper::LowerAllHands)
        .def("LowerAllAttendeesHands", &IParticipantHelper::LowerAllAttendeesHands)
        .def("ExpelUser", &IParticipantHelper::ExpelUser)
        .def("ExpelUsers", &IParticipantHelper::ExpelUsers)
        .def("HideProfilePictures", &IParticipantHelper::HideProfilePictures)
        .def("IsFullRoomViewAvailableForUser", [](IParticipantHelper* self, int32_t userID) {
            bool isAvailable;
            ZRCSDKError result = self->IsFullRoomViewAvailableForUser(isAvailable, userID);
            return py::make_tuple(result, isAvailable);
        })
        .def("HideFullRoomView", &IParticipantHelper::HideFullRoomView)
        .def("DownloadUserAvatar", &IParticipantHelper::DownloadUserAvatar)
        .def("AllowAttendeesShareWhiteboards", &IParticipantHelper::AllowAttendeesShareWhiteboards)
        .def("SuspendParticipantsActivities", &IParticipantHelper::SuspendParticipantsActivities)
        .def("ReportIssue", &IParticipantHelper::ReportIssue)
        .def("SetMySelfAsActiveSpeaker", &IParticipantHelper::SetMySelfAsActiveSpeaker)
        .def("SetMyChildAsActiveSpeaker", &IParticipantHelper::SetMyChildAsActiveSpeaker);

    // ===== Recording Helper Enums =====
    py::enum_<MeetingRecordingError>(m, "MeetingRecordingError")
        .value("MeetingRecordingErrorSuccess", MeetingRecordingError::MeetingRecordingErrorSuccess)
        .value("MeetingRecordingErrorUnknown", MeetingRecordingError::MeetingRecordingErrorUnknown)
        .value("MeetingRecordingErrorStorageFull", MeetingRecordingError::MeetingRecordingErrorStorageFull)
        .value("MeetingRecordingErrorKMSKeyNotReady", MeetingRecordingError::MeetingRecordingErrorKMSKeyNotReady)
        .export_values();

    py::enum_<RecordingRequestType>(m, "RecordingRequestType")
        .value("RecordingRequestTypeUnknown", RecordingRequestType::RecordingRequestTypeUnknown)
        .value("RecordingRequestTypeStart", RecordingRequestType::RecordingRequestTypeStart)
        .value("RecordingRequestTypeStop", RecordingRequestType::RecordingRequestTypeStop)
        .value("RecordingRequestTypePause", RecordingRequestType::RecordingRequestTypePause)
        .value("RecordingRequestTypeResume", RecordingRequestType::RecordingRequestTypeResume)
        .export_values();

    py::enum_<RecordingPermissionType>(m, "RecordingPermissionType")
        .value("RecordingPermissionTypeUnknown", RecordingPermissionType::RecordingPermissionTypeUnknown)
        .value("RecordingPermissionTypeLocalRecording", RecordingPermissionType::RecordingPermissionTypeLocalRecording)
        .value("RecordingPermissionTypeRequestLocalRecording", RecordingPermissionType::RecordingPermissionTypeRequestLocalRecording)
        .value("RecordingPermissionTypeRequestCloudRecording", RecordingPermissionType::RecordingPermissionTypeRequestCloudRecording)
        .export_values();

    py::enum_<RecordingType>(m, "RecordingType")
        .value("RecordingTypeUnknown", RecordingType::RecordingTypeUnknown)
        .value("RecordingTypeLocal", RecordingType::RecordingTypeLocal)
        .value("RecordingTypeCloud", RecordingType::RecordingTypeCloud)
        .export_values();

    // ===== Recording Helper Structs =====
    py::class_<MeetingRecordingInfo>(m, "MeetingRecordingInfo")
        .def(py::init<>())
        .def_readwrite("isMeetingBeingRecorded", &MeetingRecordingInfo::isMeetingBeingRecorded)
        .def_readwrite("canIRecord", &MeetingRecordingInfo::canIRecord)
        .def_readwrite("amIRecording", &MeetingRecordingInfo::amIRecording)
        .def_readwrite("isConnectingToCMR", &MeetingRecordingInfo::isConnectingToCMR)
        .def_readwrite("isCMRPaused", &MeetingRecordingInfo::isCMRPaused)
        .def_readwrite("isCMRInProgress", &MeetingRecordingInfo::isCMRInProgress)
        .def_readwrite("isRecordingOnCloud", &MeetingRecordingInfo::isRecordingOnCloud)
        .def_readwrite("hasLocalRecording", &MeetingRecordingInfo::hasLocalRecording);

    py::class_<RecordingRequestInfo>(m, "RecordingRequestInfo")
        .def(py::init<>())
        .def_readwrite("recordingType", &RecordingRequestInfo::recordingType)
        .def_readwrite("senderName", &RecordingRequestInfo::senderName);

    py::class_<RecordPermissionInfo>(m, "RecordPermissionInfo")
        .def(py::init<>())
        .def_readwrite("type", &RecordPermissionInfo::type)
        .def_readwrite("isEnable", &RecordPermissionInfo::isEnable)
        .def_readwrite("isLocked", &RecordPermissionInfo::isLocked);

    // ===== Recording Helper =====
    py::class_<IRecordingHelper>(m, "IRecordingHelper")
        .def("ConfirmRecordingError", &IRecordingHelper::ConfirmRecordingError)
        .def("IsNeedPromptStartRecordingDisclaimer", [](IRecordingHelper* self) {
            bool need;
            ZRCSDKError result = self->IsNeedPromptStartRecordingDisclaimer(need);
            return py::make_tuple(result, need);
        })
        .def("PromptStartRecordingDisclaimer", &IRecordingHelper::PromptStartRecordingDisclaimer)
        .def("IsMeetingCMRNoStorage", [](IRecordingHelper* self) {
            bool full;
            ZRCSDKError result = self->IsMeetingCMRNoStorage(full);
            return py::make_tuple(result, full);
        })
        .def("QueryMeetingRecordingStorage", &IRecordingHelper::QueryMeetingRecordingStorage)
        .def("SetMeetingRecordingNotificationEmail", &IRecordingHelper::SetMeetingRecordingNotificationEmail)
        .def("StartMeetingCloudRecording", &IRecordingHelper::StartMeetingCloudRecording)
        .def("StopMeetingCloudRecording", &IRecordingHelper::StopMeetingCloudRecording)
        .def("PauseMeetingCloudRecording", &IRecordingHelper::PauseMeetingCloudRecording)
        .def("ResumeMeetingCloudRecording", &IRecordingHelper::ResumeMeetingCloudRecording)
        .def("AllowUserRecording", &IRecordingHelper::AllowUserRecording)
        .def("ResponseToRecordingRequest", &IRecordingHelper::ResponseToRecordingRequest)
        .def("ChangeRecordingPermission", &IRecordingHelper::ChangeRecordingPermission)
        .def("GetRecoringPemissionInfo", [](IRecordingHelper* self) {
            std::vector<RecordPermissionInfo> permissionInfo;
            ZRCSDKError result = self->GetRecoringPemissionInfo(permissionInfo);
            return py::make_tuple(result, permissionInfo);
        });

    // ===== Meeting Reminder Enums ====-
    py::enum_<MeetingReminderType>(m, "MeetingReminderType")
        .value("REMINDER_TYPE_NONE", MeetingReminderType::REMINDER_TYPE_NONE)
        .value("REMINDER_TYPE_START_OR_JOIN_MEETING", MeetingReminderType::REMINDER_TYPE_START_OR_JOIN_MEETING)
        .value("REMINDER_TYPE_JOIN_EXTERNAL_MEETING", MeetingReminderType::REMINDER_TYPE_JOIN_EXTERNAL_MEETING)
        .value("REMINDER_TYPE_RECORDING_REMINDER", MeetingReminderType::REMINDER_TYPE_RECORDING_REMINDER)
        .value("REMINDER_TYPE_RECORDING_DISCLAIMER", MeetingReminderType::REMINDER_TYPE_RECORDING_DISCLAIMER)
        .value("REMINDER_TYPE_ARCHIVING_FAIL", MeetingReminderType::REMINDER_TYPE_ARCHIVING_FAIL)
        .value("REMINDER_TYPE_JOIN_WEBINAR_AS_PANELIST", MeetingReminderType::REMINDER_TYPE_JOIN_WEBINAR_AS_PANELIST)
        .export_values();

    py::enum_<ConsentType>(m, "ConsentType")
        .value("CONSENT_TYPE_NONE", ConsentType::CONSENT_TYPE_NONE)
        .value("CONSENT_TYPE_LIVE_STREAMING", ConsentType::CONSENT_TYPE_LIVE_STREAMING)
        .value("CONSENT_TYPE_PROMOTED_TO_PANELIST", ConsentType::CONSENT_TYPE_PROMOTED_TO_PANELIST)
        .value("CONSENT_TYPE_ARCHIVING", ConsentType::CONSENT_TYPE_ARCHIVING)
        .value("CONSENT_TYPE_NDI", ConsentType::CONSENT_TYPE_NDI)
        .value("CONSENT_TYPE_FOCUS_MODE_START", ConsentType::CONSENT_TYPE_FOCUS_MODE_START)
        .value("CONSENT_TYPE_FOCUS_MODE_ENDING", ConsentType::CONSENT_TYPE_FOCUS_MODE_ENDING)
        .value("CONSENT_TYPE_ADMIN_PAY_REMIND", ConsentType::CONSENT_TYPE_ADMIN_PAY_REMIND)
        .value("CONSENT_TYPE_PAC", ConsentType::CONSENT_TYPE_PAC)
        .value("CONSENT_TYPE_ZOOM_PHONE_ACR", ConsentType::CONSENT_TYPE_ZOOM_PHONE_ACR)
        .value("CONSENT_TYPE_HDMI_CONNECTED", ConsentType::CONSENT_TYPE_HDMI_CONNECTED)
        .value("CONSENT_TYPE_MEETING_SUMMARY", ConsentType::CONSENT_TYPE_MEETING_SUMMARY)
        .value("CONSENT_TYPE_MEETING_QUERY", ConsentType::CONSENT_TYPE_MEETING_QUERY)
        .value("CONSENT_TYPE_CUSTOM_AI_COMPANION", ConsentType::CONSENT_TYPE_CUSTOM_AI_COMPANION)
        .value("CONSENT_TYPE_COMMON", ConsentType::CONSENT_TYPE_COMMON)
        .value("CONSENT_TYPE_SIMULIVE_WEBINAR", ConsentType::CONSENT_TYPE_SIMULIVE_WEBINAR)
        .value("CONSENT_TYPE_CUSTOM_RECORDING", ConsentType::CONSENT_TYPE_CUSTOM_RECORDING)
        .export_values();
 
    py::enum_<PrivacyAlertAction>(m, "PrivacyAlertAction")
        .value("PRIVACY_ALERT_ACTION_NONE", PrivacyAlertAction::PRIVACY_ALERT_ACTION_NONE)
        .value("PRIVACY_ALERT_ACTION_SHOW", PrivacyAlertAction::PRIVACY_ALERT_ACTION_SHOW)
        .value("PRIVACY_ALERT_ACTION_CLOSE", PrivacyAlertAction::PRIVACY_ALERT_ACTION_CLOSE)
        .value("PRIVACY_ALERT_ACTION_SHOW_DISCLAIMER", PrivacyAlertAction::PRIVACY_ALERT_ACTION_SHOW_DISCLAIMER)
        .value("PRIVACY_ALERT_ACTION_CLOSE_DISCLAIMER", PrivacyAlertAction::PRIVACY_ALERT_ACTION_CLOSE_DISCLAIMER)
        .export_values();

    py::enum_<PrivacyAlertType>(m, "PrivacyAlertType")
        .value("PRIVACY_ALERT_TYPE_LIVE_TRANSCRIPTION", PrivacyAlertType::PRIVACY_ALERT_TYPE_LIVE_TRANSCRIPTION)
        .value("PRIVACY_ALERT_TYPE_NEW_LTT_CAPTION", PrivacyAlertType::PRIVACY_ALERT_TYPE_NEW_LTT_CAPTION)
        .export_values();     
    py::enum_<CustomizedMeetingReminderType>(m, "CustomizedMeetingReminderType")
        .value("CUSTOMIZED_REMINDER_TYPE_NONE", CustomizedMeetingReminderType::CUSTOMIZED_REMINDER_TYPE_NONE)
        .value("CUSTOMIZED_REMINDER_TYPE_ONZOOM_JOIN_AS_PANELIST", CustomizedMeetingReminderType::CUSTOMIZED_REMINDER_TYPE_ONZOOM_JOIN_AS_PANELIST)
        .export_values();

    py::enum_<MessageEvent>(m, "MessageEvent")
        .value("MESSAGE_EVENT_UNKNOWN", MessageEvent::MESSAGE_EVENT_UNKNOWN)
        .value("MESSAGE_EVENT_OpenVideoFailForHostStop", MessageEvent::MESSAGE_EVENT_OpenVideoFailForHostStop)
        .value("MESSAGE_EVENT_OpenVideoFailForForceVBEnabledButUserOptionDisabled", MessageEvent::MESSAGE_EVENT_OpenVideoFailForForceVBEnabledButUserOptionDisabled)
        .value("MESSAGE_EVENT_OpenVideoFailForForceVBEnabledButUserNoGreenScreen", MessageEvent::MESSAGE_EVENT_OpenVideoFailForForceVBEnabledButUserNoGreenScreen)
        .value("MESSAGE_EVENT_OpenVideoFailForForceVBEnabledButDeviceNotSupport", MessageEvent::MESSAGE_EVENT_OpenVideoFailForForceVBEnabledButDeviceNotSupport)
        .export_values();
        
    // ===== Meeting Reminder Structs =====
    py::class_<MeetingReminderContent>(m, "MeetingReminderContent")
        .def(py::init<>())
        .def_readwrite("reminderType", &MeetingReminderContent::reminderType)
        .def_readwrite("disclaimerPrivacy", &MeetingReminderContent::disclaimerPrivacy)
        .def_readwrite("isShowing", &MeetingReminderContent::isShowing);

    py::class_<CustomizedMeetingReminderContent>(m, "CustomizedMeetingReminderContent")
        .def(py::init<>())
        .def_readwrite("customizedDisclaimerType", &CustomizedMeetingReminderContent::customizedDisclaimerType)
        .def_readwrite("disclaimerPrivacy", &CustomizedMeetingReminderContent::disclaimerPrivacy)
        .def_readwrite("isShowing", &CustomizedMeetingReminderContent::isShowing);

    py::class_<CombinedConsent>(m, "CombinedConsent")
        .def(py::init<>())
        .def_readwrite("isShowing", &CombinedConsent::isShowing)
        .def_readwrite("type", &CombinedConsent::type)
        .def_readwrite("disclaimerPrivacy", &CombinedConsent::disclaimerPrivacy);

    py::class_<PrivacyMessage>(m, "PrivacyMessage")
        .def(py::init<>())
        .def_readwrite("privacyMessage", &PrivacyMessage::privacyMessage)
        .def_readwrite("hyperlinkKey", &PrivacyMessage::hyperlinkKey)
        .def_readwrite("hyperlinkURL", &PrivacyMessage::hyperlinkURL);  

    py::class_<DisclaimerPrivacy>(m, "DisclaimerPrivacy")
        .def(py::init<>())
        .def_readwrite("title", &DisclaimerPrivacy::title)
        .def_readwrite("privacyMessage", &DisclaimerPrivacy::privacyMessage)
        .def_readwrite("message", &DisclaimerPrivacy::message)
        .def_readwrite("linkUrl", &DisclaimerPrivacy::linkUrl)
        .def_readwrite("linkText", &DisclaimerPrivacy::linkText)
        .def_readwrite("positiveActionText", &DisclaimerPrivacy::positiveActionText)
        .def_readwrite("negativeActionText", &DisclaimerPrivacy::negativeActionText)
        .def_readwrite("privacySection", &DisclaimerPrivacy::privacySection);

    py::class_<ConsentInfo>(m, "ConsentInfo")
        .def(py::init<>())
        .def_readwrite("type", &ConsentInfo::type)
        .def_readwrite("disclaimer", &ConsentInfo::disclaimer)
        .def_readwrite("is_showing", &ConsentInfo::isShowing)
        .def_readwrite("consent_id", &ConsentInfo::consentID);
        
    // ===== Meeting Reminder Helper ====-
    py::class_<IMeetingReminderHelper>(m, "IMeetingReminderHelper")
        .def("RegisterSink", [](IMeetingReminderHelper* self, py::object py_sink) {
            // Create a trampoline and keep it alive in a static map
            static std::map<IMeetingReminderHelper*, std::shared_ptr<MeetingReminderHelperSinkTrampoline>> sinks;
            auto trampoline = std::make_shared<MeetingReminderHelperSinkTrampoline>(py_sink);
            sinks[self] = trampoline;
            return self->RegisterSink(trampoline.get());
        })
        .def("DeregisterSink", [](IMeetingReminderHelper* self) {
            static std::map<IMeetingReminderHelper*, std::shared_ptr<MeetingReminderHelperSinkTrampoline>> sinks;
            auto it = sinks.find(self);
            if (it != sinks.end()) {
                auto result = self->DeregisterSink(it->second.get());
                sinks.erase(it);
                return result;
            }
            return ZRCSDKERR_INTERNAL_ERROR;
        })
        .def("ConfirmMeetingReminder", &IMeetingReminderHelper::ConfirmMeetingReminder)
        .def("ConfirmCustomizedMeetingReminder", &IMeetingReminderHelper::ConfirmCustomizedMeetingReminder)
        .def("ConfirmConsent", &IMeetingReminderHelper::ConfirmConsent)
        .def("ConfirmCombinedConsent", &IMeetingReminderHelper::ConfirmCombinedConsent)
        .def("HandlePrivacyAlert", &IMeetingReminderHelper::HandlePrivacyAlert)
        .def("ContinueMeetingOnInactivity", &IMeetingReminderHelper::ContinueMeetingOnInactivity);

    // ===== Setting Service Enums =====
    py::enum_<AudioCheckupCommand>(m, "AudioCheckupCommand")
        .value("AudioCheckupCommandStart", AudioCheckupCommand::AudioCheckupCommandStart)
        .value("AudioCheckupCommandCancel", AudioCheckupCommand::AudioCheckupCommandCancel)
        .export_values();

    py::enum_<AudioCheckupStatus>(m, "AudioCheckupStatus")
        .value("AudioCheckupStatusIdle", AudioCheckupStatus::AudioCheckupStatusIdle)
        .value("AudioCheckupStatusScheduled", AudioCheckupStatus::AudioCheckupStatusScheduled)
        .value("AudioCheckupStatusStarting", AudioCheckupStatus::AudioCheckupStatusStarting)
        .value("AudioCheckupStatusChecking", AudioCheckupStatus::AudioCheckupStatusChecking)
        .value("AudioCheckupStatusSucceeded", AudioCheckupStatus::AudioCheckupStatusSucceeded)
        .value("AudioCheckupStatusFailed", AudioCheckupStatus::AudioCheckupStatusFailed)
        .value("AudioCheckupStatusFailedLikely", AudioCheckupStatus::AudioCheckupStatusFailedLikely)
        .export_values();

    py::enum_<AdvancedNoiseSuppressionMode>(m, "AdvancedNoiseSuppressionMode")
        .value("AdvancedNoiseSuppressionModeNone", AdvancedNoiseSuppressionMode::AdvancedNoiseSuppressionModeNone)
        .value("AdvancedNoiseSuppressionModeAuto", AdvancedNoiseSuppressionMode::AdvancedNoiseSuppressionModeAuto)
        .value("AdvancedNoiseSuppressionModeHigh", AdvancedNoiseSuppressionMode::AdvancedNoiseSuppressionModeHigh)
        .value("AdvancedNoiseSuppressionModeOff", AdvancedNoiseSuppressionMode::AdvancedNoiseSuppressionModeOff)
        .export_values();

    py::enum_<MicRecordTestStatus>(m, "MicRecordTestStatus")
        .value("MicRecordTestStatusNone", MicRecordTestStatus::MicRecordTestStatusNone)
        .value("MicRecordTestStatusRecording", MicRecordTestStatus::MicRecordTestStatusRecording)
        .value("MicRecordTestStatusPlaying", MicRecordTestStatus::MicRecordTestStatusPlaying)
        .export_values();

    py::enum_<ScreenResolutionStatus>(m, "ScreenResolutionStatus")
        .value("ScreenResolutionStatusOptimizable", ScreenResolutionStatus::ScreenResolutionStatusOptimizable)
        .value("ScreenResolutionStatusOptimized", ScreenResolutionStatus::ScreenResolutionStatusOptimized)
        .export_values();

    py::enum_<ScreenSequenceCalibrationAction>(m, "ScreenSequenceCalibrationAction")
        .value("ScreenSequenceCalibrationNone", ScreenSequenceCalibrationAction::ScreenSequenceCalibrationNone)
        .value("ScreenSequenceCalibrationStart", ScreenSequenceCalibrationAction::ScreenSequenceCalibrationStart)
        .value("ScreenSequenceCalibrationIdentify", ScreenSequenceCalibrationAction::ScreenSequenceCalibrationIdentify)
        .value("ScreenSequenceCalibrationConfirm", ScreenSequenceCalibrationAction::ScreenSequenceCalibrationConfirm)
        .value("ScreenSequenceCalibrationCancel", ScreenSequenceCalibrationAction::ScreenSequenceCalibrationCancel)
        .value("ScreenSequenceCalibrationConfidenceStart", ScreenSequenceCalibrationAction::ScreenSequenceCalibrationConfidenceStart)
        .value("ScreenSequenceCalibrationConfidenceIdentify", ScreenSequenceCalibrationAction::ScreenSequenceCalibrationConfidenceIdentify)
        .export_values();

    py::enum_<ChannelSignalType>(m, "ChannelSignalType")
        .value("ChannelSignalTypeUnknown", ChannelSignalType::ChannelSignalTypeUnknown)
        .value("ChannelSignalTypeMono", ChannelSignalType::ChannelSignalTypeMono)
        .value("ChannelSignalTypeStereoLeft", ChannelSignalType::ChannelSignalTypeStereoLeft)
        .value("ChannelSignalTypeStereoRight", ChannelSignalType::ChannelSignalTypeStereoRight)
        .export_values();

    py::enum_<NetworkType>(m, "NetworkType")
        .value("NetworkTypeUnknown", NetworkType::NetworkTypeUnknown)
        .value("NetworkTypeWired", NetworkType::NetworkTypeWired)
        .value("NetworkTypeWifi", NetworkType::NetworkTypeWifi)
        .value("NetworkTypePPP", NetworkType::NetworkTypePPP)
        .value("NetworkType3G", NetworkType::NetworkType3G)
        .export_values();

    py::enum_<NetworkConnectionType>(m, "NetworkConnectionType")
        .value("NetworkConnectionTypeUnknown", NetworkConnectionType::NetworkConnectionTypeUnknown)
        .value("NetworkConnectionTypeDirect", NetworkConnectionType::NetworkConnectionTypeDirect)
        .value("NetworkConnectionTypeCloud", NetworkConnectionType::NetworkConnectionTypeCloud)
        .export_values();

    py::enum_<NetworkAudioDeviceListAction>(m, "NetworkAudioDeviceListAction")
        .value("NetworkAudioDeviceListActionUnknown", NetworkAudioDeviceListAction::NetworkAudioDeviceListActionUnknown)
        .value("NetworkAudioDeviceListActionRefreshList", NetworkAudioDeviceListAction::NetworkAudioDeviceListActionRefreshList)
        .value("NetworkAudioDeviceListActionRemoveDevice", NetworkAudioDeviceListAction::NetworkAudioDeviceListActionRemoveDevice)
        .value("NetworkAudioDeviceListActionAddDevice", NetworkAudioDeviceListAction::NetworkAudioDeviceListActionAddDevice)
        .value("NetworkAudioDeviceListActionUpdateDevice", NetworkAudioDeviceListAction::NetworkAudioDeviceListActionUpdateDevice)
        .value("NetworkAudioDeviceListActionUseDanteController", NetworkAudioDeviceListAction::NetworkAudioDeviceListActionUseDanteController)
        .export_values();

    py::enum_<NetworkAudioDeviceState>(m, "NetworkAudioDeviceState")
        .value("NetworkAudioDeviceStateNone", NetworkAudioDeviceState::NetworkAudioDeviceStateNone)
        .value("NetworkAudioDeviceStateAvailable", NetworkAudioDeviceState::NetworkAudioDeviceStateAvailable)
        .value("NetworkAudioDeviceStateConnecting", NetworkAudioDeviceState::NetworkAudioDeviceStateConnecting)
        .value("NetworkAudioDeviceStateConnected", NetworkAudioDeviceState::NetworkAudioDeviceStateConnected)
        .value("NetworkAudioDeviceStateDisconnected", NetworkAudioDeviceState::NetworkAudioDeviceStateDisconnected)
        .value("NetworkAudioDeviceStateError", NetworkAudioDeviceState::NetworkAudioDeviceStateError)
        .value("NetworkAudioDeviceStateOccupied", NetworkAudioDeviceState::NetworkAudioDeviceStateOccupied)
        .export_values();

    py::enum_<NetworkAdapterUpdateType>(m, "NetworkAdapterUpdateType")
        .value("NetworkAdapterUpdateTypeNone", NetworkAdapterUpdateType::NetworkAdapterUpdateTypeNone)
        .value("NetworkAdapterUpdateTypeDante", NetworkAdapterUpdateType::NetworkAdapterUpdateTypeDante)
        .value("NetworkAdapterUpdateTypeNRC", NetworkAdapterUpdateType::NetworkAdapterUpdateTypeNRC)
        .export_values();

    py::enum_<CalibrationAction>(m, "CalibrationAction")
        .value("CalibrationActionPageAdjustCamera", CalibrationAction::CalibrationActionPageAdjustCamera)
        .value("CalibrationActionPageCameraControl", CalibrationAction::CalibrationActionPageCameraControl)
        .value("CalibrationActionPageReadyToMove", CalibrationAction::CalibrationActionPageReadyToMove)
        .value("CalibrationActionEventStartToCalibrate", CalibrationAction::CalibrationActionEventStartToCalibrate)
        .value("CalibrationActionEventFinishToCheckResult", CalibrationAction::CalibrationActionEventFinishToCheckResult)
        .value("CalibrationActionEventAcceptResult", CalibrationAction::CalibrationActionEventAcceptResult)
        .value("CalibrationActionEventStop", CalibrationAction::CalibrationActionEventStop)
        .value("CalibrationActionPageAskNeedSetCameraBoundary", CalibrationAction::CalibrationActionPageAskNeedSetCameraBoundary)
        .value("CalibrationActionEventSwitchBoundaryCamera", CalibrationAction::CalibrationActionEventSwitchBoundaryCamera)
        .value("CalibrationActionEventAdjustBoundary", CalibrationAction::CalibrationActionEventAdjustBoundary)
        .value("CalibrationActionPageVerifyBoundary", CalibrationAction::CalibrationActionPageVerifyBoundary)
        .value("CalibrationActionPagePreAcceptBoundary", CalibrationAction::CalibrationActionPagePreAcceptBoundary)
        .value("CalibrationActionEventAcceptBoundaryResult", CalibrationAction::CalibrationActionEventAcceptBoundaryResult)
        .value("CalibrationActionPagePreviewIDBoundary", CalibrationAction::CalibrationActionPagePreviewIDBoundary)
        .export_values();

    // ===== Setting Service Structs =====
    py::class_<QualityStatisticalAudio>(m, "QualityStatisticalAudio")
        .def(py::init<>())
        .def_readwrite("sampleRate", &QualityStatisticalAudio::sampleRate)
        .def_readwrite("recSampleRates", &QualityStatisticalAudio::recSampleRates);

    py::class_<QualityStatisticalVideo>(m, "QualityStatisticalVideo")
        .def(py::init<>())
        .def_readwrite("fpsOfRecvMaxVideo", &QualityStatisticalVideo::fpsOfRecvMaxVideo)
        .def_readwrite("widthOfMaxRecvVideo", &QualityStatisticalVideo::widthOfMaxRecvVideo)
        .def_readwrite("heightOfMaxRecvVideo", &QualityStatisticalVideo::heightOfMaxRecvVideo)
        .def_readwrite("resolutionOfSend", &QualityStatisticalVideo::resolutionOfSend)
        .def_readwrite("fpsOfSend", &QualityStatisticalVideo::fpsOfSend);

    py::class_<QualityStatisticalShare>(m, "QualityStatisticalShare")
        .def(py::init<>())
        .def_readwrite("fpsOfRecvShare", &QualityStatisticalShare::fpsOfRecvShare)
        .def_readwrite("widthOfRecvShare", &QualityStatisticalShare::widthOfRecvShare)
        .def_readwrite("heightOfRecvShare", &QualityStatisticalShare::heightOfRecvShare)
        .def_readwrite("resolutionOfSend", &QualityStatisticalShare::resolutionOfSend)
        .def_readwrite("fpsOfSend", &QualityStatisticalShare::fpsOfSend);

    py::class_<QualityStatisticalInfo>(m, "QualityStatisticalInfo")
        .def(py::init<>())
        .def_readwrite("audioStatisticalInfo", &QualityStatisticalInfo::audioStatisticalInfo)
        .def_readwrite("videoStatisticalInfo", &QualityStatisticalInfo::videoStatisticalInfo)
        .def_readwrite("shareStatisticalInfo", &QualityStatisticalInfo::shareStatisticalInfo);

    py::class_<StatisticalNetWorkStatusInfo>(m, "StatisticalNetWorkStatusInfo")
        .def(py::init<>())
        .def_readwrite("avgLossRatio", &StatisticalNetWorkStatusInfo::avgLossRatio)
        .def_readwrite("maxLossRatio", &StatisticalNetWorkStatusInfo::maxLossRatio)
        .def_readwrite("rtt", &StatisticalNetWorkStatusInfo::rtt)
        .def_readwrite("jitter", &StatisticalNetWorkStatusInfo::jitter)
        .def_readwrite("rate", &StatisticalNetWorkStatusInfo::rate);

    py::class_<StatisticalMediaInfo>(m, "StatisticalMediaInfo")
        .def(py::init<>())
        .def_readwrite("networkSendingStatus", &StatisticalMediaInfo::networkSendingStatus)
        .def_readwrite("networkReceivingStatus", &StatisticalMediaInfo::networkReceivingStatus)
        .def_readwrite("qualityStatisticalInfo", &StatisticalMediaInfo::qualityStatisticalInfo);

    py::class_<StatisticalOverallInfo>(m, "StatisticalOverallInfo")
        .def(py::init<>())
        .def_readwrite("cpuCoreNumber", &StatisticalOverallInfo::cpuCoreNumber)
        .def_readwrite("cpuFrequency", &StatisticalOverallInfo::cpuFrequency)
        .def_readwrite("cpuZRUsage", &StatisticalOverallInfo::cpuZRUsage)
        .def_readwrite("cpuOverallUsage", &StatisticalOverallInfo::cpuOverallUsage)
        .def_readwrite("memorySize", &StatisticalOverallInfo::memorySize)
        .def_readwrite("memoryZRUsage", &StatisticalOverallInfo::memoryZRUsage)
        .def_readwrite("memoryOverallUsage", &StatisticalOverallInfo::memoryOverallUsage)
        .def_readwrite("networkType", &StatisticalOverallInfo::networkType)
        .def_readwrite("proxy", &StatisticalOverallInfo::proxy)
        .def_readwrite("netWorkConnectionType", &StatisticalOverallInfo::netWorkConnectionType)
        .def_readwrite("dataCenterRegionMessage", &StatisticalOverallInfo::dataCenterRegionMessage)
        .def_readwrite("encryption", &StatisticalOverallInfo::encryption);

    py::class_<StatisticalPhoneNetworkInfo>(m, "StatisticalPhoneNetworkInfo")
        .def(py::init<>())
        .def_readwrite("packetsNumber", &StatisticalPhoneNetworkInfo::packetsNumber)
        .def_readwrite("frequency", &StatisticalPhoneNetworkInfo::frequency)
        .def_readwrite("packetLoss", &StatisticalPhoneNetworkInfo::packetLoss)
        .def_readwrite("packetLossMax", &StatisticalPhoneNetworkInfo::packetLossMax)
        .def_readwrite("jitter", &StatisticalPhoneNetworkInfo::jitter)
        .def_readwrite("bandwidth", &StatisticalPhoneNetworkInfo::bandwidth)
        .def_readwrite("codec", &StatisticalPhoneNetworkInfo::codec);

    py::class_<StatisticalPhonePeerInfo>(m, "StatisticalPhonePeerInfo")
        .def(py::init<>())
        .def_readwrite("peerNumber", &StatisticalPhonePeerInfo::peerNumber)
        .def_readwrite("localIp", &StatisticalPhonePeerInfo::localIp)
        .def_readwrite("localPort", &StatisticalPhonePeerInfo::localPort)
        .def_readwrite("remoteIp", &StatisticalPhonePeerInfo::remoteIp)
        .def_readwrite("remotePort", &StatisticalPhonePeerInfo::remotePort)
        .def_readwrite("networkDelay", &StatisticalPhonePeerInfo::networkDelay)
        .def_readwrite("networkSendingStatus", &StatisticalPhonePeerInfo::networkSendingStatus)
        .def_readwrite("networkReceivingStatus", &StatisticalPhonePeerInfo::networkReceivingStatus);

    py::class_<StatisticalPhoneInfo>(m, "StatisticalPhoneInfo")
        .def(py::init<>())
        .def_readwrite("registerId", &StatisticalPhoneInfo::registerId)
        .def_readwrite("registerServerIp", &StatisticalPhoneInfo::registerServerIp)
        .def_readwrite("registerServerPort", &StatisticalPhoneInfo::registerServerPort)
        .def_readwrite("networkSwitch", &StatisticalPhoneInfo::networkSwitch)
        .def_readwrite("localNetworkInterface", &StatisticalPhoneInfo::localNetworkInterface)
        .def_readwrite("phonePeers", &StatisticalPhoneInfo::phonePeers);

    py::class_<DiagnosticMsg>(m, "DiagnosticMsg")
        .def(py::init<>())
        .def_readwrite("field", &DiagnosticMsg::field)
        .def_readwrite("description", &DiagnosticMsg::description);

    py::class_<DiagnosticMsgGroup>(m, "DiagnosticMsgGroup")
        .def(py::init<>())
        .def_readwrite("name", &DiagnosticMsgGroup::name)
        .def_readwrite("msgs", &DiagnosticMsgGroup::msgs);

    py::class_<DiagnosticInfo>(m, "DiagnosticInfo")
        .def(py::init<>())
        .def_readwrite("groups", &DiagnosticInfo::groups);

    py::class_<StatisticalInfo>(m, "StatisticalInfo")
        .def(py::init<>())
        .def_readwrite("overallInfo", &StatisticalInfo::overallInfo)
        .def_readwrite("audioInfo", &StatisticalInfo::audioInfo)
        .def_readwrite("videoInfo", &StatisticalInfo::videoInfo)
        .def_readwrite("shareInfo", &StatisticalInfo::shareInfo)
        .def_readwrite("phoneInfo", &StatisticalInfo::phoneInfo);

    py::class_<AudioCheckupInfo>(m, "AudioCheckupInfo")
        .def(py::init<>())
        .def_readwrite("status", &AudioCheckupInfo::status)
        .def_readwrite("intervalAfterScheduled", &AudioCheckupInfo::intervalAfterScheduled)
        .def_readwrite("percentageOfCheckup", &AudioCheckupInfo::percentageOfCheckup)
        .def_readwrite("canRestartZoomRoomsSystem", &AudioCheckupInfo::canRestartZoomRoomsSystem)
        .def_readwrite("intervalAfterFinished", &AudioCheckupInfo::intervalAfterFinished)
        .def_readwrite("aecLevel", &AudioCheckupInfo::aecLevel)
        .def_readwrite("testTime", &AudioCheckupInfo::testTime);

    py::class_<RoomProfile>(m, "RoomProfile")
        .def(py::init<>())
        .def_readwrite("ID", &RoomProfile::ID)
        .def_readwrite("name", &RoomProfile::name)
        .def_readwrite("isSelected", &RoomProfile::isSelected)
        .def_readwrite("issueDevices", &RoomProfile::issueDevices);

    py::class_<RoomProfileList>(m, "RoomProfileList")
        .def(py::init<>())
        .def_readwrite("roomProfileList", &RoomProfileList::roomProfileList);

    py::class_<RoomCapability>(m, "RoomCapability")
        .def(py::init<>())
        .def_readwrite("supportAutoLoginOS", &RoomCapability::supportAutoLoginOS)
        .def_readwrite("supportRestartOS", &RoomCapability::supportRestartOS)
        .def_readwrite("notSupportDigitalSignage", &RoomCapability::notSupportDigitalSignage)
        .def_readwrite("notSupportMicAdvancedOption", &RoomCapability::notSupportMicAdvancedOption);

    py::class_<AdjustScreensRes>(m, "AdjustScreensRes")
        .def(py::init<>())
        .def_readwrite("result", &AdjustScreensRes::result)
        .def_readwrite("currentScreen", &AdjustScreensRes::currentScreen)
        .def_readwrite("quantityOfScreens", &AdjustScreensRes::quantityOfScreens)
        .def_readwrite("action", &AdjustScreensRes::action);

    py::class_<ScreenInfos>(m, "ScreenInfos")
        .def(py::init<>())
        .def_readwrite("quantityOfScreens", &ScreenInfos::quantityOfScreens)
        .def_readwrite("quantityOfCecAdapterAttachedScreens", &ScreenInfos::quantityOfCecAdapterAttachedScreens)
        .def_readwrite("hasConfidenceMonitor", &ScreenInfos::hasConfidenceMonitor)
        .def_readwrite("mainDisplayPosition", &ScreenInfos::mainDisplayPosition);

    py::class_<NetworkAudioChannelInfo>(m, "NetworkAudioChannelInfo")
        .def(py::init<>())
        .def_readwrite("state", &NetworkAudioChannelInfo::state)
        .def_readwrite("signalType", &NetworkAudioChannelInfo::signalType)
        .def_readwrite("deviceId", &NetworkAudioChannelInfo::deviceId)
        .def_readwrite("channelName", &NetworkAudioChannelInfo::channelName);

    py::class_<NetworkAudioDevice>(m, "NetworkAudioDevice")
        .def(py::init<>())
        .def_readwrite("state", &NetworkAudioDevice::state)
        .def_readwrite("channels", &NetworkAudioDevice::channels)
        .def_readwrite("ID", &NetworkAudioDevice::ID)
        .def_readwrite("name", &NetworkAudioDevice::name)
        .def_readwrite("identifiable", &NetworkAudioDevice::identifiable);

    py::class_<AudioChannelAndCameraBindInfo>(m, "AudioChannelAndCameraBindInfo")
        .def(py::init<>())
        .def_readwrite("cameraDeviceID", &AudioChannelAndCameraBindInfo::cameraDeviceID)
        .def_readwrite("networkDeviceName", &AudioChannelAndCameraBindInfo::networkDeviceName)
        .def_readwrite("networkChannelName", &AudioChannelAndCameraBindInfo::networkChannelName)
        .def_readwrite("rxChannelID", &AudioChannelAndCameraBindInfo::rxChannelID);

    py::class_<IntelligentDirectorInfo>(m, "IntelligentDirectorInfo")
        .def(py::init<>())
        .def_readwrite("supportsDirectorMode", &IntelligentDirectorInfo::supportsDirectorMode)
        .def_readwrite("isCalibrationConfigured", &IntelligentDirectorInfo::isCalibrationConfigured)
        .def_readwrite("allowDirectorAndMultiCameraParallel", &IntelligentDirectorInfo::allowDirectorAndMultiCameraParallel)
        .def_readwrite("isRegionLimited", &IntelligentDirectorInfo::isRegionLimited)
        .def_readwrite("supportedCameraNumber", &IntelligentDirectorInfo::supportedCameraNumber)
        .def_readwrite("multiCameraParallelNumInDirector", &IntelligentDirectorInfo::multiCameraParallelNumInDirector)
        .def_readwrite("supportSavePresetImage", &IntelligentDirectorInfo::supportSavePresetImage);

    py::class_<CameraBoundaryConfigurationInfo>(m, "CameraBoundaryConfigurationInfo")
        .def(py::init<>())
        .def_readwrite("supportsBoundary", &CameraBoundaryConfigurationInfo::supportsBoundary)
        .def_readwrite("isBoundaryConfigured", &CameraBoundaryConfigurationInfo::isBoundaryConfigured)
        .def_readwrite("cameraBoundaryCapability", &CameraBoundaryConfigurationInfo::cameraBoundaryCapability)
        .def_readwrite("cameraBoundaryEnableStatus", &CameraBoundaryConfigurationInfo::cameraBoundaryEnableStatus);

    py::class_<NetworkAdapterInfo>(m, "NetworkAdapterInfo")
        .def(py::init<>())
        .def_readwrite("updateType", &NetworkAdapterInfo::updateType)
        .def_readwrite("adapter", &NetworkAdapterInfo::adapter)
        .def_readwrite("ip", &NetworkAdapterInfo::ip);

    py::class_<VirtualAudioDevice>(m, "VirtualAudioDevice")
        .def(py::init<>())
        .def_readwrite("type", &VirtualAudioDevice::type)
        .def_readwrite("vendor", &VirtualAudioDevice::vendor)
        .def_readwrite("maxSelectedCount", &VirtualAudioDevice::maxSelectedCount);

    py::class_<Device>(m, "Device")
        .def(py::init<>())
        .def_readwrite("id", &Device::id)
        .def_readwrite("name", &Device::name)
        .def_readwrite("alias", &Device::alias)
        .def_readwrite("displayName", &Device::displayName)
        .def_readwrite("isSelected", &Device::isSelected)
        .def_readwrite("manuallySelected", &Device::manuallySelected)
        .def_readwrite("combinedDevice", &Device::combinedDevice)
        .def_readwrite("numberOfCombinedDevices", &Device::numberOfCombinedDevices)
        .def_readwrite("ptzComId", &Device::ptzComId)
        .def_readwrite("isSelectedAsMultiDevice", &Device::isSelectedAsMultiDevice)
        .def_readwrite("selectedDirectorDevice", &Device::selectedDirectorDevice)
        .def_readwrite("isSupportCalibration", &Device::isSupportCalibration)
        .def_readwrite("virtualAudioDevice", &Device::virtualAudioDevice);

    // ===== Setting Service =====
    py::class_<ICalibrationHelper>(m, "ICalibrationHelper");

    py::class_<ISettingService>(m, "ISettingService")
        .def("GetMicrophoneList", [](ISettingService* self) {
            std::vector<Device> microphones;
            ZRCSDKError result = self->GetMicrophoneList(microphones);
            return py::make_tuple(result, microphones);
        })
        .def("GetSpeakerList", [](ISettingService* self) {
            std::vector<Device> speakers;
            ZRCSDKError result = self->GetSpeakerList(speakers);
            return py::make_tuple(result, speakers);
        })
        .def("GetCameraList", [](ISettingService* self) {
            std::vector<Device> cameras;
            ZRCSDKError result = self->GetCameraList(cameras);
            return py::make_tuple(result, cameras);
        })
        .def("GetCompanionZRList", [](ISettingService* self) {
            std::vector<CompanionZRDeviceInfo> CZRs;
            ZRCSDKError result = self->GetCompanionZRList(CZRs);
            return py::make_tuple(result, CZRs);
        })
        .def("GetNetworkAudioDeviceList", [](ISettingService* self, const std::string& virtualDeviceID) {
            std::vector<NetworkAudioDevice> networkAudioDeviceList;
            ZRCSDKError result = self->GetNetworkAudioDeviceList(virtualDeviceID, networkAudioDeviceList);
            return py::make_tuple(result, networkAudioDeviceList);
        })
        .def("GetCurrentMicrophone", [](ISettingService* self) {
            Device microphone;
            ZRCSDKError result = self->GetCurrentMicrophone(microphone);
            return py::make_tuple(result, microphone);
        })
        .def("GetCurrentSpeaker", [](ISettingService* self) {
            Device speaker;
            ZRCSDKError result = self->GetCurrentSpeaker(speaker);
            return py::make_tuple(result, speaker);
        })
        .def("GetCurrentCamera", [](ISettingService* self) {
            Device camera;
            ZRCSDKError result = self->GetCurrentCamera(camera);
            return py::make_tuple(result, camera);
        })
        .def("SetCurrentMicrophone", &ISettingService::SetCurrentMicrophone)
        .def("SetCurrentSpeaker", &ISettingService::SetCurrentSpeaker)
        .def("SetCurrentCamera", &ISettingService::SetCurrentCamera)
        .def("GetMicrophoneVolume", [](ISettingService* self) {
            float volume;
            ZRCSDKError result = self->GetMicrophoneVolume(volume);
            return py::make_tuple(result, volume);
        })
        .def("GetSpeakerVolume", [](ISettingService* self) {
            float volume;
            ZRCSDKError result = self->GetSpeakerVolume(volume);
            return py::make_tuple(result, volume);
        })
        .def("SetMicrophoneVolume", &ISettingService::SetMicrophoneVolume)
        .def("SetSpeakerVolume", &ISettingService::SetSpeakerVolume)
        .def("SetSpeakerTempVolumeInMeeting", &ISettingService::SetSpeakerTempVolumeInMeeting)
        .def("TestMicrophone", &ISettingService::TestMicrophone)
        .def("StartTestingMicrophoneVolume", &ISettingService::StartTestingMicrophoneVolume)
        .def("StopTestingMicrophoneVolume", &ISettingService::StopTestingMicrophoneVolume)
        .def("ConfirmNumberOfCombinedMicrophone", &ISettingService::ConfirmNumberOfCombinedMicrophone)
        .def("IsSupportAcousticEchoCancellation", [](ISettingService* self) {
            bool support;
            ZRCSDKError result = self->IsSupportAcousticEchoCancellation(support);
            return py::make_tuple(result, support);
        })
        .def("EnableAcousticEchoCancellation", &ISettingService::EnableAcousticEchoCancellation)
        .def("IsSupportAdvancedNoiseSuppression", [](ISettingService* self) {
            bool support;
            ZRCSDKError result = self->IsSupportAdvancedNoiseSuppression(support);
            return py::make_tuple(result, support);
        })
        .def("GetCurrentAdvancedNoiseSuppressionMode", [](ISettingService* self) {
            AdvancedNoiseSuppressionMode mode;
            ZRCSDKError result = self->GetCurrentAdvancedNoiseSuppressionMode(mode);
            return py::make_tuple(result, mode);
        })
        .def("SelectAdvancedNoiseSuppressionMode", &ISettingService::SelectAdvancedNoiseSuppressionMode)
        .def("EnableMicrophoneHardwareTroubleshooting", &ISettingService::EnableMicrophoneHardwareTroubleshooting)
        .def("AudioCheckup", &ISettingService::AudioCheckup)
        .def("IsAudioFramingAvailable", [](ISettingService* self) {
            bool available;
            ZRCSDKError result = self->IsAudioFramingAvailable(available);
            return py::make_tuple(result, available);
        })
        .def("EnableAudioFraming", &ISettingService::EnableAudioFraming)
        .def("StartTestingSpeaker", &ISettingService::StartTestingSpeaker)
        .def("StopTestingSpeaker", &ISettingService::StopTestingSpeaker)
        .def("IsSpatialAudioAvailable", [](ISettingService* self) {
            bool available;
            ZRCSDKError result = self->IsSpatialAudioAvailable(available);
            return py::make_tuple(result, available);
        })
        .def("EnableSpatialAudio", &ISettingService::EnableSpatialAudio)
        .def("SelectMultipleCamera", &ISettingService::SelectMultipleCamera,
            py::arg("deviceID"), py::arg("isSelected"), py::arg("companionZRID") = "")
        .def("SelectIntelligentDirectorCamera", &ISettingService::SelectIntelligentDirectorCamera)
        .def("CalibrateIntelligentDirectorMode", &ISettingService::CalibrateIntelligentDirectorMode,
            py::arg("actionType"), py::arg("deviceID") = "",
            py::arg("boundaryAdjustField") = CameraBoundaryAdjustFieldUnknown, py::arg("boundaryAdjustValue") = 0)
        .def("SetCameraCOMId", &ISettingService::SetCameraCOMId,
            py::arg("deviceID"), py::arg("comID"), py::arg("companionZRID") = "")
        .def("SetCameraDisplayName", &ISettingService::SetCameraDisplayName,
            py::arg("deviceID"), py::arg("displayName"), py::arg("companionZRID") = "")
        .def("SelectRoomProfile", &ISettingService::SelectRoomProfile)
        .def("EnableStatisticalInfo", &ISettingService::EnableStatisticalInfo)
        .def("StartAdjustZRScreens", &ISettingService::StartAdjustZRScreens)
        .def("StartOverAdjustZRScreens", &ISettingService::StartOverAdjustZRScreens)
        .def("IdentifyZRConfidenceMonitor", &ISettingService::IdentifyZRConfidenceMonitor)
        .def("IdentifyZRScreens", &ISettingService::IdentifyZRScreens)
        .def("ConfirmAdjustZRScreens", &ISettingService::ConfirmAdjustZRScreens)
        .def("CancelAdjustZRScreens", &ISettingService::CancelAdjustZRScreens)
        .def("TurnCECScreensOn", &ISettingService::TurnCECScreensOn)
        .def("RefreshDiagnosticInfo", &ISettingService::RefreshDiagnosticInfo)
        .def("GetWindowsIoTAccountName", [](ISettingService* self) {
            std::string osAccountName;
            ZRCSDKError result = self->GetWindowsIoTAccountName(osAccountName);
            return py::make_tuple(result, osAccountName);
        })
        .def("ChangeWindowsPassword", &ISettingService::ChangeWindowsPassword)
        .def("ListVirtualAudioDevices", &ISettingService::ListVirtualAudioDevices)
        .def("SelectVirtualAudioDevice", &ISettingService::SelectVirtualAudioDevice)
        .def("UnselectVirtualAudioDevice", &ISettingService::UnselectVirtualAudioDevice)
        .def("IdentifyVirtualAudioDevice", &ISettingService::IdentifyVirtualAudioDevice)
        .def("UseDanteController", &ISettingService::UseDanteController)
        .def("IsUseDanteController", [](ISettingService* self, const std::string& virtualDeviceID) {
            bool isUseDanteController;
            ZRCSDKError result = self->IsUseDanteController(virtualDeviceID, isUseDanteController);
            return py::make_tuple(result, isUseDanteController);
        })
        .def("ListAudioChannelAndCameraBindInfo", &ISettingService::ListAudioChannelAndCameraBindInfo)
        .def("BindCameraToAudioChannel", &ISettingService::BindCameraToAudioChannel)
        .def("UnbindCameraFromAudioChannel", &ISettingService::UnbindCameraFromAudioChannel)
        .def("UnbindAudioChannelFromCamera", &ISettingService::UnbindAudioChannelFromCamera)
        .def("UnbindAllAudioChannelAndCameraConnections", &ISettingService::UnbindAllAudioChannelAndCameraConnections)
        .def("RenameCompanionZR", &ISettingService::RenameCompanionZR)
        .def("GetNetWorkAdapterInfo", [](ISettingService* self) {
            std::vector<NetworkAdapterInfo> networkAdapterInfos;
            ZRCSDKError result = self->GetNetWorkAdapterInfo(networkAdapterInfos);
            return py::make_tuple(result, networkAdapterInfos);
        })
        .def("GetCalibrationHelper", &ISettingService::GetCalibrationHelper, py::return_value_policy::reference)
        .def("EnableMultiCameraOnlyMode", &ISettingService::EnableMultiCameraOnlyMode);

    // ===== Third Party Meeting Helper Enums =====
    py::enum_<RoomSystemCallingStatus>(m, "RoomSystemCallingStatus")
        .value("RoomSystemCallingStatusAccepted", RoomSystemCallingStatus::RoomSystemCallingStatusAccepted)
        .value("RoomSystemCallingStatusRinging", RoomSystemCallingStatus::RoomSystemCallingStatusRinging)
        .value("RoomSystemCallingStatusTimeOut", RoomSystemCallingStatus::RoomSystemCallingStatusTimeOut)
        .value("RoomSystemCallingStatusFailed", RoomSystemCallingStatus::RoomSystemCallingStatusFailed)
        .value("RoomSystemCallingStatusFailedNotSupportEncryption", RoomSystemCallingStatus::RoomSystemCallingStatusFailedNotSupportEncryption)
        .value("RoomSystemCallingStatusExceedFreePorts", RoomSystemCallingStatus::RoomSystemCallingStatusExceedFreePorts)
        .export_values();

    py::enum_<IntegrationMeetingState>(m, "IntegrationMeetingState")
        .value("IntegrationMeetingStateNone", IntegrationMeetingState::IntegrationMeetingStateNone)
        .value("IntegrationMeetingStateRejoining", IntegrationMeetingState::IntegrationMeetingStateRejoining)
        .value("IntegrationMeetingStateJoining", IntegrationMeetingState::IntegrationMeetingStateJoining)
        .value("IntegrationMeetingStateWaitingRoom", IntegrationMeetingState::IntegrationMeetingStateWaitingRoom)
        .value("IntegrationMeetingStateConnected", IntegrationMeetingState::IntegrationMeetingStateConnected)
        .value("IntegrationMeetingStateDisconnecting", IntegrationMeetingState::IntegrationMeetingStateDisconnecting)
        .value("IntegrationMeetingStateDisconnected", IntegrationMeetingState::IntegrationMeetingStateDisconnected)
        .value("IntegrationMeetingStateNeedPassword", IntegrationMeetingState::IntegrationMeetingStateNeedPassword)
        .export_values();

    py::enum_<IntegrationContentShareState>(m, "IntegrationContentShareState")
        .value("IntegrationContentShareStateInactive", IntegrationContentShareState::IntegrationContentShareStateInactive)
        .value("IntegrationContentShareStateActive", IntegrationContentShareState::IntegrationContentShareStateActive)
        .export_values();

    py::enum_<IntegrationMeetingLayoutType>(m, "IntegrationMeetingLayoutType")
        .value("INTEGRATION_MEETING_FULL_SCREEN", IntegrationMeetingLayoutType::INTEGRATION_MEETING_FULL_SCREEN)
        .value("INTEGRATION_MEETING_SIDEBAR_LEFT", IntegrationMeetingLayoutType::INTEGRATION_MEETING_SIDEBAR_LEFT)
        .value("INTEGRATION_MEETING_SIDEBAR_RIGHT", IntegrationMeetingLayoutType::INTEGRATION_MEETING_SIDEBAR_RIGHT)
        .value("INTEGRATION_MEETING_GRID", IntegrationMeetingLayoutType::INTEGRATION_MEETING_GRID)
        .value("INTEGRATION_MEETING_TOP_BAR", IntegrationMeetingLayoutType::INTEGRATION_MEETING_TOP_BAR)
        .value("INTEGRATION_MEETING_BOTTOM_BAR", IntegrationMeetingLayoutType::INTEGRATION_MEETING_BOTTOM_BAR)
        .export_values();

    py::enum_<IntegrationMeetingJoinMethod>(m, "IntegrationMeetingJoinMethod")
        .value("IntegrationMeetingJoinMethodWebClient", IntegrationMeetingJoinMethod::IntegrationMeetingJoinMethodWebClient)
        .value("IntegrationMeetingJoinMethodSIP", IntegrationMeetingJoinMethod::IntegrationMeetingJoinMethodSIP)
        .export_values();

    // ===== Third Party Meeting Helper Structs =====
    py::class_<IntegrationMeetingInfo>(m, "IntegrationMeetingInfo")
        .def(py::init<>())
        .def_readwrite("provider", &IntegrationMeetingInfo::provider)
        .def_readwrite("meetingState", &IntegrationMeetingInfo::meetingState)
        .def_readwrite("meetingTitle", &IntegrationMeetingInfo::meetingTitle)
        .def_readwrite("meetingID", &IntegrationMeetingInfo::meetingID)
        .def_readwrite("isAudioMuted", &IntegrationMeetingInfo::isAudioMuted)
        .def_readwrite("isVideoMuted", &IntegrationMeetingInfo::isVideoMuted)
        .def_readwrite("meetingListItem", &IntegrationMeetingInfo::meetingListItem)
        .def_readwrite("isSupportCameraControl", &IntegrationMeetingInfo::isSupportCameraControl);

    py::class_<InterOperabilityInfo>(m, "InterOperabilityInfo")
        .def(py::init<>())
        .def_readwrite("meetingType", &InterOperabilityInfo::meetingType)
        .def_readwrite("supportJoinMeeting", &InterOperabilityInfo::supportJoinMeeting)
        .def_readwrite("supportJoinWebClient", &InterOperabilityInfo::supportJoinWebClient)
        .def_readwrite("supportSipJoin", &InterOperabilityInfo::supportSipJoin)
        .def_readwrite("supportPhoneJoin", &InterOperabilityInfo::supportPhoneJoin)
        .def_readwrite("preferredJoinMethod", &InterOperabilityInfo::preferredJoinMethod)
        .def_readwrite("isPexipEnabled", &InterOperabilityInfo::isPexipEnabled);

    py::class_<IntegrationMeetingErrorInfo>(m, "IntegrationMeetingErrorInfo")
        .def(py::init<>())
        .def_readwrite("errorCode", &IntegrationMeetingErrorInfo::errorCode)
        .def_readwrite("errorMessage", &IntegrationMeetingErrorInfo::errorMessage);

    py::class_<IntegrationMeetingProblemReportInfo>(m, "IntegrationMeetingProblemReportInfo")
        .def(py::init<>())
        .def_readwrite("correlationID", &IntegrationMeetingProblemReportInfo::correlationID);

    py::class_<IntegrationMeetingContentShareInfo>(m, "IntegrationMeetingContentShareInfo")
        .def(py::init<>())
        .def_readwrite("isHDMIContentShareAvailable", &IntegrationMeetingContentShareInfo::isHDMIContentShareAvailable)
        .def_readwrite("contentShareState", &IntegrationMeetingContentShareInfo::contentShareState);

    py::class_<IntegrationMeetingLayoutInfo>(m, "IntegrationMeetingLayoutInfo")
        .def(py::init<>())
        .def_readwrite("availableLayoutType", &IntegrationMeetingLayoutInfo::availableLayoutType)
        .def_readwrite("selectedLayoutType", &IntegrationMeetingLayoutInfo::selectedLayoutType);

    // ===== Third Party Meeting Helper =====
    py::class_<IThirdPartyMeetingHelper>(m, "IThirdPartyMeetingHelper")
        .def("CallOutPSTNUser", &IThirdPartyMeetingHelper::CallOutPSTNUser)
        .def("StartThirdPartyMeetingByPSTNCall", &IThirdPartyMeetingHelper::StartThirdPartyMeetingByPSTNCall)
        .def("SwitchPstnCallToMeeting", &IThirdPartyMeetingHelper::SwitchPstnCallToMeeting)
        .def("StartThirdPartyMeetingByRoomSystemCall", &IThirdPartyMeetingHelper::StartThirdPartyMeetingByRoomSystemCall)
        .def("StartIntegrationMeeting", &IThirdPartyMeetingHelper::StartIntegrationMeeting)
        .def("JoinIntegrationMeeting", &IThirdPartyMeetingHelper::JoinIntegrationMeeting)
        .def("RejoinIntegrationMeeting", &IThirdPartyMeetingHelper::RejoinIntegrationMeeting)
        .def("LeaveIntegrationMeeting", &IThirdPartyMeetingHelper::LeaveIntegrationMeeting)
        .def("MuteIntegrationAudio", &IThirdPartyMeetingHelper::MuteIntegrationAudio)
        .def("StopIntegrationVideo", &IThirdPartyMeetingHelper::StopIntegrationVideo)
        .def("StopIntegrationContentShare", &IThirdPartyMeetingHelper::StopIntegrationContentShare)
        .def("ChangeIntegrationLayout", &IThirdPartyMeetingHelper::ChangeIntegrationLayout)
        .def("GetInterOperabilityInfoByMeetingType", [](IThirdPartyMeetingHelper* self, ThirdPartyMeetingServiceProvider meetingType) {
            InterOperabilityInfo info;
            ZRCSDKError result = self->GetInterOperabilityInfoByMeetingType(meetingType, info);
            return py::make_tuple(result, info);
        });

    // ===== Phone Call Service =====
    py::class_<IPhoneCallService>(m, "IPhoneCallService")
        .def("AcceptIncomingSIPCall", &IPhoneCallService::AcceptIncomingSIPCall)
        .def("HoldAndAcceptIncomingSIPCall", &IPhoneCallService::HoldAndAcceptIncomingSIPCall)
        .def("EndAndAcceptIncomingSIPCall", &IPhoneCallService::EndAndAcceptIncomingSIPCall)
        .def("DeclineIncomingSIPCall", &IPhoneCallService::DeclineIncomingSIPCall)
        .def("AcceptSIPCallToMeeting", &IPhoneCallService::AcceptSIPCallToMeeting)
        .def("DeclineSIPCallToMeeting", &IPhoneCallService::DeclineSIPCallToMeeting)
        .def("CallSIP", &IPhoneCallService::CallSIP)
        .def("HangupSIPCall", &IPhoneCallService::HangupSIPCall)
        .def("MuteSIPCallAudio", &IPhoneCallService::MuteSIPCallAudio)
        .def("SendDTMFToSIPCall", &IPhoneCallService::SendDTMFToSIPCall)
        .def("HoldSIPCall", &IPhoneCallService::HoldSIPCall)
        .def("UnholdSIPCall", &IPhoneCallService::UnholdSIPCall)
        .def("MergeSIPCall", &IPhoneCallService::MergeSIPCall)
        .def("TransferSIPCall", &IPhoneCallService::TransferSIPCall)
        .def("CompleteWarmTransfer", &IPhoneCallService::CompleteWarmTransfer)
        .def("CancelWarmTransfer", &IPhoneCallService::CancelWarmTransfer)
        .def("UpgradeSIPCallToMeeting", &IPhoneCallService::UpgradeSIPCallToMeeting)
        .def("SetLocationPermissionEnable", &IPhoneCallService::SetLocationPermissionEnable)
        .def("GetLocationPermissionEnable", [](IPhoneCallService* self) {
            bool enable;
            ZRCSDKError result = self->GetLocationPermissionEnable(enable);
            return py::make_tuple(result, enable);
        })
        .def("GetSIPCallList", [](IPhoneCallService* self) {
            std::vector<SIPCallInfo> sipCalls;
            ZRCSDKError result = self->GetSIPCallList(sipCalls);
            return py::make_tuple(result, sipCalls);
        })
        .def("GetUnholdSIPCall", [](IPhoneCallService* self) {
            SIPCallInfo unholdCall;
            ZRCSDKError result = self->GetUnholdSIPCall(unholdCall);
            return py::make_tuple(result, unholdCall);
        });

    // ===== Pro AV Service Enums =====
    py::enum_<ProAVVideoNameStrapPosition>(m, "ProAVVideoNameStrapPosition")
        .value("ProAVVideoNameStrapPositionUnknown", ProAVVideoNameStrapPosition::ProAVVideoNameStrapPositionUnknown)
        .value("ProAVVideoNameStrapPositionLeft", ProAVVideoNameStrapPosition::ProAVVideoNameStrapPositionLeft)
        .value("ProAVVideoNameStrapPositionCenter", ProAVVideoNameStrapPosition::ProAVVideoNameStrapPositionCenter)
        .value("ProAVVideoNameStrapPositionRight", ProAVVideoNameStrapPosition::ProAVVideoNameStrapPositionRight)
        .export_values();

    py::enum_<ProAVUnassignedBehaviorType>(m, "ProAVUnassignedBehaviorType")
        .value("ProAVUnassignedBehaviorTypeOff", ProAVUnassignedBehaviorType::ProAVUnassignedBehaviorTypeOff)
        .value("ProAVUnassignedBehaviorTypeWallpaper", ProAVUnassignedBehaviorType::ProAVUnassignedBehaviorTypeWallpaper)
        .export_values();

    py::enum_<ProAVWallpaperRoomType>(m, "ProAVWallpaperRoomType")
        .value("ProAVWallpaperRoomTypeNone", ProAVWallpaperRoomType::ProAVWallpaperRoomTypeNone)
        .value("ProAVWallpaperRoomTypeMain", ProAVWallpaperRoomType::ProAVWallpaperRoomTypeMain)
        .value("ProAVWallpaperRoomTypeCZR", ProAVWallpaperRoomType::ProAVWallpaperRoomTypeCZR)
        .value("ProAVWallpaperRoomTypeCWB", ProAVWallpaperRoomType::ProAVWallpaperRoomTypeCWB)
        .export_values();

    py::enum_<ProAVGalleryDistributionMode>(m, "ProAVGalleryDistributionMode")
        .value("ProAVGalleryDistributionModeWaterfall", ProAVGalleryDistributionMode::ProAVGalleryDistributionModeWaterfall)
        .value("ProAVGalleryDistributionModeRoundRobin", ProAVGalleryDistributionMode::ProAVGalleryDistributionModeRoundRobin)
        .export_values();

    py::enum_<ProAVVideoLossBehaviorType>(m, "ProAVVideoLossBehaviorType")
        .value("ProAVVideoLossBehaviorTypeDefault", ProAVVideoLossBehaviorType::ProAVVideoLossBehaviorTypeDefault)
        .value("ProAVVideoLossBehaviorTypeBlackFrame", ProAVVideoLossBehaviorType::ProAVVideoLossBehaviorTypeBlackFrame)
        .value("ProAVVideoLossBehaviorTypeFreezeFrame", ProAVVideoLossBehaviorType::ProAVVideoLossBehaviorTypeFreezeFrame)
        .value("ProAVVideoLossBehaviorTypeWallpaper", ProAVVideoLossBehaviorType::ProAVVideoLossBehaviorTypeWallpaper)
        .export_values();

    // ===== Pro AV Service Structs =====
    py::class_<ProAVVideoOverlaySettings>(m, "ProAVVideoOverlaySettings")
        .def(py::init<>())
        .def_readwrite("isActiveSpeakerGreenOutlineEnabled", &ProAVVideoOverlaySettings::isActiveSpeakerGreenOutlineEnabled)
        .def_readwrite("isReactionIconsEnabled", &ProAVVideoOverlaySettings::isReactionIconsEnabled)
        .def_readwrite("isRaiseHandIconEnabled", &ProAVVideoOverlaySettings::isRaiseHandIconEnabled)
        .def_readwrite("isNameStrapEnabled", &ProAVVideoOverlaySettings::isNameStrapEnabled)
        .def_readwrite("position", &ProAVVideoOverlaySettings::position)
        .def_readwrite("isMuteIconEnabled", &ProAVVideoOverlaySettings::isMuteIconEnabled)
        .def_readwrite("isPollOverlayEnabled", &ProAVVideoOverlaySettings::isPollOverlayEnabled)
        .def_readwrite("galleryDistributionMode", &ProAVVideoOverlaySettings::galleryDistributionMode)
        .def_readwrite("maxGalleryPageCount", &ProAVVideoOverlaySettings::maxGalleryPageCount)
        .def_readwrite("elementScale", &ProAVVideoOverlaySettings::elementScale);

    py::class_<ProAVUnassignedBehavior>(m, "ProAVUnassignedBehavior")
        .def(py::init<>())
        .def_readwrite("unassignedType", &ProAVUnassignedBehavior::unassignedType)
        .def_readwrite("roomType", &ProAVUnassignedBehavior::roomType)
        .def_readwrite("wallpaperIndex", &ProAVUnassignedBehavior::wallpaperIndex);

    py::class_<ProAVVideoLossBehavior>(m, "ProAVVideoLossBehavior")
        .def(py::init<>())
        .def_readwrite("behaviorType", &ProAVVideoLossBehavior::behaviorType)
        .def_readwrite("wallpaperRoomType", &ProAVVideoLossBehavior::wallpaperRoomType)
        .def_readwrite("wallpaperIndex", &ProAVVideoLossBehavior::wallpaperIndex);

    // ===== Pro AV Helper Classes (opaque for now) =====
    py::class_<IDanteOutputHelper>(m, "IDanteOutputHelper");
    py::class_<IHWIOHelper>(m, "IHWIOHelper");

    // ===== Pro AV Service =====
    py::class_<IProAVService>(m, "IProAVService")
        .def("GetDanteOutputHelper", &IProAVService::GetDanteOutputHelper, py::return_value_policy::reference)
        .def("GetHWIOHelper", &IProAVService::GetHWIOHelper, py::return_value_policy::reference)
        .def("GetProAVVideoOverlaySettings", [](IProAVService* self) {
            ProAVVideoOverlaySettings settings;
            ZRCSDKError result = self->GetProAVVideoOverlaySettings(settings);
            return py::make_tuple(result, settings);
        })
        .def("EnableProAVVideoActiveSpeakerGreenOutline", &IProAVService::EnableProAVVideoActiveSpeakerGreenOutline)
        .def("EnableProAVVideoReactionIcons", &IProAVService::EnableProAVVideoReactionIcons)
        .def("EnableProAVVideoRaiseHandIcon", &IProAVService::EnableProAVVideoRaiseHandIcon)
        .def("EnableProAVVideoMuteIcon", &IProAVService::EnableProAVVideoMuteIcon)
        .def("EnableProAVVideoPollOverlay", &IProAVService::EnableProAVVideoPollOverlay)
        .def("EnableProAVVideoNameStrap", &IProAVService::EnableProAVVideoNameStrap)
        .def("SetProAVVideoNameStrapPosition", &IProAVService::SetProAVVideoNameStrapPosition)
        .def("SetProAVGalleryDistributionMode", &IProAVService::SetProAVGalleryDistributionMode)
        .def("SetProAVMaxGalleryPageCount", &IProAVService::SetProAVMaxGalleryPageCount)
        .def("SetProAVVideoElementScale", &IProAVService::SetProAVVideoElementScale)
        .def("SetProAVUnassignedBehavior", &IProAVService::SetProAVUnassignedBehavior)
        .def("GetProAVUnassignedBehavior", [](IProAVService* self) {
            ProAVUnassignedBehavior behavior;
            ZRCSDKError result = self->GetProAVUnassignedBehavior(behavior);
            return py::make_tuple(result, behavior);
        })
        .def("SetProAVVideoLossBehavior", &IProAVService::SetProAVVideoLossBehavior)
        .def("GetProAVVideoLossBehavior", [](IProAVService* self) {
            ProAVVideoLossBehavior behavior;
            ZRCSDKError result = self->GetProAVVideoLossBehavior(behavior);
            return py::make_tuple(result, behavior);
        });
}
