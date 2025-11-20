# Controllers package
from .rooms import router as rooms_router
from .meetings import router as meetings_router
from .meeting_controls import router as meeting_controls_router
from .meeting_list import router as meeting_list_router
from .meeting_share import router as meeting_share_router
from .meeting_video import router as meeting_video_router
from .meeting_view_layout import router as meeting_view_layout_router
from .ndi import router as ndi_router
from .participant import router as participant_router
from .phone_call import router as phone_call_router
from .pre_meeting import router as pre_meeting_router
from .pro_av import router as pro_av_router
from .recording import router as recording_router

__all__ = ['rooms_router', 'meetings_router', 'meeting_controls_router', 'meeting_list_router', 'meeting_share_router', 'meeting_video_router', 'meeting_view_layout_router', 'ndi_router', 'participant_router', 'phone_call_router', 'pre_meeting_router', 'pro_av_router', 'recording_router']
