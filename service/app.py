"""
Zoom Rooms SDK Microservice
FastAPI-based web service wrapping the Zoom Rooms C++ SDK
"""

import asyncio
import logging
from typing import Dict, Optional, List
from contextlib import asynccontextmanager
from collections import defaultdict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Import the C++ SDK bindings (will be available after build)
try:
    import zrc_sdk
except ImportError:
    print("WARNING: zrc_sdk module not found. Run './build.sh' first.")
    zrc_sdk = None


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
    meeting_status: Optional[str] = None


# ===== SDK Callback Implementations =====

class SDKSinkImpl:
    """Implementation of IZRCSDKSink callbacks"""

    def OnGetDeviceManufacturer(self) -> str:
        return "CustomZoomRoomsWrapper"

    def OnGetDeviceModel(self) -> str:
        return "v1.0"

    def OnGetDeviceSerialNumber(self) -> str:
        return "12345"

    def OnGetDeviceMacAddress(self) -> str:
        return "00:00:00:00:00:00"

    def OnGetDeviceIP(self) -> str:
        return "0.0.0.0"

    def OnGetFirmwareVersion(self) -> str:
        return "1.0.0"

    def OnGetAppName(self) -> str:
        return "Zoom Rooms Microservice"

    def OnGetAppVersion(self) -> str:
        return "1.0.0"

    def OnGetAppDeveloper(self) -> str:
        return "Custom Development"

    def OnGetAppContact(self) -> str:
        return "support@example.com"

    def OnGetAppContentDirPath(self) -> str:
        return "/tmp/zrc_sdk"


class RoomServiceCallbacks:
    """Manages callbacks for a specific room"""

    def __init__(self, room_id: str, manager: 'RoomManager'):
        self.room_id = room_id
        self.manager = manager
        self.room_sink = None
        self.premeeting_sink = None
        self.meeting_sink = None

    def setup_sinks(self, room_service):
        """Set up all callback sinks for this room"""
        # Room service sink
        class RoomSink:
            def __init__(self, callbacks):
                self.callbacks = callbacks

            def OnPairRoomResult(self, result: int):
                logger.info(f"Room {self.callbacks.room_id}: Pair result = {result}")
                self.callbacks.manager.broadcast_event(
                    self.callbacks.room_id,
                    {"event": "OnPairRoomResult", "result": result}
                )

            def OnRoomUnpairedReason(self, reason):
                logger.info(f"Room {self.callbacks.room_id}: Unpaired, reason = {reason}")
                self.callbacks.manager.broadcast_event(
                    self.callbacks.room_id,
                    {"event": "OnRoomUnpairedReason", "reason": str(reason)}
                )

        # Meeting service sink
        class MeetingSink:
            def __init__(self, callbacks):
                self.callbacks = callbacks

            def OnUpdateMeetingStatus(self, status):
                logger.info(f"Room {self.callbacks.room_id}: Meeting status = {status}")
                self.callbacks.manager.broadcast_event(
                    self.callbacks.room_id,
                    {"event": "OnUpdateMeetingStatus", "status": str(status)}
                )

            def OnConfReadyNotification(self):
                logger.info(f"Room {self.callbacks.room_id}: Conference ready")
                self.callbacks.manager.broadcast_event(
                    self.callbacks.room_id,
                    {"event": "OnConfReadyNotification"}
                )

            def OnExitMeetingNotification(self):
                logger.info(f"Room {self.callbacks.room_id}: Meeting exited")
                self.callbacks.manager.broadcast_event(
                    self.callbacks.room_id,
                    {"event": "OnExitMeetingNotification"}
                )

        # Pre-meeting service sink
        class PreMeetingSink:
            def __init__(self, callbacks):
                self.callbacks = callbacks

            def OnZRConnectionStateChanged(self, state):
                logger.info(f"Room {self.callbacks.room_id}: Connection state = {state}")
                self.callbacks.manager.broadcast_event(
                    self.callbacks.room_id,
                    {"event": "OnZRConnectionStateChanged", "state": str(state)}
                )

        self.room_sink = RoomSink(self)
        self.meeting_sink = MeetingSink(self)
        self.premeeting_sink = PreMeetingSink(self)


# ===== Room Manager =====

class RoomManager:
    """Manages multiple Zoom Room connections"""

    def __init__(self):
        self.sdk = None
        self.rooms: Dict[str, any] = {}  # room_id -> IZoomRoomsService
        self.callbacks: Dict[str, RoomServiceCallbacks] = {}
        self.websockets: Dict[str, List[WebSocket]] = defaultdict(list)
        self.heartbeat_task = None

    def initialize(self):
        """Initialize the SDK"""
        if zrc_sdk is None:
            raise RuntimeError("zrc_sdk module not available")

        logger.info("Initializing Zoom Rooms SDK...")
        self.sdk = zrc_sdk.IZRCSDK.GetInstance()

        # Register global SDK sink
        sdk_sink = SDKSinkImpl()
        self.sdk.RegisterSink(sdk_sink)

        logger.info("✓ SDK initialized")

    async def start_heartbeat(self):
        """Start the SDK HeartBeat timer (required on Linux)"""
        async def heartbeat_loop():
            logger.info("Starting SDK HeartBeat loop...")
            while True:
                try:
                    if self.sdk:
                        self.sdk.HeartBeat()
                    await asyncio.sleep(0.15)  # 150ms interval
                except Exception as e:
                    logger.error(f"HeartBeat error: {e}")

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

        # Set up callbacks
        callbacks = RoomServiceCallbacks(room_id, self)
        callbacks.setup_sinks(room_service)

        # Register sinks (Note: pybind11 will handle ownership)
        room_service.RegisterSink(callbacks.room_sink)

        meeting_service = room_service.GetMeetingService()
        meeting_service.RegisterSink(callbacks.meeting_sink)

        premeeting_service = room_service.GetPreMeetingService()
        premeeting_service.RegisterSink(callbacks.premeeting_sink)

        self.rooms[room_id] = room_service
        self.callbacks[room_id] = callbacks

        return room_service

    def get_room_service(self, room_id: str):
        """Get existing room service or None"""
        return self.rooms.get(room_id)

    def broadcast_event(self, room_id: str, event: dict):
        """Broadcast event to all WebSocket clients for this room"""
        if room_id in self.websockets:
            for ws in self.websockets[room_id]:
                try:
                    asyncio.create_task(ws.send_json(event))
                except Exception as e:
                    logger.error(f"Failed to send event to WebSocket: {e}")

    def add_websocket(self, room_id: str, websocket: WebSocket):
        """Register a WebSocket connection for room events"""
        self.websockets[room_id].append(websocket)

    def remove_websocket(self, room_id: str, websocket: WebSocket):
        """Unregister a WebSocket connection"""
        if room_id in self.websockets:
            try:
                self.websockets[room_id].remove(websocket)
            except ValueError:
                pass

    def shutdown(self):
        """Clean up SDK resources"""
        logger.info("Shutting down SDK...")
        if self.sdk:
            zrc_sdk.IZRCSDK.DestroyInstance()


# ===== FastAPI Application =====

room_manager = RoomManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management for the app"""
    # Startup
    try:
        room_manager.initialize()
        await room_manager.start_heartbeat()
        logger.info("✓ Microservice started")
        yield
    finally:
        # Shutdown
        await room_manager.stop_heartbeat()
        room_manager.shutdown()
        logger.info("✓ Microservice stopped")


app = FastAPI(
    title="Zoom Rooms SDK Microservice",
    description="REST + WebSocket wrapper around Zoom Rooms C++ SDK",
    version="1.0.0",
    lifespan=lifespan
)


# ===== API Endpoints =====

@app.get("/")
async def root():
    return {
        "service": "Zoom Rooms SDK Microservice",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/api/rooms")
async def list_rooms():
    """List all room services"""
    rooms = []
    for room_id in room_manager.rooms.keys():
        rooms.append(RoomStatus(
            room_id=room_id,
            paired=True,  # If it exists, it's been paired
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
            "success": result == zrc_sdk.ZRCSDKError.ZRCSDKERR_SUCCESS
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
            "success": result == zrc_sdk.ZRCSDKError.ZRCSDKERR_SUCCESS
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
            "success": result == zrc_sdk.ZRCSDKError.ZRCSDKERR_SUCCESS
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
            "success": result == zrc_sdk.ZRCSDKError.ZRCSDKERR_SUCCESS
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
        result = meeting_service.ExitMeeting(zrc_sdk.ExitMeetingCmd.Leave)

        return {
            "room_id": room_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKError.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rooms/{room_id}/audio/mute")
async def mute_audio(room_id: str, mute: bool = True):
    """Mute/unmute audio"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        audio_helper = meeting_service.GetMeetingAudioHelper()
        result = audio_helper.MuteAudio(mute)

        return {
            "room_id": room_id,
            "muted": mute,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKError.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rooms/{room_id}/video/mute")
async def mute_video(room_id: str, mute: bool = True):
    """Mute/unmute video"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        video_helper = meeting_service.GetMeetingVideoHelper()
        result = video_helper.MuteVideo(mute)

        return {
            "room_id": room_id,
            "muted": mute,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKError.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/api/rooms/{room_id}/events")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    """WebSocket endpoint for real-time room events"""
    await websocket.accept()
    room_manager.add_websocket(room_id, websocket)

    try:
        logger.info(f"WebSocket connected for room: {room_id}")

        # Send initial connection message
        await websocket.send_json({
            "event": "connected",
            "room_id": room_id
        })

        # Keep connection alive and receive any client messages
        while True:
            data = await websocket.receive_text()
            # Echo back (or handle commands if needed)
            await websocket.send_json({
                "event": "echo",
                "data": data
            })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for room: {room_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        room_manager.remove_websocket(room_id, websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
