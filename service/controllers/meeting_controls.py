"""
Meeting control endpoints - lock, focus mode, AI Companion, panels, etc.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import Callable

try:
    import zrc_sdk
except ImportError:
    print("ERROR: zrc_sdk module not found.")
    raise

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rooms/{room_id}", tags=["meeting-controls"])

# This will be set by app.py
get_room_manager: Callable = None


# ===== Endpoints =====

@router.post("/meeting/topbanner")
async def show_top_banner(room_id: str, show: bool = True, room_manager = Depends(lambda: get_room_manager())):
    """Show or hide the top banner"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        control_helper = meeting_service.GetMeetingControlHelper()
        result = control_helper.ShowTopBanner(show)

        return {
            "room_id": room_id,
            "show": show,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meeting/lock")
async def lock_meeting(room_id: str, lock: bool = True, room_manager = Depends(lambda: get_room_manager())):
    """Lock or unlock the meeting"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        control_helper = meeting_service.GetMeetingControlHelper()
        result = control_helper.LockMeeting(lock)

        return {
            "room_id": room_id,
            "locked": lock,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meeting/focus-mode")
async def start_focus_mode(room_id: str, start: bool = True, room_manager = Depends(lambda: get_room_manager())):
    """Start or stop focus mode"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        control_helper = meeting_service.GetMeetingControlHelper()
        result = control_helper.StartFocusMode(start)

        return {
            "room_id": room_id,
            "started": start,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meeting/hifi-music")
async def enable_hifi_music(room_id: str, enable: bool = True, room_manager = Depends(lambda: get_room_manager())):
    """Enable or disable high-fidelity music mode"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        control_helper = meeting_service.GetMeetingControlHelper()
        result = control_helper.EnableHiFiMusicMode(enable)

        return {
            "room_id": room_id,
            "enabled": enable,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meeting/summary")
async def start_meeting_summary(room_id: str, start: bool = True, room_manager = Depends(lambda: get_room_manager())):
    """Start or stop meeting summary (AI Companion)"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        control_helper = meeting_service.GetMeetingControlHelper()
        result = control_helper.StartMeetingSummary(start)

        return {
            "room_id": room_id,
            "started": start,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meeting/summary/email")
async def set_summary_email(room_id: str, email: str, room_manager = Depends(lambda: get_room_manager())):
    """Set meeting summary notification email"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        control_helper = meeting_service.GetMeetingControlHelper()
        result = control_helper.SetMeetingSummaryNotificationEmail(email)

        return {
            "room_id": room_id,
            "email": email,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meeting/query")
async def start_meeting_query(room_id: str, start: bool = True, room_manager = Depends(lambda: get_room_manager())):
    """Start or stop meeting query (AI Companion)"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        control_helper = meeting_service.GetMeetingControlHelper()
        result = control_helper.StartMeetingQuery(start)

        return {
            "room_id": room_id,
            "started": start,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-companion/turn-on")
async def turn_on_ai_companion(room_id: str, features: int, room_manager = Depends(lambda: get_room_manager())):
    """Turn on AI Companion features (SmartSummary=32, SmartQuestion=64, SmartRecording=256)"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        control_helper = meeting_service.GetMeetingControlHelper()
        result = control_helper.TurnOnAICompanion(features)

        return {
            "room_id": room_id,
            "features": features,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-companion/turn-off")
async def turn_off_ai_companion(room_id: str, features: int, delete_assets: bool = False, room_manager = Depends(lambda: get_room_manager())):
    """Turn off AI Companion features"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        control_helper = meeting_service.GetMeetingControlHelper()
        result = control_helper.TurnOffAICompanion(features, delete_assets)

        return {
            "room_id": room_id,
            "features": features,
            "delete_assets": delete_assets,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-companion/respond-to-turn-on")
async def respond_to_turn_on_ai_companion(room_id: str, agree: bool = True, room_manager = Depends(lambda: get_room_manager())):
    """Accept or deny a participant's request to turn on AI Companion."""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        control_helper = meeting_service.GetMeetingControlHelper()
        result = control_helper.RespondToTurnOnAICompanion(agree)
        if result != zrc_sdk.ZRCSDKERR_SUCCESS:
            raise RuntimeError(f"failed to respond to AI Companion turn-on request: {result}")

        return {
            "room_id": room_id,
            "agree": agree,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-companion/respond-to-turn-off")
async def respond_to_turn_off_ai_companion(room_id: str, agree: bool = True, delete_assets: bool = False, room_manager = Depends(lambda: get_room_manager())):
    """Accept or deny a participant's request to turn off AI Companion."""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        control_helper = meeting_service.GetMeetingControlHelper()
        result = control_helper.RespondToTurnOffAICompanion(agree, delete_assets)
        if result != zrc_sdk.ZRCSDKERR_SUCCESS:
            raise RuntimeError(f"failed to respond to AI Companion turn-off request: {result}")

        return {
            "room_id": room_id,
            "agree": agree,
            "delete_assets": delete_assets,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-companion/confirm-status-when-join")
async def confirm_ai_companion_status_when_join(room_id: str, agree: bool = True, room_manager = Depends(lambda: get_room_manager())):
    """Confirm AI Companion changes made by a participant before the host joined."""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        meeting_service = room_service.GetMeetingService()
        control_helper = meeting_service.GetMeetingControlHelper()
        result = control_helper.ConfirmAICompanionStatusWhenJoin(agree)
        if result != zrc_sdk.ZRCSDKERR_SUCCESS:
            raise RuntimeError(f"failed to confirm AI Companion status: {result}")

        return {
            "room_id": room_id,
            "agree": agree,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/panel/control")
async def control_side_panel(room_id: str, panel_type: str = "PList", action: str = "Show", room_manager = Depends(lambda: get_room_manager())):
    """Control side panel (panel_type: None, PList; action: Show, Hide, SwitchTab, ScrollUp, ScrollDown)"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        # Map string values to enums
        panel_map = {
            "None": zrc_sdk.PanelTypeNone,
            "PList": zrc_sdk.PanelTypePList
        }
        action_map = {
            "Show": zrc_sdk.PanelActionShow,
            "Hide": zrc_sdk.PanelActionHide,
            "SwitchTab": zrc_sdk.PanelActionSwitchTab,
            "ScrollUp": zrc_sdk.PanelActionScrollUp,
            "ScrollDown": zrc_sdk.PanelActionScrollDown
        }

        panel_enum = panel_map.get(panel_type)
        action_enum = action_map.get(action)

        if panel_enum is None or action_enum is None:
            raise HTTPException(status_code=400, detail="Invalid panel_type or action")

        meeting_service = room_service.GetMeetingService()
        control_helper = meeting_service.GetMeetingControlHelper()
        result = control_helper.ControlSidePanel(panel_enum, action_enum)

        return {
            "room_id": room_id,
            "panel_type": panel_type,
            "action": action,
            "result": int(result),
            "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
