"""
config.py - Master Configuration & Feature Toggles for Smart File Organizer Pro

Every feature can be enabled/disabled via boolean flags and customized in detail.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Set, Dict, Any, Optional
import json
import os

# ==============================================================================
# 🎛️ MASTER FEATURE TOGGLES (ON / OFF)
# ==============================================================================
# Set any of these to True/False to enable or disable features globally.

ENABLE_METADATA_EXTRACTION: bool = True     # 1. Video metadata extraction via FFprobe
ENABLE_AI_PATTERN_PARSER: bool = True       # 2. Pattern recognition (groups, seasons, OVAs, etc.)
ENABLE_DUPLICATE_DETECTION: bool = True     # 3. Duplicate detection (hashing, size, similarity)
ENABLE_ADVANCED_FILTERS: bool = True        # 4. Multi-criteria filtering (size, res, codec, etc.)
ENABLE_CUSTOM_TEMPLATES: bool = True        # 5. User-defined naming templates
ENABLE_ROLLBACK_JOURNAL: bool = True        # 6. SQLite operation journal & 1-click Undo
ENABLE_QUALITY_CONTROL: bool = True         # 7. File corruption & incomplete download checks
ENABLE_SUBTITLE_MANAGEMENT: bool = True     # 8. Sidecar subtitle pairing (.srt, .ass)
ENABLE_AUTOMATION_WATCH: bool = True        # 9. Watch folder & scheduled auto-organizer
ENABLE_NOTIFICATIONS: bool = True           # 10. Desktop alerts & Discord/Telegram webhooks
ENABLE_ANALYTICS: bool = True               # 11. Statistics tracking & CSV/JSON/HTML export
ENABLE_SECURITY_VALIDATION: bool = True     # 12. Path traversal & reserved name protection


# ==============================================================================
# ⚙️ CONFIGURATION DATA MODEL
# ==============================================================================

@dataclass
class OrganizerConfig:
    """Complete runtime configuration object for the file organizer."""

    # Paths
    source_path: str = ""
    output_path: str = ""
    quarantine_path: str = "quarantine"
    reports_path: str = "reports"
    logs_path: str = "logs"
    journal_db_path: str = "logs/operations_journal.db"

    # Core Execution Options
    dry_run: bool = True
    process_subfolders: bool = True
    auto_folder_year: bool = True
    skip_existing_year: bool = True
    ask_user_input: bool = False
    safe_mode: bool = True                      # Overwrite protection with safe auto-increment
    move_files: bool = True                     # True = Move, False = Copy

    # Feature Switches (per-run overrides of global switches)
    enable_metadata: bool = ENABLE_METADATA_EXTRACTION
    enable_parser: bool = ENABLE_AI_PATTERN_PARSER
    enable_duplicates: bool = ENABLE_DUPLICATE_DETECTION
    enable_filters: bool = ENABLE_ADVANCED_FILTERS
    enable_templates: bool = ENABLE_CUSTOM_TEMPLATES
    enable_rollback: bool = ENABLE_ROLLBACK_JOURNAL
    enable_quality_control: bool = ENABLE_QUALITY_CONTROL
    enable_subtitles: bool = ENABLE_SUBTITLE_MANAGEMENT
    enable_watch_folder: bool = ENABLE_AUTOMATION_WATCH
    enable_notifications: bool = ENABLE_NOTIFICATIONS
    enable_analytics: bool = ENABLE_ANALYTICS

    # File Extensions
    video_extensions: Set[str] = field(default_factory=lambda: {
        ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm",
        ".m4v", ".mpeg", ".mpg", ".ts", ".m2ts", ".iso"
    })
    subtitle_extensions: Set[str] = field(default_factory=lambda: {
        ".srt", ".ass", ".ssa", ".vtt", ".sub", ".idx"
    })
    custom_extensions: str = ""

    # Naming Template Settings
    # Available tokens: {Title}, {Year}, {Season}, {Episode}, {Resolution}, {Codec},
    #                   {AudioCodec}, {AudioChannels}, {AudioLang}, {Group}, {Bitrate}, {FPS}, {Type}
    naming_template: str = "{Title} ({Year}) [{Languages}] [{Resolution}] - S{Season}E{Episode}"
    clean_title_replace_spaces: bool = True
    remove_bracketed_tags: bool = True

    # Metadata Inclusion Options
    include_resolution: bool = True
    include_video_codec: bool = False
    include_audio_codec: bool = False
    include_audio_channels: bool = False
    include_audio_language: bool = True
    include_bitrate: bool = False
    include_fps: bool = False

    # Duplicate Handling Options
    duplicate_action: str = "quarantine"        # Options: 'quarantine', 'skip', 'overwrite_if_better', 'tag'
    hash_algorithm: str = "fast"                # Options: 'fast' (chunks), 'sha256', 'md5'
    duplicate_similarity_threshold: float = 0.85

    # Advanced Filters
    min_file_size_mb: float = 0.0               # 0 = no minimum
    max_file_size_mb: float = 0.0               # 0 = no maximum
    resolution_whitelist: List[str] = field(default_factory=list) # e.g. ["1080p", "4K"]
    codec_whitelist: List[str] = field(default_factory=list)      # e.g. ["x265", "HEVC"]
    release_group_filter: str = ""             # Regex or comma-separated
    language_filter: List[str] = field(default_factory=list)      # e.g. ["Japanese", "English", "Hindi"]
    min_year: int = 1900
    max_year: int = 2099
    custom_regex_filter: str = ""

    # Quality Control
    skip_corrupt_files: bool = True
    skip_incomplete_downloads: bool = True      # .part, .crdownload, !qB

    # Watch Folder & Scheduler
    watch_interval_seconds: int = 60
    watch_file_stability_wait_seconds: int = 10

    # Webhooks & Notifications
    discord_webhook_url: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    desktop_notifications: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Converts configuration to serializable dictionary."""
        d = {}
        for k, v in self.__dict__.items():
            if isinstance(v, set):
                d[k] = list(v)
            else:
                d[k] = v
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrganizerConfig":
        """Builds configuration from dictionary."""
        cfg = cls()
        for k, v in data.items():
            if hasattr(cfg, k):
                if k in ("video_extensions", "subtitle_extensions") and isinstance(v, list):
                    setattr(cfg, k, set(v))
                else:
                    setattr(cfg, k, v)
        return cfg

    def save_profile(self, file_path: str):
        """Saves current config as a JSON profile."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=4)

    @classmethod
    def load_profile(cls, file_path: str) -> "OrganizerConfig":
        """Loads configuration from a JSON profile."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)


# ==============================================================================
# 📑 BUILT-IN TEMPLATE PRESETS
# ==============================================================================
DEFAULT_TEMPLATES = {
    "Standard": "{Title} ({Year}) [{Languages}] [{Resolution}] - S{Season}E{Episode}",
    "Scene / Anime Release": "[{Group}] {Title} - {Episode} [{Resolution}] [{Codec}]",
    "Plex / Jellyfin": "{Title} ({Year})/Season {Season:02d}/{Title} - S{Season:02d}E{Episode:02d}",
    "Archival Full Info": "{Title} ({Year}) [{Resolution}] [{Codec}] [{AudioCodec} {AudioChannels}] - S{Season}E{Episode}",
    "Compact Title Only": "{Title} ({Year}) - E{Episode}",
    "Movie / Feature": "{Title} ({Year}) [{Resolution}] [{Codec}]"
}


# ==============================================================================
# 📂 DEFAULT SYSTEM DIRECTORIES
# ==============================================================================
BASE_DIR = Path(__file__).parent
BIN_DIR = BASE_DIR / "bin"
LOGS_DIR = BASE_DIR / "logs"
PRESETS_DIR = BASE_DIR / "presets"
REPORTS_DIR = BASE_DIR / "reports"
QUARANTINE_DIR = BASE_DIR / "quarantine"

for directory in (LOGS_DIR, PRESETS_DIR, REPORTS_DIR, QUARANTINE_DIR):
    directory.mkdir(parents=True, exist_ok=True)


def get_default_config() -> OrganizerConfig:
    """Returns a fresh default OrganizerConfig instance."""
    return OrganizerConfig()
