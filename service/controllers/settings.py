"""
Settings Controller
Handles Zoom Room settings including audio/video devices, room configuration, and diagnostics
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import zrc_sdk

router = APIRouter(prefix="/api/rooms/{room_id}/settings", tags=["settings"])

# Dependency injection placeholder - will be set by app.py
get_room_manager = None


# ===== Request Models =====

class SetDeviceRequest(BaseModel):
    device_id: str
    device_name: str = ""


class SetVolumeRequest(BaseModel):
    volume: float


class TestMicrophoneRequest(BaseModel):
    on: bool


class ConfirmMicrophoneNumberRequest(BaseModel):
    number: int


class EnableBoolRequest(BaseModel):
    enable: bool


class SelectNoiseSuppressionModeRequest(BaseModel):
    mode: str  # None, Auto, High, Off


class AudioCheckupRequest(BaseModel):
    command: str  # Start, Cancel


class SelectMultipleCameraRequest(BaseModel):
    device_id: str
    is_selected: bool
    companion_zr_id: str = ""


class SelectIntelligentDirectorCameraRequest(BaseModel):
    device_id: str
    is_selected: bool


class CalibrateIntelligentDirectorRequest(BaseModel):
    action_type: str  # CalibrationAction enum value name
    device_id: str = ""
    boundary_adjust_field: Optional[str] = None
    boundary_adjust_value: int = 0


class SetCameraCOMRequest(BaseModel):
    device_id: str
    com_id: int
    companion_zr_id: str = ""


class SetCameraDisplayNameRequest(BaseModel):
    device_id: str
    display_name: str
    companion_zr_id: str = ""


class SelectRoomProfileRequest(BaseModel):
    profile_id: str
    profile_name: str


class IdentifyConfidenceMonitorRequest(BaseModel):
    position: int


class IdentifyScreensRequest(BaseModel):
    current_screen: int
    position: int


class TurnCECScreensRequest(BaseModel):
    on: bool


class ChangeWindowsPasswordRequest(BaseModel):
    old_password: str
    new_password: str


class ListVirtualAudioDevicesRequest(BaseModel):
    virtual_device_id: str
    device_type: str  # VirtualAudioDeviceType enum


class SelectVirtualAudioDeviceRequest(BaseModel):
    virtual_device_id: str
    device_type: str
    network_device_id: str
    channel_device_id: str = ""
    channel_name: str = ""


class UnselectVirtualAudioDeviceRequest(BaseModel):
    virtual_device_id: str
    device_type: str
    network_device_id: str
    channel_device_id: str = ""
    channel_name: str = ""


class IdentifyVirtualAudioDeviceRequest(BaseModel):
    virtual_device_id: str
    device_type: str
    network_device_id: str


class UseDanteControllerRequest(BaseModel):
    virtual_device_id: str
    device_type: str
    is_used: bool


class BindAudioChannelRequest(BaseModel):
    camera_device_id: str
    rx_channel_id: int


class UnbindCameraRequest(BaseModel):
    camera_device_id: str


class UnbindChannelRequest(BaseModel):
    rx_channel_id: int


class RenameCompanionZRRequest(BaseModel):
    czr_id: str
    display_name: str


# ===== Helper Functions =====

def get_setting_service(room_id: str, room_manager):
    """Get setting service for a room"""
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail=f"Room {room_id} not found")

    return room_service.GetSettingService()


def device_to_dict(device):
    """Convert Device struct to dictionary"""
    return {
        "id": device.id,
        "name": device.name,
        "is_selected": device.isSelected,
        "device_type": device.deviceType
    }


def advanced_noise_suppression_mode_to_string(mode: int) -> str:
    """Convert AdvancedNoiseSuppressionMode enum to string"""
    mode_map = {
        zrc_sdk.AdvancedNoiseSuppressionModeNone: "None",
        zrc_sdk.AdvancedNoiseSuppressionModeAuto: "Auto",
        zrc_sdk.AdvancedNoiseSuppressionModeHigh: "High",
        zrc_sdk.AdvancedNoiseSuppressionModeOff: "Off"
    }
    return mode_map.get(mode, f"Unknown({mode})")


def string_to_advanced_noise_suppression_mode(mode_str: str) -> int:
    """Convert string to AdvancedNoiseSuppressionMode enum"""
    mode_map = {
        "None": zrc_sdk.AdvancedNoiseSuppressionModeNone,
        "Auto": zrc_sdk.AdvancedNoiseSuppressionModeAuto,
        "High": zrc_sdk.AdvancedNoiseSuppressionModeHigh,
        "Off": zrc_sdk.AdvancedNoiseSuppressionModeOff
    }
    if mode_str not in mode_map:
        raise HTTPException(status_code=400, detail=f"Invalid mode: {mode_str}")
    return mode_map[mode_str]


def string_to_audio_checkup_command(command_str: str) -> int:
    """Convert string to AudioCheckupCommand enum"""
    command_map = {
        "Start": zrc_sdk.AudioCheckupCommandStart,
        "Cancel": zrc_sdk.AudioCheckupCommandCancel
    }
    if command_str not in command_map:
        raise HTTPException(status_code=400, detail=f"Invalid command: {command_str}")
    return command_map[command_str]


# ===== Device Management Endpoints =====

@router.get("/devices/microphones")
async def get_microphone_list(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Get list of available microphones"""
    setting_service = get_setting_service(room_id, room_manager)
    result, microphones = setting_service.GetMicrophoneList()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to get microphone list: {result}")

    return {
        "microphones": [device_to_dict(mic) for mic in microphones]
    }


@router.get("/devices/speakers")
async def get_speaker_list(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Get list of available speakers"""
    setting_service = get_setting_service(room_id, room_manager)
    result, speakers = setting_service.GetSpeakerList()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to get speaker list: {result}")

    return {
        "speakers": [device_to_dict(spk) for spk in speakers]
    }


@router.get("/devices/cameras")
async def get_camera_list(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Get list of available cameras"""
    setting_service = get_setting_service(room_id, room_manager)
    result, cameras = setting_service.GetCameraList()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to get camera list: {result}")

    return {
        "cameras": [device_to_dict(cam) for cam in cameras]
    }


@router.get("/devices/companion-zr")
async def get_companion_zr_list(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Get list of Companion ZR devices"""
    setting_service = get_setting_service(room_id, room_manager)
    result, czrs = setting_service.GetCompanionZRList()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to get Companion ZR list: {result}")

    return {
        "companion_zrs": czrs
    }


@router.get("/devices/current/microphone")
async def get_current_microphone(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Get current microphone"""
    setting_service = get_setting_service(room_id, room_manager)
    result, microphone = setting_service.GetCurrentMicrophone()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to get current microphone: {result}")

    return device_to_dict(microphone)


@router.get("/devices/current/speaker")
async def get_current_speaker(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Get current speaker"""
    setting_service = get_setting_service(room_id, room_manager)
    result, speaker = setting_service.GetCurrentSpeaker()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to get current speaker: {result}")

    return device_to_dict(speaker)


@router.get("/devices/current/camera")
async def get_current_camera(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Get current camera"""
    setting_service = get_setting_service(room_id, room_manager)
    result, camera = setting_service.GetCurrentCamera()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to get current camera: {result}")

    return device_to_dict(camera)


@router.post("/devices/current/microphone")
async def set_current_microphone(
    room_id: str,
    request: SetDeviceRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Set current microphone"""
    setting_service = get_setting_service(room_id, room_manager)

    device = zrc_sdk.Device()
    device.id = request.device_id
    device.name = request.device_name

    result = setting_service.SetCurrentMicrophone(device)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to set current microphone: {result}")

    return {"message": f"Microphone set to {request.device_id}"}


@router.post("/devices/current/speaker")
async def set_current_speaker(
    room_id: str,
    request: SetDeviceRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Set current speaker"""
    setting_service = get_setting_service(room_id, room_manager)

    device = zrc_sdk.Device()
    device.id = request.device_id
    device.name = request.device_name

    result = setting_service.SetCurrentSpeaker(device)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to set current speaker: {result}")

    return {"message": f"Speaker set to {request.device_id}"}


@router.post("/devices/current/camera")
async def set_current_camera(
    room_id: str,
    request: SetDeviceRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Set current camera"""
    setting_service = get_setting_service(room_id, room_manager)

    device = zrc_sdk.Device()
    device.id = request.device_id
    device.name = request.device_name

    result = setting_service.SetCurrentCamera(device)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to set current camera: {result}")

    return {"message": f"Camera set to {request.device_id}"}


# ===== Volume Control Endpoints =====

@router.get("/volume/microphone")
async def get_microphone_volume(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Get microphone volume"""
    setting_service = get_setting_service(room_id, room_manager)
    result, volume = setting_service.GetMicrophoneVolume()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to get microphone volume: {result}")

    return {"volume": volume}


@router.get("/volume/speaker")
async def get_speaker_volume(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Get speaker volume"""
    setting_service = get_setting_service(room_id, room_manager)
    result, volume = setting_service.GetSpeakerVolume()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to get speaker volume: {result}")

    return {"volume": volume}


@router.post("/volume/microphone")
async def set_microphone_volume(
    room_id: str,
    request: SetVolumeRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Set microphone volume"""
    setting_service = get_setting_service(room_id, room_manager)
    result = setting_service.SetMicrophoneVolume(request.volume)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to set microphone volume: {result}")

    return {"message": f"Microphone volume set to {request.volume}"}


@router.post("/volume/speaker")
async def set_speaker_volume(
    room_id: str,
    request: SetVolumeRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Set speaker volume"""
    setting_service = get_setting_service(room_id, room_manager)
    result = setting_service.SetSpeakerVolume(request.volume)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to set speaker volume: {result}")

    return {"message": f"Speaker volume set to {request.volume}"}


@router.post("/volume/speaker-temp")
async def set_speaker_temp_volume(
    room_id: str,
    request: SetVolumeRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Set temporary speaker volume for current meeting"""
    setting_service = get_setting_service(room_id, room_manager)
    result = setting_service.SetSpeakerTempVolumeInMeeting(request.volume)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to set temporary speaker volume: {result}")

    return {"message": f"Temporary speaker volume set to {request.volume}"}


# ===== Microphone Settings Endpoints =====

@router.post("/microphone/test")
async def test_microphone(
    room_id: str,
    request: TestMicrophoneRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Test microphone recording"""
    setting_service = get_setting_service(room_id, room_manager)
    result = setting_service.TestMicrophone(request.on)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to test microphone: {result}")

    return {"message": f"Microphone test {'started' if request.on else 'stopped'}"}


@router.post("/microphone/test-volume/start")
async def start_testing_microphone_volume(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Start testing microphone volume"""
    setting_service = get_setting_service(room_id, room_manager)
    result = setting_service.StartTestingMicrophoneVolume()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to start testing microphone volume: {result}")

    return {"message": "Started testing microphone volume"}


@router.post("/microphone/test-volume/stop")
async def stop_testing_microphone_volume(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Stop testing microphone volume"""
    setting_service = get_setting_service(room_id, room_manager)
    result = setting_service.StopTestingMicrophoneVolume()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to stop testing microphone volume: {result}")

    return {"message": "Stopped testing microphone volume"}


@router.post("/microphone/confirm-number")
async def confirm_microphone_number(
    room_id: str,
    request: ConfirmMicrophoneNumberRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Confirm number of combined microphones"""
    setting_service = get_setting_service(room_id, room_manager)
    result = setting_service.ConfirmNumberOfCombinedMicrophone(request.number)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to confirm microphone number: {result}")

    return {"message": f"Confirmed {request.number} combined microphones"}


@router.get("/microphone/acoustic-echo-cancellation/support")
async def check_aec_support(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Check if acoustic echo cancellation is supported"""
    setting_service = get_setting_service(room_id, room_manager)
    result, support = setting_service.IsSupportAcousticEchoCancellation()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to check AEC support: {result}")

    return {"supported": support}


@router.post("/microphone/acoustic-echo-cancellation")
async def enable_acoustic_echo_cancellation(
    room_id: str,
    request: EnableBoolRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Enable or disable acoustic echo cancellation"""
    setting_service = get_setting_service(room_id, room_manager)
    result = setting_service.EnableAcousticEchoCancellation(request.enable)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to set AEC: {result}")

    return {"message": f"Acoustic echo cancellation {'enabled' if request.enable else 'disabled'}"}


@router.get("/microphone/advanced-noise-suppression/support")
async def check_noise_suppression_support(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Check if advanced noise suppression is supported"""
    setting_service = get_setting_service(room_id, room_manager)
    result, support = setting_service.IsSupportAdvancedNoiseSuppression()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to check noise suppression support: {result}")

    return {"supported": support}


@router.get("/microphone/advanced-noise-suppression/mode")
async def get_noise_suppression_mode(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Get current advanced noise suppression mode"""
    setting_service = get_setting_service(room_id, room_manager)
    result, mode = setting_service.GetCurrentAdvancedNoiseSuppressionMode()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to get noise suppression mode: {result}")

    return {
        "mode": advanced_noise_suppression_mode_to_string(mode),
        "mode_value": mode
    }


@router.post("/microphone/advanced-noise-suppression/mode")
async def select_noise_suppression_mode(
    room_id: str,
    request: SelectNoiseSuppressionModeRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Select advanced noise suppression mode"""
    setting_service = get_setting_service(room_id, room_manager)
    mode = string_to_advanced_noise_suppression_mode(request.mode)
    result = setting_service.SelectAdvancedNoiseSuppressionMode(mode)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to select noise suppression mode: {result}")

    return {"message": f"Noise suppression mode set to {request.mode}"}


@router.post("/microphone/hardware-troubleshooting")
async def enable_mic_hardware_troubleshooting(
    room_id: str,
    request: EnableBoolRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Enable or disable microphone hardware troubleshooting"""
    setting_service = get_setting_service(room_id, room_manager)
    result = setting_service.EnableMicrophoneHardwareTroubleshooting(request.enable)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to set microphone troubleshooting: {result}")

    return {"message": f"Microphone hardware troubleshooting {'enabled' if request.enable else 'disabled'}"}


@router.post("/audio-checkup")
async def audio_checkup(
    room_id: str,
    request: AudioCheckupRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Start or cancel audio checkup"""
    setting_service = get_setting_service(room_id, room_manager)
    command = string_to_audio_checkup_command(request.command)
    result = setting_service.AudioCheckup(command)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to run audio checkup: {result}")

    return {"message": f"Audio checkup {request.command.lower()}ed"}


@router.get("/audio-framing/available")
async def check_audio_framing_available(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Check if audio framing is available"""
    setting_service = get_setting_service(room_id, room_manager)
    result, available = setting_service.IsAudioFramingAvailable()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to check audio framing availability: {result}")

    return {"available": available}


@router.post("/audio-framing")
async def enable_audio_framing(
    room_id: str,
    request: EnableBoolRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Enable or disable audio framing"""
    setting_service = get_setting_service(room_id, room_manager)
    result = setting_service.EnableAudioFraming(request.enable)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to set audio framing: {result}")

    return {"message": f"Audio framing {'enabled' if request.enable else 'disabled'}"}


# ===== Speaker Settings Endpoints =====

@router.post("/speaker/test/start")
async def start_testing_speaker(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Start testing speaker"""
    setting_service = get_setting_service(room_id, room_manager)
    result = setting_service.StartTestingSpeaker()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to start testing speaker: {result}")

    return {"message": "Started testing speaker"}


@router.post("/speaker/test/stop")
async def stop_testing_speaker(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Stop testing speaker"""
    setting_service = get_setting_service(room_id, room_manager)
    result = setting_service.StopTestingSpeaker()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to stop testing speaker: {result}")

    return {"message": "Stopped testing speaker"}


@router.get("/speaker/spatial-audio/available")
async def check_spatial_audio_available(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Check if spatial audio is available"""
    setting_service = get_setting_service(room_id, room_manager)
    result, available = setting_service.IsSpatialAudioAvailable()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to check spatial audio availability: {result}")

    return {"available": available}


@router.post("/speaker/spatial-audio")
async def enable_spatial_audio(
    room_id: str,
    request: EnableBoolRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Enable or disable spatial audio"""
    setting_service = get_setting_service(room_id, room_manager)
    result = setting_service.EnableSpatialAudio(request.enable)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to set spatial audio: {result}")

    return {"message": f"Spatial audio {'enabled' if request.enable else 'disabled'}"}


# ===== Camera Settings Endpoints =====

@router.post("/camera/multiple")
async def select_multiple_camera(
    room_id: str,
    request: SelectMultipleCameraRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Select or unselect a camera for multiple camera mode"""
    setting_service = get_setting_service(room_id, room_manager)
    result = setting_service.SelectMultipleCamera(request.device_id, request.is_selected, request.companion_zr_id)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to select multiple camera: {result}")

    return {
        "message": f"Camera {request.device_id} {'selected' if request.is_selected else 'unselected'} for multiple camera mode"
    }


@router.post("/camera/intelligent-director")
async def select_intelligent_director_camera(
    room_id: str,
    request: SelectIntelligentDirectorCameraRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Select or unselect a camera for intelligent director mode"""
    setting_service = get_setting_service(room_id, room_manager)
    result = setting_service.SelectIntelligentDirectorCamera(request.device_id, request.is_selected)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to select intelligent director camera: {result}")

    return {
        "message": f"Camera {request.device_id} {'selected' if request.is_selected else 'unselected'} for intelligent director mode"
    }


@router.post("/camera/com-id")
async def set_camera_com_id(
    room_id: str,
    request: SetCameraCOMRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Set camera COM ID"""
    setting_service = get_setting_service(room_id, room_manager)
    result = setting_service.SetCameraCOMId(request.device_id, request.com_id, request.companion_zr_id)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to set camera COM ID: {result}")

    return {"message": f"Camera {request.device_id} COM ID set to {request.com_id}"}


@router.post("/camera/display-name")
async def set_camera_display_name(
    room_id: str,
    request: SetCameraDisplayNameRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Set camera display name"""
    setting_service = get_setting_service(room_id, room_manager)
    result = setting_service.SetCameraDisplayName(request.device_id, request.display_name, request.companion_zr_id)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to set camera display name: {result}")

    return {"message": f"Camera {request.device_id} display name set to {request.display_name}"}


@router.post("/camera/multi-camera-only-mode")
async def enable_multi_camera_only_mode(
    room_id: str,
    request: EnableBoolRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Enable or disable multi-camera only mode"""
    setting_service = get_setting_service(room_id, room_manager)
    result = setting_service.EnableMultiCameraOnlyMode(request.enable)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to set multi-camera only mode: {result}")

    return {"message": f"Multi-camera only mode {'enabled' if request.enable else 'disabled'}"}


# ===== Room Settings Endpoints =====

@router.post("/room-profile")
async def select_room_profile(
    room_id: str,
    request: SelectRoomProfileRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Select room profile"""
    setting_service = get_setting_service(room_id, room_manager)
    result = setting_service.SelectRoomProfile(request.profile_id, request.profile_name)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to select room profile: {result}")

    return {"message": f"Room profile {request.profile_name} selected"}


@router.post("/statistical-info")
async def enable_statistical_info(
    room_id: str,
    request: EnableBoolRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Enable or disable statistical info"""
    setting_service = get_setting_service(room_id, room_manager)
    result = setting_service.EnableStatisticalInfo(request.enable)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to set statistical info: {result}")

    return {"message": f"Statistical info {'enabled' if request.enable else 'disabled'}"}


@router.post("/screens/adjust/start")
async def start_adjust_screens(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Start adjusting Zoom Room screens"""
    setting_service = get_setting_service(room_id, room_manager)
    result = setting_service.StartAdjustZRScreens()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to start adjusting screens: {result}")

    return {"message": "Started adjusting screens"}


@router.post("/screens/adjust/start-over")
async def start_over_adjust_screens(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Start over adjusting Zoom Room screens"""
    setting_service = get_setting_service(room_id, room_manager)
    result = setting_service.StartOverAdjustZRScreens()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to start over adjusting screens: {result}")

    return {"message": "Started over adjusting screens"}


@router.post("/screens/confidence-monitor/identify")
async def identify_confidence_monitor(
    room_id: str,
    request: IdentifyConfidenceMonitorRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Identify confidence monitor position"""
    setting_service = get_setting_service(room_id, room_manager)
    result = setting_service.IdentifyZRConfidenceMonitor(request.position)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to identify confidence monitor: {result}")

    return {"message": f"Confidence monitor identified at position {request.position}"}


@router.post("/screens/identify")
async def identify_screens(
    room_id: str,
    request: IdentifyScreensRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Identify screen sequence"""
    setting_service = get_setting_service(room_id, room_manager)
    result = setting_service.IdentifyZRScreens(request.current_screen, request.position)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to identify screens: {result}")

    return {"message": f"Screen {request.current_screen} identified at position {request.position}"}


@router.post("/screens/adjust/confirm")
async def confirm_adjust_screens(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Confirm screen adjustment"""
    setting_service = get_setting_service(room_id, room_manager)
    result = setting_service.ConfirmAdjustZRScreens()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to confirm screen adjustment: {result}")

    return {"message": "Screen adjustment confirmed"}


@router.post("/screens/adjust/cancel")
async def cancel_adjust_screens(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Cancel screen adjustment"""
    setting_service = get_setting_service(room_id, room_manager)
    result = setting_service.CancelAdjustZRScreens()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to cancel screen adjustment: {result}")

    return {"message": "Screen adjustment cancelled"}


@router.post("/screens/cec")
async def turn_cec_screens(
    room_id: str,
    request: TurnCECScreensRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Turn CEC screens on or off"""
    setting_service = get_setting_service(room_id, room_manager)
    result = setting_service.TurnCECScreensOn(request.on)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to turn CEC screens: {result}")

    return {"message": f"CEC screens turned {'on' if request.on else 'off'}"}


@router.post("/diagnostics/refresh")
async def refresh_diagnostic_info(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Refresh diagnostic information"""
    setting_service = get_setting_service(room_id, room_manager)
    result = setting_service.RefreshDiagnosticInfo()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to refresh diagnostic info: {result}")

    return {"message": "Diagnostic info refreshed"}


# ===== System Settings Endpoints =====

@router.get("/system/windows-iot-account")
async def get_windows_iot_account(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Get Windows IoT account name"""
    setting_service = get_setting_service(room_id, room_manager)
    result, account_name = setting_service.GetWindowsIoTAccountName()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to get Windows IoT account: {result}")

    return {"account_name": account_name}


@router.post("/system/windows-password")
async def change_windows_password(
    room_id: str,
    request: ChangeWindowsPasswordRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Change Windows password"""
    setting_service = get_setting_service(room_id, room_manager)
    result = setting_service.ChangeWindowsPassword(request.old_password, request.new_password)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to change Windows password: {result}")

    return {"message": "Windows password changed successfully"}


@router.get("/network/adapter-info")
async def get_network_adapter_info(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Get network adapter information"""
    setting_service = get_setting_service(room_id, room_manager)
    result, adapter_infos = setting_service.GetNetWorkAdapterInfo()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to get network adapter info: {result}")

    return {"network_adapters": adapter_infos}


@router.post("/companion-zr/rename")
async def rename_companion_zr(
    room_id: str,
    request: RenameCompanionZRRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Rename Companion ZR device"""
    setting_service = get_setting_service(room_id, room_manager)
    result = setting_service.RenameCompanionZR(request.czr_id, request.display_name)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to rename Companion ZR: {result}")

    return {"message": f"Companion ZR renamed to {request.display_name}"}


# ===== Virtual Audio Device Endpoints =====

@router.post("/virtual-audio/list")
async def list_virtual_audio_devices(
    room_id: str,
    request: ListVirtualAudioDevicesRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """List virtual audio devices"""
    setting_service = get_setting_service(room_id, room_manager)

    # Convert string device type to enum value
    device_type_map = {
        "Microphone": zrc_sdk.VirtualAudioDeviceTypeMicrophone,
        "Speaker": zrc_sdk.VirtualAudioDeviceTypeSpeaker
    }

    if request.device_type not in device_type_map:
        raise HTTPException(status_code=400, detail=f"Invalid device type: {request.device_type}")

    device_type = device_type_map[request.device_type]
    result = setting_service.ListVirtualAudioDevices(request.virtual_device_id, device_type)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to list virtual audio devices: {result}")

    return {"message": "Virtual audio devices listed"}


@router.get("/virtual-audio/network-devices/{virtual_device_id}")
async def get_network_audio_device_list(
    room_id: str,
    virtual_device_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Get network audio device list for a virtual device"""
    setting_service = get_setting_service(room_id, room_manager)
    result, devices = setting_service.GetNetworkAudioDeviceList(virtual_device_id)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to get network audio device list: {result}")

    return {"devices": devices}


@router.post("/audio-channel/bind")
async def bind_camera_to_audio_channel(
    room_id: str,
    request: BindAudioChannelRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Bind camera to audio channel"""
    setting_service = get_setting_service(room_id, room_manager)
    result = setting_service.BindCameraToAudioChannel(request.camera_device_id, request.rx_channel_id)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to bind camera to audio channel: {result}")

    return {"message": f"Camera {request.camera_device_id} bound to channel {request.rx_channel_id}"}


@router.post("/audio-channel/unbind-camera")
async def unbind_camera_from_audio_channel(
    room_id: str,
    request: UnbindCameraRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Unbind camera from audio channel"""
    setting_service = get_setting_service(room_id, room_manager)
    result = setting_service.UnbindCameraFromAudioChannel(request.camera_device_id)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to unbind camera: {result}")

    return {"message": f"Camera {request.camera_device_id} unbound"}


@router.post("/audio-channel/unbind-channel")
async def unbind_audio_channel_from_camera(
    room_id: str,
    request: UnbindChannelRequest,
    room_manager = Depends(lambda: get_room_manager())
):
    """Unbind audio channel from camera"""
    setting_service = get_setting_service(room_id, room_manager)
    result = setting_service.UnbindAudioChannelFromCamera(request.rx_channel_id)

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to unbind channel: {result}")

    return {"message": f"Channel {request.rx_channel_id} unbound"}


@router.post("/audio-channel/unbind-all")
async def unbind_all_audio_channel_connections(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """Unbind all audio channel and camera connections"""
    setting_service = get_setting_service(room_id, room_manager)
    result = setting_service.UnbindAllAudioChannelAndCameraConnections()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to unbind all connections: {result}")

    return {"message": "All audio channel and camera connections unbound"}


@router.post("/audio-channel/list-bind-info")
async def list_audio_channel_bind_info(
    room_id: str,
    room_manager = Depends(lambda: get_room_manager())
):
    """List audio channel and camera binding information"""
    setting_service = get_setting_service(room_id, room_manager)
    result = setting_service.ListAudioChannelAndCameraBindInfo()

    if result != zrc_sdk.ZRCSDKERR_SUCCESS:
        raise HTTPException(status_code=500, detail=f"Failed to list binding info: {result}")

    return {"message": "Binding info requested"}
