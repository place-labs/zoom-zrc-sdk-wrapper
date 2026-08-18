"""
Zoom Rooms SDK Microservice
FastAPI-based web service wrapping the Zoom Rooms C++ SDK
"""

import logging
from contextlib import asynccontextmanager
from typing import Annotated
from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse

from room_manager import RoomManager
from controllers import rooms, meetings, meeting_controls, meeting_list, meeting_share, meeting_reminder, meeting_video, meeting_view_layout, ndi, participant, phone_call, pre_meeting, pro_av, recording, settings, third_party_meeting, events

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
    # Startup — failures must propagate so the process exits non-zero with a
    # traceback; only a clean shutdown may reach the hard-exit below.
    room_manager.initialize()
    await room_manager.start_heartbeat()
    logger.info("✓ Microservice started successfully")
    try:
        yield
    finally:
        # Shutdown
        await room_manager.stop_heartbeat()
        room_manager.shutdown()
        logger.info("✓ Microservice stopped")
        # Hard-exit to skip Python finalization. The SDK holds ~20 static std::map sink
        # registries (+ g_sdk_sink_impl) whose py::object members would be decref'd during
        # C++ static teardown AFTER Py_Finalize -> "thread state is NULL" abort. The process
        # is exiting anyway and nothing needs flushing (DB writes are live), so bypass it.
        import os
        os._exit(0)


# ===== FastAPI Application =====

app = FastAPI(
    title="Zoom Rooms SDK Microservice",
    description="REST API for controlling Zoom Rooms via the ZRC SDK",
    version="1.5.0",
    lifespan=lifespan
)


# ===== Root & Health Endpoints =====

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Zoom Rooms SDK Microservice",
        "version": "1.5.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint — the k8s liveness/readiness probe target.

    Returns 503 when a pod restart is the correct remediation (heartbeat pump
    crashed, or the SDK is gone): the probes can only self-heal what this handler
    is willing to report (PRODUCTION-REVIEW.md 1.2). Includes SDK-call latency
    stats so slow (loop-stalling) calls are visible without grepping logs — see
    room_manager.SDKCallMonitor."""
    hb = room_manager.heartbeat_task
    reason = None
    if room_manager.sdk is None:
        reason = "sdk not initialized"
    elif hb is not None and hb.done():
        # The heartbeat loop runs forever; a *finished* task means it crashed.
        # Without the pump the SDK services nothing — restart is the remedy.
        reason = "heartbeat loop has stopped"
    body = {
        "status": "unhealthy" if reason else "healthy",
        "sdk_initialized": room_manager.sdk is not None,
        "active_rooms": len(room_manager.rooms),
        "sdk_call_timing": room_manager.sdk_monitor.stats()
    }
    if reason:
        body["reason"] = reason
        return JSONResponse(status_code=503, content=body)
    return body


# ===== Include Controllers =====

# Set the get_room_manager dependency for all controllers
rooms.get_room_manager = get_room_manager
meetings.get_room_manager = get_room_manager
meeting_controls.get_room_manager = get_room_manager
meeting_list.get_room_manager = get_room_manager
meeting_reminder.get_room_manager = get_room_manager
meeting_share.get_room_manager = get_room_manager
meeting_video.get_room_manager = get_room_manager
meeting_view_layout.get_room_manager = get_room_manager
ndi.get_room_manager = get_room_manager
participant.get_room_manager = get_room_manager
phone_call.get_room_manager = get_room_manager
pre_meeting.get_room_manager = get_room_manager
pro_av.get_room_manager = get_room_manager
recording.get_room_manager = get_room_manager
settings.get_room_manager = get_room_manager
third_party_meeting.get_room_manager = get_room_manager
events.get_room_manager = get_room_manager

app.include_router(rooms.router)
app.include_router(meetings.router)
app.include_router(meeting_controls.router)
app.include_router(meeting_list.router)
app.include_router(meeting_reminder.router)
app.include_router(meeting_share.router)
app.include_router(meeting_video.router)
app.include_router(meeting_view_layout.router)
app.include_router(ndi.router)
app.include_router(participant.router)
app.include_router(phone_call.router)
app.include_router(pre_meeting.router)
app.include_router(pro_av.router)
app.include_router(recording.router)
app.include_router(settings.router)
app.include_router(third_party_meeting.router)
app.include_router(events.router)

# ===== Server Launch =====

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
