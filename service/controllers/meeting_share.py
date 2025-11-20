"""
Meeting share endpoints - screen sharing, HDMI, camera, breakout room sharing
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

router = APIRouter(prefix="/api/rooms/{room_id}/share", tags=["meeting-share"])

# This will be set by app.py
get_room_manager: Callable = None


# ===== Pydantic Models =====

class LaunchSharingMeetingRequest(BaseModel):
    is_local_share: bool = False
    display_state: str = "None"  # None, Desktop, iOS, WhiteboardCamera


class ShowSharingInstructionRequest(BaseModel):
    show: bool
    instruction_state: str = "None"  # None, Desktop, iOS, WhiteboardCamera


class ShareBlackMagicRequest(BaseModel):
    start: bool
    view_locally: bool = False


class ShareCameraRequest(BaseModel):
    start: bool
    device_id: str


class PinShareRequest(BaseModel):
    user_id: int
    share_source_id: int
    share_source_type: str = "Normal"  # Unknown, Normal, CloudWB, CollaborationZapps
    screen_index: int
    confirmed: bool = False


class PinIncomingShareRequest(BaseModel):
    user_id: int
    share_source_id: int
    current_share_type: str = "Unknown"  # Unknown, Normal, Camera, Annotated, ZoomApp, Whiteboard, LocalHDMI, AnnotatedLocalHDMI
    pin: bool


class ControlSlideRequest(BaseModel):
    user_id: int
    user_name: str = ""
    share_source_id: int
    operation: str = "Right"  # Left, Right


class MuteShareAudioRequest(BaseModel):
    user_id: int
    share_source_id: int
    mute: bool


class SetMeetingShareSettingRequest(BaseModel):
    privilege_type: str = "HostGrab"  # Unknown, HostGrab, LockShare, AnyoneGrab, MultiShare


class SetMeetingShareViewPrivilegeRequest(BaseModel):
    privilege: str = "FocusModeOff"  # FocusModeOff, FocusModeHostOnly, FocusModeAllParticipants


class DocsSharePrivilegeRequest(BaseModel):
    privilege_type: str = "HostGrab"  # Unknown, HostGrab, AnyoneGrab


class DocsInitiatePrivilegeRequest(BaseModel):
    privilege_type: str = "HostOnly"  # Unknown, HostOnly, InternalUsers, AllParticipants


# ===== Endpoints =====

@router.post("/launch")
async def launch_sharing_meeting(
    room_id: str,
    request: LaunchSharingMeetingRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Launch a sharing meeting or local presentation"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        share_helper = meeting_service.GetMeetingShareHelper()

        # Map display state
        display_state_map = {
            "None": zrc_sdk.SharingInstructionDisplayStateNone,
            "Desktop": zrc_sdk.SharingInstructionDisplayStateDesktop,
            "iOS": zrc_sdk.SharingInstructionDisplayStateIOS,
            "WhiteboardCamera": zrc_sdk.SharingInstructionDisplayStateWhiteboardCamera
        }
        display_state = display_state_map.get(request.display_state, zrc_sdk.SharingInstructionDisplayStateNone)

        result = share_helper.LaunchSharingMeeting(request.is_local_share, display_state)

        return {
            "room_id": room_id,
            "is_local_share": request.is_local_share,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/switch-to-normal")
async def switch_to_normal_meeting(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """Switch from local presentation to normal meeting"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        share_helper = meeting_service.GetMeetingShareHelper()
        result = share_helper.SwitchFromLocalPresentationToNormalMeeting()

        return {
            "room_id": room_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/instruction")
async def show_sharing_instruction(
    room_id: str,
    request: ShowSharingInstructionRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Show or dismiss sharing instruction on ZR screen"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        share_helper = meeting_service.GetMeetingShareHelper()

        # Map instruction state
        instruction_state_map = {
            "None": zrc_sdk.SharingInstructionDisplayStateNone,
            "Desktop": zrc_sdk.SharingInstructionDisplayStateDesktop,
            "iOS": zrc_sdk.SharingInstructionDisplayStateIOS,
            "WhiteboardCamera": zrc_sdk.SharingInstructionDisplayStateWhiteboardCamera
        }
        instruction_state = instruction_state_map.get(request.instruction_state, zrc_sdk.SharingInstructionDisplayStateNone)

        result = share_helper.ShowSharingInstruction(request.show, instruction_state)

        return {
            "room_id": room_id,
            "show": request.show,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hdmi")
async def share_hdmi(
    room_id: str,
    request: ShareBlackMagicRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Start or stop HDMI sharing"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        share_helper = meeting_service.GetMeetingShareHelper()
        result = share_helper.ShareBlackMagic(request.start, request.view_locally)

        return {
            "room_id": room_id,
            "start": request.start,
            "view_locally": request.view_locally,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/camera")
async def share_camera(
    room_id: str,
    request: ShareCameraRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Start or stop camera sharing"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        share_helper = meeting_service.GetMeetingShareHelper()
        result = share_helper.ShareCamera(request.start, request.device_id)

        return {
            "room_id": room_id,
            "start": request.start,
            "device_id": request.device_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/breakout-rooms/start")
async def share_to_breakout_rooms(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """Share current source to all breakout rooms"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        share_helper = meeting_service.GetMeetingShareHelper()
        result = share_helper.ShareToBreakoutRooms()

        return {
            "room_id": room_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/breakout-rooms/stop")
async def stop_share_to_breakout_rooms(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """Stop sharing to breakout rooms"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        share_helper = meeting_service.GetMeetingShareHelper()
        result = share_helper.StopShareToBreakoutRooms()

        return {
            "room_id": room_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_sharing(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """Stop Zoom Room's sharing"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        share_helper = meeting_service.GetMeetingShareHelper()
        result = share_helper.StopSharing()

        return {
            "room_id": room_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/zrw/stop")
async def stop_zrw_sharing(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """Stop Zoom Room Companion Whiteboard's sharing"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        share_helper = meeting_service.GetMeetingShareHelper()
        result = share_helper.StopZRWSharing()

        return {
            "room_id": room_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multi-share")
async def enable_multi_share(room_id: str, enabled: bool, room_manager = Depends(lambda: get_room_manager())):
    """Enable or disable multi-share for current meeting"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        share_helper = meeting_service.GetMeetingShareHelper()
        result = share_helper.EnableMultiShare(enabled)

        return {
            "room_id": room_id,
            "enabled": enabled,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pin-instruction")
async def show_pin_share_instruction(room_id: str, show: bool, room_manager = Depends(lambda: get_room_manager())):
    """Show or hide screen index for pin share"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        share_helper = meeting_service.GetMeetingShareHelper()
        result = share_helper.ShowPinShareInstruction(show)

        return {
            "room_id": room_id,
            "show": show,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pin/zr")
async def pin_share_on_zr(
    room_id: str,
    request: PinShareRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Pin share source on Zoom Room's screen"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        share_helper = meeting_service.GetMeetingShareHelper()

        # Create share source
        share_source = zrc_sdk.ShareSource()
        share_source.userID = request.user_id
        share_source.shareSourceID = request.share_source_id

        # Map share source type
        source_type_map = {
            "Unknown": zrc_sdk.ShareSourceTypeUnknown,
            "Normal": zrc_sdk.ShareSourceTypeNormal,
            "CloudWB": zrc_sdk.ShareSourceTypeCloudWB,
            "CollaborationZapps": zrc_sdk.ShareSourceTypeCollaborationZapps
        }
        share_source.shareSourceType = source_type_map.get(request.share_source_type, zrc_sdk.ShareSourceTypeNormal)

        result = share_helper.PinShareOnZRScreen(share_source, request.screen_index, request.confirmed)

        return {
            "room_id": room_id,
            "user_id": request.user_id,
            "share_source_id": request.share_source_id,
            "screen_index": request.screen_index,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pin/zrw")
async def pin_share_on_zrw(
    room_id: str,
    request: PinShareRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Pin share source on Zoom Room Companion Whiteboard's screen"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        share_helper = meeting_service.GetMeetingShareHelper()

        # Create share source
        share_source = zrc_sdk.ShareSource()
        share_source.userID = request.user_id
        share_source.shareSourceID = request.share_source_id

        # Map share source type
        source_type_map = {
            "Unknown": zrc_sdk.ShareSourceTypeUnknown,
            "Normal": zrc_sdk.ShareSourceTypeNormal,
            "CloudWB": zrc_sdk.ShareSourceTypeCloudWB,
            "CollaborationZapps": zrc_sdk.ShareSourceTypeCollaborationZapps
        }
        share_source.shareSourceType = source_type_map.get(request.share_source_type, zrc_sdk.ShareSourceTypeNormal)

        result = share_helper.PinShareOnZRWScreen(share_source, request.screen_index)

        return {
            "room_id": room_id,
            "user_id": request.user_id,
            "share_source_id": request.share_source_id,
            "screen_index": request.screen_index,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pin/incoming")
async def pin_incoming_share(
    room_id: str,
    request: PinIncomingShareRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Pin incoming meeting share"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        share_helper = meeting_service.GetMeetingShareHelper()

        # Create incoming share source
        share_source = zrc_sdk.ShareSource()
        share_source.userID = request.user_id
        share_source.shareSourceID = request.share_source_id

        # Map current share type
        share_type_map = {
            "Unknown": zrc_sdk.CurrentShareTypeUnknown,
            "Normal": zrc_sdk.CurrentShareTypeNormal,
            "Camera": zrc_sdk.CurrentShareTypeCamera,
            "Annotated": zrc_sdk.CurrentShareTypeAnnotated,
            "ZoomApp": zrc_sdk.CurrentShareTypeZoomApp,
            "Whiteboard": zrc_sdk.CurrentShareTypeWhiteboard,
            "LocalHDMI": zrc_sdk.CurrentShareTypeLocalHDMI,
            "AnnotatedLocalHDMI": zrc_sdk.CurrentShareTypeAnnotatedLocalHDMI
        }
        current_share = share_type_map.get(request.current_share_type, zrc_sdk.CurrentShareTypeUnknown)

        result = share_helper.PinIncomingMeetingShare(share_source, current_share, request.pin)

        return {
            "room_id": room_id,
            "user_id": request.user_id,
            "pin": request.pin,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/slide/control")
async def control_slide(
    room_id: str,
    request: ControlSlideRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Control slide (left/right)"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        share_helper = meeting_service.GetMeetingShareHelper()

        # Create slide control info
        slide_info = zrc_sdk.SlideControlInfo()
        slide_info.userID = request.user_id
        slide_info.userName = request.user_name
        slide_info.shareSourceID = request.share_source_id

        # Map operation type
        operation_map = {
            "Left": zrc_sdk.SlideOperationTypeLeft,
            "Right": zrc_sdk.SlideOperationTypeRight
        }
        operation = operation_map.get(request.operation, zrc_sdk.SlideOperationTypeRight)

        result = share_helper.ControlSlide(slide_info, operation)

        return {
            "room_id": room_id,
            "operation": request.operation,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/audio/mute")
async def mute_share_audio(
    room_id: str,
    request: MuteShareAudioRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Mute or unmute sharing audio"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        share_helper = meeting_service.GetMeetingShareHelper()

        # Create share source
        source = zrc_sdk.ShareSource()
        source.userID = request.user_id
        source.shareSourceID = request.share_source_id

        result = share_helper.MuteShareAudio(source, request.mute)

        return {
            "room_id": room_id,
            "mute": request.mute,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hdmi/60fps")
async def enable_hdmi_60fps(room_id: str, enabled: bool, room_manager = Depends(lambda: get_room_manager())):
    """Enable or disable HDMI 60fps share"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        share_helper = meeting_service.GetMeetingShareHelper()
        result = share_helper.EnableHDMI60FPSShare(enabled)

        return {
            "room_id": room_id,
            "enabled": enabled,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hdmi/audio-playback/status")
async def get_hdmi_audio_playback_status(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """Get local HDMI share audio playback status"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        share_helper = meeting_service.GetMeetingShareHelper()
        result, is_support, is_enabled = share_helper.GetLocalHDMIShareAudioPlaybackStatus()

        return {
            "room_id": room_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS,
            "is_support": is_support,
            "is_enabled": is_enabled
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hdmi/audio-playback")
async def enable_hdmi_audio_playback(room_id: str, enabled: bool, room_manager = Depends(lambda: get_room_manager())):
    """Enable or disable local HDMI share audio playback"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        share_helper = meeting_service.GetMeetingShareHelper()
        result = share_helper.EnableLocalHDMIShareAudioPlayback(enabled)

        return {
            "room_id": room_id,
            "enabled": enabled,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/settings/privilege")
async def set_share_privilege(
    room_id: str,
    request: SetMeetingShareSettingRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Set meeting share privilege type"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        share_helper = meeting_service.GetMeetingShareHelper()

        # Map privilege type
        privilege_map = {
            "Unknown": zrc_sdk.MeetingSharePrivilegeTypeUnknown,
            "HostGrab": zrc_sdk.MeetingSharePrivilegeTypeHostGrab,
            "LockShare": zrc_sdk.MeetingSharePrivilegeTypeLockShare,
            "AnyoneGrab": zrc_sdk.MeetingSharePrivilegeTypeAnyoneGrab,
            "MultiShare": zrc_sdk.MeetingSharePrivilegeTypeMultiShare
        }
        privilege = privilege_map.get(request.privilege_type, zrc_sdk.MeetingSharePrivilegeTypeHostGrab)

        result = share_helper.SetMeetingShareSetting(privilege)

        return {
            "room_id": room_id,
            "privilege_type": request.privilege_type,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/settings/view-privilege")
async def set_share_view_privilege(
    room_id: str,
    request: SetMeetingShareViewPrivilegeRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Set meeting share view privilege"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        share_helper = meeting_service.GetMeetingShareHelper()

        # Map privilege
        privilege_map = {
            "FocusModeOff": zrc_sdk.MeetingShareViewPrivilege_FocusModeOff,
            "FocusModeHostOnly": zrc_sdk.MeetingShareViewPrivilege_FocusModeHostOnly,
            "FocusModeAllParticipants": zrc_sdk.MeetingShareViewPrivilege_FocusModeAllParticipants
        }
        privilege = privilege_map.get(request.privilege, zrc_sdk.MeetingShareViewPrivilege_FocusModeOff)

        result = share_helper.SetMeetingShareViewPrivilege(privilege)

        return {
            "room_id": room_id,
            "privilege": request.privilege,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize-video")
async def optimize_video_sharing(room_id: str, optimize: bool, room_manager = Depends(lambda: get_room_manager())):
    """Enable or disable optimize video sharing"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        share_helper = meeting_service.GetMeetingShareHelper()
        result = share_helper.OptimizeVideoSharing(optimize)

        return {
            "room_id": room_id,
            "optimize": optimize,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/docs/allow-participants")
async def allow_participants_share_docs(room_id: str, allow: bool, room_manager = Depends(lambda: get_room_manager())):
    """Allow or disallow participants to share docs"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        share_helper = meeting_service.GetMeetingShareHelper()
        result = share_helper.AllowParticipantsShareDocs(allow)

        return {
            "room_id": room_id,
            "allow": allow,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/docs/share-privilege")
async def change_docs_share_privilege(
    room_id: str,
    request: DocsSharePrivilegeRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Change docs share privilege type"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        share_helper = meeting_service.GetMeetingShareHelper()

        # Map privilege type
        privilege_map = {
            "Unknown": zrc_sdk.DocsSharePrivilegeTypeUnknown,
            "HostGrab": zrc_sdk.DocsSharePrivilegeTypeHostGrab,
            "AnyoneGrab": zrc_sdk.DocsSharePrivilegeTypeAnyoneGrab
        }
        privilege = privilege_map.get(request.privilege_type, zrc_sdk.DocsSharePrivilegeTypeHostGrab)

        result = share_helper.ChangeDocsSharePrivilege(privilege)

        return {
            "room_id": room_id,
            "privilege_type": request.privilege_type,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/docs/initiate-privilege")
async def change_docs_initiate_privilege(
    room_id: str,
    request: DocsInitiatePrivilegeRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Change docs initiate privilege type"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        share_helper = meeting_service.GetMeetingShareHelper()

        # Map privilege type
        privilege_map = {
            "Unknown": zrc_sdk.DocsInitiatePrivilegeTypeUnknown,
            "HostOnly": zrc_sdk.DocsInitiatePrivilegeTypeHostOnly,
            "InternalUsers": zrc_sdk.DocsInitiatePrivilegeTypeInternalUsers,
            "AllParticipants": zrc_sdk.DocsInitiatePrivilegeTypeAllParticipants
        }
        privilege = privilege_map.get(request.privilege_type, zrc_sdk.DocsInitiatePrivilegeTypeHostOnly)

        result = share_helper.ChangeDocsInitiatePrivilege(privilege)

        return {
            "room_id": room_id,
            "privilege_type": request.privilege_type,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/docs/settings")
async def get_docs_share_settings(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """Get docs share settings info"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        share_helper = meeting_service.GetMeetingShareHelper()
        result, info = share_helper.GetDocsShareSettingsInfo()

        if result == zrc_sdk.ZRCSDKERR_SUCCESS:
            return {
                "room_id": room_id,
                "result": int(result),
                "success": True,
                "is_supported": info.isSupported,
                "is_allow_participants_to_share": info.isAllowParticipantsToShare,
                "share_privilege": int(info.sharePrivilege),
                "initiate_privilege": int(info.initiatePrivilege),
                "is_locked": info.isLocked
            }
        else:
            return {
                "room_id": room_id,
                "result": int(result),
                "success": False
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/annotation-over-hdmi")
async def enable_annotation_over_hdmi(room_id: str, enabled: bool, room_manager = Depends(lambda: get_room_manager())):
    """Enable or disable annotation over HDMI"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        share_helper = meeting_service.GetMeetingShareHelper()
        result = share_helper.EnableAnnotationOverHDMI(enabled)

        return {
            "room_id": room_id,
            "enabled": enabled,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
