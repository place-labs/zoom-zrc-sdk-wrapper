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
#include "ServiceComponents/IMeetingAudioHelper.h"
#include "ServiceComponents/IMeetingVideoHelper.h"
#include "ServiceComponents/IMeetingControlHelper.h"
#include "ServiceComponents/IMeetingListHelper.h"
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

    // ===== Core SDK =====
    py::class_<IZRCSDK>(m, "IZRCSDK")
        .def_static("GetInstance", &IZRCSDK::GetInstance, py::return_value_policy::reference)
        .def_static("DestroyInstance", &IZRCSDK::DestroyInstance)
        .def("InitWebDomain", &IZRCSDK::InitWebDomain)
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
        .def("GetMeetingService", &IZoomRoomsService::GetMeetingService, py::return_value_policy::reference)
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
        });

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
        .def("JoinMeeting",
            static_cast<ZRCSDKError(IMeetingService::*)(const std::string&, bool)>(&IMeetingService::JoinMeeting),
            py::arg("meetingNumber"), py::arg("bringShareToMeeting") = false)
        .def("JoinMeetingWithURL", &IMeetingService::JoinMeetingWithURL, py::arg("url"), py::arg("bringShareToMeeting") = false)
        .def("JoinMeetingWithContactID", &IMeetingService::JoinMeetingWithContactID, py::arg("contactID"), py::arg("bringShareToMeeting") = false)
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
        .def("GetMeetingListHelper", &IMeetingService::GetMeetingListHelper, py::return_value_policy::reference);

    // ===== Meeting Audio Helper =====
    py::class_<IMeetingAudioHelper>(m, "IMeetingAudioHelper")
        .def("UpdateMyAudioStatus", &IMeetingAudioHelper::UpdateMyAudioStatus);

    // ===== Meeting Video Helper =====
    py::class_<IMeetingVideoHelper>(m, "IMeetingVideoHelper")
        .def("UpdateMyVideo", &IMeetingVideoHelper::UpdateMyVideo);

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
        .def("ListMeeting", &IMeetingListHelper::ListMeeting)
        .def("ScheduleCalendarEvent", &IMeetingListHelper::ScheduleCalendarEvent)
        .def("DeleteCalendarEvent", &IMeetingListHelper::DeleteCalendarEvent)
        .def("CheckInCalendarEvent", &IMeetingListHelper::CheckInCalendarEvent)
        .def("CheckOutCalendarEvent", &IMeetingListHelper::CheckOutCalendarEvent)
        .def("ShowUpcomingMeetingAlert", &IMeetingListHelper::ShowUpcomingMeetingAlert)
        .def("CloseUpcomingMeetingAlert", &IMeetingListHelper::CloseUpcomingMeetingAlert)
        .def("CloseAutoReleaseMeetingAlert", &IMeetingListHelper::CloseAutoReleaseMeetingAlert);
}
