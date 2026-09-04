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
    """Resolve an SDK enum from its int value, digit-string, or member name.

    The event stream emits enums by NAME (e.g. "CONSENT_TYPE_ARCHIVING"), so a
    client that echoes a captured value back sends the name; ints are still
    accepted for direct callers, and digit strings ("3") coerce like ints —
    pydantic v2 no longer coerces those on int|str fields, but pre-widening
    clients relied on it. Resolved against the wrapper's own bound enum, so it
    can never drift across SDK rebuilds. An unknown value is the CLIENT's error:
    raises HTTPException 422 listing the allowed members, never an internal
    error (PRODUCTION-REVIEW.md 3.6).
    """
    try:
        if isinstance(value, str):
            v = value.strip()
            if v.lstrip("+-").isdigit():
                return enum_cls(int(v))
            return getattr(enum_cls, v)
        return enum_cls(value)
    except (AttributeError, ValueError, TypeError, KeyError):
        members = list(getattr(enum_cls, "__members__", {}))
        raise HTTPException(
            status_code=422,
            detail=f"invalid {getattr(enum_cls, '__name__', 'enum')} value {value!r}; "
                   f"expected an integer value or one of {members}")


def _resolve_open_int(enum_cls, value, field_name: str) -> int:
    """Resolve an SDK open-integer field while preserving known enum names.

    Some reminder callback fields are deliberately plain integers for forward
    compatibility. Their bound enum lists known values but must not be used to
    reject new integer values sent by a newer Zoom Room.
    """
    if isinstance(value, str):
        raw = value.strip()
        if raw.lstrip("+-").isdigit():
            return int(raw)
        try:
            return int(getattr(enum_cls, raw))
        except (AttributeError, TypeError, ValueError):
            members = list(getattr(enum_cls, "__members__", {}))
            raise HTTPException(
                status_code=422,
                detail=f"invalid {field_name} value {value!r}; expected an "
                       f"integer value or one of {members}",
            )
    try:
        return int(value)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=422,
            detail=f"invalid {field_name} value {value!r}; expected an integer",
        )

# ===== Pydantic Models =====

class ConfirmConsentRequest(BaseModel):
    is_agree: bool = False
    consent_type: int | str
    consent_id: str = ""

class NotificationRequest(BaseModel):
    is_agree: bool = False
    notification_type: int | str


class ConsolidatedCustomizedConsentRequest(BaseModel):
    is_agree: bool = False


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
    except HTTPException:
        raise
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

        # The SDK struct and operation both use a plain int32 for forward
        # compatibility. Accept any echoed integer while retaining enum names
        # for callers using the currently documented values.
        custom_type = _resolve_open_int(
            zrc_sdk.CustomizedMeetingReminderType,
            request.notification_type,
            "notification_type",
        )
        result = reminder_helper.ConfirmCustomizedMeetingReminder(
            request.is_agree, custom_type
        )

        return {
            "room_id": room_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except HTTPException:
        raise
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
    except HTTPException:
        raise
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

        # The SDK contract is an OPEN int64 — the CombinedConsent.type value the
        # room sent in OnCombinedConsentNotification (serialized as a plain int on
        # the WS; there are no names to echo). No enum table applies — the
        # MeetingReminderType resolution previously here was the wrong surface's
        # table and rejected legitimate echoed values (PRODUCTION-REVIEW.md 3.7).
        raw = request.notification_type
        if isinstance(raw, str):
            v = raw.strip()
            if not v.lstrip("+-").isdigit():
                raise HTTPException(
                    status_code=422,
                    detail=f"notification_type is an open integer for combined consent — "
                           f"echo the combinedConsent.type value from the notification "
                           f"event; got {raw!r}")
            raw = int(v)
        result = reminder_helper.ConfirmCombinedConsent(request.is_agree, raw)

        return {
            "room_id": room_id,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meeting/reminder/agree-consolidated-customized-consent")
async def agree_consolidated_customized_consent(
    room_id: str,
    request: ConsolidatedCustomizedConsentRequest,
    room_manager = Depends(lambda: get_room_manager()),
):
    """Respond to the SDK 7.1 consolidated customized-consent prompt."""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        reminder_helper = meeting_service.GetMeetingReminderHelper()
        result = reminder_helper.AgreeConsolidatedCustomizedConsent(
            request.is_agree
        )

        return {
            "room_id": room_id,
            "is_agree": request.is_agree,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS,
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
    except HTTPException:
        raise
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
