"""
Room Manager - Manages multiple Zoom Room connections
"""

import asyncio
import logging
import sqlite3
import os
from typing import Dict, Optional

try:
    import zrc_sdk
except ImportError:
    print("ERROR: zrc_sdk module not found. Run '../build.sh' first.")
    raise

logger = logging.getLogger(__name__)


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

        # Initialize web domain (required for SDK to work properly)
        result = self.sdk.InitWebDomain("https://zoom.us")
        logger.info(f"InitWebDomain result: {result}")

        # Register SDK sink using the helper function
        result = zrc_sdk.RegisterSDKSink(self.sdk, self.sdk_sink)
        logger.info(f"SDK sink registered: {result}")

        # Try QueryAllZoomRoomsServices first (should work according to docs)
        logger.info("Querying for previously paired rooms...")
        logger.info(f"Data directory: {self.sdk_sink.OnGetAppContentDirPath()}")

        room_infos = []
        result = self.sdk.QueryAllZoomRoomsServices(room_infos)

        logger.info(f"QueryAllZoomRoomsServices result: {result}")
        logger.info(f"Found {len(room_infos)} room(s) via QueryAllZoomRoomsServices")

        if result == zrc_sdk.ZRCSDKERR_SUCCESS and room_infos:
            # SDK successfully returned previously paired rooms
            for room_info in room_infos:
                logger.info(f"  - Room: {room_info.roomID}")
                logger.info(f"    Name: {room_info.roomName}")
                logger.info(f"    Display: {room_info.displayName}")
                logger.info(f"    Can retry: {room_info.canRetryToPair}")

                if room_info.worker:
                    self.rooms[room_info.roomID] = room_info.worker
                    self.register_sinks_for_room(room_info.roomID, room_info.worker)

                    if room_info.canRetryToPair:
                        logger.info(f"  Attempting to reconnect {room_info.roomID}...")
                        retry_result = room_info.worker.RetryToPairRoom()
                        logger.info(f"  RetryToPairRoom result: {retry_result}")

                    logger.info(f"✓ Restored room service for: {room_info.roomID}")
        else:
            # QueryAllZoomRoomsServices returned empty - fallback to database query
            # This happens when rooms are paired but never fully connected
            logger.info("QueryAllZoomRoomsServices returned no rooms, querying database directly...")

            db_path = os.path.join(self.sdk_sink.OnGetAppContentDirPath(), "third_zrc_data.db")

            if os.path.exists(db_path):
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT pk_id FROM ThirdRoomList")
                    room_ids = [row[0] for row in cursor.fetchall()]
                    conn.close()

                    if room_ids:
                        logger.info(f"Found {len(room_ids)} previously paired room(s) in database")
                        for room_id in room_ids:
                            logger.info(f"  - Restoring room: {room_id}")
                            # Create service for this room ID
                            room_service = self.sdk.CreateZoomRoomsService(room_id)
                            if room_service:
                                self.rooms[room_id] = room_service
                                self.register_sinks_for_room(room_id, room_service)

                                # Try to reconnect using stored credentials
                                logger.info(f"  Attempting to reconnect {room_id}...")
                                retry_result = room_service.RetryToPairRoom()
                                logger.info(f"  RetryToPairRoom result: {retry_result}")
                                logger.info(f"✓ Restored room service for: {room_id}")
                    else:
                        logger.info("No previously paired rooms found in database")
                except Exception as e:
                    logger.error(f"Error querying database: {e}")
            else:
                logger.info(f"Database file not found: {db_path}")

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

    def register_sinks_for_room(self, room_id: str, room_service):
        """Register callback sinks for a room service"""
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

    def create_room_service(self, room_id: str):
        """Create a new room service instance with callbacks"""
        if room_id in self.rooms:
            return self.rooms[room_id]

        logger.info(f"Creating service for room: {room_id}")
        room_service = self.sdk.CreateZoomRoomsService(room_id)

        # Register callback sinks
        self.register_sinks_for_room(room_id, room_service)

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
