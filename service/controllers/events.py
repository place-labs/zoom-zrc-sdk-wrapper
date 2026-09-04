"""
Live event streaming - WebSocket endpoint for real-time SDK callbacks.

Clients connect to /api/rooms/{room_id}/events and receive flat JSON events as the
SDK fires callbacks for that room, e.g.:

    {"event": "OnUpdateMeetingStatus", "status": 3, "statusName": "MeetingStatusInMeeting"}
    {"event": "OnUserJoin", "session": 1, "sessionName": "ConfSessionTypeGeneral",
     "participants": [{"userID": 16778240, "userName": "Alice", "isHost": true, ...}]}

Events originate in the room_manager sink callbacks (which run on SDK threads) and are
fanned out to each subscriber's queue via the RoomManager event loop.
"""

import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Callable

logger = logging.getLogger(__name__)

router = APIRouter()

# This will be set by app.py
get_room_manager: Callable = None

# Idle keepalive interval (seconds); keeps the socket alive through proxy/ingress timeouts.
_KEEPALIVE_INTERVAL = 30.0


async def _forward(websocket: WebSocket, queue: asyncio.Queue):
    """Drain the subscriber queue to the client, sending a keepalive when idle."""
    while True:
        try:
            payload = await asyncio.wait_for(queue.get(), timeout=_KEEPALIVE_INTERVAL)
        except asyncio.TimeoutError:
            await websocket.send_json({"event": "keepalive"})
            continue
        await websocket.send_json(payload)


@router.websocket("/api/rooms/{room_id}/events")
async def room_events(websocket: WebSocket, room_id: str):
    """Stream live SDK events for a room. Accepts even if the room isn't paired yet
    (events begin flowing once it pairs/connects)."""
    room_manager = get_room_manager()
    await websocket.accept()
    queue = room_manager.subscribe_events(room_id)
    logger.info(f"[{room_id}] WebSocket subscriber connected")

    async def _receiver():
        # We don't expect inbound messages; this just detects client disconnect.
        while True:
            await websocket.receive_text()

    forward_task = asyncio.create_task(_forward(websocket, queue))
    receive_task = asyncio.create_task(_receiver())
    try:
        # Whichever finishes first (client disconnect, or a send failure) ends the session.
        done, _ = await asyncio.wait({forward_task, receive_task}, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            exc = task.exception()
            if exc and not isinstance(exc, WebSocketDisconnect):
                logger.debug(f"[{room_id}] WebSocket task ended: {exc}")
    finally:
        for task in (forward_task, receive_task):
            if not task.done():
                task.cancel()
        room_manager.unsubscribe_events(room_id, queue)
        logger.info(f"[{room_id}] WebSocket subscriber disconnected")
