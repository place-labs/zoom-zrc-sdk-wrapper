"""
Recording Helper Controller
Handles meeting recording operations including cloud and local recording
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
import zrc_sdk

from sdk_errors import zrcsdk_error_name

router = APIRouter(prefix="/api/rooms/{room_id}/recording", tags=["recording"])

# Dependency injection placeholder - will be set by app.py
get_room_manager = None


# ===== Request Models =====

class RecordingNotificationEmailRequest(BaseModel):
    email: str


class AllowUserRecordingRequest(BaseModel):
    user_id: int
    allow: bool


class ResponseToRecordingRequestRequest(BaseModel):
    agree: bool
    is_persist: bool = False


class ChangeRecordingPermissionRequest(BaseModel):
    permission_type: str  # LocalRecording, RequestLocalRecording, RequestCloudRecording
    enable: bool


# ===== Helper Functions =====

def get_recording_helper(room_id: str, room_manager):
    """Get recording helper for a room"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail=f"Room {room_id} not found")

    meeting_service = room_service.GetMeetingService()
    if not meeting_service:
        raise HTTPException(status_code=404, detail=f"Meeting service not available for room {room_id}")

    recording_helper = meeting_service.GetRecordingHelper()
    if not recording_helper:
        raise HTTPException(status_code=404, detail=f"Recording helper not available for room {room_id}")
    return recording_helper


def recording_type_to_string(recording_type: int) -> str:
    """Convert recording type enum to string"""
    type_map = {
        zrc_sdk.RecordingTypeUnknown: "Unknown",
        zrc_sdk.RecordingTypeLocal: "Local",
        zrc_sdk.RecordingTypeCloud: "Cloud"
    }
    return type_map.get(recording_type, f"Unknown({recording_type})")


def permission_type_to_string(permission_type: int) -> str:
    """Convert permission type enum to string"""
    type_map = {
        zrc_sdk.RecordingPermissionTypeUnknown: "Unknown",
        zrc_sdk.RecordingPermissionTypeLocalRecording: "LocalRecording",
        zrc_sdk.RecordingPermissionTypeRequestLocalRecording: "RequestLocalRecording",
        zrc_sdk.RecordingPermissionTypeRequestCloudRecording: "RequestCloudRecording"
    }
    return type_map.get(permission_type, f"Unknown({permission_type})")


def permission_info_to_dict(info) -> dict:
    return {
        "type": int(info.type),
        "type_name": permission_type_to_string(info.type),
        "is_enabled": info.isEnable,
        "is_locked": info.isLocked,
    }


def raise_recording_sdk_error(message: str, result, status_code: int = 500) -> None:
    """Expose a stable non-success contract for recording SDK failures."""
    raise HTTPException(
        status_code=status_code,
        detail={
            "message": message,
            "error_code": int(result),
            "error_name": zrcsdk_error_name(result),
        },
    )


# ===== Endpoints =====

@router.post("/confirm-error")
async def confirm_recording_error(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Confirm recording error to close error dialog"""
    recording_helper = get_recording_helper(room_id, room_manager)
    result = recording_helper.ConfirmRecordingError()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to confirm recording error: {result}")

    return {"message": "Recording error confirmed"}


@router.get("/disclaimer-needed")
async def check_disclaimer_needed(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Check if recording disclaimer prompt is needed"""
    recording_helper = get_recording_helper(room_id, room_manager)
    result, need = recording_helper.IsNeedPromptStartRecordingDisclaimer()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to check disclaimer status: {result}")

    return {
        "disclaimer_needed": need
    }


@router.post("/prompt-disclaimer")
async def prompt_disclaimer(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Prompt recording disclaimer on Zoom Room"""
    recording_helper = get_recording_helper(room_id, room_manager)
    result = recording_helper.PromptStartRecordingDisclaimer()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to prompt disclaimer: {result}")

    return {"message": "Recording disclaimer prompt sent"}


@router.get("/storage-status")
async def check_storage_status(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Check if cloud recording storage is full"""
    recording_helper = get_recording_helper(room_id, room_manager)
    result, full = recording_helper.IsMeetingCMRNoStorage()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to check storage status: {result}")

    return {
        "storage_full": full
    }


@router.post("/query-storage")
async def query_storage(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Query current meeting recording storage status"""
    recording_helper = get_recording_helper(room_id, room_manager)
    result = recording_helper.QueryMeetingRecordingStorage()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to query storage: {result}")

    return {"message": "Storage query initiated"}


@router.post("/notification-email")
async def set_notification_email(
    room_id: str,
    request: RecordingNotificationEmailRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Set recording notification email"""
    recording_helper = get_recording_helper(room_id, room_manager)
    result = recording_helper.SetMeetingRecordingNotificationEmail(request.email)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise_recording_sdk_error("Failed to set notification email", result)

    return {"message": f"Notification email set to {request.email}"}


@router.post("/cloud/start")
async def start_cloud_recording(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Start cloud recording"""
    recording_helper = get_recording_helper(room_id, room_manager)

    precheck = {}
    try:
        result, need_disclaimer = recording_helper.IsNeedPromptStartRecordingDisclaimer()
        precheck["disclaimer_check_result"] = int(result)
        precheck["disclaimer_needed"] = need_disclaimer if result == zrc_sdk.ZRCSDKERR_SUCCESS else None
    except Exception:
        precheck["disclaimer_check_result"] = None

    try:
        result, storage_full = recording_helper.IsMeetingCMRNoStorage()
        precheck["storage_check_result"] = int(result)
        precheck["storage_full"] = storage_full if result == zrc_sdk.ZRCSDKERR_SUCCESS else None
    except Exception:
        precheck["storage_check_result"] = None

    try:
        result, permissions = recording_helper.GetRecoringPemissionInfo()
        precheck["permission_check_result"] = int(result)
        if result == zrc_sdk.ZRCSDKERR_SUCCESS:
            precheck["recording_permissions"] = [permission_info_to_dict(item) for item in permissions]
    except Exception:
        precheck["permission_check_result"] = None

    if precheck.get("disclaimer_needed"):
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Recording disclaimer required before starting cloud recording",
                "precheck": precheck,
                "next_step": "POST /api/rooms/{room_id}/recording/prompt-disclaimer",
            },
        )

    if precheck.get("storage_full"):
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Cloud recording storage is full",
                "precheck": precheck,
                "next_step": "POST /api/rooms/{room_id}/recording/query-storage",
            },
        )

    result = recording_helper.StartMeetingCloudRecording()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to start cloud recording",
                "error_code": int(result),
                "error_name": zrcsdk_error_name(result),
                "precheck": precheck,
            },
        )

    return {"message": "Cloud recording started"}


@router.post("/cloud/stop")
async def stop_cloud_recording(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Stop cloud recording"""
    recording_helper = get_recording_helper(room_id, room_manager)
    result = recording_helper.StopMeetingCloudRecording()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to stop cloud recording",
                "error_code": int(result),
                "error_name": zrcsdk_error_name(result),
            },
        )

    return {"message": "Cloud recording stopped"}


@router.post("/cloud/pause")
async def pause_cloud_recording(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Pause cloud recording"""
    recording_helper = get_recording_helper(room_id, room_manager)
    result = recording_helper.PauseMeetingCloudRecording()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to pause cloud recording: {result}")

    return {"message": "Cloud recording paused"}


@router.post("/cloud/resume")
async def resume_cloud_recording(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Resume cloud recording"""
    recording_helper = get_recording_helper(room_id, room_manager)
    result = recording_helper.ResumeMeetingCloudRecording()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to resume cloud recording: {result}")

    return {"message": "Cloud recording resumed"}


@router.post("/allow-user")
async def allow_user_recording(
    room_id: str,
    request: AllowUserRecordingRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Allow or disallow user to record"""
    recording_helper = get_recording_helper(room_id, room_manager)
    result = recording_helper.AllowUserRecording(request.user_id, request.allow)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to set user recording permission: {result}")

    return {
        "message": f"User {request.user_id} recording {'allowed' if request.allow else 'disallowed'}",
        "user_id": request.user_id,
        "allowed": request.allow
    }


@router.post("/respond-to-request")
async def respond_to_recording_request(
    room_id: str,
    request: ResponseToRecordingRequestRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Respond to recording request from participant"""
    recording_helper = get_recording_helper(room_id, room_manager)
    result = recording_helper.ResponseToRecordingRequest(request.agree, request.is_persist)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise_recording_sdk_error(
            "Failed to respond to recording request", result, status_code=502
        )

    return {
        "message": f"Recording request {'approved' if request.agree else 'denied'}",
        "agreed": request.agree,
        "persist": request.is_persist
    }


@router.post("/change-permission")
async def change_recording_permission(
    room_id: str,
    request: ChangeRecordingPermissionRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Change recording permission in meeting"""
    recording_helper = get_recording_helper(room_id, room_manager)

    permission_type_map = {
        "LocalRecording": zrc_sdk.RecordingPermissionTypeLocalRecording,
        "RequestLocalRecording": zrc_sdk.RecordingPermissionTypeRequestLocalRecording,
        "RequestCloudRecording": zrc_sdk.RecordingPermissionTypeRequestCloudRecording
    }

    if request.permission_type not in permission_type_map:
        raise HTTPException(status_code=400, detail=f"Invalid permission type: {request.permission_type}")

    permission_type = permission_type_map[request.permission_type]
    result = recording_helper.ChangeRecordingPermission(permission_type, request.enable)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to change recording permission: {result}")

    return {
        "message": f"Recording permission {request.permission_type} {'enabled' if request.enable else 'disabled'}",
        "permission_type": request.permission_type,
        "enabled": request.enable
    }


@router.get("/permissions")
async def get_recording_permissions(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Get current recording permissions"""
    recording_helper = get_recording_helper(room_id, room_manager)
    result, permission_info = recording_helper.GetRecoringPemissionInfo()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to get recording permissions: {result}")

    permissions = []
    for perm in permission_info:
        permissions.append({
            "type": permission_type_to_string(perm.type),
            "is_enable": perm.isEnable,
            "is_locked": perm.isLocked
        })

    return {
        "permissions": permissions
    }
