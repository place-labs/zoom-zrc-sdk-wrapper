"""
Meeting list endpoints - calendar, scheduling, check-in/out
"""

import logging
import asyncio
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

def dial_number_to_dict(dial_number: zrc_sdk.DialNumber) -> dict:
    return {
        "country_code": dial_number.countryCode,
        "phone_number": dial_number.phoneNumber,
    }


def third_party_meeting_to_dict(info: zrc_sdk.ThirdPartyMeeting) -> dict:
    return {
        "service_provider": int(info.serviceProvider),
        "meeting_number": info.meetingNumber,
        "sip_address": info.sipAddress,
        "h323_address": info.h323Address,
        "join_meeting_url": info.joinMeetingURL,
        "dial_numbers": [dial_number_to_dict(item) for item in info.dialNumbers],
    }


def scheduled_by_to_dict(info: zrc_sdk.EventScheduledByUserInfo) -> dict:
    return {
        "user_id": info.userID,
        "user_name": info.userName,
        "user_avatar_url": info.userAvatarURL,
    }


def meeting_item_to_dict(item: zrc_sdk.MeetingItem) -> dict:
    return {
        "zoom_meeting_item_type": int(item.zoomMeetingItemType),
        "meeting_number": item.meetingNumber,
        "meeting_name": item.meetingName,
        "host_name": item.hostName,
        "start_time": item.startTime,
        "end_time": item.endTime,
        "scheduled_from": item.scheduledFrom,
        "is_private": item.isPrivate,
        "is_all_day_event": item.isAllDayEvent,
        "is_checked_in": item.isCheckedIn,
        "meeting_domain": item.meetingDomain,
        "is_instant_meeting": item.isInstantMeeting,
        "third_party_meeting_info": third_party_meeting_to_dict(item.thirdPartyMeetingInfo),
        "scheduled_by_info": scheduled_by_to_dict(item.scheduledByInfo),
    }


@router.get("/meetings/list")
async def list_meetings(
    room_id: str,
    timeout: float = 15.0,
    room_manager = Depends(lambda: get_room_manager()),
):
    """List all meetings from the room's calendar"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        if not meeting_service:
            raise HTTPException(status_code=500, detail="Meeting service not available")
        list_helper = meeting_service.GetMeetingListHelper()
        if not list_helper:
            raise HTTPException(status_code=500, detail="Meeting list helper not available")
        meeting_list_sink = room_manager.get_meeting_list_sink(room_id)
        if not meeting_list_sink:
            raise HTTPException(status_code=500, detail="Meeting list callbacks not registered")

        future = meeting_list_sink.create_list_future()
        result = list_helper.ListMeeting()

        if result != zrc_sdk.ZRCSDKERR_SUCCESS:
            meeting_list_sink.cancel_list_future(future)
            raise HTTPException(status_code=500, detail=f"ListMeeting request failed: {result}")

        try:
            list_result, meeting_list = await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            meeting_list_sink.cancel_list_future(future)
            raise HTTPException(status_code=408, detail="ListMeeting timeout - no callback received")

        meetings = [meeting_item_to_dict(item) for item in (meeting_list or [])]

        return {
            "room_id": room_id,
            "request_result": int(result),
            "request_success": result == zrc_sdk.ZRCSDKERR_SUCCESS,
            "list_result": int(list_result),
            "list_success": list_result == zrc_sdk.ListMeetingResult.LIST_MEETING_SUCCESS,
            "meetings": meetings,
        }
    except HTTPException:
        raise
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
