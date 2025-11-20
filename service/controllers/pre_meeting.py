"""
Pre-Meeting Service Controller
Handles pre-meeting operations like connection state, problem reports, and room management
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import zrc_sdk

router = APIRouter(prefix="/api/rooms/{room_id}/pre-meeting", tags=["pre-meeting"])

# Dependency injection placeholder - will be set by app.py
get_room_manager = None


# ===== Request Models =====

class ProblemReportRequest(BaseModel):
    subject: str
    body: str
    log_type: str = "Basic"  # Basic, Audio, ContentSharing, CrashDump


# ===== Helper Functions =====

def get_pre_meeting_service(room_id: str, room_manager):
    """Get pre-meeting service for a room"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail=f"Room {room_id} not found")
    return room_service.GetPreMeetingService()


def connection_state_to_string(state: int) -> str:
    """Convert connection state enum to string"""
    state_map = {
        zrc_sdk.ConnectionStateNone: "None",
        zrc_sdk.ConnectionStateEstablished: "Established",
        zrc_sdk.ConnectionStateConnected: "Connected",
        zrc_sdk.ConnectionStateDisconnected: "Disconnected"
    }
    return state_map.get(state, f"Unknown({state})")


# ===== Endpoints =====

@router.get("/connection-state")
async def get_connection_state(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Get connection state with Zoom Room"""
    pre_meeting_service = get_pre_meeting_service(room_id, room_manager)
    result, state = pre_meeting_service.GetConnectionState()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to get connection state: {result}")

    return {
        "connection_state": connection_state_to_string(state),
        "connection_state_value": int(state)
    }


@router.post("/problem-report")
async def send_problem_report(
    room_id: str,
    request: ProblemReportRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Send problem report to Zoom"""
    pre_meeting_service = get_pre_meeting_service(room_id, room_manager)

    # Map log type string to enum
    log_type_map = {
        "Basic": zrc_sdk.LogTypeBasic,
        "Audio": zrc_sdk.LogTypeAudio,
        "ContentSharing": zrc_sdk.LogTypeContentSharing,
        "CrashDump": zrc_sdk.LogTypeCrashDump
    }

    log_type = log_type_map.get(request.log_type, zrc_sdk.LogTypeBasic)

    result = pre_meeting_service.NotifyZoomRoomsSendProblemReport(
        request.subject,
        request.body,
        log_type
    )

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to send problem report: {result}")

    return {
        "message": "Problem report sent successfully",
        "subject": request.subject,
        "log_type": request.log_type
    }


@router.get("/restart-os-support")
async def check_restart_os_support(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Check if Zoom Room supports restart OS"""
    pre_meeting_service = get_pre_meeting_service(room_id, room_manager)
    result, support = pre_meeting_service.IsZoomRoomSupportRestartOS()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to check restart OS support: {result}")

    return {
        "supports_restart_os": support
    }


@router.post("/restart-os")
async def restart_zoom_room_os(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Restart Zoom Room OS (displays, scheduling displays, and controllers)"""
    pre_meeting_service = get_pre_meeting_service(room_id, room_manager)
    result = pre_meeting_service.RestartZoomRoomOS()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to restart Zoom Room OS: {result}")

    return {
        "message": "Zoom Room OS restart initiated"
    }


@router.post("/logout")
async def logout_zoom_room_device(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Logout Zoom Room and other paired devices"""
    pre_meeting_service = get_pre_meeting_service(room_id, room_manager)
    result = pre_meeting_service.LogoutZoomRoomDevice()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to logout Zoom Room device: {result}")

    return {
        "message": "Zoom Room device logout initiated"
    }


@router.post("/wake-up")
async def wake_zoom_room_up(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Wake Zoom Room up"""
    pre_meeting_service = get_pre_meeting_service(room_id, room_manager)
    result = pre_meeting_service.WakeZoomRoomUp()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to wake Zoom Room up: {result}")

    return {
        "message": "Zoom Room wake up command sent"
    }
