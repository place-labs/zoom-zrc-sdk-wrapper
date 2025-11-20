# Controllers package
from .rooms import router as rooms_router
from .meetings import router as meetings_router
from .meeting_controls import router as meeting_controls_router
from .meeting_list import router as meeting_list_router
from .meeting_share import router as meeting_share_router
from .meeting_video import router as meeting_video_router

__all__ = ['rooms_router', 'meetings_router', 'meeting_controls_router', 'meeting_list_router', 'meeting_share_router', 'meeting_video_router']
