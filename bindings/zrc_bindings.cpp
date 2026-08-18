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
#include "ServiceComponents/IWaitingRoomHelper.h"
#include "ServiceComponents/IClosedCaptionHelper.h"
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
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnGetDeviceManufacturer")) {
            try {
                return py_sink.attr("OnGetDeviceManufacturer")().cast<std::string>();
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnGetDeviceManufacturer");
            }
        }
        return "ZRC_Wrapper";
    }

    std::string OnGetDeviceModel() override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnGetDeviceModel")) {
            try {
                return py_sink.attr("OnGetDeviceModel")().cast<std::string>();
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnGetDeviceModel");
            }
        }
        return "v1.0";
    }

    std::string OnGetDeviceSerialNumber() override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnGetDeviceSerialNumber")) {
            try {
                return py_sink.attr("OnGetDeviceSerialNumber")().cast<std::string>();
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnGetDeviceSerialNumber");
            }
        }
        return "0000";
    }

    std::string OnGetDeviceMacAddress() override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnGetDeviceMacAddress")) {
            try {
                return py_sink.attr("OnGetDeviceMacAddress")().cast<std::string>();
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnGetDeviceMacAddress");
            }
        }
        return "00:00:00:00:00:00";
    }

    std::string OnGetDeviceIP() override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnGetDeviceIP")) {
            try {
                return py_sink.attr("OnGetDeviceIP")().cast<std::string>();
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnGetDeviceIP");
            }
        }
        return "0.0.0.0";
    }

    std::string OnGetFirmwareVersion() override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnGetFirmwareVersion")) {
            try {
                return py_sink.attr("OnGetFirmwareVersion")().cast<std::string>();
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnGetFirmwareVersion");
            }
        }
        return "1.0.0";
    }

    std::string OnGetAppName() override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnGetAppName")) {
            try {
                return py_sink.attr("OnGetAppName")().cast<std::string>();
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnGetAppName");
            }
        }
        return "ZRC_Wrapper";
    }

    std::string OnGetAppVersion() override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnGetAppVersion")) {
            try {
                return py_sink.attr("OnGetAppVersion")().cast<std::string>();
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnGetAppVersion");
            }
        }
        return "1.0.0";
    }

    std::string OnGetAppDeveloper() override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnGetAppDeveloper")) {
            try {
                return py_sink.attr("OnGetAppDeveloper")().cast<std::string>();
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnGetAppDeveloper");
            }
        }
        return "Custom";
    }

    std::string OnGetAppContact() override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnGetAppContact")) {
            try {
                return py_sink.attr("OnGetAppContact")().cast<std::string>();
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnGetAppContact");
            }
        }
        return "support@example.com";
    }

    std::string OnGetAppContentDirPath() override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnGetAppContentDirPath")) {
            try {
                return py_sink.attr("OnGetAppContentDirPath")().cast<std::string>();
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnGetAppContentDirPath");
            }
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
            try {
                py_sink.attr("OnPairRoomResult")(result);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnPairRoomResult");
            }
        }
    }

    void OnRoomUnpairedReason(RoomUnpairedReason reason) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnRoomUnpairedReason")) {
            try {
                py_sink.attr("OnRoomUnpairedReason")(reason);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnRoomUnpairedReason");
            }
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
            try {
                py_sink.attr("OnZRConnectionStateChanged")(connectionState);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnZRConnectionStateChanged");
            }
        }
    }

    void OnShutdownOSNot(bool restartOS) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnShutdownOSNot")) {
            try {
                py_sink.attr("OnShutdownOSNot")(restartOS);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnShutdownOSNot");
            }
        }
    }
    // Added in SDK 7.0+ (required override — no-op):
    void OnZRWarningNotification(const ZRWarningInfo& warningInfo) override {}
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
            try {
                py_sink.attr("OnUpdateMeetingList")(result, meetingList);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnUpdateMeetingList");
            }
        }
    }

    void OnUpdatedScheduleCalendarEventNotification(ScheduleCalendarEventResult scheduleResult) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnUpdatedScheduleCalendarEventNotification")) {
            try {
                py_sink.attr("OnUpdatedScheduleCalendarEventNotification")(scheduleResult);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnUpdatedScheduleCalendarEventNotification");
            }
        }
    }

    void OnUpdatedDeleteCalendarEventNotification(DeleteCalendarEventResult deleteResult) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnUpdatedDeleteCalendarEventNotification")) {
            try {
                py_sink.attr("OnUpdatedDeleteCalendarEventNotification")(deleteResult);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnUpdatedDeleteCalendarEventNotification");
            }
        }
    }

    void OnShowUpcomingMeetingAlertResult(int32_t result, const MeetingItem& meetingItem) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnShowUpcomingMeetingAlertResult")) {
            try {
                py_sink.attr("OnShowUpcomingMeetingAlertResult")(result, meetingItem);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnShowUpcomingMeetingAlertResult");
            }
        }
    }

    void OnCloseUpcomingMeetingAlertResult(int32_t result) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnCloseUpcomingMeetingAlertResult")) {
            try {
                py_sink.attr("OnCloseUpcomingMeetingAlertResult")(result);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnCloseUpcomingMeetingAlertResult");
            }
        }
    }

    void OnMeetingWillReleaseAutomatically(const MeetingItem& meetingItem) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnMeetingWillReleaseAutomatically")) {
            try {
                py_sink.attr("OnMeetingWillReleaseAutomatically")(meetingItem);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnMeetingWillReleaseAutomatically");
            }
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
            try {
                py_sink.attr("OnConsentNotification")(info);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnConsentNotification");
            }
        } 
    }
        
    void OnMeetingReminderNotification(const MeetingReminderContent& reminderContent) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnMeetingReminderNotification")) {
            try {
                py_sink.attr("OnMeetingReminderNotification")(reminderContent);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnMeetingReminderNotification");
            }
        }
    }
    
    void OnCustomizedReminderNotification(const CustomizedMeetingReminderContent& customizedContent) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnCustomizedReminderNotification")) {
            try {
                py_sink.attr("OnCustomizedReminderNotification")(customizedContent);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnCustomizedReminderNotification");
            }
        }
    }
    
    void OnCombinedConsentNotification(const CombinedConsent& combinedConsent) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnCombinedConsentNotification")) {
            try {
                py_sink.attr("OnCombinedConsentNotification")(combinedConsent);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnCombinedConsentNotification");
            }
        }
    }
    
    void OnPrivacyAlertNotification(PrivacyAlertAction action, PrivacyAlertType type, const DisclaimerPrivacy& message) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnPrivacyAlertNotification")) {
            try {
                py_sink.attr("OnPrivacyAlertNotification")(action, type, message);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnPrivacyAlertNotification");
            }
        }
    }
    
    void OnMessageEventNotification(MessageEvent messageEvent) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnMessageEventNotification")) {
            try {
                py_sink.attr("OnMessageEventNotification")(messageEvent);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnMessageEventNotification");
            }
        }
    }
    
    void OnInactiveDetectionNotification(bool isShowPrompt, time_t autoEndTime) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnInactiveDetectionNotification")) {
            try {
                py_sink.attr("OnInactiveDetectionNotification")(isShowPrompt, autoEndTime);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnInactiveDetectionNotification");
            }
        }
    }
    void OnConsolidatedCustomizedConsentNotification(const std::vector<DisclaimerPrivacy>& disclaimers, bool isAudioVideoBlocked) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnConsolidatedCustomizedConsentNotification")) {
            try {
                py_sink.attr("OnConsolidatedCustomizedConsentNotification")(disclaimers, isAudioVideoBlocked);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnConsolidatedCustomizedConsentNotification");
            }
        }
    }
};

// Trampoline for IMeetingServiceSink (forwards live-event callbacks to Python; others are no-ops)
class MeetingServiceSinkTrampoline : public IMeetingServiceSink {
private:
    py::object py_sink;
public:
    MeetingServiceSinkTrampoline(py::object obj) : py_sink(obj) {}

    void OnStartMeetingResult(int32_t result) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnStartMeetingResult")) {
            try {
                py_sink.attr("OnStartMeetingResult")(result);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnStartMeetingResult");
            }
        }
    }
    void OnStartPmiResult(int32_t result, const std::string& meetingNumber, MeetingType meetingType) override {}
    void OnStartPmiNotification(bool success) override {}
    void OnUpdateMeetingStatus(MeetingStatus meetingStatus) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnUpdateMeetingStatus")) {
            try {
                py_sink.attr("OnUpdateMeetingStatus")(meetingStatus);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnUpdateMeetingStatus");
            }
        }
    }
    void OnConfReadyNotification() override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnConfReadyNotification")) {
            try {
                py_sink.attr("OnConfReadyNotification")();
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnConfReadyNotification");
            }
        }
    }
    void OnUpdateMeetingInfoNotification(const MeetingInfo& meetingInfo) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnUpdateMeetingInfoNotification")) {
            try {
                py_sink.attr("OnUpdateMeetingInfoNotification")(meetingInfo);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnUpdateMeetingInfoNotification");
            }
        }
    }
    void OnExitMeetingNotification(int32_t result, ExitMeetingReason reason) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnExitMeetingNotification")) {
            try {
                py_sink.attr("OnExitMeetingNotification")(result, reason);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnExitMeetingNotification");
            }
        }
    }
    void OnMeetingErrorNotification(const MeetingErrorInfo& errorInfo) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnMeetingErrorNotification")) {
            try {
                py_sink.attr("OnMeetingErrorNotification")(errorInfo);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnMeetingErrorNotification");
            }
        }
    }
    void OnMeetingEndedNotification(const MeetingErrorInfo& errorInfo) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnMeetingEndedNotification")) {
            try {
                py_sink.attr("OnMeetingEndedNotification")(errorInfo);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnMeetingEndedNotification");
            }
        }
    }
    void OnReceiveMeetingInviteNotification(const MeetingInvitationInfo& invitation) override {}
    void OnAnswerMeetingInviteResponse(int32_t result, const MeetingInvitationInfo& invitation, bool accepted) override {}
    void OnTreatedMeetingInviteNotification(const MeetingInvitationInfo& invitation, bool accepted) override {}
    void OnStartMeetingWithHostKeyResult(int32_t result) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnStartMeetingWithHostKeyResult")) {
            try {
                py_sink.attr("OnStartMeetingWithHostKeyResult")(result);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnStartMeetingWithHostKeyResult");
            }
        }
    }
    void OnUpdateDataCenterRegionNotification(const DataCenterRegion& dcRegion) override {}
    void OnUpdateE2ESecurityCode(const E2ESecurityCode& code) override {}
    void OnBandwidthLimitNotification(const BandwidthLimitInfo& info) override {}
    void OnSendMeetingInviteEmailNotification(int32_t result) override {}
    void OnSetRoomTempDisplayNameNotification(bool isShow) override {}
    void OnMeetingNeedsPasswordNotification(bool showPasswordDialog, bool wrongAndRetry, const ConfDeviceLockStatus& lockStatus) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnMeetingNeedsPasswordNotification")) {
            try {
                py_sink.attr("OnMeetingNeedsPasswordNotification")(showPasswordDialog, wrongAndRetry, lockStatus);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnMeetingNeedsPasswordNotification");
            }
        }
    }
    void OnConfDeviceLockStatusNotification(const ConfDeviceLockStatus& status) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnConfDeviceLockStatusNotification")) {
            try {
                py_sink.attr("OnConfDeviceLockStatusNotification")(status);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnConfDeviceLockStatusNotification");
            }
        }
    }
    void OnJBHWaitingHostNotification(bool showWaitForHostDialog, WaitingHostReason reason) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnJBHWaitingHostNotification")) {
            try {
                py_sink.attr("OnJBHWaitingHostNotification")(showWaitForHostDialog, reason);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnJBHWaitingHostNotification");
            }
        }
    }
    void OnE2eeMeetingStatusNotification(const E2eeMeetingStatus& e2eeMeetingStatus) override {}
    void OnMeshInfoNotification(const MeshInfoNotification& meshInfo) override {}
    void OnMeetingWillStopAutomatically() override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnMeetingWillStopAutomatically")) {
            try {
                py_sink.attr("OnMeetingWillStopAutomatically")();
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnMeetingWillStopAutomatically");
            }
        }
    }
    void OnExtendMeetingResult(int32_t extendMins) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnExtendMeetingResult")) {
            try {
                py_sink.attr("OnExtendMeetingResult")(extendMins);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnExtendMeetingResult");
            }
        }
    }
    void OnConfirmPersonalLink(const std::string& personalLink) override {}
};

// Trampoline for IParticipantHelperSink (forwards live-event callbacks to Python; others are no-ops)
class ParticipantHelperSinkTrampoline : public IParticipantHelperSink {
private:
    py::object py_sink;
public:
    ParticipantHelperSinkTrampoline(py::object obj) : py_sink(obj) {}

    void OnInitMeetingParticipants(const std::vector<MeetingParticipant>& participants, int32_t totalParticipantsCount, bool needCleanUpUserList, ConfSessionType session) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnInitMeetingParticipants")) {
            try {
                py_sink.attr("OnInitMeetingParticipants")(participants, totalParticipantsCount, needCleanUpUserList, session);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnInitMeetingParticipants");
            }
        }
    }
    void OnUserJoin(const std::vector<MeetingParticipant>& participants, ConfSessionType session) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnUserJoin")) {
            try {
                py_sink.attr("OnUserJoin")(participants, session);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnUserJoin");
            }
        }
    }
    void OnUserLeave(const std::vector<MeetingParticipant>& participants, ConfSessionType session) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnUserLeave")) {
            try {
                py_sink.attr("OnUserLeave")(participants, session);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnUserLeave");
            }
        }
    }
    void OnUserUpdate(const std::vector<MeetingParticipant>& participants, ConfSessionType session) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnUserUpdate")) {
            try {
                py_sink.attr("OnUserUpdate")(participants, session);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnUserUpdate");
            }
        }
    }
    void OnHostChangedNotification(int32_t hostUserID, bool amIHost, ConfSessionType session) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnHostChangedNotification")) {
            try {
                py_sink.attr("OnHostChangedNotification")(hostUserID, amIHost, session);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnHostChangedNotification");
            }
        }
    }
    void OnMeetingParticipantsChanged(ConfSessionType session) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnMeetingParticipantsChanged")) {
            try {
                py_sink.attr("OnMeetingParticipantsChanged")(session);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnMeetingParticipantsChanged");
            }
        }
    }
    void OnUpdateHideProfilePictures(bool isHideProfilePictures) override {}
    void OnHideFullRoomViewNotification(const std::vector<int32_t>& userIDs) override {}
    void OnClaimHostNotification(ClaimHostResult result) override {}
    void OnUpdateSharingAnnotationInfo(bool support, bool enable) override {}
    void OnAllowAttendeesRenameThemselvesNotification(bool allow) override {}
    void OnAllowAttendeesShareWhiteboardsNotification(bool isSupported, bool isAllowed) override {}
    void OnAllowRaiseHandForAttendeeNotification(bool canRaiseHandForAttendee) override {}
    void OnUpdateOnZRWUserChangeNotification(ZRWUserChangeType type, int32_t zrwUserID) override {}
    void OnUpdateHasRemoteControlAdmin(bool isAdminExist) override {}
    void OnUpdateHasRemoteControlAssistant(bool isAssistantExist) override {}
    void OnDownloadingFinished(const std::string& localFilePath, uint32_t result) override {}
    // Added in SDK 7.0+ (required override — no-op):
    void OnShowParticipantLocalTimeNotification(bool isShowing) override {}
};

class WaitingRoomHelperSinkTrampoline : public IWaitingRoomHelperSink {
private:
    py::object py_sink;
public:
    WaitingRoomHelperSinkTrampoline(py::object obj) : py_sink(obj) {}

    void OnInSilentModeNotification(const InSilentModeInfo& info) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnInSilentModeNotification")) {
            try {
                py_sink.attr("OnInSilentModeNotification")(info);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnInSilentModeNotification");
            }
        }
    }
    void OnEnableWaitingRoomOnEntryNotification(bool isEnable) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnEnableWaitingRoomOnEntryNotification")) {
            try {
                py_sink.attr("OnEnableWaitingRoomOnEntryNotification")(isEnable);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnEnableWaitingRoomOnEntryNotification");
            }
        }
    }
    void OnUpdateAdmitGuestEnableNotification(bool isEnabled) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnUpdateAdmitGuestEnableNotification")) {
            try {
                py_sink.attr("OnUpdateAdmitGuestEnableNotification")(isEnabled);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnUpdateAdmitGuestEnableNotification");
            }
        }
    }
};

class MeetingControlHelperSinkTrampoline : public IMeetingControlHelperSink {
private:
    py::object py_sink;
public:
    MeetingControlHelperSinkTrampoline(py::object obj) : py_sink(obj) {}

    void OnUpdateMeetingLockStatus(bool meetingLocked) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnUpdateMeetingLockStatus")) {
            try {
                py_sink.attr("OnUpdateMeetingLockStatus")(meetingLocked);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnUpdateMeetingLockStatus");
            }
        }
    }
    void OnUpdateFocusModeOptionsNotification(bool enable, FocusModeStatus status) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnUpdateFocusModeOptionsNotification")) {
            try {
                py_sink.attr("OnUpdateFocusModeOptionsNotification")(enable, status);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnUpdateFocusModeOptionsNotification");
            }
        }
    }
    void OnUpdateLiveStreamStatus(const LiveStreamStatus& status) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnUpdateLiveStreamStatus")) {
            try {
                py_sink.attr("OnUpdateLiveStreamStatus")(status);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnUpdateLiveStreamStatus");
            }
        }
    }
    void OnArchivingStatusNotification(bool isInProgress) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnArchivingStatusNotification")) {
            try {
                py_sink.attr("OnArchivingStatusNotification")(isInProgress);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnArchivingStatusNotification");
            }
        }
    }
    void OnShowArchivingStatusFailNotification(bool showArchivingFail) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnShowArchivingStatusFailNotification")) {
            try {
                py_sink.attr("OnShowArchivingStatusFailNotification")(showArchivingFail);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnShowArchivingStatusFailNotification");
            }
        }
    }
    void OnSmartSummaryOn(bool summaryOn, bool hasSetEmail) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnSmartSummaryOn")) {
            try {
                py_sink.attr("OnSmartSummaryOn")(summaryOn, hasSetEmail);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnSmartSummaryOn");
            }
        }
    }
    void OnReceiveAICompanionRequest(const AICompanionRequestInfo& info) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnReceiveAICompanionRequest")) {
            try {
                py_sink.attr("OnReceiveAICompanionRequest")(info);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnReceiveAICompanionRequest");
            }
        }
    }
    void OnAICompanionStatusNeedConfirm(const AICompanionStatusInfo& info) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnAICompanionStatusNeedConfirm")) {
            try {
                py_sink.attr("OnAICompanionStatusNeedConfirm")(info);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnAICompanionStatusNeedConfirm");
            }
        }
    }
    void OnShowSidePanel(bool isShow, PanelType currentPanel) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnShowSidePanel")) {
            try {
                py_sink.attr("OnShowSidePanel")(isShow, currentPanel);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnShowSidePanel");
            }
        }
    }
    // Unforwarded callbacks (required overrides — no-ops):
    void OnUpdateIsDisplayTopBannerNotification(bool isDisplayTopBanner) override {}
    void OnHiFiMusicModeNotification(bool isAllow, bool isEnable) override {}
    void OnHasAppSignalingChanged(bool hasNewAppSignaling) override {}
    void OnUpdateSignalingApps(const SignalingAppList& list) override {}
    void OnUpdateAccessedUsers(const SignalingAppAccessedUserList& list) override {}
    void OnUpdateAppPermissionLink(const SignalingAppPermissionLink& link) override {}
    void OnZoomPhoneACRStatusNotification(bool isInProgress) override {}
    void OnSetMeetingSummaryNotificationEmailNotification(int32_t result) override {}
    void OnUpdateMeetingQueryBaseInfo(const MeetingQueryInfo& info) override {}
    void OnChangeMeetingQueryPrivilegeSettingID(int32_t settingID) override {}
    void OnUpdateMeetingMynotesSetting(const MeetingMynotesSetting& setting) override {}
};

class RecordingHelperSinkTrampoline : public IRecordingHelperSink {
private:
    py::object py_sink;
public:
    RecordingHelperSinkTrampoline(py::object obj) : py_sink(obj) {}

    void OnUpdateMeetingRecordingInfo(const MeetingRecordingInfo& recordingInfo) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnUpdateMeetingRecordingInfo")) {
            try {
                py_sink.attr("OnUpdateMeetingRecordingInfo")(recordingInfo);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnUpdateMeetingRecordingInfo");
            }
        }
    }
    void OnMeetingCloudRecordingErrorNotification(bool show, MeetingRecordingError errorCode, bool hasCMREdit, uint64_t gracePeriodDate) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnMeetingCloudRecordingErrorNotification")) {
            try {
                py_sink.attr("OnMeetingCloudRecordingErrorNotification")(show, errorCode, hasCMREdit, gracePeriodDate);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnMeetingCloudRecordingErrorNotification");
            }
        }
    }
    // Second (2-arg) overload forwarded under a distinct Python name.
    void OnMeetingCloudRecordingErrorNotification(bool result, const std::string& reason) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnMeetingCloudRecordingErrorReason")) {
            try {
                py_sink.attr("OnMeetingCloudRecordingErrorReason")(result, reason);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnMeetingCloudRecordingErrorReason");
            }
        }
    }
    void OnNeedPromptStartRecordingDisclaimerUpdate(bool need) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnNeedPromptStartRecordingDisclaimerUpdate")) {
            try {
                py_sink.attr("OnNeedPromptStartRecordingDisclaimerUpdate")(need);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnNeedPromptStartRecordingDisclaimerUpdate");
            }
        }
    }
    void OnQueryMeetingCloudRecordingNotification(MeetingRecordingError errorCode, bool hasCMREdit) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnQueryMeetingCloudRecordingNotification")) {
            try {
                py_sink.attr("OnQueryMeetingCloudRecordingNotification")(errorCode, hasCMREdit);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnQueryMeetingCloudRecordingNotification");
            }
        }
    }
    void OnUpdateMeetingUserRecordingStatus(int32_t userID, bool canRecord, bool isRecording, bool isLocalRecordingDisabled) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnUpdateMeetingUserRecordingStatus")) {
            try {
                py_sink.attr("OnUpdateMeetingUserRecordingStatus")(userID, canRecord, isRecording, isLocalRecordingDisabled);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnUpdateMeetingUserRecordingStatus");
            }
        }
    }
    void OnSetRecordingNotificationEmailNotification(int32_t result) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnSetRecordingNotificationEmailNotification")) {
            try {
                py_sink.attr("OnSetRecordingNotificationEmailNotification")(result);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnSetRecordingNotificationEmailNotification");
            }
        }
    }
    void OnSetMeetingRecordingResult(int32_t result, const std::string& recordingNotificationEmail, RecordingRequestType type) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnSetMeetingRecordingResult")) {
            try {
                py_sink.attr("OnSetMeetingRecordingResult")(result, recordingNotificationEmail, type);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnSetMeetingRecordingResult");
            }
        }
    }
    void OnUpdateRecordingPermission(const std::vector<RecordPermissionInfo>& info) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnUpdateRecordingPermission")) {
            try {
                py_sink.attr("OnUpdateRecordingPermission")(info);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnUpdateRecordingPermission");
            }
        }
    }
    void OnReceiveRecordingRequest(const RecordingRequestInfo& info) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnReceiveRecordingRequest")) {
            try {
                py_sink.attr("OnReceiveRecordingRequest")(info);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnReceiveRecordingRequest");
            }
        }
    }
};

class MeetingAudioHelperSinkTrampoline : public IMeetingAudioHelperSink {
private:
    py::object py_sink;
public:
    MeetingAudioHelperSinkTrampoline(py::object obj) : py_sink(obj) {}

    void OnUpdateMyAudioStatus(const AudioStatus& audioStatus) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnUpdateMyAudioStatus")) {
            try {
                py_sink.attr("OnUpdateMyAudioStatus")(audioStatus);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnUpdateMyAudioStatus");
            }
        }
    }
    void OnMuteUserAudioNotification(int32_t userID, const AudioStatus& audioStatus) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnMuteUserAudioNotification")) {
            try {
                py_sink.attr("OnMuteUserAudioNotification")(userID, audioStatus);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnMuteUserAudioNotification");
            }
        }
    }
    void OnMuteOnEntryNotification(bool isMuteOnEntry) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnMuteOnEntryNotification")) {
            try {
                py_sink.attr("OnMuteOnEntryNotification")(isMuteOnEntry);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnMuteOnEntryNotification");
            }
        }
    }
    void OnAskUnmuteAudioByHostNotification(bool show, AskUnmuteAudioByHostType type) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnAskUnmuteAudioByHostNotification")) {
            try {
                py_sink.attr("OnAskUnmuteAudioByHostNotification")(show, type);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnAskUnmuteAudioByHostNotification");
            }
        }
    }
    void OnAllowAttendeesUnmuteThemselvesNotification(bool canAttendeesUnmuteThemselves) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnAllowAttendeesUnmuteThemselvesNotification")) {
            try {
                py_sink.attr("OnAllowAttendeesUnmuteThemselvesNotification")(canAttendeesUnmuteThemselves);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnAllowAttendeesUnmuteThemselvesNotification");
            }
        }
    }
    // Unforwarded (required overrides — no-ops):
    void OnEnablePlayJoinOrLeaveChimeNotification(bool enable) override {}
    void OnUpdateAudioTroubleShootingStatus(const AudioTroubleShootingStatus& status) override {}
    void OnFEACApproveNotification(int32_t farEndUserID, const std::string& farEndUserName) override {}
    void OnFEACDeclineNotification(int32_t farEndUserID, const std::string& farEndUserName) override {}
    void OnFEACTakeOverNotification(int32_t farEndUserID, const std::string& farEndUserName, int32_t controllingUserID, const std::string& controllingUserName) override {}
    void OnFEACMicListChangedNotification(int32_t farEndUserID, const std::vector<FarEndAudioDeviceInfo>& micList) override {}
    void OnFEACSpeakerListChangedNotification(int32_t farEndUserID, const std::vector<FarEndAudioDeviceInfo>& speakerList) override {}
    void OnFEACMuteStateChangedNotification(int32_t farEndUserID, bool muteState) override {}
    void OnFEACUnmuteDisabledByHostNotification(int32_t farEndUserID) override {}
    void OnFEACRequestNotification(int32_t requesterUserID, const std::string& requesterUserName) override {}
    void OnFEACGiveUpNotification(int32_t requesterUserID, const std::string& requesterUserName) override {}
    void OnFEACApproveControlRequestNotification(int32_t requesterUserID) override {}
    void OnFEACDeclineControlRequestNotification(int32_t requesterUserID) override {}
};

class MeetingVideoHelperSinkTrampoline : public IMeetingVideoHelperSink {
private:
    py::object py_sink;
public:
    MeetingVideoHelperSinkTrampoline(py::object obj) : py_sink(obj) {}

    void OnUpdateMyVideoNotification(const VideoStatus& videoStatus) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnUpdateMyVideoNotification")) {
            try {
                py_sink.attr("OnUpdateMyVideoNotification")(videoStatus);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnUpdateMyVideoNotification");
            }
        }
    }
    void OnMuteUserVideoNotification(int32_t userID, const VideoStatus& videoStatus) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnMuteUserVideoNotification")) {
            try {
                py_sink.attr("OnMuteUserVideoNotification")(userID, videoStatus);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnMuteUserVideoNotification");
            }
        }
    }
    void OnAskStartVideoByHostNotification(int32_t userID) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnAskStartVideoByHostNotification")) {
            try {
                py_sink.attr("OnAskStartVideoByHostNotification")(userID);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnAskStartVideoByHostNotification");
            }
        }
    }
    void OnSpotlightStatusNotification(const SpotlightStatus& spotlightStatus) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnSpotlightStatusNotification")) {
            try {
                py_sink.attr("OnSpotlightStatusNotification")(spotlightStatus);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnSpotlightStatusNotification");
            }
        }
    }
    void OnUpdateAllowAttendeesStartVideo(bool allow) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnUpdateAllowAttendeesStartVideo")) {
            try {
                py_sink.attr("OnUpdateAllowAttendeesStartVideo")(allow);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnUpdateAllowAttendeesStartVideo");
            }
        }
    }
    // Unforwarded (deep-nested settings structs — required overrides, no-ops):
    void OnUpdateScreenStatusForPinNotification(const std::vector<ScreenStatusForPin>& pinStatusList, PinShareWarningType warningType) override {}
    void OnMyVideoSettingsNotification(const MyVideoSettings& settings) override {}
    void OnMyMeetingVideoSettingsNotification(const MyMeetingVideoSettings& settings) override {}
};

class MeetingShareHelperSinkTrampoline : public IMeetingShareHelperSink {
private:
    py::object py_sink;
public:
    MeetingShareHelperSinkTrampoline(py::object obj) : py_sink(obj) {}

    void OnSharingStatusNotification(const SharingStatus& status) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnSharingStatusNotification")) {
            try {
                py_sink.attr("OnSharingStatusNotification")(status);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnSharingStatusNotification");
            }
        }
    }
    void OnShareSettingNotification(const ShareSetting& setting) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnShareSettingNotification")) {
            try {
                py_sink.attr("OnShareSettingNotification")(setting);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnShareSettingNotification");
            }
        }
    }
    void OnSharingSourceNotification(const std::vector<ShareSource>& zrShareSources, const std::vector<ShareSource>& zrwShareSources) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnSharingSourceNotification")) {
            try {
                py_sink.attr("OnSharingSourceNotification")(zrShareSources, zrwShareSources);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnSharingSourceNotification");
            }
        }
    }
    void OnIncomingMeetingShareNotification(const IncomingMeetingShareNot& noti) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnIncomingMeetingShareNotification")) {
            try {
                py_sink.attr("OnIncomingMeetingShareNotification")(noti);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnIncomingMeetingShareNotification");
            }
        }
    }
    void OnUpdateLocalViewStatus(bool isOn) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnUpdateLocalViewStatus")) {
            try {
                py_sink.attr("OnUpdateLocalViewStatus")(isOn);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnUpdateLocalViewStatus");
            }
        }
    }
    void OnStartLocalPresentResult(bool isSharingMeeting, SharingInstructionDisplayState displayState) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnStartLocalPresentResult")) {
            try {
                py_sink.attr("OnStartLocalPresentResult")(isSharingMeeting, displayState);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnStartLocalPresentResult");
            }
        }
    }
    // Unforwarded (required overrides — no-ops):
    void OnStartLocalPresentNotification(const LocalPresentationInfo& info) override {}
    void OnSwitchToNormalMeetingResult(int result) override {}
    void OnShowSharingInstructionResult(int result, bool show, SharingInstructionDisplayState instructionState) override {}
    void OnUpdateAirPlayBlackMagicStatus(const AirplayBlackMagicStatus& status) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnUpdateAirPlayBlackMagicStatus")) {
            try {
                py_sink.attr("OnUpdateAirPlayBlackMagicStatus")(status);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnUpdateAirPlayBlackMagicStatus");
            }
        }
    }
    void OnUpdateCameraSharingStatus(const CameraSharingStatus& status) override {}
    void OnHDMI60FPSShareInfoNotification(bool isAllow, bool isOn, HDMI60FPSShareDisableReason disableReason) override {}
    void OnHDMIShareResolutionAndFrameRateNotification(const std::vector<HDMIShareResolutionAndFrameRateOption>& selectionList, uint32_t selectedType) override {}
    void OnLocalHDMIShareAudioPlaybackNotification(bool isEnabled) override {}
    void OnUpdateClassicWhiteboardShareStatusNotification(const ClassicWhiteboardShareStatus& status) override {}
    void OnZRWSharingStatusNotification(const ZRWSharingStatus& status) override {}
    void OnSlideControlNotification(const std::vector<SlideControlInfo>& slideControlInfos) override {}
    void OnDocsShareSettingsNotification(const DocsShareSettingsInfo& info) override {}
};

class PhoneCallServiceSinkTrampoline : public IPhoneCallServiceSink {
private:
    py::object py_sink;
public:
    PhoneCallServiceSinkTrampoline(py::object obj) : py_sink(obj) {}

    void OnReceiveIncomingSIPCallNotification(const SIPCallInfo& sipCallInfo) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnReceiveIncomingSIPCallNotification")) {
            try {
                py_sink.attr("OnReceiveIncomingSIPCallNotification")(sipCallInfo);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnReceiveIncomingSIPCallNotification");
            }
        }
    }
    void OnUpdateSIPCallStatusNotification(const SIPCallInfo& sipCallInfo) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnUpdateSIPCallStatusNotification")) {
            try {
                py_sink.attr("OnUpdateSIPCallStatusNotification")(sipCallInfo);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnUpdateSIPCallStatusNotification");
            }
        }
    }
    void OnUpdateSIPServiceStatusNotification(const SIPService& sipService) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnUpdateSIPServiceStatusNotification")) {
            try {
                py_sink.attr("OnUpdateSIPServiceStatusNotification")(sipService);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnUpdateSIPServiceStatusNotification");
            }
        }
    }
    void OnTerminateSIPCallNotification(SIPCallTerminateReason reason, const SIPCallInfo& sipCallInfo) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnTerminateSIPCallNotification")) {
            try {
                py_sink.attr("OnTerminateSIPCallNotification")(reason, sipCallInfo);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnTerminateSIPCallNotification");
            }
        }
    }
    void OnUpdateSIPCallAudioStatusNotification(bool muted) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnUpdateSIPCallAudioStatusNotification")) {
            try {
                py_sink.attr("OnUpdateSIPCallAudioStatusNotification")(muted);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnUpdateSIPCallAudioStatusNotification");
            }
        }
    }
    void OnAnswerSIPCallResult(bool succeeded, const SIPCallInfo& sipCallInfo, bool accepted) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnAnswerSIPCallResult")) {
            try {
                py_sink.attr("OnAnswerSIPCallResult")(succeeded, sipCallInfo, accepted);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnAnswerSIPCallResult");
            }
        }
    }
    void OnUpgradeSIPCallToMeetingResult(bool succeeded, const SIPCallInfo& sipCallInfo) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnUpgradeSIPCallToMeetingResult")) {
            try {
                py_sink.attr("OnUpgradeSIPCallToMeetingResult")(succeeded, sipCallInfo);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnUpgradeSIPCallToMeetingResult");
            }
        }
    }
    void OnUpgradeSIPCallToMeetingNotification(bool succeeded, const SIPCallInfo& sipCallInfo) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnUpgradeSIPCallToMeetingNotification")) {
            try {
                py_sink.attr("OnUpgradeSIPCallToMeetingNotification")(succeeded, sipCallInfo);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnUpgradeSIPCallToMeetingNotification");
            }
        }
    }
    void OnTransferSIPCallResult(bool succeeded, const SIPCallInfo& sipCallInfo, const SIPCallTransferInfo& transferInfo) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnTransferSIPCallResult")) {
            try {
                py_sink.attr("OnTransferSIPCallResult")(succeeded, sipCallInfo, transferInfo);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnTransferSIPCallResult");
            }
        }
    }
    void OnTransferSIPCallNotification(bool succeeded, const SIPCallInfo& sipCallInfo) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnTransferSIPCallNotification")) {
            try {
                py_sink.attr("OnTransferSIPCallNotification")(succeeded, sipCallInfo);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnTransferSIPCallNotification");
            }
        }
    }
    // Unforwarded (required overrides — no-ops):
    void OnAcceptSIPCallToMeetingResult(bool succeeded, const SIPCallInfo& sipCallInfo) override {}
    void OnUpdateSIPCallPeerResult(bool succeeded, const SIPCallInfo& sipCallInfo) override {}
    void OnUpdateSIPCallAudioResult(bool succeeded) override {}
    void OnTreatSIPCallNotification(bool accepted, const SIPCallInfo& sipCallInfo) override {}
    void OnInviteSIPCallToJoinMeetingNotification(const SIPCallInfo& sipCallInfo) override {}
};

class MeetingViewLayoutHelperSinkTrampoline : public IMeetingViewLayoutHelperSink {
private:
    py::object py_sink;
public:
    MeetingViewLayoutHelperSinkTrampoline(py::object obj) : py_sink(obj) {}

    void OnUpdateWallviewStyleNotification(const WallViewStyleStatus& status) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnUpdateWallviewStyleNotification")) {
            try {
                py_sink.attr("OnUpdateWallviewStyleNotification")(status);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnUpdateWallviewStyleNotification");
            }
        }
    }
    void OnUpdateVideoThumbInfo(const VideoThumbInfo& info) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnUpdateVideoThumbInfo")) {
            try {
                py_sink.attr("OnUpdateVideoThumbInfo")(info);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnUpdateVideoThumbInfo");
            }
        }
    }
    void OnUpdateVideoPageStatusNotification(const VideoPageStatus& noti) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnUpdateVideoPageStatusNotification")) {
            try {
                py_sink.attr("OnUpdateVideoPageStatusNotification")(noti);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnUpdateVideoPageStatusNotification");
            }
        }
    }
    void OnUpdateIsNonVideoParticipantsShowedNotification(bool isShowNonVideoParticipants) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnUpdateIsNonVideoParticipantsShowedNotification")) {
            try {
                py_sink.attr("OnUpdateIsNonVideoParticipantsShowedNotification")(isShowNonVideoParticipants);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnUpdateIsNonVideoParticipantsShowedNotification");
            }
        }
    }
    void OnUpdateScreenLayoutStatus(const ScreenLayoutStatus& status) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnUpdateScreenLayoutStatus")) {
            try {
                py_sink.attr("OnUpdateScreenLayoutStatus")(status);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnUpdateScreenLayoutStatus");
            }
        }
    }
    void OnConfidenceMonitorNotification(const ConfidenceMonitorInfo& info) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnConfidenceMonitorNotification")) {
            try {
                py_sink.attr("OnConfidenceMonitorNotification")(info);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnConfidenceMonitorNotification");
            }
        }
    }
    void OnDynamicLayoutOptionNotification(DynamicLayoutType layout) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnDynamicLayoutOptionNotification")) {
            try {
                py_sink.attr("OnDynamicLayoutOptionNotification")(layout);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnDynamicLayoutOptionNotification");
            }
        }
    }
    void OnThumbnailsPositionNotification(ThumbnailsPositionType type) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnThumbnailsPositionNotification")) {
            try {
                py_sink.attr("OnThumbnailsPositionNotification")(type);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnThumbnailsPositionNotification");
            }
        }
    }
    void OnChangeAttendeeViewNotification(AttendeeViewLayoutType layout) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnChangeAttendeeViewNotification")) {
            try {
                py_sink.attr("OnChangeAttendeeViewNotification")(layout);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnChangeAttendeeViewNotification");
            }
        }
    }
    void OnVideoOrderNotification(const VideoOrderInfo& videoOrderInfo) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnVideoOrderNotification")) {
            try {
                py_sink.attr("OnVideoOrderNotification")(videoOrderInfo);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnVideoOrderNotification");
            }
        }
    }
    // Unforwarded (required overrides — no-ops):
    void OnUpdateShowUpTo49PerPageInGallery(bool enabled) override {}
    void OnAutoSwitchSpeakerNotification(bool support, bool enable) override {}
    void OnAttendeeViewLayoutEnableShareContentOnlyNotification(bool isSupport, bool isEnable) override {}
    void OnUpdateGalleryGridSelectionNotification(bool isEnabled, uint32_t row, uint32_t column) override {}
};

class SettingServiceSinkTrampoline : public ISettingServiceSink {
private:
    py::object py_sink;
public:
    SettingServiceSinkTrampoline(py::object obj) : py_sink(obj) {}

    void OnMicrophoneListChanged(const std::vector<Device>& microphones) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnMicrophoneListChanged")) {
            try {
                py_sink.attr("OnMicrophoneListChanged")(microphones);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnMicrophoneListChanged");
            }
        }
    }
    void OnSpeakerListChanged(const std::vector<Device>& speakers) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnSpeakerListChanged")) {
            try {
                py_sink.attr("OnSpeakerListChanged")(speakers);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnSpeakerListChanged");
            }
        }
    }
    void OnCameraListChanged(const std::vector<Device>& cameras) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnCameraListChanged")) {
            try {
                py_sink.attr("OnCameraListChanged")(cameras);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnCameraListChanged");
            }
        }
    }
    void OnUpdateCOMList(const std::vector<Device>& comList) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnUpdateCOMList")) {
            try {
                py_sink.attr("OnUpdateCOMList")(comList);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnUpdateCOMList");
            }
        }
    }
    void OnCurrentMicrophoneChanged(bool exist, const Device& microphone) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnCurrentMicrophoneChanged")) {
            try {
                py_sink.attr("OnCurrentMicrophoneChanged")(exist, microphone);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnCurrentMicrophoneChanged");
            }
        }
    }
    void OnCurrentSpeakerChanged(bool exist, const Device& speaker) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnCurrentSpeakerChanged")) {
            try {
                py_sink.attr("OnCurrentSpeakerChanged")(exist, speaker);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnCurrentSpeakerChanged");
            }
        }
    }
    void OnCurrentCameraChanged(bool exist, const Device& camera) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnCurrentCameraChanged")) {
            try {
                py_sink.attr("OnCurrentCameraChanged")(exist, camera);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnCurrentCameraChanged");
            }
        }
    }
    void OnCurrentMicrophoneVolumeChanged(float volume) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnCurrentMicrophoneVolumeChanged")) {
            try {
                py_sink.attr("OnCurrentMicrophoneVolumeChanged")(volume);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnCurrentMicrophoneVolumeChanged");
            }
        }
    }
    void OnCurrentSpeakerVolumeChanged(float volume) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnCurrentSpeakerVolumeChanged")) {
            try {
                py_sink.attr("OnCurrentSpeakerVolumeChanged")(volume);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnCurrentSpeakerVolumeChanged");
            }
        }
    }
    void OnCurrentSelectedMicrophoneMuted(bool muted) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnCurrentSelectedMicrophoneMuted")) {
            try {
                py_sink.attr("OnCurrentSelectedMicrophoneMuted")(muted);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnCurrentSelectedMicrophoneMuted");
            }
        }
    }
    void OnNetworkAdapterUpdateInfo(const std::vector<NetworkAdapterInfo>& networkAdapterInfos) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnNetworkAdapterUpdateInfo")) {
            try {
                py_sink.attr("OnNetworkAdapterUpdateInfo")(networkAdapterInfos);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnNetworkAdapterUpdateInfo");
            }
        }
    }
    // Unforwarded (required overrides — no-ops; deep/niche settings state):
    void OnCompanionZRDeviceUpdateNotification(const CompanionZRDeviceUpdateNot& noti) override {}
    void OnUpdateHardwareStatus(const HardwareStatus& status) override {}
    void OnUpdatedGenericSettings(const GenericSettings& genericSettings) override {}
    void OnUpdateVoiceCommandStatus(const VoiceCommandStatus& status) override {}
    void OnUpdateRoomProfileList(const RoomProfileList& list) override {}
    void OnUpdateZoomRoomCapability(const RoomCapability& roomCapability) override {}
    void OnMicrophoneTestingNotification(int32_t volume) override {}
    void OnMicrophoneRecordingNotification(MicRecordTestStatus status) override {}
    void OnSpeakerTestingNotification(int32_t volume, bool isEnabled) override {}
    void OnSpeakerTestingResult(int32_t result, float duration, bool isStopped) override {}
    void OnStatisticalInfoNotification(const StatisticalInfo& info) override {}
    void OnAudioCheckupNotification(const AudioCheckupInfo& info) override {}
    void OnAudioSystemFailureNotification(bool isDismiss) override {}
    void OnScreenInfosNotification(const ScreenInfos& screenInfos) override {}
    void OnAdjustScreensResponse(const AdjustScreensRes& response) override {}
    void OnZoomPresenceScreenSaverNotification(bool running) override {}
    void OnUpdatedOperationTimeStatusNotification(bool shouldDimScreen) override {}
    void OnDirectorCalibrationNotification(const DirectorCalibrationNot& noti) override {}
    void OnIntelligentDirectorInfoNotification(const IntelligentDirectorInfo& info) override {}
    void OnCameraBoundaryConfigurationInfoNotification(const CameraBoundaryConfigurationInfo& info) override {}
    void OnUpdateDiagnosticInfo(const DiagnosticInfo& info) override {}
    void OnChangeWindowsPasswordNotification(int32_t result) override {}
    void OnUpdateNetworkAudioDeviceList(const std::string& virtualDeviceID, NetworkAudioDeviceListAction action, const std::vector<NetworkAudioDevice>& networkAudioDeviceList, bool isUsedDanteController) override {}
    void OnListAudioChannelAndCameraBindInfoNotification(const std::vector<AudioChannelAndCameraBindInfo>& bindInfoList) override {}
    void OnBindAudioChannelAndCameraNotification(const std::vector<AudioChannelAndCameraBindInfo>& bindInfoList) override {}
    void OnUnbindAudioChannelAndCameraNotification(const std::vector<AudioChannelAndCameraBindInfo>& bindInfoList) override {}
    void OnUnbindAllAudioChannelAndCameraConnectionsNotification(const std::vector<AudioChannelAndCameraBindInfo>& bindInfoList) override {}
    void OnUpdateMicStethoscopeModeEnabledStatus(bool isMicStethoscopeModeEnabled) override {}
    void OnUpdateSystemAudioEnhancementsMode(SystemAudioEnhancementsMode mode) override {}
};

class ClosedCaptionHelperSinkTrampoline : public IClosedCaptionHelperSink {
private:
    py::object py_sink;
public:
    ClosedCaptionHelperSinkTrampoline(py::object obj) : py_sink(obj) {}

    void OnUpdateClosedCaptionNotification(const ClosedCaptionInfo& closedCaptionInfo) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnUpdateClosedCaptionNotification")) {
            try {
                py_sink.attr("OnUpdateClosedCaptionNotification")(closedCaptionInfo);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnUpdateClosedCaptionNotification");
            }
        }
    }
    void OnNewLTTLanguageNotification(const NewLTTCaptionInfo& newLttCaptionInfo) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnNewLTTLanguageNotification")) {
            try {
                py_sink.attr("OnNewLTTLanguageNotification")(newLttCaptionInfo);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnNewLTTLanguageNotification");
            }
        }
    }
    void OnNewLTTCaptionNotification(NewLTTCaptionNotificationType type) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnNewLTTCaptionNotification")) {
            try {
                py_sink.attr("OnNewLTTCaptionNotification")(type);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnNewLTTCaptionNotification");
            }
        }
    }
    void OnMessageAdd(const LTTCaptionMessage& message) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnMessageAdd")) {
            try {
                py_sink.attr("OnMessageAdd")(message);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnMessageAdd");
            }
        }
    }
    void OnMessageUpdate(const LTTCaptionMessage& message) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnMessageUpdate")) {
            try {
                py_sink.attr("OnMessageUpdate")(message);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnMessageUpdate");
            }
        }
    }
    void OnMessageLoad(const std::vector<LTTCaptionMessage>& messages, bool hasMoreHistory) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnMessageLoad")) {
            try {
                py_sink.attr("OnMessageLoad")(messages, hasMoreHistory);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnMessageLoad");
            }
        }
    }
    // Unforwarded (required overrides — no-ops):
    void OnClosedCaptionResponse(int32_t result, ClosedCaptionFontSize fontSize) override {}
    void OnUpdateInterpretLanguageNotification(const InterpretLanguageInfoList& infoList) override {}
    void OnMessageNotSupported(const LTTCaptionMessage& message) override {}
    void OnMessageInstanceOnlySpeakerTagUpdate(const LTTCaptionMessage& message) override {}
};

class ProAVServiceSinkTrampoline : public IProAVServiceSink {
private:
    py::object py_sink;
public:
    ProAVServiceSinkTrampoline(py::object obj) : py_sink(obj) {}

    void OnProAVVideoOverlaySettingsNotification(const ProAVVideoOverlaySettings& settings) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnProAVVideoOverlaySettingsNotification")) {
            try {
                py_sink.attr("OnProAVVideoOverlaySettingsNotification")(settings);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnProAVVideoOverlaySettingsNotification");
            }
        }
    }
    void OnProAVUnassignedBehaviorNotification(const ProAVUnassignedBehavior& behavior) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnProAVUnassignedBehaviorNotification")) {
            try {
                py_sink.attr("OnProAVUnassignedBehaviorNotification")(behavior);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnProAVUnassignedBehaviorNotification");
            }
        }
    }
    void OnProAVVideoLossBehaviorNotification(const ProAVVideoLossBehavior& behavior) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnProAVVideoLossBehaviorNotification")) {
            try {
                py_sink.attr("OnProAVVideoLossBehaviorNotification")(behavior);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnProAVVideoLossBehaviorNotification");
            }
        }
    }
    void OnProAVNonPersistentAssignedGalleryUpdate(const ProAVAssignedGalleryInfo& info) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnProAVNonPersistentAssignedGalleryUpdate")) {
            try {
                py_sink.attr("OnProAVNonPersistentAssignedGalleryUpdate")(info);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnProAVNonPersistentAssignedGalleryUpdate");
            }
        }
    }
    void OnProAVPersistentAssignedGalleryUpdate(const std::vector<ProAVAssignedGalleryInfo>& infos) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnProAVPersistentAssignedGalleryUpdate")) {
            try {
                py_sink.attr("OnProAVPersistentAssignedGalleryUpdate")(infos);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnProAVPersistentAssignedGalleryUpdate");
            }
        }
    }
    void OnProAVAssignedGalleryStatusUpdate(const ProAVAssignedGalleryStatus& status, const std::vector<uint32_t>& deleteIndices) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnProAVAssignedGalleryStatusUpdate")) {
            try {
                py_sink.attr("OnProAVAssignedGalleryStatusUpdate")(status, deleteIndices);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnProAVAssignedGalleryStatusUpdate");
            }
        }
    }
    void OnProAVAssignedGalleryHideOptionsUpdate(const ProAVAssignedGalleryHideOptions& options) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnProAVAssignedGalleryHideOptionsUpdate")) {
            try {
                py_sink.attr("OnProAVAssignedGalleryHideOptionsUpdate")(options);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnProAVAssignedGalleryHideOptionsUpdate");
            }
        }
    }
    void OnProAVDeleteAssignedGallerySeatFailed(const std::vector<uint32_t>& deleteIndices) override {}
};

class HWIOHelperSinkTrampoline : public IHWIOHelperSink {
private:
    py::object py_sink;
public:
    HWIOHelperSinkTrampoline(py::object obj) : py_sink(obj) {}

    void OnHWIOServiceStatusUpdated(bool isServiceAvailable, bool isFeatureAllowed, const std::string& companionZRID) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnHWIOServiceStatusUpdated")) {
            try {
                py_sink.attr("OnHWIOServiceStatusUpdated")(isServiceAvailable, isFeatureAllowed, companionZRID);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnHWIOServiceStatusUpdated");
            }
        }
    }
    // Unforwarded (heavy device-tree structs — required overrides, no-ops):
    void OnHWIOListDevicesResult(int32_t result, const HWIOInfo& info, const std::string& companionZRID) override {}
    void OnHWIOConfigureDeviceResult(int32_t result, const HWIODeviceConfiguration& configuration, const std::string& companionZRID) override {}
    void OnHWIOAssignDeviceResult(int32_t result, const HWIOAssignDeviceInfo& assignDeviceInfo, const std::string& companionZRID) override {}
    void OnHWIODeviceUpdated(const HWIODeviceUpdate& deviceUpdate, const std::string& companionZRID) override {}
    void OnHWIOSetVideoConvertPreferenceResult(int32_t result, const HWIOVideoConvertPreference& preference, const std::string& companionZRID) override {}
    void OnHWIOSetInputSignalDetectionResult(int32_t result, const HWIOInputSignalDetection& signalDetection, const std::string& companionZRID) override {}
};

class DanteOutputHelperSinkTrampoline : public IDanteOutputHelperSink {
private:
    py::object py_sink;
public:
    DanteOutputHelperSinkTrampoline(py::object obj) : py_sink(obj) {}

    void OnCreateLocalNetworkAudioDevice(int32_t result, const LocalNetworkAudioDeviceInfo& info) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnCreateLocalNetworkAudioDevice")) {
            try {
                py_sink.attr("OnCreateLocalNetworkAudioDevice")(result, info);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnCreateLocalNetworkAudioDevice");
            }
        }
    }
    void OnDestroyLocalNetworkAudioDevice(int32_t result) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnDestroyLocalNetworkAudioDevice")) {
            try {
                py_sink.attr("OnDestroyLocalNetworkAudioDevice")(result);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnDestroyLocalNetworkAudioDevice");
            }
        }
    }
    void OnLocalNetworkAudioDeviceError(const NetworkAudioError& error) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnLocalNetworkAudioDeviceError")) {
            try {
                py_sink.attr("OnLocalNetworkAudioDeviceError")(error);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnLocalNetworkAudioDeviceError");
            }
        }
    }
    void OnLocalNetworkAudioDeviceInfoNotification(const LocalNetworkAudioDeviceInfo& info) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnLocalNetworkAudioDeviceInfoNotification")) {
            try {
                py_sink.attr("OnLocalNetworkAudioDeviceInfoNotification")(info);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnLocalNetworkAudioDeviceInfoNotification");
            }
        }
    }
    // Unforwarded (heavy connection-graph structs — required overrides, no-ops):
    void OnBindUserAudioConnectionSuccess(const std::vector<NetworkAudioBroadcastConnectionInfo>& connections) override {}
    void OnBindUserAudioConnectionError(const NetworkAudioError& result, int32_t userID, const LocalNetworkAudioChannelInfo& channel, AudioSignalType signalType) override {}
    void OnUnbindUserAudioConnectionSuccess(const std::vector<NetworkAudioBroadcastConnectionInfo>& connections) override {}
    void OnUnbindUserAudioConnectionError(const NetworkAudioError& result, int32_t userID, AudioSignalType signalType) override {}
    void OnBindMixedAudioConnectionSuccess(const std::vector<NetworkAudioBroadcastConnectionInfo>& connections) override {}
    void OnBindMixedAudioConnectionError(const NetworkAudioError& result, const LocalNetworkAudioChannelInfo& channel, AudioSignalType signalType) override {}
    void OnUnbindMixedAudioConnectionSuccess(const std::vector<NetworkAudioBroadcastConnectionInfo>& connections) override {}
    void OnUnbindMixedAudioConnectionError(const NetworkAudioError& result, AudioSignalType signalType) override {}
    void OnUnbindAllAudioConnection(const NetworkAudioError& result, const std::vector<NetworkAudioBroadcastConnectionInfo>& connections) override {}
    void OnListAllAudioConnection(const NetworkAudioError& result, const std::vector<NetworkAudioBroadcastConnectionInfo>& connections) override {}
    void OnUpdateAudioConnection(const std::vector<NetworkAudioBroadcastConnectionInfo>& connections) override {}
    void OnUnbindChannelAudioConnectionSuccess(const std::vector<NetworkAudioBroadcastConnectionInfo>& connections) override {}
    void OnUnbindChannelAudioConnectionError(const NetworkAudioError& result, const LocalNetworkAudioChannelInfo& channel) override {}
    void OnListAllUnbindChannel(const NetworkAudioError& result, const std::vector<LocalNetworkAudioChannelInfo>& txChannels) override {}
    void OnBindShareContentAudioConnectionSuccess(const std::vector<NetworkAudioBroadcastConnectionInfo>& connections) override {}
    void OnBindShareContentAudioConnectionError(const NetworkAudioError& result, const LocalNetworkAudioChannelInfo& channel, AudioSignalType signalType) override {}
    void OnUnbindShareContentAudioConnectionSuccess(const std::vector<NetworkAudioBroadcastConnectionInfo>& connections) override {}
    void OnUnbindShareContentAudioConnectionError(const NetworkAudioError& result, AudioSignalType signalType) override {}
    void OnBindGalleryMixedAudioConnectionSuccess(const std::vector<NetworkAudioBroadcastConnectionInfo>& connections) override {}
    void OnBindGalleryMixedAudioConnectionError(const NetworkAudioError& result, const NetworkAudioBroadcastGalleryBindInfo& galleryBindInfo, const LocalNetworkAudioChannelInfo& channel) override {}
    void OnUnbindGalleryMixedAudioConnectionSuccess(const std::vector<NetworkAudioBroadcastConnectionInfo>& connections) override {}
    void OnUnbindGalleryMixedAudioConnectionError(const NetworkAudioError& result, const NetworkAudioBroadcastGalleryBindInfo& galleryBindInfo) override {}
    void OnBindInterpretationAudioConnectionSuccess(const std::vector<NetworkAudioBroadcastConnectionInfo>& connections) override {}
    void OnBindInterpretationAudioConnectionError(const NetworkAudioError& result, int32_t languageID, const LocalNetworkAudioChannelInfo& channel) override {}
    void OnUnbindInterpretationAudioConnectionSuccess(const std::vector<NetworkAudioBroadcastConnectionInfo>& connections) override {}
    void OnUnbindInterpretationAudioConnectionError(const NetworkAudioError& result, int32_t languageID) override {}
    void OnListAllOutputMixScreen(const NetworkAudioError& result, const std::vector<NetworkAudioBroadcastOutputMixBindInfo>& screens) override {}
    void OnBindOutputMixAudioConnectionSuccess(const std::vector<NetworkAudioBroadcastConnectionInfo>& connections) override {}
    void OnBindOutputMixAudioConnectionError(const NetworkAudioError& result, const NetworkAudioBroadcastOutputMixBindInfo& outputMixBindInfo, const LocalNetworkAudioChannelInfo& channel) override {}
    void OnUnbindOutputMixAudioConnectionSuccess(const std::vector<NetworkAudioBroadcastConnectionInfo>& connections) override {}
    void OnUnbindOutputMixAudioConnectionError(const NetworkAudioError& result, const NetworkAudioBroadcastOutputMixBindInfo& outputMixBindInfo) override {}
};

class NDIHelperSinkTrampoline : public INDIHelperSink {
private:
    py::object py_sink;
public:
    NDIHelperSinkTrampoline(py::object obj) : py_sink(obj) {}

    void OnNDIUsageSettingsNotification(const NDIUsageSettings& settings) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnNDIUsageSettingsNotification")) {
            try {
                py_sink.attr("OnNDIUsageSettingsNotification")(settings);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnNDIUsageSettingsNotification");
            }
        }
    }
    void OnNDIDeviceListNotification(const std::vector<Device>& devices) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnNDIDeviceListNotification")) {
            try {
                py_sink.attr("OnNDIDeviceListNotification")(devices);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnNDIDeviceListNotification");
            }
        }
    }
    // Unforwarded (NDISource-deep — required overrides, no-ops):
    void OnNDIUsageNotification(const NDIUsageInfo& ndiUsageInfo) override {}
    void OnNDIAvailableSourcesNotification(const std::vector<NDISource>& sources) override {}
    void OnPersistentNDISourcesNotification(const std::vector<NDIPinnedSource>& sources) override {}
};

class ControlSystemHelperSinkTrampoline : public IControlSystemHelperSink {
private:
    py::object py_sink;
public:
    ControlSystemHelperSinkTrampoline(py::object obj) : py_sink(obj) {}

    void OnEnableZRCSNotification(bool enable) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnEnableZRCSNotification")) {
            try {
                py_sink.attr("OnEnableZRCSNotification")(enable);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnEnableZRCSNotification");
            }
        }
    }
    void OnUpdateZRCSSceneList(const std::vector<ControlSystemSceneInfo>& scenes) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnUpdateZRCSSceneList")) {
            try {
                py_sink.attr("OnUpdateZRCSSceneList")(scenes);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnUpdateZRCSSceneList");
            }
        }
    }
    // Unforwarded (device-list tree — required override, no-op):
    void OnUpdateZRCSDeviceList(ControlSystemUpdateDeviceType type, const ControlSystemDeviceList& list) override {}
};

class BYODHelperSinkTrampoline : public IBYODHelperSink {
private:
    py::object py_sink;
public:
    BYODHelperSinkTrampoline(py::object obj) : py_sink(obj) {}

    void OnMakeEmergencyCallInBYODModeNotification(bool succeed) override {
        py::gil_scoped_acquire acquire;
        if (py::hasattr(py_sink, "OnMakeEmergencyCallInBYODModeNotification")) {
            try {
                py_sink.attr("OnMakeEmergencyCallInBYODModeNotification")(succeed);
            } catch (py::error_already_set& e) {
                e.discard_as_unraisable("OnMakeEmergencyCallInBYODModeNotification");
            }
        }
    }
    // Unforwarded (BYOD mode structs — required overrides, no-ops):
    void OnBYODModeInfoNotification(const BYODModeInfo& info) override {}
    void OnBYODModeResult(const BYODModeResult& result) override {}
};

class CalibrationHelperSinkTrampoline : public ICalibrationHelperSink {
private:
    py::object py_sink;
public:
    CalibrationHelperSinkTrampoline(py::object obj) : py_sink(obj) {}
    // Camera-calibration wizard callbacks — sink registered; all no-op (deep/niche).
    void OnDirectorCalibrationNotification(const DirectorCalibrationNot& noti) override {}
    void OnIntelligentDirectorCalibrationActionChanged(IDCalibrationAction currentAction, const std::vector<IDCalibrationAction>& actionsOfNextStep, const std::vector<IDCalibrationAction>& actionsOfPreviousStep) override {}
    void OnCameraBoundaryConfigurationNotification(const CameraBoundaryConfigurationNot& noti) override {}
    void OnCameraBoundaryConfigurationActionChanged(CBConfigurationAction currentAction, const std::vector<CBConfigurationAction>& actionsOfNextStep, const std::vector<CBConfigurationAction>& actionsOfPreviousStep) override {}
};

// One trampoline registry per (interface, trampoline) pair, shared by the
// RegisterSink and DeregisterSink lambdas below. A `static` map declared inside
// a lambda body is a distinct object per lambda (each lambda is its own closure
// type), so a deregister lambda with its own map could never find what the
// register lambda stored -- the sink would stay registered with the SDK forever.
// Intentionally leaked at process exit (see the os._exit note in service/app.py):
// destroying py::objects during static teardown after Py_Finalize would abort.
template <typename Iface, typename Trampoline>
std::map<Iface*, std::shared_ptr<Trampoline>>& SinkRegistry() {
    static std::map<Iface*, std::shared_ptr<Trampoline>> registry;
    return registry;
}

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
            auto& sinks = SinkRegistry<IZoomRoomsService, ZoomRoomsServiceSinkTrampoline>();
            auto trampoline = std::make_shared<ZoomRoomsServiceSinkTrampoline>(py_sink);
            sinks[self] = trampoline;
            return self->RegisterSink(trampoline.get());
        })
        .def("DeregisterSink", [](IZoomRoomsService* self) {
            auto& sinks = SinkRegistry<IZoomRoomsService, ZoomRoomsServiceSinkTrampoline>();
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
    py::class_<IBYODHelper>(m, "IBYODHelper")
        .def("RegisterSink", [](IBYODHelper* self, py::object py_sink) {
            auto& sinks = SinkRegistry<IBYODHelper, BYODHelperSinkTrampoline>();
            auto trampoline = std::make_shared<BYODHelperSinkTrampoline>(py_sink);
            sinks[self] = trampoline;
            return self->RegisterSink(trampoline.get());
        })
        .def("DeregisterSink", [](IBYODHelper* self) {
            auto& sinks = SinkRegistry<IBYODHelper, BYODHelperSinkTrampoline>();
            auto it = sinks.find(self);
            if (it != sinks.end()) {
                auto result = self->DeregisterSink(it->second.get());
                sinks.erase(it);
                return result;
            }
            return ZRCSDKERR_INTERNAL_ERROR;
        });
    py::class_<ControlSystemSceneInfo>(m, "ControlSystemSceneInfo")
        .def(py::init<>())
        .def_readwrite("sceneID", &ControlSystemSceneInfo::sceneID)
        .def_readwrite("name", &ControlSystemSceneInfo::name)
        .def_readwrite("icon", &ControlSystemSceneInfo::icon);
    py::class_<IControlSystemHelper>(m, "IControlSystemHelper")
        .def("RegisterSink", [](IControlSystemHelper* self, py::object py_sink) {
            auto& sinks = SinkRegistry<IControlSystemHelper, ControlSystemHelperSinkTrampoline>();
            auto trampoline = std::make_shared<ControlSystemHelperSinkTrampoline>(py_sink);
            sinks[self] = trampoline;
            return self->RegisterSink(trampoline.get());
        })
        .def("DeregisterSink", [](IControlSystemHelper* self) {
            auto& sinks = SinkRegistry<IControlSystemHelper, ControlSystemHelperSinkTrampoline>();
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
            auto& sinks = SinkRegistry<IPreMeetingService, PreMeetingServiceSinkTrampoline>();
            auto trampoline = std::make_shared<PreMeetingServiceSinkTrampoline>(py_sink);
            sinks[self] = trampoline;
            return self->RegisterSink(trampoline.get());
        })
        .def("DeregisterSink", [](IPreMeetingService* self) {
            auto& sinks = SinkRegistry<IPreMeetingService, PreMeetingServiceSinkTrampoline>();
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

    py::enum_<ExitMeetingReason>(m, "ExitMeetingReason")
        .value("ExitMeetingReasonDefault", ExitMeetingReason::ExitMeetingReasonDefault)
        .value("ExitMeetingReasonJoinBO", ExitMeetingReason::ExitMeetingReasonJoinBO)
        .value("ExitMeetingReasonLeaveBO", ExitMeetingReason::ExitMeetingReasonLeaveBO)
        .value("ExitMeetingReasonRejoinNewMeeting", ExitMeetingReason::ExitMeetingReasonRejoinNewMeeting)
        .export_values();

    py::enum_<WaitingHostReason>(m, "WaitingHostReason")
        .value("WaitingHostStartMeeting", WaitingHostReason::WaitingHostStartMeeting)
        .value("WaitingHostEndAnotherMeeting", WaitingHostReason::WaitingHostEndAnotherMeeting)
        .export_values();

    py::enum_<RoomSystemProtocolType>(m, "RoomSystemProtocolType")
        .value("RoomSystemProtocolTypeUnknown", RoomSystemProtocolType::RoomSystemProtocolTypeUnknown)
        .value("RoomSystemProtocolTypeH323", RoomSystemProtocolType::RoomSystemProtocolTypeH323)
        .value("RoomSystemProtocolTypeSIP", RoomSystemProtocolType::RoomSystemProtocolTypeSIP)
        .export_values();

    // ===== Meeting Service Structs =====
    py::class_<MeetingErrorInfo>(m, "MeetingErrorInfo")
        .def(py::init<>())
        .def_readwrite("errorCode", &MeetingErrorInfo::errorCode)
        .def_readwrite("errorInfo", &MeetingErrorInfo::errorInfo)
        .def_readwrite("errorTitle", &MeetingErrorInfo::errorTitle)
        .def_readwrite("errorDescLink", &MeetingErrorInfo::errorDescLink);

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

    py::class_<ConfDeviceLockStatus>(m, "ConfDeviceLockStatus")
        .def(py::init<>())
        .def_readwrite("isLocked", &ConfDeviceLockStatus::isLocked)
        .def_readwrite("remainTimeSec", &ConfDeviceLockStatus::remainTimeSec)
        .def_readwrite("wrongPwdInputCount", &ConfDeviceLockStatus::wrongPwdInputCount);

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
        .def("GetThirdPartyMeetingHelper", &IMeetingService::GetThirdPartyMeetingHelper, py::return_value_policy::reference)
        .def("GetWaitingRoomHelper", &IMeetingService::GetWaitingRoomHelper, py::return_value_policy::reference)
        .def("GetClosedCaptionHelper", &IMeetingService::GetClosedCaptionHelper, py::return_value_policy::reference)
        .def("RegisterSink", [](IMeetingService* self, py::object py_sink) {
            auto& sinks = SinkRegistry<IMeetingService, MeetingServiceSinkTrampoline>();
            auto trampoline = std::make_shared<MeetingServiceSinkTrampoline>(py_sink);
            sinks[self] = trampoline;
            return self->RegisterSink(trampoline.get());
        })
        .def("DeregisterSink", [](IMeetingService* self) {
            auto& sinks = SinkRegistry<IMeetingService, MeetingServiceSinkTrampoline>();
            auto it = sinks.find(self);
            if (it != sinks.end()) {
                auto result = self->DeregisterSink(it->second.get());
                sinks.erase(it);
                return result;
            }
            return ZRCSDKERR_INTERNAL_ERROR;
        });

    // ===== Meeting Audio Helper =====
    py::enum_<AskUnmuteAudioByHostType>(m, "AskUnmuteAudioByHostType")
        .value("AskUnmuteAudioByHostTypeUnmuteAudio", AskUnmuteAudioByHostType::AskUnmuteAudioByHostTypeUnmuteAudio)
        .value("AskUnmuteAudioByHostTypeSpotlight", AskUnmuteAudioByHostType::AskUnmuteAudioByHostTypeSpotlight)
        .value("AskUnmuteAudioByHostTypeViewOnlyTalk", AskUnmuteAudioByHostType::AskUnmuteAudioByHostTypeViewOnlyTalk)
        .export_values();

    py::class_<IMeetingAudioHelper>(m, "IMeetingAudioHelper")
        .def("UpdateMyAudioStatus", &IMeetingAudioHelper::UpdateMyAudioStatus)
        .def("AnswerUnmuteAudioByHostRequest", &IMeetingAudioHelper::AnswerUnmuteAudioByHostRequest)
        .def("RegisterSink", [](IMeetingAudioHelper* self, py::object py_sink) {
            auto& sinks = SinkRegistry<IMeetingAudioHelper, MeetingAudioHelperSinkTrampoline>();
            auto trampoline = std::make_shared<MeetingAudioHelperSinkTrampoline>(py_sink);
            sinks[self] = trampoline;
            return self->RegisterSink(trampoline.get());
        })
        .def("DeregisterSink", [](IMeetingAudioHelper* self) {
            auto& sinks = SinkRegistry<IMeetingAudioHelper, MeetingAudioHelperSinkTrampoline>();
            auto it = sinks.find(self);
            if (it != sinks.end()) {
                auto result = self->DeregisterSink(it->second.get());
                sinks.erase(it);
                return result;
            }
            return ZRCSDKERR_INTERNAL_ERROR;
        });

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
            static_cast<ZRCSDKError(IMeetingVideoHelper::*)(bool, PreviewVideoType, const MeetingItem&)>(&IMeetingVideoHelper::ShowVideoPreview))
        .def("RegisterSink", [](IMeetingVideoHelper* self, py::object py_sink) {
            auto& sinks = SinkRegistry<IMeetingVideoHelper, MeetingVideoHelperSinkTrampoline>();
            auto trampoline = std::make_shared<MeetingVideoHelperSinkTrampoline>(py_sink);
            sinks[self] = trampoline;
            return self->RegisterSink(trampoline.get());
        })
        .def("DeregisterSink", [](IMeetingVideoHelper* self) {
            auto& sinks = SinkRegistry<IMeetingVideoHelper, MeetingVideoHelperSinkTrampoline>();
            auto it = sinks.find(self);
            if (it != sinks.end()) {
                auto result = self->DeregisterSink(it->second.get());
                sinks.erase(it);
                return result;
            }
            return ZRCSDKERR_INTERNAL_ERROR;
        });

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
        .def("ControlSidePanel", &IMeetingControlHelper::ControlSidePanel)
        .def("RegisterSink", [](IMeetingControlHelper* self, py::object py_sink) {
            auto& sinks = SinkRegistry<IMeetingControlHelper, MeetingControlHelperSinkTrampoline>();
            auto trampoline = std::make_shared<MeetingControlHelperSinkTrampoline>(py_sink);
            sinks[self] = trampoline;
            return self->RegisterSink(trampoline.get());
        })
        .def("DeregisterSink", [](IMeetingControlHelper* self) {
            auto& sinks = SinkRegistry<IMeetingControlHelper, MeetingControlHelperSinkTrampoline>();
            auto it = sinks.find(self);
            if (it != sinks.end()) {
                auto result = self->DeregisterSink(it->second.get());
                sinks.erase(it);
                return result;
            }
            return ZRCSDKERR_INTERNAL_ERROR;
        });

    // ===== Meeting Control Helper sink structs/enums (AI Companion, live stream) =====
    py::enum_<AICompanionRequestType>(m, "AICompanionRequestType")
        .value("AICompanionRequestNone", AICompanionRequestType::AICompanionRequestNone)
        .value("AICompanionRequestSwitch", AICompanionRequestType::AICompanionRequestSwitch)
        .value("AICompanionRequestEnable", AICompanionRequestType::AICompanionRequestEnable)
        .export_values();
    py::class_<AICompanionRequestInfo>(m, "AICompanionRequestInfo")
        .def(py::init<>())
        .def_readwrite("type", &AICompanionRequestInfo::type)
        .def_readwrite("senderNames", &AICompanionRequestInfo::senderNames)
        .def_readwrite("AICFeatures", &AICompanionRequestInfo::AICFeatures)
        .def_readwrite("switchAction", &AICompanionRequestInfo::switchAction);
    py::class_<AICompanionStatusInfo>(m, "AICompanionStatusInfo")
        .def(py::init<>())
        .def_readwrite("AICFeatures", &AICompanionStatusInfo::AICFeatures)
        .def_readwrite("assetsOption", &AICompanionStatusInfo::assetsOption);
    py::class_<LiveStreamStatusInfo>(m, "LiveStreamStatusInfo")
        .def(py::init<>())
        .def_readwrite("isInProgress", &LiveStreamStatusInfo::isInProgress)
        .def_readwrite("liveChannelName", &LiveStreamStatusInfo::liveChannelName);
    py::class_<LiveStreamStatus>(m, "LiveStreamStatus")
        .def(py::init<>())
        .def_readwrite("isLiveStreamUnencrypted", &LiveStreamStatus::isLiveStreamUnencrypted)
        .def_readwrite("liveStreamStatusInfo", &LiveStreamStatus::liveStreamStatusInfo);

    // ===== Waiting Room Helper =====
    py::class_<InSilentModeInfo>(m, "InSilentModeInfo")
        .def(py::init<>())
        .def_readwrite("isInSilentMode", &InSilentModeInfo::isInSilentMode)
        .def_readwrite("silentModeForNoHost", &InSilentModeInfo::silentModeForNoHost)
        .def_readwrite("isPutInByManual", &InSilentModeInfo::isPutInByManual);
    py::class_<IWaitingRoomHelper>(m, "IWaitingRoomHelper")
        .def("PutUsersIntoMeeting", &IWaitingRoomHelper::PutUsersIntoMeeting)
        .def("PutUsersIntoWaitingRoom", &IWaitingRoomHelper::PutUsersIntoWaitingRoom)
        .def("PutAllUsersIntoMeeting", &IWaitingRoomHelper::PutAllUsersIntoMeeting)
        .def("EnableWaitingRoomOnEntry", &IWaitingRoomHelper::EnableWaitingRoomOnEntry)
        .def("IsWaitingRoomLocked", [](IWaitingRoomHelper* self) {
            bool locked = false;
            auto r = self->IsWaitingRoomLocked(locked);
            return py::make_tuple(r, locked);
        })
        .def("IsWaitingRoomOnEntry", [](IWaitingRoomHelper* self) {
            bool onEntry = false;
            auto r = self->IsWaitingRoomOnEntry(onEntry);
            return py::make_tuple(r, onEntry);
        })
        .def("RegisterSink", [](IWaitingRoomHelper* self, py::object py_sink) {
            auto& sinks = SinkRegistry<IWaitingRoomHelper, WaitingRoomHelperSinkTrampoline>();
            auto trampoline = std::make_shared<WaitingRoomHelperSinkTrampoline>(py_sink);
            sinks[self] = trampoline;
            return self->RegisterSink(trampoline.get());
        })
        .def("DeregisterSink", [](IWaitingRoomHelper* self) {
            auto& sinks = SinkRegistry<IWaitingRoomHelper, WaitingRoomHelperSinkTrampoline>();
            auto it = sinks.find(self);
            if (it != sinks.end()) {
                auto result = self->DeregisterSink(it->second.get());
                sinks.erase(it);
                return result;
            }
            return ZRCSDKERR_INTERNAL_ERROR;
        });

    // ===== Closed Caption Helper (captions / live transcript) =====
    py::enum_<ClosedCaptionFontSize>(m, "ClosedCaptionFontSize")
        .value("ClosedCaptionFontSizeSmall", ClosedCaptionFontSize::ClosedCaptionFontSizeSmall)
        .value("ClosedCaptionFontSizeMedium", ClosedCaptionFontSize::ClosedCaptionFontSizeMedium)
        .value("ClosedCaptionFontSizeLarge", ClosedCaptionFontSize::ClosedCaptionFontSizeLarge)
        .export_values();
    py::enum_<NewLTTCaptionNotificationType>(m, "NewLTTCaptionNotificationType")
        .value("NewLTTCaptionNotificationTypeCaptionStart", NewLTTCaptionNotificationType::NewLTTCaptionNotificationTypeCaptionStart)
        .value("NewLTTCaptionNotificationTypeEnableCaptionRequestReceived", NewLTTCaptionNotificationType::NewLTTCaptionNotificationTypeEnableCaptionRequestReceived)
        .value("NewLTTCaptionNotificationTypeEnableCaptionRequestDeclined", NewLTTCaptionNotificationType::NewLTTCaptionNotificationTypeEnableCaptionRequestDeclined)
        .value("NewLTTCaptionNotificationTypeSpeakerLanguageMismatch", NewLTTCaptionNotificationType::NewLTTCaptionNotificationTypeSpeakerLanguageMismatch)
        .export_values();
    py::enum_<LTTCaptionWritingDirection>(m, "LTTCaptionWritingDirection")
        .value("LTTCaptionWritingDirectionLeftToRight", LTTCaptionWritingDirection::LTTCaptionWritingDirectionLeftToRight)
        .value("LTTCaptionWritingDirectionRightToLeft", LTTCaptionWritingDirection::LTTCaptionWritingDirectionRightToLeft)
        .export_values();
    py::enum_<LTTCaptionMessageResultType>(m, "LTTCaptionMessageResultType")
        .value("LTTCaptionMessageResultTypeSuccess", LTTCaptionMessageResultType::LTTCaptionMessageResultTypeSuccess)
        .value("LTTCaptionMessageResultTypeTranslationNotSupport", LTTCaptionMessageResultType::LTTCaptionMessageResultTypeTranslationNotSupport)
        .export_values();
    py::class_<ClosedCaptionInfo>(m, "ClosedCaptionInfo")
        .def(py::init<>())
        .def_readwrite("available", &ClosedCaptionInfo::available)
        .def_readwrite("visible", &ClosedCaptionInfo::visible)
        .def_readwrite("fontSize", &ClosedCaptionInfo::fontSize);
    py::class_<NewLTTCaptionLanguage>(m, "NewLTTCaptionLanguage")
        .def(py::init<>())
        .def_readwrite("languageID", &NewLTTCaptionLanguage::languageID)
        .def_readwrite("displayName", &NewLTTCaptionLanguage::displayName)
        .def_readwrite("abbreviatedName", &NewLTTCaptionLanguage::abbreviatedName);
    py::class_<NewLTTCaptionSpeakerLanguageInfo>(m, "NewLTTCaptionSpeakerLanguageInfo")
        .def(py::init<>())
        .def_readwrite("currentLanguage", &NewLTTCaptionSpeakerLanguageInfo::currentLanguage)
        .def_readwrite("availableLanguages", &NewLTTCaptionSpeakerLanguageInfo::availableLanguages);
    py::class_<NewLTTCaptionTranslationInfo>(m, "NewLTTCaptionTranslationInfo")
        .def(py::init<>())
        .def_readwrite("currentLanguage", &NewLTTCaptionTranslationInfo::currentLanguage)
        .def_readwrite("availableLanguages", &NewLTTCaptionTranslationInfo::availableLanguages)
        .def_readwrite("recentlyUsedLanguages", &NewLTTCaptionTranslationInfo::recentlyUsedLanguages);
    py::class_<NewLTTCaptionInfo>(m, "NewLTTCaptionInfo")
        .def(py::init<>())
        .def_readwrite("isNewLttCaptionFeatureOn", &NewLTTCaptionInfo::isNewLttCaptionFeatureOn)
        .def_readwrite("isAutomatedCaptionFeatureOn", &NewLTTCaptionInfo::isAutomatedCaptionFeatureOn)
        .def_readwrite("isTranslatedCaptionFeatureOn", &NewLTTCaptionInfo::isTranslatedCaptionFeatureOn)
        .def_readwrite("isShowCaptionOn", &NewLTTCaptionInfo::isShowCaptionOn)
        .def_readwrite("fontSize", &NewLTTCaptionInfo::fontSize)
        .def_readwrite("isManualCaptionerEnabled", &NewLTTCaptionInfo::isManualCaptionerEnabled)
        .def_readwrite("isShowOriginalAndTranslated", &NewLTTCaptionInfo::isShowOriginalAndTranslated)
        .def_readwrite("speakingLanguageInfo", &NewLTTCaptionInfo::speakingLanguageInfo)
        .def_readwrite("translationInfo", &NewLTTCaptionInfo::translationInfo)
        .def_readwrite("isMmrSupportDisableLttCaption", &NewLTTCaptionInfo::isMmrSupportDisableLttCaption)
        .def_readwrite("isCaptionDisabled", &NewLTTCaptionInfo::isCaptionDisabled)
        .def_readwrite("isAllowShowCaption", &NewLTTCaptionInfo::isAllowShowCaption)
        .def_readwrite("isAllowRequestCaption", &NewLTTCaptionInfo::isAllowRequestCaption)
        .def_readwrite("isShowTranscriptPanelOnZR", &NewLTTCaptionInfo::isShowTranscriptPanelOnZR)
        .def_readwrite("isAllowViewFullTranscript", &NewLTTCaptionInfo::isAllowViewFullTranscript);
    py::class_<SmartTagUser>(m, "SmartTagUser")
        .def(py::init<>())
        .def_readwrite("tagID", &SmartTagUser::tagID)
        .def_readwrite("tagName", &SmartTagUser::tagName)
        .def_readwrite("avatarUrl", &SmartTagUser::avatarUrl)
        .def_readwrite("avatarData", &SmartTagUser::avatarData)
        .def_readwrite("bindNodeID", &SmartTagUser::bindNodeID)
        .def_readwrite("bindEmail", &SmartTagUser::bindEmail)
        .def_readwrite("bindJid", &SmartTagUser::bindJid)
        .def_readwrite("defaultName", &SmartTagUser::defaultName)
        .def_readwrite("streamUserID", &SmartTagUser::streamUserID);
    py::class_<LTTCaptionMessage>(m, "LTTCaptionMessage")
        .def(py::init<>())
        .def_readwrite("result", &LTTCaptionMessage::result)
        .def_readwrite("messageID", &LTTCaptionMessage::messageID)
        .def_readwrite("userNodeID", &LTTCaptionMessage::userNodeID)
        .def_readwrite("userName", &LTTCaptionMessage::userName)
        .def_readwrite("messageTime", &LTTCaptionMessage::messageTime)
        .def_readwrite("messageContent", &LTTCaptionMessage::messageContent)
        .def_readwrite("direction", &LTTCaptionMessage::direction)
        .def_readwrite("speakerTagID", &LTTCaptionMessage::speakerTagID)
        .def_readwrite("speakerTagName", &LTTCaptionMessage::speakerTagName)
        .def_readwrite("instanceOnlySpeakerTag", &LTTCaptionMessage::instanceOnlySpeakerTag)
        .def_readwrite("attendeeJid", &LTTCaptionMessage::attendeeJid);
    py::class_<IClosedCaptionHelper>(m, "IClosedCaptionHelper")
        .def("EnableCaption", &IClosedCaptionHelper::EnableCaption)
        .def("ShowCaption", &IClosedCaptionHelper::ShowCaption)
        .def("SendEnableCaptionRequest", &IClosedCaptionHelper::SendEnableCaptionRequest)
        .def("ApproveEnableCaptionRequest", &IClosedCaptionHelper::ApproveEnableCaptionRequest)
        .def("SetNewLTTSpeakerLanguage", &IClosedCaptionHelper::SetNewLTTSpeakerLanguage)
        .def("SetNewLTTTranslationLanguage", &IClosedCaptionHelper::SetNewLTTTranslationLanguage)
        .def("ShowNewLTTOriginalAndTranslated", &IClosedCaptionHelper::ShowNewLTTOriginalAndTranslated)
        .def("SetNewLTTCaptionFontSize", &IClosedCaptionHelper::SetNewLTTCaptionFontSize)
        .def("LoadLTTCaptionMessage", &IClosedCaptionHelper::LoadLTTCaptionMessage)
        .def("ShowTranscriptPanelOnZR", &IClosedCaptionHelper::ShowTranscriptPanelOnZR)
        .def("ShowTranscriptPanelOnZRC", &IClosedCaptionHelper::ShowTranscriptPanelOnZRC)
        .def("RegisterSink", [](IClosedCaptionHelper* self, py::object py_sink) {
            auto& sinks = SinkRegistry<IClosedCaptionHelper, ClosedCaptionHelperSinkTrampoline>();
            auto trampoline = std::make_shared<ClosedCaptionHelperSinkTrampoline>(py_sink);
            sinks[self] = trampoline;
            return self->RegisterSink(trampoline.get());
        })
        .def("DeregisterSink", [](IClosedCaptionHelper* self) {
            auto& sinks = SinkRegistry<IClosedCaptionHelper, ClosedCaptionHelperSinkTrampoline>();
            auto it = sinks.find(self);
            if (it != sinks.end()) {
                auto result = self->DeregisterSink(it->second.get());
                sinks.erase(it);
                return result;
            }
            return ZRCSDKERR_INTERNAL_ERROR;
        });

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
            auto& sinks = SinkRegistry<IMeetingListHelper, MeetingListHelperSinkTrampoline>();
            auto trampoline = std::make_shared<MeetingListHelperSinkTrampoline>(py_sink);
            sinks[self] = trampoline;
            return self->RegisterSink(trampoline.get());
        })
        .def("DeregisterSink", [](IMeetingListHelper* self) {
            auto& sinks = SinkRegistry<IMeetingListHelper, MeetingListHelperSinkTrampoline>();
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
        .def("EnableAnnotationOverHDMI", &IMeetingShareHelper::EnableAnnotationOverHDMI)
        .def("RegisterSink", [](IMeetingShareHelper* self, py::object py_sink) {
            auto& sinks = SinkRegistry<IMeetingShareHelper, MeetingShareHelperSinkTrampoline>();
            auto trampoline = std::make_shared<MeetingShareHelperSinkTrampoline>(py_sink);
            sinks[self] = trampoline;
            return self->RegisterSink(trampoline.get());
        })
        .def("DeregisterSink", [](IMeetingShareHelper* self) {
            auto& sinks = SinkRegistry<IMeetingShareHelper, MeetingShareHelperSinkTrampoline>();
            auto it = sinks.find(self);
            if (it != sinks.end()) {
                auto result = self->DeregisterSink(it->second.get());
                sinks.erase(it);
                return result;
            }
            return ZRCSDKERR_INTERNAL_ERROR;
        });

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
        .def("ShowMyAutoGeneratedVideoStreams", &IMeetingViewLayoutHelper::ShowMyAutoGeneratedVideoStreams)
        .def("RegisterSink", [](IMeetingViewLayoutHelper* self, py::object py_sink) {
            auto& sinks = SinkRegistry<IMeetingViewLayoutHelper, MeetingViewLayoutHelperSinkTrampoline>();
            auto trampoline = std::make_shared<MeetingViewLayoutHelperSinkTrampoline>(py_sink);
            sinks[self] = trampoline;
            return self->RegisterSink(trampoline.get());
        })
        .def("DeregisterSink", [](IMeetingViewLayoutHelper* self) {
            auto& sinks = SinkRegistry<IMeetingViewLayoutHelper, MeetingViewLayoutHelperSinkTrampoline>();
            auto it = sinks.find(self);
            if (it != sinks.end()) {
                auto result = self->DeregisterSink(it->second.get());
                sinks.erase(it);
                return result;
            }
            return ZRCSDKERR_INTERNAL_ERROR;
        });

    // MeetingScreen enum (used by ScreenLayoutInfo::screen — was previously unregistered).
    py::enum_<MeetingScreen>(m, "MeetingScreen")
        .value("MeetingScreenUnknown", MeetingScreen::MeetingScreenUnknown)
        .value("MeetingScreenFirst", MeetingScreen::MeetingScreenFirst)
        .value("MeetingScreenSecond", MeetingScreen::MeetingScreenSecond)
        .value("MeetingScreenThird", MeetingScreen::MeetingScreenThird)
        .value("MeetingScreenConfidence", MeetingScreen::MeetingScreenConfidence)
        .export_values();

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
        .def("ListPersistentNDISources", &INDIHelper::ListPersistentNDISources)
        .def("RegisterSink", [](INDIHelper* self, py::object py_sink) {
            auto& sinks = SinkRegistry<INDIHelper, NDIHelperSinkTrampoline>();
            auto trampoline = std::make_shared<NDIHelperSinkTrampoline>(py_sink);
            sinks[self] = trampoline;
            return self->RegisterSink(trampoline.get());
        })
        .def("DeregisterSink", [](INDIHelper* self) {
            auto& sinks = SinkRegistry<INDIHelper, NDIHelperSinkTrampoline>();
            auto it = sinks.find(self);
            if (it != sinks.end()) {
                auto result = self->DeregisterSink(it->second.get());
                sinks.erase(it);
                return result;
            }
            return ZRCSDKERR_INTERNAL_ERROR;
        });
    // (NDIResolution / NDIFrameRate / NDIUsageSettings are already registered earlier.)

    py::class_<MeetingParticipant>(m, "MeetingParticipant")
        .def(py::init<>())
        .def_readwrite("userID", &MeetingParticipant::userID)
        .def_readwrite("parentUserID", &MeetingParticipant::parentUserID)
        .def_readwrite("userGUID", &MeetingParticipant::userGUID)
        .def_readwrite("userName", &MeetingParticipant::userName)
        .def_readwrite("pronouns", &MeetingParticipant::pronouns)
        .def_readwrite("avatarUrl", &MeetingParticipant::avatarUrl)
        .def_readwrite("isMySelf", &MeetingParticipant::isMySelf)
        .def_readwrite("isMyself", &MeetingParticipant::isMySelf)  // backwards-compat alias
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
        .def("SetMyChildAsActiveSpeaker", &IParticipantHelper::SetMyChildAsActiveSpeaker)
        .def("RegisterSink", [](IParticipantHelper* self, py::object py_sink) {
            auto& sinks = SinkRegistry<IParticipantHelper, ParticipantHelperSinkTrampoline>();
            auto trampoline = std::make_shared<ParticipantHelperSinkTrampoline>(py_sink);
            sinks[self] = trampoline;
            return self->RegisterSink(trampoline.get());
        })
        .def("DeregisterSink", [](IParticipantHelper* self) {
            auto& sinks = SinkRegistry<IParticipantHelper, ParticipantHelperSinkTrampoline>();
            auto it = sinks.find(self);
            if (it != sinks.end()) {
                auto result = self->DeregisterSink(it->second.get());
                sinks.erase(it);
                return result;
            }
            return ZRCSDKERR_INTERNAL_ERROR;
        });

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
        })
        .def("RegisterSink", [](IRecordingHelper* self, py::object py_sink) {
            auto& sinks = SinkRegistry<IRecordingHelper, RecordingHelperSinkTrampoline>();
            auto trampoline = std::make_shared<RecordingHelperSinkTrampoline>(py_sink);
            sinks[self] = trampoline;
            return self->RegisterSink(trampoline.get());
        })
        .def("DeregisterSink", [](IRecordingHelper* self) {
            auto& sinks = SinkRegistry<IRecordingHelper, RecordingHelperSinkTrampoline>();
            auto it = sinks.find(self);
            if (it != sinks.end()) {
                auto result = self->DeregisterSink(it->second.get());
                sinks.erase(it);
                return result;
            }
            return ZRCSDKERR_INTERNAL_ERROR;
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
            auto& sinks = SinkRegistry<IMeetingReminderHelper, MeetingReminderHelperSinkTrampoline>();
            auto trampoline = std::make_shared<MeetingReminderHelperSinkTrampoline>(py_sink);
            sinks[self] = trampoline;
            return self->RegisterSink(trampoline.get());
        })
        .def("DeregisterSink", [](IMeetingReminderHelper* self) {
            auto& sinks = SinkRegistry<IMeetingReminderHelper, MeetingReminderHelperSinkTrampoline>();
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
        .def("AgreeConsolidatedCustomizedConsent", &IMeetingReminderHelper::AgreeConsolidatedCustomizedConsent)
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
    py::class_<ICalibrationHelper>(m, "ICalibrationHelper")
        .def("RegisterSink", [](ICalibrationHelper* self, py::object py_sink) {
            auto& sinks = SinkRegistry<ICalibrationHelper, CalibrationHelperSinkTrampoline>();
            auto trampoline = std::make_shared<CalibrationHelperSinkTrampoline>(py_sink);
            sinks[self] = trampoline;
            return self->RegisterSink(trampoline.get());
        })
        .def("DeregisterSink", [](ICalibrationHelper* self) {
            auto& sinks = SinkRegistry<ICalibrationHelper, CalibrationHelperSinkTrampoline>();
            auto it = sinks.find(self);
            if (it != sinks.end()) {
                auto result = self->DeregisterSink(it->second.get());
                sinks.erase(it);
                return result;
            }
            return ZRCSDKERR_INTERNAL_ERROR;
        });

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
        .def("EnableMultiCameraOnlyMode", &ISettingService::EnableMultiCameraOnlyMode)
        .def("RegisterSink", [](ISettingService* self, py::object py_sink) {
            auto& sinks = SinkRegistry<ISettingService, SettingServiceSinkTrampoline>();
            auto trampoline = std::make_shared<SettingServiceSinkTrampoline>(py_sink);
            sinks[self] = trampoline;
            return self->RegisterSink(trampoline.get());
        })
        .def("DeregisterSink", [](ISettingService* self) {
            auto& sinks = SinkRegistry<ISettingService, SettingServiceSinkTrampoline>();
            auto it = sinks.find(self);
            if (it != sinks.end()) {
                auto result = self->DeregisterSink(it->second.get());
                sinks.erase(it);
                return result;
            }
            return ZRCSDKERR_INTERNAL_ERROR;
        });

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
        })
        .def("RegisterSink", [](IPhoneCallService* self, py::object py_sink) {
            auto& sinks = SinkRegistry<IPhoneCallService, PhoneCallServiceSinkTrampoline>();
            auto trampoline = std::make_shared<PhoneCallServiceSinkTrampoline>(py_sink);
            sinks[self] = trampoline;
            return self->RegisterSink(trampoline.get());
        })
        .def("DeregisterSink", [](IPhoneCallService* self) {
            auto& sinks = SinkRegistry<IPhoneCallService, PhoneCallServiceSinkTrampoline>();
            auto it = sinks.find(self);
            if (it != sinks.end()) {
                auto result = self->DeregisterSink(it->second.get());
                sinks.erase(it);
                return result;
            }
            return ZRCSDKERR_INTERNAL_ERROR;
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
    py::enum_<LocalNetworkAudioChannelType>(m, "LocalNetworkAudioChannelType")
        .value("LocalNetworkAudioChannelTypeUnknown", LocalNetworkAudioChannelType::LocalNetworkAudioChannelTypeUnknown)
        .value("LocalNetworkAudioChannelTypeRX", LocalNetworkAudioChannelType::LocalNetworkAudioChannelTypeRX)
        .value("LocalNetworkAudioChannelTypeTX", LocalNetworkAudioChannelType::LocalNetworkAudioChannelTypeTX)
        .export_values();
    py::class_<NetworkAudioError>(m, "NetworkAudioError")
        .def(py::init<>())
        .def_readwrite("errorCode", &NetworkAudioError::errorCode)
        .def_readwrite("errorName", &NetworkAudioError::errorName);
    py::class_<LocalNetworkAudioChannelInfo>(m, "LocalNetworkAudioChannelInfo")
        .def(py::init<>())
        .def_readwrite("channelName", &LocalNetworkAudioChannelInfo::channelName)
        .def_readwrite("channelID", &LocalNetworkAudioChannelInfo::channelID)
        .def_readwrite("channelType", &LocalNetworkAudioChannelInfo::channelType)
        .def_readwrite("networkDeviceName", &LocalNetworkAudioChannelInfo::networkDeviceName);
    py::class_<LocalNetworkAudioDeviceInfo>(m, "LocalNetworkAudioDeviceInfo")
        .def(py::init<>())
        .def_readwrite("networkDeviceName", &LocalNetworkAudioDeviceInfo::networkDeviceName)
        .def_readwrite("rxChannels", &LocalNetworkAudioDeviceInfo::rxChannels)
        .def_readwrite("txChannels", &LocalNetworkAudioDeviceInfo::txChannels)
        .def_readwrite("identifiable", &LocalNetworkAudioDeviceInfo::identifiable);
    py::class_<IDanteOutputHelper>(m, "IDanteOutputHelper")
        .def("RegisterSink", [](IDanteOutputHelper* self, py::object py_sink) {
            auto& sinks = SinkRegistry<IDanteOutputHelper, DanteOutputHelperSinkTrampoline>();
            auto trampoline = std::make_shared<DanteOutputHelperSinkTrampoline>(py_sink);
            sinks[self] = trampoline;
            return self->RegisterSink(trampoline.get());
        })
        .def("DeregisterSink", [](IDanteOutputHelper* self) {
            auto& sinks = SinkRegistry<IDanteOutputHelper, DanteOutputHelperSinkTrampoline>();
            auto it = sinks.find(self);
            if (it != sinks.end()) {
                auto result = self->DeregisterSink(it->second.get());
                sinks.erase(it);
                return result;
            }
            return ZRCSDKERR_INTERNAL_ERROR;
        });
    py::class_<IHWIOHelper>(m, "IHWIOHelper")
        .def("RegisterSink", [](IHWIOHelper* self, py::object py_sink) {
            auto& sinks = SinkRegistry<IHWIOHelper, HWIOHelperSinkTrampoline>();
            auto trampoline = std::make_shared<HWIOHelperSinkTrampoline>(py_sink);
            sinks[self] = trampoline;
            return self->RegisterSink(trampoline.get());
        })
        .def("DeregisterSink", [](IHWIOHelper* self) {
            auto& sinks = SinkRegistry<IHWIOHelper, HWIOHelperSinkTrampoline>();
            auto it = sinks.find(self);
            if (it != sinks.end()) {
                auto result = self->DeregisterSink(it->second.get());
                sinks.erase(it);
                return result;
            }
            return ZRCSDKERR_INTERNAL_ERROR;
        });

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
        })
        .def("RegisterSink", [](IProAVService* self, py::object py_sink) {
            auto& sinks = SinkRegistry<IProAVService, ProAVServiceSinkTrampoline>();
            auto trampoline = std::make_shared<ProAVServiceSinkTrampoline>(py_sink);
            sinks[self] = trampoline;
            return self->RegisterSink(trampoline.get());
        })
        .def("DeregisterSink", [](IProAVService* self) {
            auto& sinks = SinkRegistry<IProAVService, ProAVServiceSinkTrampoline>();
            auto it = sinks.find(self);
            if (it != sinks.end()) {
                auto result = self->DeregisterSink(it->second.get());
                sinks.erase(it);
                return result;
            }
            return ZRCSDKERR_INTERNAL_ERROR;
        });

    // ProAV assigned-gallery structs (used by IProAVServiceSink callbacks)
    py::class_<ProAVAssignedSeatInfo>(m, "ProAVAssignedSeatInfo")
        .def(py::init<>())
        .def_readwrite("index", &ProAVAssignedSeatInfo::index)
        .def_readwrite("isReserved", &ProAVAssignedSeatInfo::isReserved)
        .def_readwrite("email", &ProAVAssignedSeatInfo::email)
        .def_readwrite("name", &ProAVAssignedSeatInfo::name);
    py::class_<ProAVAssignedGalleryHideUser>(m, "ProAVAssignedGalleryHideUser")
        .def(py::init<>())
        .def_readwrite("name", &ProAVAssignedGalleryHideUser::name)
        .def_readwrite("email", &ProAVAssignedGalleryHideUser::email)
        .def_readwrite("userGuid", &ProAVAssignedGalleryHideUser::userGuid);
    py::class_<ProAVAssignedSeatStatus>(m, "ProAVAssignedSeatStatus")
        .def(py::init<>())
        .def_readwrite("seat", &ProAVAssignedSeatStatus::seat)
        .def_readwrite("userGuid", &ProAVAssignedSeatStatus::userGuid);
    py::class_<ProAVAssignedGalleryInfo>(m, "ProAVAssignedGalleryInfo")
        .def(py::init<>())
        .def_readwrite("seats", &ProAVAssignedGalleryInfo::seats)
        .def_readwrite("meetingId", &ProAVAssignedGalleryInfo::meetingId)
        .def_readwrite("hideUsers", &ProAVAssignedGalleryInfo::hideUsers);
    py::class_<ProAVAssignedGalleryStatus>(m, "ProAVAssignedGalleryStatus")
        .def(py::init<>())
        .def_readwrite("fullUpdate", &ProAVAssignedGalleryStatus::fullUpdate)
        .def_readwrite("configApplied", &ProAVAssignedGalleryStatus::configApplied)
        .def_readwrite("seats", &ProAVAssignedGalleryStatus::seats)
        .def_readwrite("hideUsers", &ProAVAssignedGalleryStatus::hideUsers);
    py::class_<ProAVAssignedGalleryHideOptions>(m, "ProAVAssignedGalleryHideOptions")
        .def(py::init<>())
        .def_readwrite("hideSelf", &ProAVAssignedGalleryHideOptions::hideSelf)
        .def_readwrite("hideHostCoHost", &ProAVAssignedGalleryHideOptions::hideHostCoHost)
        .def_readwrite("hideNonVideo", &ProAVAssignedGalleryHideOptions::hideNonVideo);
}
