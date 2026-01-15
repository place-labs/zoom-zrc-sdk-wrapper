"""
NDI Controller
Endpoints for managing NDI (Network Device Interface) output
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import zrc_sdk

router = APIRouter(prefix="/api/rooms/{room_id}/ndi", tags=["NDI"])

# This will be set by the main app
get_room_manager = None


# ===== Request Models =====

class NDISourceRequest(BaseModel):
    type: str = "None"  # None, ActiveSpeaker, User, Share, PinGroup, SpotlightGroup, Gallery
    source_id: int = 0
    from_type: str = "CurrentConf"  # CurrentConf, ParentConf
    source_type_index: int = 0
    share_source_id: int = 0
    grid_size_row: int = 3
    grid_size_column: int = 3


class PinNDIRequest(BaseModel):
    source: NDISourceRequest
    index: int


class UnpinNDIRequest(BaseModel):
    source: NDISourceRequest
    index: int


class PersistentNDISourceRequest(BaseModel):
    source: NDISourceRequest
    index: int


# ===== Helper Functions =====

def get_ndi_helper(room_id: str, room_manager):
    """Get NDI helper for a room"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail=f"Room {room_id} not found")

    meeting_service = room_service.GetMeetingService()
    if not meeting_service:
        raise HTTPException(status_code=500, detail="Meeting service not available")

    ndi_helper = meeting_service.GetNDIHelper()
    if not ndi_helper:
        raise HTTPException(status_code=500, detail="NDI helper not available")

    return ndi_helper


def ndi_source_to_cpp(source: NDISourceRequest):
    """Convert request model to C++ NDISource struct"""
    cpp_source = zrc_sdk.NDISource()

    # Map type string to enum
    type_map = {
        "None": zrc_sdk.NDISourceTypeNone,
        "ActiveSpeaker": zrc_sdk.NDISourceTypeActiveSpeaker,
        "User": zrc_sdk.NDISourceTypeUser,
        "Share": zrc_sdk.NDISourceTypeShare,
        "PinGroup": zrc_sdk.NDISourceTypePinGroup,
        "SpotlightGroup": zrc_sdk.NDISourceTypeSpotlightGroup,
        "Gallery": zrc_sdk.NDISourceTypeGallery
    }
    cpp_source.type = type_map.get(source.type, zrc_sdk.NDISourceTypeNone)
    cpp_source.sourceID = source.source_id

    # Map from_type string to enum
    from_type_map = {
        "CurrentConf": zrc_sdk.ConfInstTypeCurrentConf,
        "ParentConf": zrc_sdk.ConfInstTypeParentConf
    }
    cpp_source.fromType = from_type_map.get(source.from_type, zrc_sdk.ConfInstTypeCurrentConf)
    cpp_source.sourceTypeIndex = source.source_type_index
    cpp_source.shareSourceID = source.share_source_id

    # Set grid size
    grid_size = zrc_sdk.GalleryGridSize()
    grid_size.row = source.grid_size_row
    grid_size.column = source.grid_size_column
    cpp_source.gridSize = grid_size

    return cpp_source


# ===== Endpoints =====

@router.post("/resolution")
async def set_ndi_resolution(room_id: str, resolution: str, room_manager = Depends(lambda: get_room_manager())):
    """Set NDI output resolution"""
    ndi_helper = get_ndi_helper(room_id, room_manager)

    resolution_map = {
        "Unknown": zrc_sdk.NDIResolutionUnknown,
        "360p": zrc_sdk.NDIResolution360p,
        "720p": zrc_sdk.NDIResolution720p,
        "1080p": zrc_sdk.NDIResolution1080p
    }

    ndi_resolution = resolution_map.get(resolution, zrc_sdk.NDIResolutionUnknown)
    result = ndi_helper.SetNDIResolution(ndi_resolution)

    return {
        "room_id": room_id,
        "resolution": resolution,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.post("/frame-rate")
async def set_ndi_frame_rate(room_id: str, frame_rate: str, room_manager = Depends(lambda: get_room_manager())):
    """Set NDI output frame rate"""
    ndi_helper = get_ndi_helper(room_id, room_manager)

    frame_rate_map = {
        "Unknown": zrc_sdk.NDIFrameRateUnknown,
        "25fps": zrc_sdk.NDIFrameRate25fps,
        "29.97fps": zrc_sdk.NDIFrameRate29_97fps,
        "30fps": zrc_sdk.NDIFrameRate30fps,
        "50fps": zrc_sdk.NDIFrameRate50fps,
        "59.94fps": zrc_sdk.NDIFrameRate59_94fps,
        "60fps": zrc_sdk.NDIFrameRate60fps
    }

    ndi_frame_rate = frame_rate_map.get(frame_rate, zrc_sdk.NDIFrameRateUnknown)
    result = ndi_helper.SetNDIFrameRate(ndi_frame_rate)

    return {
        "room_id": room_id,
        "frame_rate": frame_rate,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.post("/enable-in-premeeting")
async def set_ndi_enable_in_premeeting(room_id: str, enable: bool, room_manager = Depends(lambda: get_room_manager())):
    """Enable/disable NDI in premeeting"""
    ndi_helper = get_ndi_helper(room_id, room_manager)
    result = ndi_helper.SetNDIEnableInPreMeeting(enable)

    return {
        "room_id": room_id,
        "enable": enable,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.post("/output-count")
async def set_ndi_output_count(room_id: str, output_count: int, room_manager = Depends(lambda: get_room_manager())):
    """Set NDI output count"""
    ndi_helper = get_ndi_helper(room_id, room_manager)
    result = ndi_helper.SetNDIOutputCount(output_count)

    return {
        "room_id": room_id,
        "output_count": output_count,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.get("/available-sources")
async def get_available_ndi_sources(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """Get available NDI sources"""
    ndi_helper = get_ndi_helper(room_id, room_manager)
    result, sources = ndi_helper.GetAvailableNDISources()

    # Convert sources to dict for JSON serialization
    sources_list = []
    for source in sources:
        sources_list.append({
            "type": int(source.type),
            "source_id": source.sourceID,
            "from_type": int(source.fromType),
            "source_type_index": source.sourceTypeIndex,
            "share_source_id": source.shareSourceID,
            "grid_size": {
                "row": source.gridSize.row,
                "column": source.gridSize.column
            }
        })

    return {
        "room_id": room_id,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS,
        "sources": sources_list,
        "count": len(sources_list)
    }


@router.get("/pinned-sources")
async def get_ndi_pinned_sources(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """Get NDI pinned sources"""
    ndi_helper = get_ndi_helper(room_id, room_manager)
    result, sources = ndi_helper.GetNDIPinnedSources()

    # Convert sources to dict for JSON serialization
    sources_list = []
    for pinned_source in sources:
        sources_list.append({
            "index": pinned_source.index,
            "source": {
                "type": int(pinned_source.source.type),
                "source_id": pinned_source.source.sourceID,
                "from_type": int(pinned_source.source.fromType),
                "source_type_index": pinned_source.source.sourceTypeIndex,
                "share_source_id": pinned_source.source.shareSourceID,
                "grid_size": {
                    "row": pinned_source.source.gridSize.row,
                    "column": pinned_source.source.gridSize.column
                }
            }
        })

    return {
        "room_id": room_id,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS,
        "sources": sources_list,
        "count": len(sources_list)
    }


@router.post("/pin")
async def pin_ndi(room_id: str, request: PinNDIRequest, room_manager = Depends(lambda: get_room_manager())):
    """Pin NDI source"""
    ndi_helper = get_ndi_helper(room_id, room_manager)
    cpp_source = ndi_source_to_cpp(request.source)
    result = ndi_helper.PinNDI(cpp_source, request.index)

    return {
        "room_id": room_id,
        "index": request.index,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.post("/unpin")
async def unpin_ndi(room_id: str, request: UnpinNDIRequest, room_manager = Depends(lambda: get_room_manager())):
    """Unpin NDI source"""
    ndi_helper = get_ndi_helper(room_id, room_manager)
    cpp_source = ndi_source_to_cpp(request.source)
    result = ndi_helper.UnpinNDI(cpp_source, request.index)

    return {
        "room_id": room_id,
        "index": request.index,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.get("/devices")
async def get_ndi_device_list(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """Get NDI device list"""
    ndi_helper = get_ndi_helper(room_id, room_manager)
    result, devices = ndi_helper.GetNDIDeviceList()

    # Convert devices to dict for JSON serialization
    devices_list = []
    for device in devices:
        devices_list.append({
            "id": device.id,
            "name": device.name,
            "is_selected": device.isSelected
        })

    return {
        "room_id": room_id,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS,
        "devices": devices_list,
        "count": len(devices_list)
    }


@router.post("/persistent-sources/add")
async def add_persistent_ndi_source(room_id: str, request: PersistentNDISourceRequest, room_manager = Depends(lambda: get_room_manager())):
    """Add persistent NDI source"""
    ndi_helper = get_ndi_helper(room_id, room_manager)
    cpp_source = ndi_source_to_cpp(request.source)
    result = ndi_helper.AddPersistentNDISource(cpp_source, request.index)

    return {
        "room_id": room_id,
        "index": request.index,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.delete("/persistent-sources/{index}")
async def remove_persistent_ndi_source(room_id: str, index: int, room_manager = Depends(lambda: get_room_manager())):
    """Remove persistent NDI source"""
    ndi_helper = get_ndi_helper(room_id, room_manager)
    result = ndi_helper.RemovePersistentNDISource(index)

    return {
        "room_id": room_id,
        "index": index,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.post("/persistent-sources/list")
async def list_persistent_ndi_sources(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """List persistent NDI sources (triggers notification callback)"""
    ndi_helper = get_ndi_helper(room_id, room_manager)
    result = ndi_helper.ListPersistentNDISources()

    return {
        "room_id": room_id,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS,
        "message": "Persistent NDI sources list requested (check callback notifications)"
    }
