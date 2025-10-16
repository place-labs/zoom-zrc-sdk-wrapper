"""
Zoom Rooms SDK Microservice - Simplified Version
FastAPI-based web service wrapping the Zoom Rooms C++ SDK
"""

import asyncio
import logging
from typing import Dict, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Import the C++ SDK bindings
try:
    import zrc_sdk
except ImportError:
    print("ERROR: zrc_sdk module not found. Run '../build.sh' first.")
    raise

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ===== Pydantic Models =====

class PairRoomRequest(BaseModel):
    activation_code: str


class JoinMeetingRequest(BaseModel):
    meeting_number: str
    password: Optional[str] = ""


class RoomStatus(BaseModel):
    room_id: str
    paired: bool
    connection_state: Optional[str] = None


# ===== SDK Sink Implementation =====

class SDKSinkImpl:
    """Simple SDK sink with default values"""

    def OnGetDeviceManufacturer(self) -> str:
        return "ZoomRoomsWrapper"

    def OnGetDeviceModel(self) -> str:
        return "v1.0"

    def OnGetDeviceSerialNumber(self) -> str:
        return "SDK-WRAPPER-001"

    def OnGetDeviceMacAddress(self) -> str:
        return "00:00:00:00:00:01"

    def OnGetDeviceIP(self) -> str:
        return "127.0.0.1"

    def OnGetFirmwareVersion(self) -> str:
        return "1.0.0"

    def OnGetAppName(self) -> str:
        return "Zoom Rooms Microservice"

    def OnGetAppVersion(self) -> str:
        return "1.0.0"

    def OnGetAppDeveloper(self) -> str:
        return "Custom"

    def OnGetAppContact(self) -> str:
        return "support@example.com"

    def OnGetAppContentDirPath(self) -> str:
        import os
        log_dir = os.path.expanduser("~/.zoom/logs")
        os.makedirs(log_dir, exist_ok=True)
        return log_dir


# ===== Room Manager =====

class RoomManager:
    """Manages multiple Zoom Room connections"""

    def __init__(self):
        self.sdk = None
        self.rooms: Dict[str, any] = {}  # room_id -> IZoomRoomsService
        self.heartbeat_task = None
        self.sdk_sink = SDKSinkImpl()

    def initialize(self):
        """Initialize the SDK"""
        logger.info("Initializing Zoom Rooms SDK...")
        self.sdk = zrc_sdk.IZRCSDK.GetInstance()

        # Register SDK sink using the helper function
        result = zrc_sdk.RegisterSDKSink(self.sdk, self.sdk_sink)
        logger.info(f"SDK sink registered: {result}")

        # Query and restore previously paired rooms
        logger.info("Querying for previously paired rooms...")
        room_infos = []
        result = self.sdk.QueryAllZoomRoomsServices(room_infos)

        if result == zrc_sdk.ZRCSDKERR_SUCCESS:
            if room_infos:
                logger.info(f"Found {len(room_infos)} previously paired room(s)")
                for room_info in room_infos:
                    logger.info(f"  - Room: {room_info.roomID} ({room_info.roomName})")
                    logger.info(f"    Display: {room_info.displayName}")
                    logger.info(f"    Address: {room_info.roomAddress}")
                    logger.info(f"    Can retry: {room_info.canRetryToPair}")

                    # Get the service for this room
                    if room_info.worker:
                        self.rooms[room_info.roomID] = room_info.worker
                        logger.info(f"✓ Restored room service for: {room_info.roomID}")
            else:
                logger.info("No previously paired rooms found")
        else:
            logger.warning(f"QueryAllZoomRoomsServices returned: {result}")

        logger.info("✓ SDK initialized successfully")

    async def start_heartbeat(self):
        """Start the SDK HeartBeat timer (required on Linux)"""
        async def heartbeat_loop():
            logger.info("Starting SDK HeartBeat loop (150ms interval)...")
            while True:
                try:
                    if self.sdk:
                        self.sdk.HeartBeat()
                    await asyncio.sleep(0.15)  # 150ms interval
                except Exception as e:
                    logger.error(f"HeartBeat error: {e}")
                    break

        self.heartbeat_task = asyncio.create_task(heartbeat_loop())

    async def stop_heartbeat(self):
        """Stop the HeartBeat timer"""
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass

    def create_room_service(self, room_id: str):
        """Create a new room service instance"""
        if room_id in self.rooms:
            return self.rooms[room_id]

        logger.info(f"Creating service for room: {room_id}")
        room_service = self.sdk.CreateZoomRoomsService(room_id)

        # Note: Callback registration removed to avoid segfaults
        # Callbacks can be added later when proper sink binding is implemented

        self.rooms[room_id] = room_service
        return room_service

    def get_room_service(self, room_id: str):
        """Get existing room service or None"""
        return self.rooms.get(room_id)

    def shutdown(self):
        """Clean up SDK resources"""
        logger.info("Shutting down SDK...")
        # Don't call DestroyInstance - it can cause crashes
        # The SDK will clean up on process exit
        self.sdk = None
        logger.info("✓ SDK shutdown complete")


# ===== FastAPI Application =====

room_manager = RoomManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management for the app"""
    # Startup
    try:
        room_manager.initialize()
        await room_manager.start_heartbeat()
        logger.info("✓ Microservice started successfully")
        yield
    finally:
        # Shutdown
        await room_manager.stop_heartbeat()
        room_manager.shutdown()
        logger.info("✓ Microservice stopped")


app = FastAPI(
    title="Zoom Rooms SDK Microservice",
    description="REST API wrapper around Zoom Rooms C++ SDK",
    version="1.0.0",
    lifespan=lifespan
)


# ===== API Endpoints =====

@app.get("/")
async def root():
    return {
        "service": "Zoom Rooms SDK Microservice",
        "version": "1.0.0",
        "status": "running",
        "rooms": len(room_manager.rooms)
    }


@app.get("/api/rooms")
async def list_rooms():
    """List all room services"""
    rooms = []
    for room_id in room_manager.rooms.keys():
        try:
            room_service = room_manager.rooms[room_id]
            premeeting = room_service.GetPreMeetingService()
            state = premeeting.GetConnectionState()

            rooms.append(RoomStatus(
                room_id=room_id,
                paired=True,
                connection_state=str(state)
            ))
        except Exception as e:
            logger.error(f"Error getting room {room_id} status: {e}")
            rooms.append(RoomStatus(
                room_id=room_id,
                paired=True,
                connection_state="unknown"
            ))

    return {"rooms": rooms}


@app.post("/api/rooms/{room_id}/pair")
async def pair_room(room_id: str, request: PairRoomRequest):
    """Pair a Zoom Room with activation code"""
    try:
        # Create or get room service
        room_service = room_manager.create_room_service(room_id)

        # Pair the room
        result = room_service.PairRoomWithActivationCode(request.activation_code)

        return {
            "room_id": room_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        logger.error(f"Error pairing room {room_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rooms/{room_id}/unpair")
async def unpair_room(room_id: str):
    """Unpair a Zoom Room"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        result = room_service.UnpairRoom()
        return {
            "room_id": room_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rooms/{room_id}/status")
async def get_room_status(room_id: str):
    """Get room connection status"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        premeeting = room_service.GetPreMeetingService()
        state = premeeting.GetConnectionState()

        return {
            "room_id": room_id,
            "connection_state": str(state),
            "connected": state == zrc_sdk.ConnectionStateConnected
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rooms/{room_id}/meeting/start_instant")
async def start_instant_meeting(room_id: str):
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


@app.post("/api/rooms/{room_id}/meeting/join")
async def join_meeting(room_id: str, request: JoinMeetingRequest):
    """Join a meeting by number"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        result = meeting_service.JoinMeeting(
            request.meeting_number,
            request.password
        )

        return {
            "room_id": room_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rooms/{room_id}/meeting/exit")
async def exit_meeting(room_id: str):
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


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "sdk_initialized": room_manager.sdk is not None,
        "active_rooms": len(room_manager.rooms)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
