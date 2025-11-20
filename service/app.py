"""
Zoom Rooms SDK Microservice
FastAPI-based web service wrapping the Zoom Rooms C++ SDK
"""

import logging
from contextlib import asynccontextmanager
from typing import Annotated
from fastapi import FastAPI, Depends

from room_manager import RoomManager
from controllers import rooms, meetings, meeting_controls, meeting_list, meeting_share, meeting_video

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ===== Global Room Manager =====

room_manager = RoomManager()


# ===== Dependency Injection =====

def get_room_manager() -> RoomManager:
    """Dependency to inject room_manager into endpoints"""
    return room_manager


# ===== Application Lifecycle =====

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


# ===== FastAPI Application =====

app = FastAPI(
    title="Zoom Rooms SDK Microservice",
    description="REST API for controlling Zoom Rooms via the ZRC SDK",
    version="1.0.0",
    lifespan=lifespan
)


# ===== Root & Health Endpoints =====

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Zoom Rooms SDK Microservice",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "sdk_initialized": room_manager.sdk is not None,
        "active_rooms": len(room_manager.rooms)
    }


# ===== Include Controllers =====

# Set the get_room_manager dependency for all controllers
rooms.get_room_manager = get_room_manager
meetings.get_room_manager = get_room_manager
meeting_controls.get_room_manager = get_room_manager
meeting_list.get_room_manager = get_room_manager
meeting_share.get_room_manager = get_room_manager
meeting_video.get_room_manager = get_room_manager

app.include_router(rooms.router)
app.include_router(meetings.router)
app.include_router(meeting_controls.router)
app.include_router(meeting_list.router)
app.include_router(meeting_share.router)
app.include_router(meeting_video.router)


# ===== Server Launch =====

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
