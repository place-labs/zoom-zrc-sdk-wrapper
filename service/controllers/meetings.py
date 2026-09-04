"""
Meeting endpoints - join, exit, audio/video controls
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Callable, List

try:
    import zrc_sdk
except ImportError:
    print("ERROR: zrc_sdk module not found.")
    raise

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rooms/{room_id}", tags=["meetings"])

# This will be set by app.py
get_room_manager: Callable = None


# ===== Pydantic Models =====

class JoinMeetingRequest(BaseModel):
    meeting_number: str
    password: str | None = ""
    bring_share: bool = False


class StartMeetingRequest(BaseModel):
    meeting_number: str
    meeting_name: str = ""
    host_name: str = ""
    start_time: str = ""
    end_time: str = ""
    bring_share: bool = False


class InviteAttendeesRequest(BaseModel):
    contact_ids: List[str]


class InviteRoomSystemRequest(BaseModel):
    ip_or_e164: str
    protocol_type: str = "H323"  # H323 or SIP
    cancel: bool = False


class SendEmailRequest(BaseModel):
    recipients: str  # Semicolon-separated emails


class SendDTMFRequest(BaseModel):
    digit_key: str
    user_id: int = 0


# ===== Endpoints =====

@router.post("/meeting/start_instant")
async def start_instant_meeting(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """Start an instant meeting"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        result = meeting_service.StartInstantMeeting()

        return {
            "room_id": room_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meeting/join")
async def join_meeting(room_id: str, request: JoinMeetingRequest, room_manager = Depends(lambda: get_room_manager())):
    """Join a meeting by meeting number"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        result = meeting_service.JoinMeetingWithMeetingNumber(request.meeting_number, request.bring_share)

        return {
            "room_id": room_id,
            "meeting_number": request.meeting_number,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meeting/join-url")
async def join_meeting_url(room_id: str, url: str, room_manager = Depends(lambda: get_room_manager())):
    """Join a meeting by URL. Local sharing is not supported by SDK 6.7+."""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        result = meeting_service.JoinMeetingWithURL(url)

        return {
            "room_id": room_id,
            "url": url,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meeting/join-contact")
async def join_meeting_contact(room_id: str, contact_id: str, bring_share: bool = False, room_manager = Depends(lambda: get_room_manager())):
    """Join a meeting by contact ID"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        # Note: bring_share parameter removed in SDK 6.7+
        result = meeting_service.JoinMeetingWithContactID(contact_id)

        return {
            "room_id": room_id,
            "contact_id": contact_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meeting/start")
async def start_meeting(room_id: str, request: StartMeetingRequest, room_manager = Depends(lambda: get_room_manager())):
    """Start a scheduled meeting"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()

        # Create meeting item
        meeting_item = zrc_sdk.MeetingItem()
        meeting_item.meetingNumber = request.meeting_number
        meeting_item.meetingName = request.meeting_name
        meeting_item.hostName = request.host_name
        meeting_item.startTime = request.start_time
        meeting_item.endTime = request.end_time

        result = meeting_service.StartMeeting(meeting_item, request.bring_share)

        return {
            "room_id": room_id,
            "meeting_number": request.meeting_number,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meeting/start-hostkey")
async def start_meeting_hostkey(room_id: str, host_key: str, room_manager = Depends(lambda: get_room_manager())):
    """Start a meeting with host key"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        result = meeting_service.StartMeetingWithHostKey(host_key)

        return {
            "room_id": room_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meeting/meet-with-users")
async def meet_with_users(room_id: str, request: InviteAttendeesRequest, room_manager = Depends(lambda: get_room_manager())):
    """Start instant meeting and invite IM users"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        result = meeting_service.MeetWithIMUsers(request.contact_ids)

        return {
            "room_id": room_id,
            "contact_ids": request.contact_ids,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meeting/exit")
async def exit_meeting(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """Exit the current meeting"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        result = meeting_service.ExitMeeting(zrc_sdk.ExitMeetingCmdLeave)

        return {
            "room_id": room_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Audio/video mute is modeled strictly as verb endpoints (`/mute` + `/unmute`).
# FastAPI normally ignores unknown query params, which would make a legacy
# `/mute?mute=false` request silently mute the room. Reject the old state params
# explicitly so stale clients fail loudly instead of applying the wrong state.


def _reject_legacy_mute_query(request: Request):
    legacy = sorted({"mute", "stop"}.intersection(request.query_params))
    if legacy:
        raise HTTPException(
            status_code=422,
            detail="state query parameters are unsupported; use /mute or /unmute",
        )


def _set_audio_muted(room_id: str, muted: bool, room_manager):
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        audio_helper = meeting_service.GetMeetingAudioHelper()
        result = audio_helper.UpdateMyAudioStatus(muted)

        return {
            "room_id": room_id,
            "muted": muted,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/audio/mute")
async def mute_audio(
    room_id: str,
    request: Request,
    room_manager = Depends(lambda: get_room_manager()),
):
    """Mute the room's audio."""
    _reject_legacy_mute_query(request)
    return _set_audio_muted(room_id, True, room_manager)


@router.post("/audio/unmute")
async def unmute_audio(room_id: str, request: Request, room_manager = Depends(lambda: get_room_manager())):
    """Unmute the room's audio."""
    _reject_legacy_mute_query(request)
    return _set_audio_muted(room_id, False, room_manager)


@router.post("/audio/answer-unmute-request")
async def answer_unmute_audio_request(
    room_id: str,
    accepted: bool,
    room_manager = Depends(lambda: get_room_manager()),
):
    """Accept or deny a host's request for the room to unmute audio."""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        audio_helper = meeting_service.GetMeetingAudioHelper()
        result = audio_helper.AnswerUnmuteAudioByHostRequest(accepted)

        return {
            "room_id": room_id,
            "accepted": accepted,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _set_video_muted(room_id: str, muted: bool, room_manager):
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        video_helper = meeting_service.GetMeetingVideoHelper()
        # UpdateMyVideo's parameter is "stop"; muted == stop the video.
        result = video_helper.UpdateMyVideo(muted)

        return {
            "room_id": room_id,
            "muted": muted,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/video/mute")
async def mute_video(
    room_id: str,
    request: Request,
    room_manager = Depends(lambda: get_room_manager()),
):
    """Stop (mute) the room's video."""
    _reject_legacy_mute_query(request)
    return _set_video_muted(room_id, True, room_manager)


@router.post("/video/unmute")
async def unmute_video(room_id: str, request: Request, room_manager = Depends(lambda: get_room_manager())):
    """Start (unmute) the room's video."""
    _reject_legacy_mute_query(request)
    return _set_video_muted(room_id, False, room_manager)


@router.post("/meeting/password/send")
async def send_password(room_id: str, password: str, room_manager = Depends(lambda: get_room_manager())):
    """Send meeting password to join meeting"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        result = meeting_service.SendMeetingPassword(password)

        return {
            "room_id": room_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meeting/password/cancel")
async def cancel_password(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """Cancel entering meeting password"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        result = meeting_service.CancelEnteringMeetingPassword()

        return {
            "room_id": room_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meeting/cancel-waiting-host")
async def cancel_waiting_host(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """Cancel waiting for host"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        result = meeting_service.CancelWaitingForHost()

        return {
            "room_id": room_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meeting/invite/attendees")
async def invite_attendees(room_id: str, request: InviteAttendeesRequest, room_manager = Depends(lambda: get_room_manager())):
    """Invite attendees into current meeting"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        result = meeting_service.InviteAttendees(request.contact_ids)

        return {
            "room_id": room_id,
            "contact_ids": request.contact_ids,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meeting/invite/room-system")
async def invite_room_system(room_id: str, request: InviteRoomSystemRequest, room_manager = Depends(lambda: get_room_manager())):
    """Invite legacy room system into meeting"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()

        # Map protocol type string to enum
        protocol_map = {
            "H323": zrc_sdk.RoomSystemProtocolTypeH323,
            "SIP": zrc_sdk.RoomSystemProtocolTypeSIP
        }
        protocol = protocol_map.get(request.protocol_type.upper(), zrc_sdk.RoomSystemProtocolTypeH323)

        result = meeting_service.InviteLegacyRoomSystemWithIpOrE164Number(
            request.ip_or_e164,
            protocol,
            request.cancel
        )

        return {
            "room_id": room_id,
            "ip_or_e164": request.ip_or_e164,
            "protocol": request.protocol_type,
            "cancel": request.cancel,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meeting/invite/email")
async def send_invite_email(room_id: str, request: SendEmailRequest, room_manager = Depends(lambda: get_room_manager())):
    """Send meeting invite email to recipients"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        result = meeting_service.SendMeetingInviteEmail(request.recipients)

        return {
            "room_id": room_id,
            "recipients": request.recipients,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meeting/dtmf")
async def send_dtmf(room_id: str, request: SendDTMFRequest, room_manager = Depends(lambda: get_room_manager())):
    """Send DTMF when dialing"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        result = meeting_service.SendDTMF(request.digit_key, request.user_id)

        return {
            "room_id": room_id,
            "digit_key": request.digit_key,
            "user_id": request.user_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meeting/set-temp-name")
async def set_temp_name(room_id: str, temp_name: str, room_manager = Depends(lambda: get_room_manager())):
    """Set room's temp display name for meeting"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        result = meeting_service.SetRoomTempDisplayNameForMeeting(temp_name)

        return {
            "room_id": room_id,
            "temp_name": temp_name,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meeting/extend")
async def extend_meeting(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """Extend zoom meeting scheduled with automatically stop"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        result = meeting_service.ExtendMeeting()

        return {
            "room_id": room_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meeting/e2e-security-code/request")
async def request_e2e_code(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """Request end-to-end security code"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        result = meeting_service.RequestE2ESecurityCode()

        return {
            "room_id": room_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/meeting/status")
async def get_meeting_status(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """Get meeting status"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        result, status = meeting_service.GetMeetingStatus()

        return {
            "room_id": room_id,
            "status": str(status),
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/meeting/info")
async def get_meeting_info(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """Get meeting information"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        result, info = meeting_service.GetMeetingInfo()

        if result == zrc_sdk.ZRCSDKERR_SUCCESS:
            return {
                "room_id": room_id,
                "meeting_id": info.meetingID,
                "meeting_number": info.meetingNumber,
                "meeting_name": info.meetingName,
                "meeting_password": info.meetingPassword,
                "is_webinar": info.isWebinar,
                "is_waiting_room": info.isWaitingRoom,
                "my_user_id": info.myUserId,
                "join_meeting_url": info.joinMeetingUrl,
                "result": int(result),
                "success": True
            }
        else:
            return {
                "room_id": room_id,
                "result": int(result),
                "success": False
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
