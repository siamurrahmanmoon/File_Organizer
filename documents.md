# 📑 Technical Documentation: Smart File Organizer Pro (v4.0 - Enterprise Edition)

This document provides a comprehensive overview of the modular architecture, pipeline logic, configuration system, custom naming templates, and build instructions for **Smart File Organizer Pro**.

---

## 1. System Architecture Overview

The system is designed with an enterprise-grade, fully decoupled, modular architecture:

```text
r:\filenameedit\
├── config.py                  # Master configuration & feature toggles (all features can be turned ON/OFF)
├── organizer.py               # Main application entry point (GUI + CLI dispatcher)
├── cli.py                     # Standalone CLI entry point with arguments & watch mode
│
├── core/
│   ├── __init__.py
│   ├── engine.py              # Main AnimeFileOrganizer engine orchestrating pipeline
│   ├── parser.py              # Advanced AI/Regex pattern recognition (groups, anime titles, seasons/episodes, OVAs/movies, multi-episodes)
│   ├── template_engine.py     # Custom naming template formatter with token evaluator
│   ├── duplicate_detector.py  # MD5/SHA256 hash, size, similarity, duplicate quarantine & resolution ranking
│   ├── filter_engine.py       # Multi-criteria filtering (size, resolution, codec, language, release group, year range, custom regex)
│   ├── quality_control.py     # File integrity checks, corruption detection, incomplete stream detection
│   ├── subtitle_manager.py    # Subtitle sidecar (.srt, .ass, .vtt) pairing, language tagging, audio track analysis
│   ├── rollback_manager.py    # Operation journaling, checkpointing, crash recovery, and full Undo/Rollback
│   ├── watch_folder.py        # Background folder watcher / scheduler for auto-organizing
│   ├── analytics.py           # Processing stats, session tracking, report export (CSV, JSON, HTML)
│   ├── security.py            # Path traversal sanitization, Windows reserved names protection, long path handling
│   ├── notifier.py            # Desktop notifications + Discord/Telegram webhook triggers
│   └── profiles_manager.py    # Save/load/export/import JSON profiles & preset templates
│
├── ui/
│   ├── __init__.py
│   ├── main_window.py         # Advanced Tkinter GUI with modern styling, card frames, responsive layout
│   ├── theme.py               # Modern Dark & Light color scheme and ttk styles
│   ├── widgets.py             # Custom styled widgets (PathSelector, StatCard, etc.)
│   └── tabs/
│       ├── organize_tab.py    # Main folder selection, filter controls, live progress, colored activity log
│       ├── preview_tab.py     # Side-by-side Before/After diff table, selective check/uncheck, batch rename preview
│       ├── template_tab.py    # Interactive Template Builder with live tag insertion & sample preview
│       ├── filter_tab.py      # Granular filters (codecs, resolutions, file size range, regex builder)
│       ├── duplicate_tab.py   # Duplicate scanner, resolution ranking, quarantine viewer
│       ├── rollback_tab.py    # Rollback / Undo manager, operation history, checkpoint restore
│       ├── analytics_tab.py   # History dashboard, stats breakdown, report exporter (CSV, JSON, HTML)
│       ├── watch_tab.py       # Watch folder automation, interval scheduler & webhook config
│       └── help_tab.py        # Built-in guide, template syntax cheatsheet, regex library, FAQ
│
├── utils/
│   ├── ffmpeg_installer.py    # Auto-downloader & verifier for FFmpeg/ffprobe
│   ├── metadata_extractor.py  # FFprobe stream inspection (video/audio/subtitles)
│   ├── metadata_parser.py     # Metadata formatting & tag builder
│   ├── file_utils.py          # Safe cross-platform file mover, copy, remove, Windows long path handler
│   └── logger_utils.py        # Structured logging system (file + memory + console)
│
├── presets/                   # JSON Preset Profiles (Default, Plex/Jellyfin, Anime Archival, Minimal Clean)
├── logs/                      # Log directory & SQLite operations journal
├── quarantine/                # Quarantine vault for duplicate or suspicious files
└── reports/                   # Exported CSV, JSON, and HTML dashboard reports
```

---

## 2. Master Feature Toggles (`config.py`)

Every feature can be enabled or disabled globally via boolean flags in `config.py`:

```python
ENABLE_METADATA_EXTRACTION = True     # 1. Video metadata extraction via FFprobe
ENABLE_AI_PATTERN_PARSER = True       # 2. Pattern recognition (groups, seasons, OVAs, etc.)
ENABLE_DUPLICATE_DETECTION = True     # 3. Duplicate detection (hashing, size, similarity)
ENABLE_ADVANCED_FILTERS = True        # 4. Multi-criteria filtering (size, res, codec, etc.)
ENABLE_CUSTOM_TEMPLATES = True        # 5. User-defined naming templates
ENABLE_ROLLBACK_JOURNAL = True        # 6. SQLite operation journal & 1-click Undo
ENABLE_QUALITY_CONTROL = True         # 7. File corruption & incomplete download checks
ENABLE_SUBTITLE_MANAGEMENT = True     # 8. Sidecar subtitle pairing (.srt, .ass)
ENABLE_AUTOMATION_WATCH = True        # 9. Watch folder & scheduled auto-organizer
ENABLE_NOTIFICATIONS = True           # 10. Desktop alerts & Discord/Telegram webhooks
ENABLE_ANALYTICS = True               # 11. Statistics tracking & CSV/JSON/HTML export
ENABLE_SECURITY_VALIDATION = True     # 12. Path traversal & reserved name protection
```

---

## 3. Custom Naming Template Tokens

Templates support conditional bracket tokens and formatting specifiers:

| Token | Description | Example Output |
| :--- | :--- | :--- |
| `{Title}` | Normalized, cleaned title | `Bleach Thousand-Year Blood War` |
| `{Year}` | 4-digit release year | `2023` |
| `{Season}` | Season number | `01`, `02` |
| `{Episode}` | Episode number | `01`, `1050` |
| `{EpisodeRange}` | Multi-episode range | `S01E01-E04` |
| `{Resolution}` | Video resolution | `1080p`, `4K`, `720p` |
| `{Codec}` | Video codec | `x265`, `x264`, `AV1` |
| `{AudioCodec}` | Primary audio codec | `AAC`, `FLAC`, `AC3` |
| `{AudioChannels}` | Audio channel configuration | `5.1`, `7.1`, `Stereo` |
| `{AudioLang}` | Audio languages | `Japanese`, `Hindi-English` |
| `{Group}` | Release group | `SubsPlease`, `Erai-raws` |
| `{Bitrate}` | Stream bitrate | `12Mbps`, `4500Kbps` |
| `{FPS}` | Video frame rate | `24fps`, `60fps` |
| `{Type}` | Media type | `Episode`, `Movie`, `OVA`, `Special` |

### Built-in Presets:
1. **Standard**: `{Title} ({Year}) [{Resolution}] - S{Season}E{Episode}`
2. **Scene Release**: `[{Group}] {Title} - {Episode} [{Resolution}] [{Codec}]`
3. **Plex / Jellyfin**: `{Title} ({Year})/Season {Season:02d}/{Title} - S{Season:02d}E{Episode:02d}`
4. **Anime Archival**: `[{Group}] {Title} ({Year}) [{Resolution}] [{Codec}] [{AudioCodec} {AudioChannels}] - S{Season}E{Episode}`
5. **Minimal Clean**: `{Title} ({Year}) - E{Episode}`

---

## 4. Command-Line Interface (CLI)

The CLI (`cli.py`) supports full automation, profile loading, dry-runs, continuous folder watching, and rollback:

```bash
# List available configuration presets
python cli.py --list-profiles

# Run dry-run scan on a folder using Plex preset
python cli.py -s "R:\Anime_Raw" -o "R:\Anime_Organized" -p plex_jellyfin --dry-run

# Execute organization with custom naming template
python cli.py -s "R:\Anime_Raw" -o "R:\Anime_Organized" -t "{Title} ({Year}) [{Resolution}] - S{Season}E{Episode}" --execute

# Start continuous automated watch folder service
python cli.py -s "R:\Downloads\Watch" -o "R:\Anime_Library" --watch

# View recent sessions for rollback
python cli.py --list-sessions

# 1-Click Rollback / Undo a previous session
python cli.py --rollback session_20260820_130624
```

---

## 5. Building the Standalone Windows Executable (.exe)

To compile the entire application into a standalone `.exe`:

```bash
# Activate virtual environment
.\venv\Scripts\activate

# Build executable with PyInstaller
pyinstaller --noconfirm --onefile --windowed --name "AnimeOrganizerPro" --icon=icon.ico organizer.py
```

The compiled standalone executable will be located in the **`dist/`** directory.