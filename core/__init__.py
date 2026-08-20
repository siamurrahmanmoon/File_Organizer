"""
core - Advanced File Organizer Pro Core Engines Package
"""

from core.engine import AnimeFileOrganizer
from core.parser import SmartMediaParser
from core.template_engine import TemplateEngine
from core.duplicate_detector import DuplicateDetector
from core.filter_engine import FilterEngine
from core.quality_control import QualityController
from core.subtitle_manager import SubtitleManager
from core.rollback_manager import RollbackManager
from core.analytics import AnalyticsTracker
from core.security import SecurityValidator
from core.notifier import Notifier
from core.profiles_manager import ProfilesManager
from core.watch_folder import WatchFolderService

__all__ = [
    "AnimeFileOrganizer",
    "SmartMediaParser",
    "TemplateEngine",
    "DuplicateDetector",
    "FilterEngine",
    "QualityController",
    "SubtitleManager",
    "RollbackManager",
    "AnalyticsTracker",
    "SecurityValidator",
    "Notifier",
    "ProfilesManager",
    "WatchFolderService",
]
