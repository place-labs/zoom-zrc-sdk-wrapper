"""
Pro AV Service Controller
Handles professional AV features like video overlays, name straps, and gallery settings
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import zrc_sdk

router = APIRouter(prefix="/api/rooms/{room_id}/pro-av", tags=["pro-av"])

# Dependency injection placeholder - will be set by app.py
get_room_manager = None


# ===== Request Models =====

class VideoOverlaySettingsRequest(BaseModel):
    active_speaker_green_outline_enabled: Optional[bool] = None
    reaction_icons_enabled: Optional[bool] = None
    raise_hand_icon_enabled: Optional[bool] = None
    name_strap_enabled: Optional[bool] = None
    name_strap_position: Optional[str] = None  # Left, Center, Right
    mute_icon_enabled: Optional[bool] = None
    poll_overlay_enabled: Optional[bool] = None
    gallery_distribution_mode: Optional[str] = None  # Waterfall, RoundRobin
    max_gallery_page_count: Optional[int] = None
    element_scale: Optional[float] = None


class UnassignedBehaviorRequest(BaseModel):
    unassigned_type: str  # Off, Wallpaper
    wallpaper_room_type: Optional[str] = None  # Main, CZR, CWB
    wallpaper_index: Optional[int] = None


class VideoLossBehaviorRequest(BaseModel):
    behavior_type: str  # Default, BlackFrame, FreezeFrame, Wallpaper
    wallpaper_room_type: Optional[str] = None  # Main, CZR, CWB
    wallpaper_index: Optional[int] = None


# ===== Helper Functions =====

def get_pro_av_service(room_id: str, room_manager):
    """Get Pro AV service for a room"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail=f"Room {room_id} not found")
    return room_service.GetProAVService()


def name_strap_position_to_string(position: int) -> str:
    """Convert name strap position enum to string"""
    position_map = {
        zrc_sdk.ProAVVideoNameStrapPositionUnknown: "Unknown",
        zrc_sdk.ProAVVideoNameStrapPositionLeft: "Left",
        zrc_sdk.ProAVVideoNameStrapPositionCenter: "Center",
        zrc_sdk.ProAVVideoNameStrapPositionRight: "Right"
    }
    return position_map.get(position, f"Unknown({position})")


def gallery_distribution_mode_to_string(mode: int) -> str:
    """Convert gallery distribution mode enum to string"""
    mode_map = {
        zrc_sdk.ProAVGalleryDistributionModeWaterfall: "Waterfall",
        zrc_sdk.ProAVGalleryDistributionModeRoundRobin: "RoundRobin"
    }
    return mode_map.get(mode, f"Unknown({mode})")


def unassigned_behavior_type_to_string(behavior_type: int) -> str:
    """Convert unassigned behavior type enum to string"""
    type_map = {
        zrc_sdk.ProAVUnassignedBehaviorTypeOff: "Off",
        zrc_sdk.ProAVUnassignedBehaviorTypeWallpaper: "Wallpaper"
    }
    return type_map.get(behavior_type, f"Unknown({behavior_type})")


def wallpaper_room_type_to_string(room_type: int) -> str:
    """Convert wallpaper room type enum to string"""
    type_map = {
        zrc_sdk.ProAVWallpaperRoomTypeNone: "None",
        zrc_sdk.ProAVWallpaperRoomTypeMain: "Main",
        zrc_sdk.ProAVWallpaperRoomTypeCZR: "CZR",
        zrc_sdk.ProAVWallpaperRoomTypeCWB: "CWB"
    }
    return type_map.get(room_type, f"Unknown({room_type})")


def video_loss_behavior_type_to_string(behavior_type: int) -> str:
    """Convert video loss behavior type enum to string"""
    type_map = {
        zrc_sdk.ProAVVideoLossBehaviorTypeDefault: "Default",
        zrc_sdk.ProAVVideoLossBehaviorTypeBlackFrame: "BlackFrame",
        zrc_sdk.ProAVVideoLossBehaviorTypeFreezeFrame: "FreezeFrame",
        zrc_sdk.ProAVVideoLossBehaviorTypeWallpaper: "Wallpaper"
    }
    return type_map.get(behavior_type, f"Unknown({behavior_type})")


# ===== Endpoints =====

@router.get("/video-overlay-settings")
async def get_video_overlay_settings(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Get Pro AV video overlay settings"""
    pro_av_service = get_pro_av_service(room_id, room_manager)
    result, settings = pro_av_service.GetProAVVideoOverlaySettings()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to get video overlay settings: {result}")

    return {
        "active_speaker_green_outline_enabled": settings.isActiveSpeakerGreenOutlineEnabled,
        "reaction_icons_enabled": settings.isReactionIconsEnabled,
        "raise_hand_icon_enabled": settings.isRaiseHandIconEnabled,
        "name_strap_enabled": settings.isNameStrapEnabled,
        "name_strap_position": name_strap_position_to_string(settings.position),
        "mute_icon_enabled": settings.isMuteIconEnabled,
        "poll_overlay_enabled": settings.isPollOverlayEnabled,
        "gallery_distribution_mode": gallery_distribution_mode_to_string(settings.galleryDistributionMode),
        "max_gallery_page_count": settings.maxGalleryPageCount,
        "element_scale": settings.elementScale
    }


@router.post("/active-speaker-outline")
async def set_active_speaker_outline(
    room_id: str,
    enable: bool,
    room_manager = Depends(lambda: get_room_manager())
):
    """Enable or disable active speaker green outline"""
    pro_av_service = get_pro_av_service(room_id, room_manager)
    result = pro_av_service.EnableProAVVideoActiveSpeakerGreenOutline(enable)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to set active speaker outline: {result}")

    return {"message": f"Active speaker outline {'enabled' if enable else 'disabled'}"}


@router.post("/reaction-icons")
async def set_reaction_icons(
    room_id: str,
    enable: bool,
    room_manager = Depends(lambda: get_room_manager())
):
    """Enable or disable reaction icons"""
    pro_av_service = get_pro_av_service(room_id, room_manager)
    result = pro_av_service.EnableProAVVideoReactionIcons(enable)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to set reaction icons: {result}")

    return {"message": f"Reaction icons {'enabled' if enable else 'disabled'}"}


@router.post("/raise-hand-icon")
async def set_raise_hand_icon(
    room_id: str,
    enable: bool,
    room_manager = Depends(lambda: get_room_manager())
):
    """Enable or disable raise hand icon"""
    pro_av_service = get_pro_av_service(room_id, room_manager)
    result = pro_av_service.EnableProAVVideoRaiseHandIcon(enable)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to set raise hand icon: {result}")

    return {"message": f"Raise hand icon {'enabled' if enable else 'disabled'}"}


@router.post("/mute-icon")
async def set_mute_icon(
    room_id: str,
    enable: bool,
    room_manager = Depends(lambda: get_room_manager())
):
    """Enable or disable mute icon"""
    pro_av_service = get_pro_av_service(room_id, room_manager)
    result = pro_av_service.EnableProAVVideoMuteIcon(enable)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to set mute icon: {result}")

    return {"message": f"Mute icon {'enabled' if enable else 'disabled'}"}


@router.post("/poll-overlay")
async def set_poll_overlay(
    room_id: str,
    enable: bool,
    room_manager = Depends(lambda: get_room_manager())
):
    """Enable or disable poll overlay"""
    pro_av_service = get_pro_av_service(room_id, room_manager)
    result = pro_av_service.EnableProAVVideoPollOverlay(enable)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to set poll overlay: {result}")

    return {"message": f"Poll overlay {'enabled' if enable else 'disabled'}"}


@router.post("/name-strap")
async def set_name_strap(
    room_id: str,
    enable: bool,
    room_manager = Depends(lambda: get_room_manager())
):
    """Enable or disable name strap"""
    pro_av_service = get_pro_av_service(room_id, room_manager)
    result = pro_av_service.EnableProAVVideoNameStrap(enable)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to set name strap: {result}")

    return {"message": f"Name strap {'enabled' if enable else 'disabled'}"}


@router.post("/name-strap-position")
async def set_name_strap_position(
    room_id: str,
    position: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Set name strap position (Left, Center, Right)"""
    pro_av_service = get_pro_av_service(room_id, room_manager)

    position_map = {
        "Left": zrc_sdk.ProAVVideoNameStrapPositionLeft,
        "Center": zrc_sdk.ProAVVideoNameStrapPositionCenter,
        "Right": zrc_sdk.ProAVVideoNameStrapPositionRight
    }

    if position not in position_map:
        raise HTTPException(status_code=400, detail=f"Invalid position: {position}")

    result = pro_av_service.SetProAVVideoNameStrapPosition(position_map[position])

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to set name strap position: {result}")

    return {"message": f"Name strap position set to {position}"}


@router.post("/gallery-distribution-mode")
async def set_gallery_distribution_mode(
    room_id: str,
    mode: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Set gallery distribution mode (Waterfall, RoundRobin)"""
    pro_av_service = get_pro_av_service(room_id, room_manager)

    mode_map = {
        "Waterfall": zrc_sdk.ProAVGalleryDistributionModeWaterfall,
        "RoundRobin": zrc_sdk.ProAVGalleryDistributionModeRoundRobin
    }

    if mode not in mode_map:
        raise HTTPException(status_code=400, detail=f"Invalid mode: {mode}")

    result = pro_av_service.SetProAVGalleryDistributionMode(mode_map[mode])

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to set gallery distribution mode: {result}")

    return {"message": f"Gallery distribution mode set to {mode}"}


@router.post("/max-gallery-page-count")
async def set_max_gallery_page_count(
    room_id: str,
    count: int,
    room_manager = Depends(lambda: get_room_manager())
):
    """Set max gallery page count"""
    pro_av_service = get_pro_av_service(room_id, room_manager)
    result = pro_av_service.SetProAVMaxGalleryPageCount(count)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to set max gallery page count: {result}")

    return {"message": f"Max gallery page count set to {count}"}


@router.post("/video-element-scale")
async def set_video_element_scale(
    room_id: str,
    scale: float,
    room_manager = Depends(lambda: get_room_manager())
):
    """Set video element scale (0.5 to 3.0)"""
    if scale < 0.5 or scale > 3.0:
        raise HTTPException(status_code=400, detail="Scale must be between 0.5 and 3.0")

    pro_av_service = get_pro_av_service(room_id, room_manager)
    result = pro_av_service.SetProAVVideoElementScale(scale)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to set video element scale: {result}")

    return {"message": f"Video element scale set to {scale}"}


@router.get("/unassigned-behavior")
async def get_unassigned_behavior(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Get unassigned behavior settings"""
    pro_av_service = get_pro_av_service(room_id, room_manager)
    result, behavior = pro_av_service.GetProAVUnassignedBehavior()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to get unassigned behavior: {result}")

    return {
        "unassigned_type": unassigned_behavior_type_to_string(behavior.unassignedType),
        "wallpaper_room_type": wallpaper_room_type_to_string(behavior.roomType),
        "wallpaper_index": behavior.wallpaperIndex
    }


@router.post("/unassigned-behavior")
async def set_unassigned_behavior(
    room_id: str,
    request: UnassignedBehaviorRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Set unassigned behavior"""
    pro_av_service = get_pro_av_service(room_id, room_manager)

    type_map = {
        "Off": zrc_sdk.ProAVUnassignedBehaviorTypeOff,
        "Wallpaper": zrc_sdk.ProAVUnassignedBehaviorTypeWallpaper
    }

    room_type_map = {
        "None": zrc_sdk.ProAVWallpaperRoomTypeNone,
        "Main": zrc_sdk.ProAVWallpaperRoomTypeMain,
        "CZR": zrc_sdk.ProAVWallpaperRoomTypeCZR,
        "CWB": zrc_sdk.ProAVWallpaperRoomTypeCWB
    }

    if request.unassigned_type not in type_map:
        raise HTTPException(status_code=400, detail=f"Invalid unassigned type: {request.unassigned_type}")

    behavior = zrc_sdk.ProAVUnassignedBehavior()
    behavior.unassignedType = type_map[request.unassigned_type]

    if request.wallpaper_room_type:
        if request.wallpaper_room_type not in room_type_map:
            raise HTTPException(status_code=400, detail=f"Invalid wallpaper room type: {request.wallpaper_room_type}")
        behavior.roomType = room_type_map[request.wallpaper_room_type]

    if request.wallpaper_index is not None:
        behavior.wallpaperIndex = request.wallpaper_index

    result = pro_av_service.SetProAVUnassignedBehavior(behavior)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to set unassigned behavior: {result}")

    return {"message": "Unassigned behavior set successfully"}


@router.get("/video-loss-behavior")
async def get_video_loss_behavior(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Get video loss behavior settings"""
    pro_av_service = get_pro_av_service(room_id, room_manager)
    result, behavior = pro_av_service.GetProAVVideoLossBehavior()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to get video loss behavior: {result}")

    return {
        "behavior_type": video_loss_behavior_type_to_string(behavior.behaviorType),
        "wallpaper_room_type": wallpaper_room_type_to_string(behavior.wallpaperRoomType),
        "wallpaper_index": behavior.wallpaperIndex
    }


@router.post("/video-loss-behavior")
async def set_video_loss_behavior(
    room_id: str,
    request: VideoLossBehaviorRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Set video loss behavior"""
    pro_av_service = get_pro_av_service(room_id, room_manager)

    type_map = {
        "Default": zrc_sdk.ProAVVideoLossBehaviorTypeDefault,
        "BlackFrame": zrc_sdk.ProAVVideoLossBehaviorTypeBlackFrame,
        "FreezeFrame": zrc_sdk.ProAVVideoLossBehaviorTypeFreezeFrame,
        "Wallpaper": zrc_sdk.ProAVVideoLossBehaviorTypeWallpaper
    }

    room_type_map = {
        "None": zrc_sdk.ProAVWallpaperRoomTypeNone,
        "Main": zrc_sdk.ProAVWallpaperRoomTypeMain,
        "CZR": zrc_sdk.ProAVWallpaperRoomTypeCZR,
        "CWB": zrc_sdk.ProAVWallpaperRoomTypeCWB
    }

    if request.behavior_type not in type_map:
        raise HTTPException(status_code=400, detail=f"Invalid behavior type: {request.behavior_type}")

    behavior = zrc_sdk.ProAVVideoLossBehavior()
    behavior.behaviorType = type_map[request.behavior_type]

    if request.wallpaper_room_type:
        if request.wallpaper_room_type not in room_type_map:
            raise HTTPException(status_code=400, detail=f"Invalid wallpaper room type: {request.wallpaper_room_type}")
        behavior.wallpaperRoomType = room_type_map[request.wallpaper_room_type]

    if request.wallpaper_index is not None:
        behavior.wallpaperIndex = request.wallpaper_index

    result = pro_av_service.SetProAVVideoLossBehavior(behavior)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to set video loss behavior: {result}")

    return {"message": "Video loss behavior set successfully"}
