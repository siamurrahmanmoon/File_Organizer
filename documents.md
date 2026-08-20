# 📑 Technical Documentation: Smart File Organizer Pro (v4.1 - Enterprise Edition)

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

### New Configuration Options (v4.1):

```python
# Output Structure Options
flatten_output_structure: bool = True   # All files directly in output folder (no subfolders)
archive_source_files: bool = True       # Backup files to archive folder after processing
archive_path: str = ""                  # Custom archive path (default: _Archive_Source)

# Cache System
user_year_cache: Dict[Tuple[str, str], str]  # Cache user year inputs per folder+title
skip_all_missing_years: bool = False          # Skip all files with missing years
```

---

## 3. Processing Pipeline Flow

```text
┌─────────────────────────────────────────────────────────────┐
│                    PROCESSING PIPELINE                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Quality Control                                          │
│     └─ Check file integrity, skip incomplete downloads      │
│                                                              │
│  2. Parse & Plan Rename                                      │
│     ├─ SmartMediaParser.parse_filename()                    │
│     ├─ Year Detection (filename → folder hierarchy)         │
│     └─ TemplateEngine.render()                              │
│                                                              │
│  3. Filter Engine                                            │
│     └─ Multi-criteria evaluation (size, res, codec, etc.)   │
│                                                              │
│  4. Year Decision Tree (if ask_user_input=True)             │
│     ├─ Check cache for previous user input                  │
│     ├─ Show GUI dialog with anime title                     │
│     └─ Cache user response for same folder+title            │
│                                                              │
│  5. Duplicate Detection                                      │
│     ├─ Hash comparison (MD5/SHA256/fast)                    │
│     ├─ Content signature matching                           │
│     └─ Resolution ranking & quarantine                      │
│                                                              │
│  6. Execute Move/Copy                                        │
│     ├─ Create target folder structure                       │
│     ├─ Move or copy file with safe_mode                     │
│     ├─ Sync sidecar subtitles                               │
│     └─ Log to rollback journal                              │
│                                                              │
│  7. Archive Backup (if enabled)                              │
│     ├─ Copy processed file to archive folder                │
│     └─ Continue even if archive fails                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Custom Naming Template Tokens

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

## 5. GUI Features

### Organize Tab
- **Folder Selection**: Source, Output, Archive directories
- **Quick Options**: Dry Run, Auto Folder Year, Recursive Subfolders
- **Flatten Output**: All files directly in output (no subfolders)
- **Archive Backup**: Copy processed files to archive folder
- **Live Progress**: Real-time processing status and activity log

### Preview Tab
- **Diff Table**: Side-by-side Before/After view
- **Selective Rename**: Check/uncheck individual files
- **Filter**: Search by filename
- **Batch Execute**: Apply selected renames

### Template Tab
- **Interactive Builder**: Drag-and-drop token insertion
- **Live Preview**: Real-time sample output
- **Preset Library**: Load/save custom templates

### Year Input Dialog (v4.1)
- **Anime Title Display**: Shows parsed anime title (not folder name)
- **Smart Caching**: Remembers user input per folder+title combination
- **Skip Options**: Skip single, skip all, or enter year

---

## 6. Command-Line Interface (CLI)

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

## 7. Building Windows Executable (.exe)

### Quick Build (Recommended):
```batch
# Double-click setup_and_build.bat
# This will:
# 1. Create virtual environment
# 2. Install all dependencies
# 3. Build both GUI and CLI executables
```

### Output Files:
```
dist/
├── AnimeOrganizerPro.exe   # GUI Version (double-click to run)
└── AnimeOrganizerCLI.exe   # CLI Version (command line)
```

### Distribution Files:
| File | Description |
|------|-------------|
| `run.bat` | Launch GUI (checks for EXE first, then Python) |
| `run_cli.bat` | Launch CLI (checks for EXE first, then Python) |
| `setup_and_build.bat` | First-time setup: install deps + build EXEs |
| `install.bat` | Install to Program Files with desktop shortcuts |

---

## 8. Error Handling & Recovery

### Rollback System
- **SQLite Journal**: All operations logged with timestamps
- **One-Click Undo**: Restore original file names and locations
- **Session Management**: Track multiple processing sessions

### Error Recovery
- **Safe Mode**: Auto-increment filenames to prevent overwrites
- **Archive Backup**: Secondary copy survives even if move fails
- **Quality Control**: Skip corrupted/incomplete files automatically

---

## 9. Performance Optimizations

- **Smart Caching**: User year inputs cached per folder+title
- **Fast Hash**: Partial file reading (head+middle+tail) for quick duplicate detection
- **Lazy Metadata**: FFprobe only when needed
- **Batch Processing**: Process all files before showing summary

---

## 10. Version History

### v4.1 (Latest)
- ✅ Archive feature with custom path support
- ✅ Flatten output structure option
- ✅ Improved year input dialog with anime title display
- ✅ Smart caching for user year inputs
- ✅ Better error handling in preview tab
- ✅ Windows build scripts (setup_and_build.bat, install.bat)

### v4.0
- ✅ Enterprise-grade modular architecture
- ✅ AI-powered pattern recognition
- ✅ Custom naming templates with tokens
- ✅ Duplicate detection and quarantine
- ✅ Rollback journaling and undo
- ✅ Watch folder automation
- ✅ Discord/Telegram notifications
- ✅ CSV/JSON/HTML analytics export

---

*Last Updated: August 20, 2026*
