"""
Meeting video endpoints - video control, pinning, spotlight, video settings
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Callable, List

try:
    import zrc_sdk
except ImportError:
    print("ERROR: zrc_sdk module not found.")
    raise

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rooms/{room_id}/video", tags=["meeting-video"])

# This will be set by app.py
get_room_manager: Callable = None


# ===== Pydantic Models =====

class VideoTouchUpSettings(BaseModel):
    enabled: bool = False
    strength: int = 0  # 0-100


class VideoLowLightSettings(BaseModel):
    enabled: bool = False
    auto_adjust: bool = False
    value: int = 0  # 0-100


class MeetingVideoSettingsRequest(BaseModel):
    meeting_number: str
    meeting_name: str = ""
    host_name: str = ""
    start_time: str = ""
    end_time: str = ""


class ShowVideoPreviewRequest(BaseModel):
    show: bool
    preview_type: str = "CameraSettings"  # CameraSettings, VirtualBackground, MeetingAlert
    meeting_number: str = ""  # Required when preview_type is MeetingAlert
    meeting_name: str = ""
    host_name: str = ""
    start_time: str = ""
    end_time: str = ""


# ===== Endpoints =====

@router.post("/mute")
async def update_my_video(room_id: str, stop: bool, room_manager = Depends(lambda: get_room_manager())):
    """Mute or unmute self video"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        video_helper = meeting_service.GetMeetingVideoHelper()
        result = video_helper.UpdateMyVideo(stop)

        return {
            "room_id": room_id,
            "stop": stop,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mute-user")
async def mute_user_video(room_id: str, user_id: int, mute: bool, room_manager = Depends(lambda: get_room_manager())):
    """Mute or unmute assigned user's video"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        video_helper = meeting_service.GetMeetingVideoHelper()
        result = video_helper.MuteUserVideo(user_id, mute)

        return {
            "room_id": room_id,
            "user_id": user_id,
            "mute": mute,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/answer-unmute-request")
async def answer_unmute_request(room_id: str, accepted: bool, room_manager = Depends(lambda: get_room_manager())):
    """Answer host request to unmute video"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        video_helper = meeting_service.GetMeetingVideoHelper()
        result = video_helper.AnswerHostRequestUnmuteVideo(accepted)

        return {
            "room_id": room_id,
            "accepted": accepted,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/allow-attendees")
async def allow_attendees_start_video(room_id: str, allow: bool, room_manager = Depends(lambda: get_room_manager())):
    """Allow or disallow attendees to start video"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        video_helper = meeting_service.GetMeetingVideoHelper()
        result = video_helper.AllowAttendeesStartVideo(allow)

        return {
            "room_id": room_id,
            "allow": allow,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pin/instruction")
async def show_pin_instruction(room_id: str, show: bool, room_manager = Depends(lambda: get_room_manager())):
    """Show or hide screen index for pin video"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        video_helper = meeting_service.GetMeetingVideoHelper()
        result = video_helper.ShowPinUserInstruction(show)

        return {
            "room_id": room_id,
            "show": show,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pin/allow-multi-pin")
async def allow_user_multi_pin(room_id: str, user_id: int, allow: bool, room_manager = Depends(lambda: get_room_manager())):
    """Allow or disallow user multi-pin"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        video_helper = meeting_service.GetMeetingVideoHelper()
        result = video_helper.AllowUserMultiPin(user_id, allow)

        return {
            "room_id": room_id,
            "user_id": user_id,
            "allow": allow,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pin/user")
async def pin_user(room_id: str, user_id: int, screen_index: int, room_manager = Depends(lambda: get_room_manager())):
    """Pin user video on screen"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        video_helper = meeting_service.GetMeetingVideoHelper()
        result = video_helper.PinUserOnScreen(user_id, screen_index)

        return {
            "room_id": room_id,
            "user_id": user_id,
            "screen_index": screen_index,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pin/add-user")
async def add_pin_user(room_id: str, user_id: int, screen_index: int, room_manager = Depends(lambda: get_room_manager())):
    """Add pin user on screen"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        video_helper = meeting_service.GetMeetingVideoHelper()
        result = video_helper.AddPinUserOnScreen(user_id, screen_index)

        return {
            "room_id": room_id,
            "user_id": user_id,
            "screen_index": screen_index,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pin/unpin-user")
async def unpin_user_from_screen(room_id: str, user_id: int, screen_index: int, room_manager = Depends(lambda: get_room_manager())):
    """Unpin user video from screen"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        video_helper = meeting_service.GetMeetingVideoHelper()
        result = video_helper.UnpinUserFromScreen(user_id, screen_index)

        return {
            "room_id": room_id,
            "user_id": user_id,
            "screen_index": screen_index,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pin/unpin-user-all")
async def unpin_user_from_all_screens(room_id: str, user_id: int, room_manager = Depends(lambda: get_room_manager())):
    """Unpin user video from all screens"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        video_helper = meeting_service.GetMeetingVideoHelper()
        result = video_helper.UnpinUserFromAllScreens(user_id)

        return {
            "room_id": room_id,
            "user_id": user_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pin/smart-tag")
async def pin_smart_name_tag(room_id: str, stream_user_id: int, screen_index: int, room_manager = Depends(lambda: get_room_manager())):
    """Pin smart name tag video stream on screen"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        video_helper = meeting_service.GetMeetingVideoHelper()
        result = video_helper.PinSmartNameTagStreamOnScreen(stream_user_id, screen_index)

        return {
            "room_id": room_id,
            "stream_user_id": stream_user_id,
            "screen_index": screen_index,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pin/add-smart-tag")
async def add_pin_smart_name_tag(room_id: str, stream_user_id: int, screen_index: int, room_manager = Depends(lambda: get_room_manager())):
    """Add pin smart name tag video stream on screen"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        video_helper = meeting_service.GetMeetingVideoHelper()
        result = video_helper.AddPinSmartNameTagStreamOnScreen(stream_user_id, screen_index)

        return {
            "room_id": room_id,
            "stream_user_id": stream_user_id,
            "screen_index": screen_index,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pin/unpin-smart-tag")
async def unpin_smart_name_tag(room_id: str, stream_user_id: int, screen_index: int, room_manager = Depends(lambda: get_room_manager())):
    """Unpin smart name tag video stream from screen"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        video_helper = meeting_service.GetMeetingVideoHelper()
        result = video_helper.UnpinSmartNameTagStreamFromScreen(stream_user_id, screen_index)

        return {
            "room_id": room_id,
            "stream_user_id": stream_user_id,
            "screen_index": screen_index,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pin/unpin-smart-tag-all")
async def unpin_smart_name_tag_all(room_id: str, stream_user_id: int, room_manager = Depends(lambda: get_room_manager())):
    """Unpin smart name tag video stream from all screens"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        video_helper = meeting_service.GetMeetingVideoHelper()
        result = video_helper.UnpinSmartNameTagStreamFromAllScreens(stream_user_id)

        return {
            "room_id": room_id,
            "stream_user_id": stream_user_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pin/remove-all")
async def remove_all_pin_users(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """Remove all pinned users"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        video_helper = meeting_service.GetMeetingVideoHelper()
        result = video_helper.RemoveAllPinUsers()

        return {
            "room_id": room_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/spotlight/user")
async def spotlight_user(room_id: str, user_id: int, room_manager = Depends(lambda: get_room_manager())):
    """Spotlight user"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        video_helper = meeting_service.GetMeetingVideoHelper()
        result = video_helper.SpotlightUser(user_id)

        return {
            "room_id": room_id,
            "user_id": user_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/spotlight/add-user")
async def add_spotlight_user(room_id: str, user_id: int, room_manager = Depends(lambda: get_room_manager())):
    """Add spotlight user"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        video_helper = meeting_service.GetMeetingVideoHelper()
        result = video_helper.AddSpotlightUser(user_id)

        return {
            "room_id": room_id,
            "user_id": user_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/spotlight/cancel-user")
async def cancel_spotlight_user(room_id: str, user_id: int, room_manager = Depends(lambda: get_room_manager())):
    """Cancel spotlight user"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        video_helper = meeting_service.GetMeetingVideoHelper()
        result = video_helper.CancelSpotlightUser(user_id)

        return {
            "room_id": room_id,
            "user_id": user_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/spotlight/remove-all")
async def remove_all_spotlight_users(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """Remove all spotlight users"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        video_helper = meeting_service.GetMeetingVideoHelper()
        result = video_helper.RemoveAllSpotlightUsers()

        return {
            "room_id": room_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hidden/support")
async def check_support_set_hidden(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """Check if setting my video hidden is supported"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        video_helper = meeting_service.GetMeetingVideoHelper()
        result, support = video_helper.IsSupportSetMyVideoHidden()

        return {
            "room_id": room_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS,
            "support": support
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hidden")
async def set_my_video_hidden(room_id: str, hidden: bool, room_manager = Depends(lambda: get_room_manager())):
    """Set my video hidden"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        video_helper = meeting_service.GetMeetingVideoHelper()
        result = video_helper.SetMyVideoHidden(hidden)

        return {
            "room_id": room_id,
            "hidden": hidden,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/settings/touch-up")
async def set_video_touch_up(room_id: str, settings: VideoTouchUpSettings, room_manager = Depends(lambda: get_room_manager())):
    """Set my video touch up settings"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        video_helper = meeting_service.GetMeetingVideoHelper()

        touch_up = zrc_sdk.MyVideoTouchUpSettings()
        touch_up.isFaceBeautyEnabled = settings.enabled
        touch_up.faceBeautyStrength = settings.strength

        result = video_helper.SetMyVideoTouchUp(touch_up)

        return {
            "room_id": room_id,
            "enabled": settings.enabled,
            "strength": settings.strength,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/settings/low-light")
async def set_video_low_light(room_id: str, settings: VideoLowLightSettings, room_manager = Depends(lambda: get_room_manager())):
    """Set my video low light settings"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        video_helper = meeting_service.GetMeetingVideoHelper()

        low_light = zrc_sdk.MyVideoLowLightSettings()
        low_light.isAdjustLowLightEnabled = settings.enabled
        low_light.isAutoAdjustLowLight = settings.auto_adjust
        low_light.adjustLowLightValue = settings.value

        result = video_helper.SetMyVideoLowLight(low_light)

        return {
            "room_id": room_id,
            "enabled": settings.enabled,
            "auto_adjust": settings.auto_adjust,
            "value": settings.value,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/settings/fetch-meeting")
async def fetch_meeting_video_settings(room_id: str, request: MeetingVideoSettingsRequest, room_manager = Depends(lambda: get_room_manager())):
    """Fetch my video settings for specific meeting"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        video_helper = meeting_service.GetMeetingVideoHelper()

        meeting_item = zrc_sdk.MeetingItem()
        meeting_item.meetingNumber = request.meeting_number
        meeting_item.meetingName = request.meeting_name
        meeting_item.hostName = request.host_name
        meeting_item.startTime = request.start_time
        meeting_item.endTime = request.end_time

        result = video_helper.FetchMyMeetingVideoSettings(meeting_item)

        return {
            "room_id": room_id,
            "meeting_number": request.meeting_number,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/settings/meeting-touch-up")
async def set_meeting_video_touch_up(
    room_id: str,
    meeting: MeetingVideoSettingsRequest,
    settings: VideoTouchUpSettings,
    room_manager = Depends(lambda: get_room_manager())
):
    """Set my video touch up settings for specific meeting"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        video_helper = meeting_service.GetMeetingVideoHelper()

        meeting_item = zrc_sdk.MeetingItem()
        meeting_item.meetingNumber = meeting.meeting_number
        meeting_item.meetingName = meeting.meeting_name
        meeting_item.hostName = meeting.host_name
        meeting_item.startTime = meeting.start_time
        meeting_item.endTime = meeting.end_time

        touch_up = zrc_sdk.MyVideoTouchUpSettings()
        touch_up.isFaceBeautyEnabled = settings.enabled
        touch_up.faceBeautyStrength = settings.strength

        result = video_helper.SetMyMeetingVideoTouchUp(meeting_item, touch_up)

        return {
            "room_id": room_id,
            "meeting_number": meeting.meeting_number,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/settings/meeting-low-light")
async def set_meeting_video_low_light(
    room_id: str,
    meeting: MeetingVideoSettingsRequest,
    settings: VideoLowLightSettings,
    room_manager = Depends(lambda: get_room_manager())
):
    """Set my video low light settings for specific meeting"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        video_helper = meeting_service.GetMeetingVideoHelper()

        meeting_item = zrc_sdk.MeetingItem()
        meeting_item.meetingNumber = meeting.meeting_number
        meeting_item.meetingName = meeting.meeting_name
        meeting_item.hostName = meeting.host_name
        meeting_item.startTime = meeting.start_time
        meeting_item.endTime = meeting.end_time

        low_light = zrc_sdk.MyVideoLowLightSettings()
        low_light.isAdjustLowLightEnabled = settings.enabled
        low_light.isAutoAdjustLowLight = settings.auto_adjust
        low_light.adjustLowLightValue = settings.value

        result = video_helper.SetMyMeetingVideoLowLight(meeting_item, low_light)

        return {
            "room_id": room_id,
            "meeting_number": meeting.meeting_number,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preview")
async def show_video_preview(room_id: str, request: ShowVideoPreviewRequest, room_manager = Depends(lambda: get_room_manager())):
    """Show or hide video preview"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        video_helper = meeting_service.GetMeetingVideoHelper()

        # Map preview type
        preview_type_map = {
            "CameraSettings": zrc_sdk.PreviewVideoTypeCameraSettings,
            "VirtualBackground": zrc_sdk.PreviewVideoTypeVirtualBackground,
            "MeetingAlert": zrc_sdk.PreviewVideoTypeMeetingAlert
        }
        preview_type = preview_type_map.get(request.preview_type, zrc_sdk.PreviewVideoTypeCameraSettings)

        # Create meeting item if needed
        meeting_item = zrc_sdk.MeetingItem()
        if request.preview_type == "MeetingAlert":
            meeting_item.meetingNumber = request.meeting_number
            meeting_item.meetingName = request.meeting_name
            meeting_item.hostName = request.host_name
            meeting_item.startTime = request.start_time
            meeting_item.endTime = request.end_time

        result = video_helper.ShowVideoPreview(request.show, preview_type, meeting_item)

        return {
            "room_id": room_id,
            "show": request.show,
            "preview_type": request.preview_type,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
