"""
Participant Controller
Endpoints for managing meeting participants
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import zrc_sdk

router = APIRouter(prefix="/api/rooms/{room_id}/participants", tags=["Participants"])

# This will be set by the main app
get_room_manager = None


# ===== Request Models =====

class AssignCohostRequest(BaseModel):
    user_id: int
    assign: bool


class RenameUserRequest(BaseModel):
    user_id: int
    name: str


class ExpelUsersRequest(BaseModel):
    user_ids: List[int]


class ReportIssueRequest(BaseModel):
    user_ids: List[int]
    issue_type: int  # Bitset of ReportIssueType values
    email: str


# ===== Helper Functions =====

def get_participant_helper(room_id: str, room_manager):
    """Get participant helper for a room"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail=f"Room {room_id} not found")

    meeting_service = room_service.GetMeetingService()
    if not meeting_service:
        raise HTTPException(status_code=500, detail="Meeting service not available")

    participant_helper = meeting_service.GetParticipantHelper()
    if not participant_helper:
        raise HTTPException(status_code=500, detail="Participant helper not available")

    return participant_helper


def audio_status_to_dict(status):
    if not status:
        return None
    return {
        "audio_type": status.audioType.name,
        "is_muted": status.isMuted,
    }


def video_status_to_dict(status):
    if not status:
        return None
    return {
        "has_source": status.hasSource,
        "receiving": status.receiving,
        "sending": status.sending,
        "can_control": status.canControl,
    }


def participant_to_dict(p):
    """Convert MeetingParticipant to dict for JSON serialization"""
    hand_status = getattr(p, "handStatus", None)
    is_raising_hand = getattr(p, "isRaisingHand", None)
    if hand_status and hasattr(hand_status, "handRaised"):
        is_raising_hand = hand_status.handRaised

    avatar_path = getattr(p, "avatarPath", None)
    if not avatar_path:
        avatar_path = getattr(p, "avatarUrl", "")

    is_myself = getattr(p, "isMyself", getattr(p, "isMySelf", False))

    # The SDK has no isInWaitingRoom; silent mode covers waiting room and
    # put-on-hold (IWaitingRoomHelper.h), so the contract field maps to it.
    is_in_silent_mode = getattr(p, "isInSilentMode", None)

    return {
        "user_id": getattr(p, "userID", 0),
        "user_name": getattr(p, "userName", ""),
        "is_host": getattr(p, "isHost", False),
        "is_cohost": getattr(p, "isCohost", False),
        "is_myself": is_myself,
        "is_in_waiting_room": is_in_silent_mode,
        "is_in_silent_mode": is_in_silent_mode,
        "is_leaving_silent_mode": getattr(p, "isLeavingSilentMode", None),
        "is_raising_hand": is_raising_hand,
        "is_talking": getattr(p, "isTalking", None),
        "audio_status": audio_status_to_dict(getattr(p, "audioStatus", None)),
        "video_status": video_status_to_dict(getattr(p, "videoStatus", None)),
        "is_on_hold": getattr(p, "isOnHold", None),
        "avatar_path": avatar_path,
        "parent_user_id": getattr(p, "parentUserID", 0),
    }


# ===== Endpoints =====

@router.get("/")
async def get_participants(room_id: str, session: str = "CurrentSession", room_manager = Depends(lambda: get_room_manager())):
    """Get participants in meeting"""
    participant_helper = get_participant_helper(room_id, room_manager)

    session_map = {
        "CurrentSession": zrc_sdk.CurrentSession,
        "MasterSession": zrc_sdk.MasterSession
    }
    conf_session = session_map.get(session, zrc_sdk.CurrentSession)

    result, participants = participant_helper.GetParticipantsInMeeting(conf_session)

    participants_list = [participant_to_dict(p) for p in participants]

    return {
        "room_id": room_id,
        "session": session,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS,
        "participants": participants_list,
        "count": len(participants_list)
    }


@router.get("/virtual")
async def get_virtual_participants(room_id: str, session: str = "CurrentSession", room_manager = Depends(lambda: get_room_manager())):
    """Get virtual participants in meeting (e.g., multi stream, multi camera)"""
    participant_helper = get_participant_helper(room_id, room_manager)

    session_map = {
        "CurrentSession": zrc_sdk.CurrentSession,
        "MasterSession": zrc_sdk.MasterSession
    }
    conf_session = session_map.get(session, zrc_sdk.CurrentSession)

    result, participants = participant_helper.GetVirtualParticipantsInMeeting(conf_session)

    participants_list = [participant_to_dict(p) for p in participants]

    return {
        "room_id": room_id,
        "session": session,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS,
        "virtual_participants": participants_list,
        "count": len(participants_list)
    }


@router.get("/silent-mode")
async def get_participants_in_silent_mode(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """Get participants in silent mode"""
    participant_helper = get_participant_helper(room_id, room_manager)
    result, participants = participant_helper.GetParticipantsInSilentMode()

    participants_list = [participant_to_dict(p) for p in participants]

    return {
        "room_id": room_id,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS,
        "participants": participants_list,
        "count": len(participants_list)
    }


@router.get("/left")
async def get_participants_left_meeting(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """Get participants who left meeting"""
    participant_helper = get_participant_helper(room_id, room_manager)
    result, participants = participant_helper.GetParticipantsLeftMeeting()

    participants_list = [participant_to_dict(p) for p in participants]

    return {
        "room_id": room_id,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS,
        "participants": participants_list,
        "count": len(participants_list)
    }


@router.post("/assign-host")
async def assign_host(room_id: str, user_id: int, room_manager = Depends(lambda: get_room_manager())):
    """Assign host to a user"""
    participant_helper = get_participant_helper(room_id, room_manager)
    # SDK 7.1 added an optional assetsPrivilege argument. pybind11 does not
    # apply the C++ default argument, so pass None to preserve the existing API.
    result = participant_helper.AssignHost(user_id, None)

    return {
        "room_id": room_id,
        "user_id": user_id,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.post("/assign-cohost")
async def assign_cohost(room_id: str, request: AssignCohostRequest, room_manager = Depends(lambda: get_room_manager())):
    """Assign/unassign cohost to a user"""
    participant_helper = get_participant_helper(room_id, room_manager)
    # See assign_host: None maps to std::nullopt for the SDK 7.1 parameter.
    result = participant_helper.AssignCohost(request.user_id, request.assign, None)

    return {
        "room_id": room_id,
        "user_id": request.user_id,
        "assign": request.assign,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.post("/claim-host")
async def claim_host(room_id: str, host_key: str, room_manager = Depends(lambda: get_room_manager())):
    """Claim host with host key"""
    participant_helper = get_participant_helper(room_id, room_manager)
    result = participant_helper.ClaimHost(host_key)

    return {
        "room_id": room_id,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.post("/annotate-on-share")
async def enable_attendees_annotate_on_share(room_id: str, enable: bool, room_manager = Depends(lambda: get_room_manager())):
    """Enable/disable attendees annotate on shared content"""
    participant_helper = get_participant_helper(room_id, room_manager)
    result = participant_helper.EnableAttendeesAnnotateOnShare(enable)

    return {
        "room_id": room_id,
        "enable": enable,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.post("/rename")
async def rename_user(room_id: str, request: RenameUserRequest, room_manager = Depends(lambda: get_room_manager())):
    """Rename a user"""
    participant_helper = get_participant_helper(room_id, room_manager)
    result = participant_helper.RenameUser(request.user_id, request.name)

    return {
        "room_id": room_id,
        "user_id": request.user_id,
        "name": request.name,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.post("/allow-rename-themselves")
async def allow_attendees_rename_themselves(room_id: str, allow: bool, room_manager = Depends(lambda: get_room_manager())):
    """Allow/disallow attendees to rename themselves"""
    participant_helper = get_participant_helper(room_id, room_manager)
    result = participant_helper.AllowAttendeesRenameThemselves(allow)

    return {
        "room_id": room_id,
        "allow": allow,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.get("/rename-themselves-enabled")
async def is_attendees_rename_themselves_enabled(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """Check if attendees can rename themselves (enabled)"""
    participant_helper = get_participant_helper(room_id, room_manager)
    result, enable = participant_helper.IsAttendeesRenameThemselvesEnabled()

    return {
        "room_id": room_id,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS,
        "enabled": enable
    }


@router.get("/rename-themselves-locked")
async def is_attendees_rename_themselves_locked(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """Check if attendees rename themselves is locked"""
    participant_helper = get_participant_helper(room_id, room_manager)
    result, locked = participant_helper.IsAttendeesRenameThemselvesLocked()

    return {
        "room_id": room_id,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS,
        "locked": locked
    }


@router.get("/rename-themselves-allowed")
async def is_attendees_rename_themselves_allowed(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """Check if attendees rename themselves is allowed"""
    participant_helper = get_participant_helper(room_id, room_manager)
    result, allow = participant_helper.IsAttendeesRenameThemselvesAllowed()

    return {
        "room_id": room_id,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS,
        "allowed": allow
    }


@router.post("/allow-webinar-raise-hand")
async def allow_webinar_attendee_raise_hand(room_id: str, allow: bool, room_manager = Depends(lambda: get_room_manager())):
    """Allow/disallow webinar attendees to raise hand"""
    participant_helper = get_participant_helper(room_id, room_manager)
    result = participant_helper.AllowWebinarAttendeeRaiseHand(allow)

    return {
        "room_id": room_id,
        "allow": allow,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.post("/raise-hand")
async def raise_hand(room_id: str, raise_hand: bool, room_manager = Depends(lambda: get_room_manager())):
    """Raise/lower self hand"""
    participant_helper = get_participant_helper(room_id, room_manager)
    result = participant_helper.RaiseHand(raise_hand)

    return {
        "room_id": room_id,
        "raise_hand": raise_hand,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.post("/lower-hand/{user_id}")
async def lower_user_hand(room_id: str, user_id: int, room_manager = Depends(lambda: get_room_manager())):
    """Lower a user's hand"""
    participant_helper = get_participant_helper(room_id, room_manager)
    result = participant_helper.LowerUserHand(user_id)

    return {
        "room_id": room_id,
        "user_id": user_id,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.post("/lower-all-hands")
async def lower_all_hands(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """Lower all hands"""
    participant_helper = get_participant_helper(room_id, room_manager)
    result = participant_helper.LowerAllHands()

    return {
        "room_id": room_id,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.post("/lower-all-attendees-hands")
async def lower_all_attendees_hands(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """Lower all attendees' hands"""
    participant_helper = get_participant_helper(room_id, room_manager)
    result = participant_helper.LowerAllAttendeesHands()

    return {
        "room_id": room_id,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.delete("/{user_id}")
async def expel_user(room_id: str, user_id: int, room_manager = Depends(lambda: get_room_manager())):
    """Expel a user from meeting"""
    participant_helper = get_participant_helper(room_id, room_manager)
    result = participant_helper.ExpelUser(user_id)

    return {
        "room_id": room_id,
        "user_id": user_id,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.post("/expel-multiple")
async def expel_users(room_id: str, request: ExpelUsersRequest, room_manager = Depends(lambda: get_room_manager())):
    """Expel multiple users from meeting"""
    participant_helper = get_participant_helper(room_id, room_manager)
    result = participant_helper.ExpelUsers(request.user_ids)

    return {
        "room_id": room_id,
        "user_ids": request.user_ids,
        "count": len(request.user_ids),
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.post("/hide-profile-pictures")
async def hide_profile_pictures(room_id: str, hidden: bool, room_manager = Depends(lambda: get_room_manager())):
    """Hide/show profile pictures"""
    participant_helper = get_participant_helper(room_id, room_manager)
    result = participant_helper.HideProfilePictures(hidden)

    return {
        "room_id": room_id,
        "hidden": hidden,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.get("/full-room-view-available/{user_id}")
async def is_full_room_view_available_for_user(room_id: str, user_id: int, room_manager = Depends(lambda: get_room_manager())):
    """Check if user supports hide/show full room view"""
    participant_helper = get_participant_helper(room_id, room_manager)
    result, is_available = participant_helper.IsFullRoomViewAvailableForUser(user_id)

    return {
        "room_id": room_id,
        "user_id": user_id,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS,
        "available": is_available
    }


@router.post("/hide-full-room-view")
async def hide_full_room_view(room_id: str, user_id: int, hide: bool, room_manager = Depends(lambda: get_room_manager())):
    """Hide/show full room view for a user"""
    participant_helper = get_participant_helper(room_id, room_manager)
    result = participant_helper.HideFullRoomView(hide, user_id)

    return {
        "room_id": room_id,
        "user_id": user_id,
        "hide": hide,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.post("/download-avatar")
async def download_user_avatar(room_id: str, avatar_url: str, local_file_path: str, room_manager = Depends(lambda: get_room_manager())):
    """Download user avatar"""
    participant_helper = get_participant_helper(room_id, room_manager)
    result = participant_helper.DownloadUserAvatar(avatar_url, local_file_path)

    return {
        "room_id": room_id,
        "avatar_url": avatar_url,
        "local_file_path": local_file_path,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS,
        "message": "Download started (check callback notifications)"
    }


@router.post("/allow-share-whiteboards")
async def allow_attendees_share_whiteboards(room_id: str, allow: bool, room_manager = Depends(lambda: get_room_manager())):
    """Allow/disallow attendees to share whiteboards"""
    participant_helper = get_participant_helper(room_id, room_manager)
    result = participant_helper.AllowAttendeesShareWhiteboards(allow)

    return {
        "room_id": room_id,
        "allow": allow,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.post("/suspend-activities")
async def suspend_participants_activities(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """Suspend all participants activities"""
    participant_helper = get_participant_helper(room_id, room_manager)
    result = participant_helper.SuspendParticipantsActivities()

    return {
        "room_id": room_id,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.post("/report-issue")
async def report_issue(room_id: str, request: ReportIssueRequest, room_manager = Depends(lambda: get_room_manager())):
    """Report participants' issues"""
    participant_helper = get_participant_helper(room_id, room_manager)
    result = participant_helper.ReportIssue(request.user_ids, request.issue_type, request.email)

    return {
        "room_id": room_id,
        "user_ids": request.user_ids,
        "issue_type": request.issue_type,
        "email": request.email,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.post("/set-myself-as-active-speaker")
async def set_myself_as_active_speaker(room_id: str, room_manager = Depends(lambda: get_room_manager())):
    """Set myself as active speaker"""
    participant_helper = get_participant_helper(room_id, room_manager)
    result = participant_helper.SetMySelfAsActiveSpeaker()

    return {
        "room_id": room_id,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }


@router.post("/set-child-as-active-speaker/{user_id}")
async def set_my_child_as_active_speaker(room_id: str, user_id: int, room_manager = Depends(lambda: get_room_manager())):
    """Set my child (multi-stream participant) as active speaker"""
    participant_helper = get_participant_helper(room_id, room_manager)
    result = participant_helper.SetMyChildAsActiveSpeaker(user_id)

    return {
        "room_id": room_id,
        "user_id": user_id,
        "result": int(result),
        "success": result == zrc_sdk.ZRCSDKERR_SUCCESS
    }
