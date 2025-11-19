"""
Meeting list endpoints - calendar, scheduling, check-in/out
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Callable, List

try:
    import zrc_sdk
except ImportError:
    print("ERROR: zrc_sdk module not found.")
    raise

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rooms/{room_id}", tags=["meeting-list"])

# This will be set by app.py
get_room_manager: Callable = None


# ===== Pydantic Models =====

class ScheduleMeetingRequest(BaseModel):
    topic: str
    password: str = ""
    start_time: str  # Format: "2017-03-15T11:30:00-07:00"
    end_time: str    # Format: "2017-03-15T11:30:00-07:00"
    attendees: List[str] = []  # Email addresses
    enable_waiting_room: bool = False


class MeetingItemRequest(BaseModel):
    meeting_number: str
    meeting_name: str = ""
    host_name: str = ""
    start_time: str = ""
    end_time: str = ""


# ===== Endpoints =====

@router.get("/meetings/list")
async def list_meetings(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """List all meetings from the room's calendar"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        list_helper = meeting_service.GetMeetingListHelper()
        result = list_helper.ListMeeting()

        return {
            "room_id": room_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS,
            "message": "ListMeeting request sent - results will be delivered via callback"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meetings/schedule")
async def schedule_meeting(room_id: str, request: ScheduleMeetingRequest, room_manager = Depends(lambda: get_room_manager())):
    """Schedule a new calendar event/meeting"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        list_helper = meeting_service.GetMeetingListHelper()

        # Create schedule param
        schedule_param = zrc_sdk.ScheduleCalendarEventParam()
        schedule_param.topic = request.topic
        schedule_param.password = request.password
        schedule_param.startTime = request.start_time
        schedule_param.endTime = request.end_time
        schedule_param.attendees = request.attendees
        schedule_param.enableWaitingRoom = request.enable_waiting_room

        result = list_helper.ScheduleCalendarEvent(schedule_param)

        return {
            "room_id": room_id,
            "topic": request.topic,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meetings/delete")
async def delete_meeting(room_id: str, request: MeetingItemRequest, room_manager = Depends(lambda: get_room_manager())):
    """Delete a calendar event/meeting"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        list_helper = meeting_service.GetMeetingListHelper()

        # Create meeting item
        meeting_item = zrc_sdk.MeetingItem()
        meeting_item.meetingNumber = request.meeting_number
        meeting_item.meetingName = request.meeting_name
        meeting_item.hostName = request.host_name
        meeting_item.startTime = request.start_time
        meeting_item.endTime = request.end_time

        result = list_helper.DeleteCalendarEvent(meeting_item)

        return {
            "room_id": room_id,
            "meeting_number": request.meeting_number,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meetings/check-in")
async def check_in_meeting(room_id: str, request: MeetingItemRequest, room_manager = Depends(lambda: get_room_manager())):
    """Check in to a calendar event/meeting"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        list_helper = meeting_service.GetMeetingListHelper()

        # Create meeting item
        meeting_item = zrc_sdk.MeetingItem()
        meeting_item.meetingNumber = request.meeting_number
        meeting_item.meetingName = request.meeting_name
        meeting_item.hostName = request.host_name
        meeting_item.startTime = request.start_time
        meeting_item.endTime = request.end_time

        result = list_helper.CheckInCalendarEvent(meeting_item)

        return {
            "room_id": room_id,
            "meeting_number": request.meeting_number,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meetings/check-out")
async def check_out_meeting(room_id: str, request: MeetingItemRequest, room_manager = Depends(lambda: get_room_manager())):
    """Check out from a calendar event/meeting"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        list_helper = meeting_service.GetMeetingListHelper()

        # Create meeting item
        meeting_item = zrc_sdk.MeetingItem()
        meeting_item.meetingNumber = request.meeting_number
        meeting_item.meetingName = request.meeting_name
        meeting_item.hostName = request.host_name
        meeting_item.startTime = request.start_time
        meeting_item.endTime = request.end_time

        result = list_helper.CheckOutCalendarEvent(meeting_item)

        return {
            "room_id": room_id,
            "meeting_number": request.meeting_number,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meetings/show-upcoming-alert")
async def show_upcoming_alert(room_id: str, request: MeetingItemRequest, room_manager = Depends(lambda: get_room_manager())):
    """Show upcoming meeting alert"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        list_helper = meeting_service.GetMeetingListHelper()

        # Create meeting item
        meeting_item = zrc_sdk.MeetingItem()
        meeting_item.meetingNumber = request.meeting_number
        meeting_item.meetingName = request.meeting_name
        meeting_item.hostName = request.host_name
        meeting_item.startTime = request.start_time
        meeting_item.endTime = request.end_time

        result = list_helper.ShowUpcomingMeetingAlert(meeting_item)

        return {
            "room_id": room_id,
            "meeting_number": request.meeting_number,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meetings/close-upcoming-alert")
async def close_upcoming_alert(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """Close upcoming meeting alert"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        list_helper = meeting_service.GetMeetingListHelper()
        result = list_helper.CloseUpcomingMeetingAlert()

        return {
            "room_id": room_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meetings/close-auto-release-alert")
async def close_auto_release_alert(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """Close auto release meeting alert"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        list_helper = meeting_service.GetMeetingListHelper()
        result = list_helper.CloseAutoReleaseMeetingAlert()

        return {
            "room_id": room_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
