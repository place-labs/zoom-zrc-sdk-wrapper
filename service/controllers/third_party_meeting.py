"""
Third Party Meeting Controller
Handles third-party meeting integrations (Teams, Google Meet, SIP, PSTN)
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import zrc_sdk

router = APIRouter(prefix="/api/rooms/{room_id}/third-party", tags=["third_party_meeting"])

# Dependency injection placeholder - will be set by app.py
get_room_manager = None


# ===== Request Models =====

class CallOutPSTNRequest(BaseModel):
    phone_number: str
    cancel_call: bool = False
    has_voice_prompt: bool = True


class JoinIntegrationMeetingRequest(BaseModel):
    meeting_id: str
    password: str = ""
    provider: str  # Teams, GoogleMeet, Webex, etc.


class MuteAudioRequest(BaseModel):
    mute: bool


class StopVideoRequest(BaseModel):
    stop: bool


class StopContentShareRequest(BaseModel):
    stop: bool


class ChangeLayoutRequest(BaseModel):
    layout_type: int  # Bit flags from IntegrationMeetingLayoutType


class GetInterOperabilityInfoRequest(BaseModel):
    meeting_type: str  # ThirdPartyMeetingServiceProvider


# ===== Helper Functions =====

def get_third_party_helper(room_id: str, room_manager):
    """Get third party meeting helper for a room"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail=f"Room {room_id} not found")

    meeting_service = room_service.GetMeetingService()
    if not meeting_service:
        raise HTTPException(status_code=404, detail=f"Meeting service not available for room {room_id}")

    return meeting_service.GetThirdPartyMeetingHelper()


def meeting_item_from_dict(data: dict):
    """Convert dictionary to MeetingItem struct"""
    item = zrc_sdk.MeetingItem()
    if "meeting_number" in data:
        item.meetingNumber = data["meeting_number"]
    if "meeting_id" in data:
        item.meetingID = data["meeting_id"]
    if "meeting_password" in data:
        item.meetingPassword = data["meeting_password"]
    if "meeting_topic" in data:
        item.meetingTopic = data["meeting_topic"]
    if "start_time" in data:
        item.startTime = data["start_time"]
    if "end_time" in data:
        item.endTime = data["end_time"]
    if "organizer" in data:
        item.organizer = data["organizer"]
    return item


def string_to_meeting_service_provider(provider_str: str) -> int:
    """Convert string to ThirdPartyMeetingServiceProvider enum"""
    provider_map = {
        "Invalid": zrc_sdk.ThirdPartyMeetingServiceProviderInvalid,
        "WebEx": zrc_sdk.ThirdPartyMeetingServiceProviderWebEx,
        "Skype": zrc_sdk.ThirdPartyMeetingServiceProviderSkype,
        "GoogleHangout": zrc_sdk.ThirdPartyMeetingServiceProviderGoogleHangout,
        "GoToMeeting": zrc_sdk.ThirdPartyMeetingServiceProviderGoToMeeting,
        "Others": zrc_sdk.ThirdPartyMeetingServiceProviderOthers,
        "Teams": zrc_sdk.ThirdPartyMeetingServiceProviderTeams,
        "GoogleMeet": zrc_sdk.ThirdPartyMeetingServiceProviderGoogleMeet,
    }
    if provider_str not in provider_map:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {provider_str}")
    return provider_map[provider_str]


# ===== PSTN Endpoints =====

@router.post("/pstn/callout")
async def callout_pstn_user(
    room_id: str,
    request: CallOutPSTNRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Call out a PSTN user"""
    third_party_helper = get_third_party_helper(room_id, room_manager)
    result = third_party_helper.CallOutPSTNUser(
        request.phone_number,
        request.cancel_call,
        request.has_voice_prompt
    )

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to call out PSTN user: {result}")

    action = "cancelled" if request.cancel_call else "initiated"
    return {
        "message": f"PSTN call {action}",
        "phone_number": request.phone_number
    }


@router.post("/pstn/switch-to-meeting")
async def switch_pstn_to_meeting(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Switch PSTN call to normal Zoom meeting"""
    third_party_helper = get_third_party_helper(room_id, room_manager)
    result = third_party_helper.SwitchPstnCallToMeeting()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to switch PSTN to meeting: {result}")

    return {"message": "PSTN call switched to Zoom meeting"}


# ===== Third Party Meeting Endpoints (PSTN/SIP) =====

@router.post("/meeting/start-by-pstn")
async def start_meeting_by_pstn(
    room_id: str,
    meeting_data: dict,
    room_manager = Depends(lambda: get_room_manager())
):
    """Start third party meeting by PSTN call"""
    third_party_helper = get_third_party_helper(room_id, room_manager)
    meeting_item = meeting_item_from_dict(meeting_data)
    result = third_party_helper.StartThirdPartyMeetingByPSTNCall(meeting_item)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to start third party meeting by PSTN: {result}")

    return {"message": "Third party meeting started by PSTN"}


@router.post("/meeting/start-by-room-system")
async def start_meeting_by_room_system(
    room_id: str,
    meeting_data: dict,
    room_manager = Depends(lambda: get_room_manager())
):
    """Start third party meeting by room system call (SIP/H.323)"""
    third_party_helper = get_third_party_helper(room_id, room_manager)
    meeting_item = meeting_item_from_dict(meeting_data)
    result = third_party_helper.StartThirdPartyMeetingByRoomSystemCall(meeting_item)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to start third party meeting by room system: {result}")

    return {"message": "Third party meeting started by room system call"}


# ===== Integration Meeting Endpoints (Teams, Google Meet, etc.) =====

@router.post("/integration/start")
async def start_integration_meeting(
    room_id: str,
    meeting_data: dict,
    room_manager = Depends(lambda: get_room_manager())
):
    """Start integration meeting from meeting list (Teams, Google Meet, etc.)"""
    third_party_helper = get_third_party_helper(room_id, room_manager)
    meeting_item = meeting_item_from_dict(meeting_data)
    result = third_party_helper.StartIntegrationMeeting(meeting_item)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to start integration meeting: {result}")

    return {"message": "Integration meeting started"}


@router.post("/integration/join")
async def join_integration_meeting(
    room_id: str,
    request: JoinIntegrationMeetingRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Join integration meeting via meeting ID"""
    third_party_helper = get_third_party_helper(room_id, room_manager)
    provider = string_to_meeting_service_provider(request.provider)
    result = third_party_helper.JoinIntegrationMeeting(
        request.meeting_id,
        request.password,
        provider
    )

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to join integration meeting: {result}")

    return {
        "message": "Joining integration meeting",
        "meeting_id": request.meeting_id,
        "provider": request.provider
    }


@router.post("/integration/rejoin")
async def rejoin_integration_meeting(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Rejoin the current integration meeting"""
    third_party_helper = get_third_party_helper(room_id, room_manager)
    result = third_party_helper.RejoinIntegrationMeeting()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to rejoin integration meeting: {result}")

    return {"message": "Rejoining integration meeting"}


@router.post("/integration/leave")
async def leave_integration_meeting(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Leave the current integration meeting"""
    third_party_helper = get_third_party_helper(room_id, room_manager)
    result = third_party_helper.LeaveIntegrationMeeting()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to leave integration meeting: {result}")

    return {"message": "Left integration meeting"}


# ===== Integration Meeting Controls =====

@router.post("/integration/audio")
async def mute_integration_audio(
    room_id: str,
    request: MuteAudioRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Mute or unmute audio in integration meeting"""
    third_party_helper = get_third_party_helper(room_id, room_manager)
    result = third_party_helper.MuteIntegrationAudio(request.mute)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to mute integration audio: {result}")

    return {"message": f"Integration audio {'muted' if request.mute else 'unmuted'}"}


@router.post("/integration/video")
async def stop_integration_video(
    room_id: str,
    request: StopVideoRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Stop or start video in integration meeting"""
    third_party_helper = get_third_party_helper(room_id, room_manager)
    result = third_party_helper.StopIntegrationVideo(request.stop)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to stop integration video: {result}")

    return {"message": f"Integration video {'stopped' if request.stop else 'started'}"}


@router.post("/integration/content-share")
async def stop_integration_content_share(
    room_id: str,
    request: StopContentShareRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Stop or start content sharing in integration meeting"""
    third_party_helper = get_third_party_helper(room_id, room_manager)
    result = third_party_helper.StopIntegrationContentShare(request.stop)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to stop integration content share: {result}")

    return {"message": f"Integration content share {'stopped' if request.stop else 'started'}"}


@router.post("/integration/layout")
async def change_integration_layout(
    room_id: str,
    request: ChangeLayoutRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Change layout in integration meeting"""
    third_party_helper = get_third_party_helper(room_id, room_manager)
    result = third_party_helper.ChangeIntegrationLayout(request.layout_type)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to change integration layout: {result}")

    return {
        "message": "Integration layout changed",
        "layout_type": request.layout_type
    }


# ===== Information Endpoints =====

@router.get("/interoperability/{meeting_type}")
async def get_interoperability_info(
    room_id: str,
    meeting_type: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Get interoperability information for a meeting type"""
    third_party_helper = get_third_party_helper(room_id, room_manager)
    provider = string_to_meeting_service_provider(meeting_type)
    result, info = third_party_helper.GetInterOperabilityInfoByMeetingType(provider)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to get interoperability info: {result}")

    return {
        "meeting_type": meeting_type,
        "support_join_meeting": info.supportJoinMeeting,
        "support_join_web_client": info.supportJoinWebClient,
        "support_sip_join": info.supportSipJoin,
        "support_phone_join": info.supportPhoneJoin,
        "is_pexip_enabled": info.isPexipEnabled
    }
