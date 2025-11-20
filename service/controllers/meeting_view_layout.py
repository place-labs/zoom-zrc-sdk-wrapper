"""
Meeting view layout endpoints - layout control, video positioning, gallery/speaker view
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

router = APIRouter(prefix="/api/rooms/{room_id}/layout", tags=["meeting-view-layout"])

# This will be set by app.py
get_room_manager: Callable = None


# ===== Pydantic Models =====

class VideoPositionRequest(BaseModel):
    position: str = "Center"  # Center, Up, Right, UpRight, Down, DownRight, Left, UpLeft, DownLeft
    size: str = "Off"  # Off, 1x, 2x, 3x, VideoStripe


class TurnVideoPageRequest(BaseModel):
    forward: bool
    page_type: str = "GalleryView"  # Unknown, GalleryView, ThumbnailView, DynamicLayoutView


class SelectGalleryGridRequest(BaseModel):
    row: int  # 2-7
    column: int  # 2-7


# ===== Endpoints =====

@router.post("/style")
async def update_video_layout_style(room_id: str, style: str, room_manager = Depends(lambda: get_room_manager())):
    """Update video layout style"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        layout_helper = meeting_service.GetMeetingViewLayoutHelper()

        # Map style
        style_map = {
            "Unknown": zrc_sdk.VideoLayoutStyleUnknown,
            "Gallery": zrc_sdk.VideoLayoutStyleGallery,
            "Speaker": zrc_sdk.VideoLayoutStyleSpeaker,
            "Thumbnail": zrc_sdk.VideoLayoutStyleThumbnail,
            "ContentOnly": zrc_sdk.VideoLayoutStyleContentOnly,
            "CancelContentOnly": zrc_sdk.VideoLayoutStyleCancelContentOnly,
            "DynamicLayout": zrc_sdk.VideoLayoutStyleDynamicLayout
        }
        video_style = style_map.get(style, zrc_sdk.VideoLayoutStyleUnknown)

        result = layout_helper.UpdateVideoLayoutStyle(video_style)

        return {
            "room_id": room_id,
            "style": style,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/video-position")
async def control_video_position(room_id: str, request: VideoPositionRequest, room_manager = Depends(lambda: get_room_manager())):
    """Control video thumb position and size"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        layout_helper = meeting_service.GetMeetingViewLayoutHelper()

        # Map position
        position_map = {
            "Center": zrc_sdk.VideoThumbPositionCenter,
            "Up": zrc_sdk.VideoThumbPositionUp,
            "Right": zrc_sdk.VideoThumbPositionRight,
            "UpRight": zrc_sdk.VideoThumbPositionUpRight,
            "Down": zrc_sdk.VideoThumbPositionDown,
            "DownRight": zrc_sdk.VideoThumbPositionDownRight,
            "Left": zrc_sdk.VideoThumbPositionLeft,
            "UpLeft": zrc_sdk.VideoThumbPositionUpLeft,
            "DownLeft": zrc_sdk.VideoThumbPositionDownLeft
        }
        position = position_map.get(request.position, zrc_sdk.VideoThumbPositionCenter)

        # Map size
        size_map = {
            "Off": zrc_sdk.VideoThumbSizeOff,
            "1x": zrc_sdk.VideoThumbSize1x,
            "2x": zrc_sdk.VideoThumbSize2x,
            "3x": zrc_sdk.VideoThumbSize3x,
            "VideoStripe": zrc_sdk.VideoThumbSizeVideoStripe
        }
        size = size_map.get(request.size, zrc_sdk.VideoThumbSizeOff)

        result = layout_helper.ControlVideoPosition(position, size)

        return {
            "room_id": room_id,
            "position": request.position,
            "size": request.size,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/turn-page")
async def turn_video_page(room_id: str, request: TurnVideoPageRequest, room_manager = Depends(lambda: get_room_manager())):
    """Turn video page forward or backward"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        layout_helper = meeting_service.GetMeetingViewLayoutHelper()

        # Map page type
        page_type_map = {
            "Unknown": zrc_sdk.PageVideoTypeUnknown,
            "GalleryView": zrc_sdk.PageVideoTypeGalleryView,
            "ThumbnailView": zrc_sdk.PageVideoTypeThumbnailView,
            "DynamicLayoutView": zrc_sdk.PageVideoTypeDynamicLayoutView
        }
        page_type = page_type_map.get(request.page_type, zrc_sdk.PageVideoTypeGalleryView)

        result = layout_helper.TurnVideoPage(request.forward, page_type)

        return {
            "room_id": room_id,
            "forward": request.forward,
            "page_type": request.page_type,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/floating-share")
async def switch_floating_share(room_id: str, floating_share: bool, room_manager = Depends(lambda: get_room_manager())):
    """Switch to floating share content (single screen)"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        layout_helper = meeting_service.GetMeetingViewLayoutHelper()
        result = layout_helper.SwitchToFloatingShareForSingleScreen(floating_share)

        return {
            "room_id": room_id,
            "floating_share": floating_share,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/non-video-participants/support")
async def check_support_non_video_participants(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """Check if showing non-video participants is supported"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        layout_helper = meeting_service.GetMeetingViewLayoutHelper()
        result, support = layout_helper.IsSupportShowNonVideoParticipants()

        return {
            "room_id": room_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS,
            "support": support
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/non-video-participants")
async def show_non_video_participants(room_id: str, show: bool, room_manager = Depends(lambda: get_room_manager())):
    """Show or hide non-video participants"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        layout_helper = meeting_service.GetMeetingViewLayoutHelper()
        result = layout_helper.ShowNonVideoParticipants(show)

        return {
            "room_id": room_id,
            "show": show,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/show-49-per-page")
async def enable_show_up_to_49(room_id: str, enabled: bool, room_manager = Depends(lambda: get_room_manager())):
    """Enable showing up to 49 users per page in gallery"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        layout_helper = meeting_service.GetMeetingViewLayoutHelper()
        result = layout_helper.EnableShowUpTo49PerPageInGallery(enabled)

        return {
            "room_id": room_id,
            "enabled": enabled,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-switch-speaker")
async def enable_auto_switch_speaker(room_id: str, enabled: bool, room_manager = Depends(lambda: get_room_manager())):
    """Enable or disable auto switch to speaker view"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        layout_helper = meeting_service.GetMeetingViewLayoutHelper()
        result = layout_helper.EnableAutoSwitchSpeaker(enabled)

        return {
            "room_id": room_id,
            "enabled": enabled,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/video-order")
async def select_video_order(room_id: str, order_type: str, room_manager = Depends(lambda: get_room_manager())):
    """Select video order type"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        layout_helper = meeting_service.GetMeetingViewLayoutHelper()

        # Map order type
        order_map = {
            "Unknown": zrc_sdk.VideoOrderTypeUnknown,
            "Default": zrc_sdk.VideoOrderTypeDefault,
            "Alphabetical": zrc_sdk.VideoOrderTypeAlphabetical,
            "ReverseAlphabetical": zrc_sdk.VideoOrderTypeReverseAlphabetical,
            "SavedOrder": zrc_sdk.VideoOrderTypeSavedOrder
        }
        order = order_map.get(order_type, zrc_sdk.VideoOrderTypeDefault)

        result = layout_helper.SelectVideoOrder(order)

        return {
            "room_id": room_id,
            "order_type": order_type,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dynamic-layout")
async def set_dynamic_layout_option(room_id: str, layout_type: str, room_manager = Depends(lambda: get_room_manager())):
    """Set dynamic layout option"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        layout_helper = meeting_service.GetMeetingViewLayoutHelper()

        # Map layout type
        layout_map = {
            "SpeakersOnUnknown": zrc_sdk.DynamicLayoutTypeSpeakersOnUnknown,
            "SpeakersOnBottom": zrc_sdk.DynamicLayoutTypeSpeakersOnBottom,
            "SpeakersOnMiddle": zrc_sdk.DynamicLayoutTypeSpeakersOnMiddle,
            "SpeakersOnTop": zrc_sdk.DynamicLayoutTypeSpeakersOnTop
        }
        layout = layout_map.get(layout_type, zrc_sdk.DynamicLayoutTypeSpeakersOnBottom)

        result = layout_helper.SetDynamicLayoutOption(layout)

        return {
            "room_id": room_id,
            "layout_type": layout_type,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/confidence-monitor")
async def set_confidence_monitor_layout(room_id: str, layout_type: str, room_manager = Depends(lambda: get_room_manager())):
    """Set confidence monitor layout"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        layout_helper = meeting_service.GetMeetingViewLayoutHelper()

        # Map layout type
        layout_map = {
            "Unknown": zrc_sdk.ConfidenceMonitorLayoutTypeUnknown,
            "Self": zrc_sdk.ConfidenceMonitorLayoutTypeSelf,
            "Active": zrc_sdk.ConfidenceMonitorLayoutTypeActive,
            "ShareContent": zrc_sdk.ConfidenceMonitorLayoutTypeShareContent
        }
        layout = layout_map.get(layout_type, zrc_sdk.ConfidenceMonitorLayoutTypeUnknown)

        result = layout_helper.SetConfidenceMonitorLayout(layout)

        return {
            "room_id": room_id,
            "layout_type": layout_type,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/attendee-view")
async def change_attendee_view(room_id: str, layout_type: str, room_manager = Depends(lambda: get_room_manager())):
    """Change attendee view layout"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        layout_helper = meeting_service.GetMeetingViewLayoutHelper()

        # Map layout type
        layout_map = {
            "None": zrc_sdk.AttendeeViewLayoutTypeNone,
            "Standard": zrc_sdk.AttendeeViewLayoutTypeStandard,
            "Speaker": zrc_sdk.AttendeeViewLayoutTypeSpeaker,
            "Gallery": zrc_sdk.AttendeeViewLayoutTypeGallery,
            "Follow": zrc_sdk.AttendeeViewLayoutTypeFollow,
            "ShareContentOnly": zrc_sdk.AttendeeViewLayoutTypeShareContentOnly
        }
        layout = layout_map.get(layout_type, zrc_sdk.AttendeeViewLayoutTypeNone)

        result = layout_helper.ChangeAttendeeView(layout)

        return {
            "room_id": room_id,
            "layout_type": layout_type,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/gallery-grid")
async def select_gallery_grid(room_id: str, request: SelectGalleryGridRequest, room_manager = Depends(lambda: get_room_manager())):
    """Select gallery grid (row x column, 2-7)"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        layout_helper = meeting_service.GetMeetingViewLayoutHelper()
        result = layout_helper.SelectGalleryGrid(request.row, request.column)

        return {
            "room_id": room_id,
            "row": request.row,
            "column": request.column,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/expand-self-video")
async def expand_conf_self_video(room_id: str, expand: bool, room_manager = Depends(lambda: get_room_manager())):
    """Expand or collapse conference self video"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        layout_helper = meeting_service.GetMeetingViewLayoutHelper()
        result = layout_helper.ExpandConfSelfVideo(expand)

        return {
            "room_id": room_id,
            "expand": expand,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/screen-layout")
async def set_screen_layout(room_id: str, screen_index: int, layout_type: str, room_manager = Depends(lambda: get_room_manager())):
    """Set screen layout for specific screen"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        layout_helper = meeting_service.GetMeetingViewLayoutHelper()

        # Map screen index
        screen_map = {
            -1: zrc_sdk.MeetingScreenUnknown,
            0: zrc_sdk.MeetingScreenFirst,
            1: zrc_sdk.MeetingScreenSecond,
            2: zrc_sdk.MeetingScreenThird,
            100: zrc_sdk.MeetingScreenConfidence
        }
        screen = screen_map.get(screen_index, zrc_sdk.MeetingScreenFirst)

        # Map layout type
        layout_map = {
            "None": zrc_sdk.ScreenLayoutSourceTypeNone,
            "ActiveVideo": zrc_sdk.ScreenLayoutSourceTypeActiveVideo,
            "SelfVideo": zrc_sdk.ScreenLayoutSourceTypeSelfVideo,
            "PinnedVideo": zrc_sdk.ScreenLayoutSourceTypePinnedVideo,
            "SharedContent": zrc_sdk.ScreenLayoutSourceTypeSharedContent,
            "ThumbnailShareView": zrc_sdk.ScreenLayoutSourceTypeThumbnailShareView
        }
        layout = layout_map.get(layout_type, zrc_sdk.ScreenLayoutSourceTypeNone)

        result = layout_helper.SetScreenLayout(screen, layout)

        return {
            "room_id": room_id,
            "screen_index": screen_index,
            "layout_type": layout_type,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/content-only")
async def set_share_content_only(room_id: str, enabled: bool, room_manager = Depends(lambda: get_room_manager())):
    """Enable or disable share content only"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        layout_helper = meeting_service.GetMeetingViewLayoutHelper()
        result = layout_helper.SetShareContentOnly(enabled)

        return {
            "room_id": room_id,
            "enabled": enabled,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/screen-index")
async def show_screen_index(room_id: str, show: bool, room_manager = Depends(lambda: get_room_manager())):
    """Show or hide screen index on Zoom Room client"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        layout_helper = meeting_service.GetMeetingViewLayoutHelper()
        result = layout_helper.ShowScreenIndex(show)

        return {
            "room_id": room_id,
            "show": show,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/thumbnails-position")
async def get_thumbnails_position(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """Get current thumbnails position"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        layout_helper = meeting_service.GetMeetingViewLayoutHelper()
        result, position_type = layout_helper.GetThumbnailsPosition()

        # Map position type back to string
        position_map = {
            zrc_sdk.ThumbnailsPositionTypeNone: "None",
            zrc_sdk.ThumbnailsPositionTypeBottom: "Bottom",
            zrc_sdk.ThumbnailsPositionTypeTop: "Top",
            zrc_sdk.ThumbnailsPositionTypeUnknown: "Unknown"
        }
        position_str = position_map.get(position_type, "Unknown")

        return {
            "room_id": room_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS,
            "position": position_str,
            "position_value": int(position_type)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/thumbnails-position")
async def change_thumbnails_position(room_id: str, position: str, room_manager = Depends(lambda: get_room_manager())):
    """Change thumbnails position"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        layout_helper = meeting_service.GetMeetingViewLayoutHelper()

        # Map position
        position_map = {
            "None": zrc_sdk.ThumbnailsPositionTypeNone,
            "Bottom": zrc_sdk.ThumbnailsPositionTypeBottom,
            "Top": zrc_sdk.ThumbnailsPositionTypeTop,
            "Unknown": zrc_sdk.ThumbnailsPositionTypeUnknown
        }
        position_type = position_map.get(position, zrc_sdk.ThumbnailsPositionTypeNone)

        result = layout_helper.ChangeThumbnailsPosition(position_type)

        return {
            "room_id": room_id,
            "position": position,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/show-auto-generated-streams")
async def show_auto_generated_video_streams(room_id: str, show: bool, room_manager = Depends(lambda: get_room_manager())):
    """Show or hide my auto generated video streams"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        layout_helper = meeting_service.GetMeetingViewLayoutHelper()
        result = layout_helper.ShowMyAutoGeneratedVideoStreams(show)

        return {
            "room_id": room_id,
            "show": show,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
