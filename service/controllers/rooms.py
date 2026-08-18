"""
Room management endpoints - pairing, unpairing, status
"""

import logging
import asyncio
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Callable

try:
    import zrc_sdk
except ImportError:
    print("ERROR: zrc_sdk module not found.")
    raise

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rooms", tags=["rooms"])

# This will be set by app.py
get_room_manager: Callable = None


# ===== Pydantic Models =====

class PairRoomRequest(BaseModel):
    activation_code: str


class RoomStatus(BaseModel):
    room_id: str
    paired: bool
    connection_state: str | None = None


# ===== Endpoints =====

@router.get("")
async def list_rooms(room_manager = Depends(lambda: get_room_manager())):
    """List all paired rooms"""
    rooms_list: List[RoomStatus] = []

    for room_id, room_service in room_manager.rooms.items():
        # Get connection state if available
        connection_state = None
        premeeting = room_service.GetPreMeetingService()
        result, state = premeeting.GetConnectionState()
        if result == zrc_sdk.ZRCSDKERR_SUCCESS:
            connection_state = str(state)

        rooms_list.append(RoomStatus(
            room_id=room_id,
            paired=True,
            connection_state=connection_state
        ))

    return {"rooms": rooms_list}


@router.post("/{room_id}/pair")
async def pair_room(room_id: str, request: PairRoomRequest, room_manager = Depends(lambda: get_room_manager())):
    """Pair a Zoom Room using activation code"""
    try:
        # Create room service
        room_service = room_manager.create_room_service(room_id)
        if room_service is None:
            raise HTTPException(status_code=502,
                                detail=f"SDK could not create a room service for '{room_id}'")

        # Get the sink for this room
        room_sink = room_manager.room_sinks.get(room_id)
        premeeting_sink = room_manager.premeeting_sinks.get(room_id)

        if not room_sink or not premeeting_sink:
            raise HTTPException(status_code=500, detail="Failed to register callback sinks")

        # Reset events
        room_sink.pair_event.clear()
        premeeting_sink.connected_event.clear()

        # Start pairing (a network round-trip on the loop thread — time it)
        logger.info(f"Pairing room: {room_id}")
        with room_manager.sdk_monitor.measure(f"PairRoomWithActivationCode[{room_id}]"):
            result = room_service.PairRoomWithActivationCode(request.activation_code)

        if result != zrc_sdk.ZRCSDKERR_SUCCESS:
            raise HTTPException(
                status_code=400,
                detail=f"PairRoom failed: {result}"
            )

        # Wait for pairing result (timeout after 60 seconds)
        try:
            await asyncio.wait_for(room_sink.pair_event.wait(), timeout=60.0)
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=408,
                detail="Pairing timeout - no response from room"
            )

        # Check pairing result
        if room_sink.pair_result != zrc_sdk.ZRCSDKERR_SUCCESS:
            error_msg = f"Pairing failed with error code: {room_sink.pair_result}"
            logger.error(error_msg)
            raise HTTPException(status_code=400, detail=error_msg)

        # Wait for connection (timeout after 30 seconds)
        try:
            await asyncio.wait_for(premeeting_sink.connected_event.wait(), timeout=30.0)
        except asyncio.TimeoutError:
            logger.warning(f"Room {room_id} paired but connection timeout")
            # Don't fail - pairing succeeded, connection might establish later

        logger.info(f"✓ Room {room_id} paired successfully")

        return {
            "room_id": room_id,
            "paired": True,
            "connection_state": str(premeeting_sink.connection_state) if premeeting_sink.connection_state else "Unknown"
        }

    except Exception as e:
        logger.error(f"Error pairing room {room_id}: {e}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{room_id}/unpair")
async def unpair_room(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """Unpair a Zoom Room"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        result = room_service.UnpairRoom()

        # Fully forget the room: stop reconnect attempts, deregister every sink
        # surface, and purge all per-room sink registries.
        room_manager.remove_room(room_id)

        return {
            "room_id": room_id,
            "unpaired": True,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{room_id}/status")
async def get_room_status(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """Get the status of a specific room"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        premeeting = room_service.GetPreMeetingService()
        result, state = premeeting.GetConnectionState()

        return {
            "room_id": room_id,
            "paired": True,
            "connection_state": str(state) if result == zrc_sdk.ZRCSDKERR_SUCCESS else "Unknown",
            "get_state_result": int(result)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
