"""
Meeting reminder endpoints - notifications, consent, reminders from ai companion, recording, transcription
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Callable

try:
    import zrc_sdk
except ImportError:
    print("ERROR: zrc_sdk module not found.")
    raise

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rooms/{room_id}", tags=["reminder"])

# This will be set by app.py
get_room_manager: Callable = None


def _resolve_enum(enum_cls, value):
    """Resolve an SDK enum from either its int value or its member name.

    The event stream emits enums by NAME (e.g. "CONSENT_TYPE_ARCHIVING"), so a
    client that echoes a captured value back sends the name; ints are still
    accepted for direct callers. Resolved against the wrapper's own bound enum,
    so it can never drift across SDK rebuilds. Raises ValueError (bad int) or
    AttributeError (bad name) on an unknown value.
    """
    if isinstance(value, int):
        return enum_cls(value)
    return getattr(enum_cls, value)

# ===== Pydantic Models =====

class ConfirmConsentRequest(BaseModel):
    is_agree: bool = False
    consent_type: int | str
    consent_id: str = ""

class NotificationRequest(BaseModel):
    is_agree: bool = False
    notification_type: int | str

class PrivacyRequest(BaseModel):
    privacy_alert_action: int | str
    privacy_alert_type: int | str

# ===== Endpoints =====
@router.post("/meeting/reminder/confirm-reminder")
async def confirm_reminder(room_id: str, request: NotificationRequest, room_manager = Depends(lambda: get_room_manager())):
    """Confirm meeting reminder"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        reminder_helper = meeting_service.GetMeetingReminderHelper()

        reminder_type_enum = _resolve_enum(zrc_sdk.MeetingReminderType, request.notification_type)
        result = reminder_helper.ConfirmMeetingReminder(request.is_agree, reminder_type_enum)

        return {
            "room_id": room_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/meeting/reminder/confirm-custom-reminder")
async def confirm_custom_reminder(room_id: str, request: NotificationRequest, room_manager = Depends(lambda: get_room_manager())):
    """Confirm customized meeting reminder"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        reminder_helper = meeting_service.GetMeetingReminderHelper()

        custom_type_enum = _resolve_enum(zrc_sdk.CustomizedMeetingReminderType, request.notification_type)
        result = reminder_helper.ConfirmCustomizedMeetingReminder(request.is_agree, custom_type_enum)

        return {
            "room_id": room_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))     

@router.post("/meeting/reminder/confirm-consent")
async def confirm_consent(room_id: str, request: ConfirmConsentRequest, room_manager = Depends(lambda: get_room_manager())):
    """Confirm consent"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        reminder_helper = meeting_service.GetMeetingReminderHelper()
        consent_type_enum = _resolve_enum(zrc_sdk.ConsentType, request.consent_type)
        result = reminder_helper.ConfirmConsent(request.is_agree, consent_type_enum, request.consent_id)

        return {
            "room_id": room_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))   

@router.post("/meeting/reminder/confirm-combined-consent")
async def confirm_combined_consent(room_id: str, request: NotificationRequest, room_manager = Depends(lambda: get_room_manager())):
    """Confirm combined consent"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        reminder_helper = meeting_service.GetMeetingReminderHelper()

        combined_type_enum = _resolve_enum(zrc_sdk.MeetingReminderType, request.notification_type)
        result = reminder_helper.ConfirmCombinedConsent(request.is_agree, combined_type_enum)

        return {
            "room_id": room_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/meeting/reminder/handle-privacy")
async def handle_privacy_alert(room_id: str, request: PrivacyRequest, room_manager = Depends(lambda: get_room_manager())):
    """Confirm combined consent"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        reminder_helper = meeting_service.GetMeetingReminderHelper()

        action_enum = _resolve_enum(zrc_sdk.PrivacyAlertAction, request.privacy_alert_action)
        type_enum = _resolve_enum(zrc_sdk.PrivacyAlertType, request.privacy_alert_type)
        result = reminder_helper.HandlePrivacyAlert(action_enum, type_enum)

        return {
            "room_id": room_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/meeting/reminder/continue-on-inactivity")
async def continue_on_inactivity(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """Continue meeting after inactivity detection notification"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        reminder_helper = meeting_service.GetMeetingReminderHelper()
        result = reminder_helper.ContinueMeetingOnInactivity()

        return {
            "room_id": room_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))