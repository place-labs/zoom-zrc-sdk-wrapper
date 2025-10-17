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
        # SDK stores paired room data in this directory
        # CRITICAL: Contains third_zrc_data.db with room credentials and tokens
        # This MUST be persisted across container restarts
        data_dir = os.path.expanduser("~/.zoom/data")
        os.makedirs(data_dir, exist_ok=True)
        return data_dir


# ===== Callback Sinks for Events =====

class ZoomRoomsServiceSink:
    """Callback sink for room service events"""

    def __init__(self, room_id: str):
        self.room_id = room_id
        self.pair_result: Optional[int] = None
        self.pair_event = asyncio.Event()

    def OnPairRoomResult(self, result: int):
        """Called when pairing completes (success or failure)"""
        logger.info(f"[{self.room_id}] OnPairRoomResult: {result}")
        self.pair_result = result
        self.pair_event.set()

    def OnRoomUnpairedReason(self, reason: int):
        """Called when room is unpaired"""
        logger.warning(f"[{self.room_id}] Room unpaired, reason: {reason}")


class PreMeetingServiceSink:
    """Callback sink for pre-meeting service events"""

    def __init__(self, room_id: str):
        self.room_id = room_id
        self.connection_state = None
        self.connected_event = asyncio.Event()

    def OnZRConnectionStateChanged(self, state):
        """Called when connection state changes"""
        logger.info(f"[{self.room_id}] Connection state changed: {state}")
        self.connection_state = state
        if state == zrc_sdk.ConnectionStateConnected:
            self.connected_event.set()

    def OnShutdownOSNot(self, restart_os: bool):
        """Called when shutdown notification received"""
        logger.info(f"[{self.room_id}] Shutdown OS notification: restart={restart_os}")


# ===== Room Manager =====

class RoomManager:
    """Manages multiple Zoom Room connections"""

    def __init__(self):
        self.sdk = None
        self.rooms: Dict[str, any] = {}  # room_id -> IZoomRoomsService
        self.room_sinks: Dict[str, ZoomRoomsServiceSink] = {}
        self.premeeting_sinks: Dict[str, PreMeetingServiceSink] = {}
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
        logger.info(f"Data directory: {self.sdk_sink.OnGetAppContentDirPath()}")
        room_infos = []
        result = self.sdk.QueryAllZoomRoomsServices(room_infos)

        logger.info(f"QueryAllZoomRoomsServices result: {result} (type: {type(result)})")
        logger.info(f"room_infos length: {len(room_infos)}")
        logger.info(f"room_infos type: {type(room_infos)}")

        if result == zrc_sdk.ZRCSDKERR_SUCCESS:
            if room_infos:
                logger.info(f"Found {len(room_infos)} previously paired room(s)")
                for room_info in room_infos:
                    logger.info(f"  - Room: {room_info.roomID} ({room_info.roomName})")
                    logger.info(f"    Display: {room_info.displayName}")
                    logger.info(f"    Address: {room_info.roomAddress}")
                    logger.info(f"    Can retry: {room_info.canRetryToPair}")
                    logger.info(f"    Worker present: {room_info.worker is not None}")

                    # Get the service for this room
                    if room_info.worker:
                        self.rooms[room_info.roomID] = room_info.worker
                        logger.info(f"✓ Restored room service for: {room_info.roomID}")
                    else:
                        logger.warning(f"  Room {room_info.roomID} has no worker, skipping")
            else:
                logger.info("No previously paired rooms found (empty list)")
        else:
            logger.warning(f"QueryAllZoomRoomsServices returned error: {result}")

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
        """Create a new room service instance with callbacks"""
        if room_id in self.rooms:
            return self.rooms[room_id]

        logger.info(f"Creating service for room: {room_id}")
        room_service = self.sdk.CreateZoomRoomsService(room_id)

        # Register room service callback sink
        room_sink = ZoomRoomsServiceSink(room_id)
        result = room_service.RegisterSink(room_sink)
        if result == zrc_sdk.ZRCSDKERR_SUCCESS:
            self.room_sinks[room_id] = room_sink
            logger.info(f"✓ Registered room service sink for: {room_id}")
        else:
            logger.error(f"Failed to register room service sink: {result}")

        # Register pre-meeting service callback sink
        premeeting = room_service.GetPreMeetingService()
        premeeting_sink = PreMeetingServiceSink(room_id)
        result = premeeting.RegisterSink(premeeting_sink)
        if result == zrc_sdk.ZRCSDKERR_SUCCESS:
            self.premeeting_sinks[room_id] = premeeting_sink
            logger.info(f"✓ Registered pre-meeting sink for: {room_id}")
        else:
            logger.error(f"Failed to register pre-meeting sink: {result}")

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
            # GetConnectionState returns (result, state) tuple
            result, state = premeeting.GetConnectionState()

            if result == zrc_sdk.ZRCSDKERR_SUCCESS:
                rooms.append(RoomStatus(
                    room_id=room_id,
                    paired=True,
                    connection_state=str(state)
                ))
            else:
                rooms.append(RoomStatus(
                    room_id=room_id,
                    paired=True,
                    connection_state="error"
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
    """
    Pair a Zoom Room with activation code and wait for full connection.

    This endpoint waits for:
    1. OnPairRoomResult callback (activation code validation)
    2. OnZRConnectionStateChanged to ConnectionStateConnected (full connection & persistence)

    Only returns success when room is fully connected and persisted to database.
    """
    try:
        # Create or get room service
        room_service = room_manager.create_room_service(room_id)

        # Get the callback sinks
        room_sink = room_manager.room_sinks.get(room_id)
        premeeting_sink = room_manager.premeeting_sinks.get(room_id)

        if not room_sink or not premeeting_sink:
            raise HTTPException(status_code=500, detail="Failed to register callbacks")

        # Reset events in case of retry
        room_sink.pair_event.clear()
        premeeting_sink.connected_event.clear()

        # Start pairing process
        logger.info(f"[{room_id}] Starting pairing with activation code...")
        result = room_service.PairRoomWithActivationCode(request.activation_code)

        if result != zrc_sdk.ZRCSDKERR_SUCCESS:
            return {
                "room_id": room_id,
                "result": int(result),
                "success": False,
                "message": "Failed to initiate pairing"
            }

        # Wait for OnPairRoomResult callback (30 second timeout)
        logger.info(f"[{room_id}] Waiting for pair result callback...")
        try:
            await asyncio.wait_for(room_sink.pair_event.wait(), timeout=30.0)
        except asyncio.TimeoutError:
            return {
                "room_id": room_id,
                "result": -1,
                "success": False,
                "message": "Timeout waiting for pairing result"
            }

        # Check pairing result
        if room_sink.pair_result != 0:
            error_messages = {
                30055016: "Invalid activation code",
                100: "Failed to connect to room",
                101: "Room cannot verify connection",
                102: "Timeout waiting for room's verify response"
            }
            message = error_messages.get(room_sink.pair_result, f"Pairing failed with code {room_sink.pair_result}")

            return {
                "room_id": room_id,
                "result": room_sink.pair_result,
                "success": False,
                "message": message
            }

        # Wait for ConnectionStateConnected (60 second timeout)
        logger.info(f"[{room_id}] Pairing successful, waiting for connection...")
        try:
            await asyncio.wait_for(premeeting_sink.connected_event.wait(), timeout=60.0)
        except asyncio.TimeoutError:
            return {
                "room_id": room_id,
                "result": 0,
                "success": False,
                "message": "Pairing succeeded but timeout waiting for connection. Room may connect later."
            }

        # Success! Room is now connected and persisted
        logger.info(f"[{room_id}] ✓ Room fully connected and persisted")
        return {
            "room_id": room_id,
            "result": 0,
            "success": True,
            "message": "Room successfully paired and connected",
            "connection_state": str(premeeting_sink.connection_state)
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
        # GetConnectionState returns (result, state) tuple
        result, state = premeeting.GetConnectionState()

        if result != zrc_sdk.ZRCSDKERR_SUCCESS:
            raise HTTPException(status_code=500, detail=f"Failed to get connection state: {result}")

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
