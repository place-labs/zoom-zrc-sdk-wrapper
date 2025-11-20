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
#include "ServiceComponents/IMeetingShareHelper.h"
#include "ServiceComponents/IMeetingViewLayoutHelper.h"
#include "ServiceComponents/INDIHelper.h"
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
        .def("GetMeetingListHelper", &IMeetingService::GetMeetingListHelper, py::return_value_policy::reference)
        .def("GetMeetingShareHelper", &IMeetingService::GetMeetingShareHelper, py::return_value_policy::reference)
        .def("GetMeetingViewLayoutHelper", &IMeetingService::GetMeetingViewLayoutHelper, py::return_value_policy::reference)
        .def("GetNDIHelper", &IMeetingService::GetNDIHelper, py::return_value_policy::reference);

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
    py::class_<VideoStatus>(m, "VideoStatus")
        .def(py::init<>())
        .def_readwrite("hasSource", &VideoStatus::hasSource)
        .def_readwrite("receiving", &VideoStatus::receiving)
        .def_readwrite("sending", &VideoStatus::sending)
        .def_readwrite("canControl", &VideoStatus::canControl);

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
}
