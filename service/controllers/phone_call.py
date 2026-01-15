"""
Phone Call Controller
Endpoints for managing SIP/Zoom Phone calls
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import zrc_sdk

router = APIRouter(prefix="/api/rooms/{room_id}/phone", tags=["Phone Calls"])

# This will be set by the main app
get_room_manager = None


# ===== Request Models =====

class SIPCallInfoRequest(BaseModel):
    call_id: str


class TransferRequest(BaseModel):
    call_id: str
    transfer_type: str  # Blind, Warm, WarmComplete, Voicemail
    peer_uri: str


class UpgradeToMeetingRequest(BaseModel):
    call_id: str
    end_current_meeting: bool = False


class DTMFRequest(BaseModel):
    call_id: str
    dtmf: str  # 0-9, *, +, #


class MergeCallsRequest(BaseModel):
    host_call_id: str
    participant_call_id: str


# ===== Helper Functions =====

def get_phone_call_service(room_id: str, room_manager):
    """Get phone call service for a room"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail=f"Room {room_id} not found")

    phone_service = room_service.GetPhoneCallService()
    if not phone_service:
        raise HTTPException(status_code=500, detail="Phone call service not available")

    return phone_service


def sip_call_to_dict(call):
    """Convert SIPCallInfo to dict for JSON serialization"""
    return {
        "call_id": call.callID,
        "status": int(call.status),
        "peer_display_name": call.peerDisplayName,
        "peer_number": call.peerNumber,
        "peer_uri": call.peerURI,
        "is_incoming_call": call.isIncomingCall,
        "elapsed_call_time": call.elapsedCallTime,
        "is_emergency_call": call.isEmergencyCall,
        "peer_spam_type": int(call.peerSpamType),
        "peer_attest_level": int(call.peerAttestLevel),
        "original_peer_uri": call.originalPeerURI if hasattr(call, 'originalPeerURI') else "",
        "related_call_id": call.relatedCallID if hasattr(call, 'relatedCallID') else "",
        "blind_display_name": call.blindDisplayName if hasattr(call, 'blindDisplayName') else "",
        "self_info": {
            "name": call.selfInfo.name,
            "number": call.selfInfo.number,
            "attest_level": int(call.selfInfo.attestLevel)
        } if hasattr(call, 'selfInfo') else {},
        "conference_info": {
            "role": int(call.conferenceInfo.role),
            "host_call_id": call.conferenceInfo.hostCallID
        } if hasattr(call, 'conferenceInfo') else {},
        "redirect_info": {
            "end_type": int(call.redirectInfo.endType),
            "end_name": call.redirectInfo.endName,
            "end_number": call.redirectInfo.endNumber
        } if hasattr(call, 'redirectInfo') else {}
    }


def find_call_by_id(phone_service, call_id):
    """Find a SIP call by ID"""
    result, calls = phone_service.GetSIPCallList()
    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to get call list: {int(result)}")

    for call in calls:
        if call.callID == call_id:
            return call

    raise HTTPException(status_code=404, detail=f"Call {call_id} not found")


# ===== Endpoints =====

@router.get("/calls")
async def get_sip_calls(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """Get all SIP/Zoom Phone calls"""
    phone_service = get_phone_call_service(room_id, room_manager)
    result, calls = phone_service.GetSIPCallList()

    calls_list = [sip_call_to_dict(call) for call in calls]

    return {
        "room_id": room_id,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS,
        "calls": calls_list,
        "count": len(calls_list)
    }


@router.get("/calls/active")
async def get_unhold_call(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """Get the active (unhold) call"""
    phone_service = get_phone_call_service(room_id, room_manager)
    result, unholdCall = phone_service.GetUnholdSIPCall()

    return {
        "room_id": room_id,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS,
        "call": sip_call_to_dict(unholdCall) if result == zrc_sdk.ZRCSDKERR_SUCCESS else None
    }


@router.post("/call")
async def make_call(room_id: str, uri: str, room_manager = Depends(lambda: get_room_manager())):
    """Make a SIP/Zoom Phone call"""
    phone_service = get_phone_call_service(room_id, room_manager)
    result = phone_service.CallSIP(uri)

    return {
        "room_id": room_id,
        "uri": uri,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.post("/accept")
async def accept_incoming_call(room_id: str, request: SIPCallInfoRequest, room_manager = Depends(lambda: get_room_manager())):
    """Accept incoming SIP call"""
    phone_service = get_phone_call_service(room_id, room_manager)
    call_info = find_call_by_id(phone_service, request.call_id)
    result = phone_service.AcceptIncomingSIPCall(call_info)

    return {
        "room_id": room_id,
        "call_id": request.call_id,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.post("/accept-and-hold")
async def hold_and_accept_incoming_call(room_id: str, request: SIPCallInfoRequest, room_manager = Depends(lambda: get_room_manager())):
    """Hold current call and accept incoming SIP call"""
    phone_service = get_phone_call_service(room_id, room_manager)
    call_info = find_call_by_id(phone_service, request.call_id)
    result = phone_service.HoldAndAcceptIncomingSIPCall(call_info)

    return {
        "room_id": room_id,
        "call_id": request.call_id,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.post("/accept-and-end")
async def end_and_accept_incoming_call(room_id: str, request: SIPCallInfoRequest, room_manager = Depends(lambda: get_room_manager())):
    """End current call and accept incoming SIP call"""
    phone_service = get_phone_call_service(room_id, room_manager)
    call_info = find_call_by_id(phone_service, request.call_id)
    result = phone_service.EndAndAcceptIncomingSIPCall(call_info)

    return {
        "room_id": room_id,
        "call_id": request.call_id,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.post("/decline")
async def decline_incoming_call(room_id: str, request: SIPCallInfoRequest, room_manager = Depends(lambda: get_room_manager())):
    """Decline incoming SIP call"""
    phone_service = get_phone_call_service(room_id, room_manager)
    call_info = find_call_by_id(phone_service, request.call_id)
    result = phone_service.DeclineIncomingSIPCall(call_info)

    return {
        "room_id": room_id,
        "call_id": request.call_id,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.post("/hangup")
async def hangup_call(room_id: str, request: SIPCallInfoRequest, room_manager = Depends(lambda: get_room_manager())):
    """Hang up SIP call"""
    phone_service = get_phone_call_service(room_id, room_manager)
    call_info = find_call_by_id(phone_service, request.call_id)
    result = phone_service.HangupSIPCall(call_info)

    return {
        "room_id": room_id,
        "call_id": request.call_id,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.post("/mute")
async def mute_call_audio(room_id: str, mute: bool, room_manager = Depends(lambda: get_room_manager())):
    """Mute/unmute SIP call audio"""
    phone_service = get_phone_call_service(room_id, room_manager)
    result = phone_service.MuteSIPCallAudio(mute)

    return {
        "room_id": room_id,
        "mute": mute,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.post("/dtmf")
async def send_dtmf(room_id: str, request: DTMFRequest, room_manager = Depends(lambda: get_room_manager())):
    """Send DTMF tones (0-9, *, +, #)"""
    phone_service = get_phone_call_service(room_id, room_manager)
    call_info = find_call_by_id(phone_service, request.call_id)
    result = phone_service.SendDTMFToSIPCall(request.dtmf, call_info)

    return {
        "room_id": room_id,
        "call_id": request.call_id,
        "dtmf": request.dtmf,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.post("/hold")
async def hold_call(room_id: str, request: SIPCallInfoRequest, room_manager = Depends(lambda: get_room_manager())):
    """Hold SIP call"""
    phone_service = get_phone_call_service(room_id, room_manager)
    call_info = find_call_by_id(phone_service, request.call_id)
    result = phone_service.HoldSIPCall(call_info)

    return {
        "room_id": room_id,
        "call_id": request.call_id,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.post("/unhold")
async def unhold_call(room_id: str, request: SIPCallInfoRequest, room_manager = Depends(lambda: get_room_manager())):
    """Unhold SIP call"""
    phone_service = get_phone_call_service(room_id, room_manager)
    call_info = find_call_by_id(phone_service, request.call_id)
    result = phone_service.UnholdSIPCall(call_info)

    return {
        "room_id": room_id,
        "call_id": request.call_id,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.post("/merge")
async def merge_calls(room_id: str, request: MergeCallsRequest, room_manager = Depends(lambda: get_room_manager())):
    """Merge two SIP calls"""
    phone_service = get_phone_call_service(room_id, room_manager)
    host_call = find_call_by_id(phone_service, request.host_call_id)
    participant_call = find_call_by_id(phone_service, request.participant_call_id)
    result = phone_service.MergeSIPCall(host_call, participant_call)

    return {
        "room_id": room_id,
        "host_call_id": request.host_call_id,
        "participant_call_id": request.participant_call_id,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.post("/transfer")
async def transfer_call(room_id: str, request: TransferRequest, room_manager = Depends(lambda: get_room_manager())):
    """Transfer SIP call"""
    phone_service = get_phone_call_service(room_id, room_manager)
    call_info = find_call_by_id(phone_service, request.call_id)

    # Create transfer info
    transfer_info = zrc_sdk.SIPCallTransferInfo()
    transfer_info.peerURI = request.peer_uri

    transfer_type_map = {
        "Blind": zrc_sdk.SIPCallTransferInfoTypeBlind,
        "Warm": zrc_sdk.SIPCallTransferInfoTypeWarm,
        "WarmComplete": zrc_sdk.SIPCallTransferInfoTypeWarmComplete,
        "Voicemail": zrc_sdk.SIPCallTransferInfoTypeVoicemail
    }
    transfer_info.type = transfer_type_map.get(request.transfer_type, zrc_sdk.SIPCallTransferInfoTypeBlind)

    result = phone_service.TransferSIPCall(call_info, transfer_info)

    return {
        "room_id": room_id,
        "call_id": request.call_id,
        "transfer_type": request.transfer_type,
        "peer_uri": request.peer_uri,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.post("/transfer/complete-warm")
async def complete_warm_transfer(room_id: str, request: SIPCallInfoRequest, room_manager = Depends(lambda: get_room_manager())):
    """Complete warm transfer"""
    phone_service = get_phone_call_service(room_id, room_manager)
    call_info = find_call_by_id(phone_service, request.call_id)
    result = phone_service.CompleteWarmTransfer(call_info)

    return {
        "room_id": room_id,
        "call_id": request.call_id,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.post("/transfer/cancel-warm")
async def cancel_warm_transfer(room_id: str, request: SIPCallInfoRequest, room_manager = Depends(lambda: get_room_manager())):
    """Cancel warm transfer"""
    phone_service = get_phone_call_service(room_id, room_manager)
    call_info = find_call_by_id(phone_service, request.call_id)
    result = phone_service.CancelWarmTransfer(call_info)

    return {
        "room_id": room_id,
        "call_id": request.call_id,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.post("/upgrade-to-meeting")
async def upgrade_to_meeting(room_id: str, request: UpgradeToMeetingRequest, room_manager = Depends(lambda: get_room_manager())):
    """Upgrade SIP call to Zoom meeting"""
    phone_service = get_phone_call_service(room_id, room_manager)
    call_info = find_call_by_id(phone_service, request.call_id)
    result = phone_service.UpgradeSIPCallToMeeting(call_info, request.end_current_meeting)

    return {
        "room_id": room_id,
        "call_id": request.call_id,
        "end_current_meeting": request.end_current_meeting,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.post("/accept-upgrade-to-meeting")
async def accept_upgrade_to_meeting(room_id: str, request: SIPCallInfoRequest, room_manager = Depends(lambda: get_room_manager())):
    """Accept invitation to upgrade SIP call to meeting"""
    phone_service = get_phone_call_service(room_id, room_manager)
    call_info = find_call_by_id(phone_service, request.call_id)
    result = phone_service.AcceptSIPCallToMeeting(call_info)

    return {
        "room_id": room_id,
        "call_id": request.call_id,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.post("/decline-upgrade-to-meeting")
async def decline_upgrade_to_meeting(room_id: str, request: SIPCallInfoRequest, room_manager = Depends(lambda: get_room_manager())):
    """Decline invitation to upgrade SIP call to meeting"""
    phone_service = get_phone_call_service(room_id, room_manager)
    call_info = find_call_by_id(phone_service, request.call_id)
    result = phone_service.DeclineSIPCallToMeeting(call_info)

    return {
        "room_id": room_id,
        "call_id": request.call_id,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.post("/location-permission")
async def set_location_permission(room_id: str, enable: bool, room_manager = Depends(lambda: get_room_manager())):
    """Set location permission for emergency calls"""
    phone_service = get_phone_call_service(room_id, room_manager)
    result = phone_service.SetLocationPermissionEnable(enable)

    return {
        "room_id": room_id,
        "enable": enable,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.get("/location-permission")
async def get_location_permission(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """Get location permission for emergency calls"""
    phone_service = get_phone_call_service(room_id, room_manager)
    result, enable = phone_service.GetLocationPermissionEnable()

    return {
        "room_id": room_id,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS,
        "enabled": enable
    }
