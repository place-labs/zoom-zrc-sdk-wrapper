"""
Meeting endpoints - join, exit, audio/video controls
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Callable

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
        result = meeting_service.JoinMeeting(request.meeting_number, request.password or "")

        return {
            "room_id": room_id,
            "meeting_number": request.meeting_number,
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


@router.post("/audio/mute")
async def mute_audio(room_id: str, mute: bool = True, room_manager = Depends(lambda: get_room_manager())):
    """Mute or unmute the room's audio"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        audio_helper = meeting_service.GetMeetingAudioHelper()
        result = audio_helper.UpdateMyAudioStatus(mute)

        return {
            "room_id": room_id,
            "muted": mute,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/video/mute")
async def mute_video(room_id: str, mute: bool = True, room_manager = Depends(lambda: get_room_manager())):
    """Mute (stop) or unmute (start) the room's video"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        video_helper = meeting_service.GetMeetingVideoHelper()
        # Note: UpdateMyVideo parameter is "stop", so we pass mute directly
        result = video_helper.UpdateMyVideo(mute)

        return {
            "room_id": room_id,
            "muted": mute,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
