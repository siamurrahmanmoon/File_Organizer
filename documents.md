# 📑 Technical Documentation: Smart File Organizer Pro (v4.1 - Enterprise Edition)

This document provides a comprehensive overview of the modular architecture, pipeline logic, configuration system, custom naming templates, and build instructions for **Smart File Organizer Pro**.

---

## 1. System Architecture Overview

```text
filenameedit/
├── organizer.py              # GUI entry point
├── cli.py                    # CLI entry point
├── config.py                 # Configuration & feature toggles
│
├── core/
│   ├── engine.py             # Main processing engine
│   ├── parser.py             # Smart media filename parser
│   ├── template_engine.py    # Naming template formatter
│   ├── duplicate_detector.py # Duplicate detection & quarantine
│   ├── filter_engine.py      # Multi-criteria filtering
│   ├── quality_control.py    # File integrity checks
│   ├── subtitle_manager.py   # Sidecar subtitle pairing
│   ├── rollback_manager.py   # Operation journal & undo
│   ├── watch_folder.py       # Auto-organize service
│   ├── analytics.py          # Stats & report export
│   ├── security.py           # Path protection
│   ├── notifier.py           # Desktop & webhook alerts
│   └── profiles_manager.py   # Preset config manager
│
├── ui/
│   ├── main_window.py        # Main GUI window
│   ├── theme.py              # Dark/Light themes
│   ├── widgets.py            # Custom widgets
│   └── tabs/
│       ├── organize_tab.py   # Main controls & log
│       ├── preview_tab.py    # Before/After diff table
│       ├── template_tab.py   # Template builder
│       ├── filter_tab.py     # Filter settings
│       ├── duplicate_tab.py  # Duplicate scanner
│       ├── rollback_tab.py   # Undo manager
│       ├── analytics_tab.py  # Stats dashboard
│       ├── watch_tab.py      # Auto-organize config
│       └── help_tab.py       # Built-in guide
│
├── utils/
│   ├── ffmpeg_installer.py   # FFmpeg auto-installer
│   ├── metadata_extractor.py # FFprobe inspection
│   ├── metadata_parser.py    # Metadata formatting
│   ├── file_utils.py         # Safe file operations
│   └── logger_utils.py       # Logging system
│
├── presets/                  # JSON preset profiles
├── logs/                     # Log directory
├── quarantine/               # Duplicate quarantine
├── reports/                  # Exported reports
└── dist/                     # Built executables
```

---

## 2. Configuration Options (`config.py`)

### Feature Toggles
```python
ENABLE_METADATA_EXTRACTION = True     # Video metadata via FFprobe
ENABLE_AI_PATTERN_PARSER = True       # Smart pattern recognition
ENABLE_DUPLICATE_DETECTION = True     # Hash & similarity detection
ENABLE_ADVANCED_FILTERS = True        # Multi-criteria filtering
ENABLE_CUSTOM_TEMPLATES = True        # Custom naming templates
ENABLE_ROLLBACK_JOURNAL = True        # SQLite journal & undo
ENABLE_QUALITY_CONTROL = True         # File integrity checks
ENABLE_SUBTITLE_MANAGEMENT = True     # Sidecar subtitle pairing
ENABLE_AUTOMATION_WATCH = True        # Auto-organize service
ENABLE_NOTIFICATIONS = True           # Desktop & webhook alerts
ENABLE_ANALYTICS = True               # Stats & reports
ENABLE_SECURITY_VALIDATION = True     # Path protection
```

### Output Options
```python
flatten_output_structure: bool = True   # All files in output root
archive_source_files: bool = True       # Backup after processing
archive_path: str = ""                  # Custom archive location
quarantine_path: str = "quarantine"     # Quarantine location
```

---

## 3. Processing Pipeline

```text
1. Quality Control → Skip corrupted files
2. Parse & Plan    → Extract metadata, detect year
3. Filter          → Apply size/res/codec filters
4. Year Input      → Cache user responses
5. Duplicate Check → Hash & signature matching
6. Move/Copy       → Safe mode with auto-increment
7. Archive Backup  → Copy to archive folder
```

---

## 4. Template Tokens

| Token | Description | Example |
|-------|-------------|---------|
| `{Title}` | Anime title | `One Piece` |
| `{Year}` | Release year | `1999` |
| `{Season}` | Season number | `01` |
| `{Episode}` | Episode number | `01` |
| `{Resolution}` | Video quality | `1080p` |
| `{Codec}` | Video codec | `x265` |
| `{AudioCodec}` | Audio codec | `AAC` |
| `{AudioLang}` | Audio language | `Japanese` |
| `{Group}` | Release group | `SubsPlease` |

---

## 5. GUI Features

### Organize Tab
- Source/Output/Archive/Quarantine path selectors
- Dry Run, Auto Year, Flatten Output options
- Live progress and activity log

### Preview Tab
- Side-by-side Before/After view
- Selective file selection
- Filter by filename

### Template Tab
- Interactive token insertion
- Live preview

### Duplicate Tab
- Resolution ranking
- Quarantine management

---

## 6. CLI Usage

```bash
# List presets
python cli.py --list-profiles

# Dry run
python cli.py -s "R:\Anime" -o "R:\Out" --dry-run

# Execute
python cli.py -s "R:\Anime" -o "R:\Out" --execute

# Watch mode
python cli.py -s "R:\Downloads" -o "R:\Library" --watch

# Rollback
python cli.py --rollback <session_id>
```

---

## 7. Building & Distribution

### Build EXE
```batch
setup_and_build.bat
```

### Create Distribution Package
```batch
dist_package.bat
```

### Install on Another PC
1. Copy distribution folder
2. Run `Install.bat`
3. Use Desktop shortcuts

---

## 8. Version History

### v4.1 (Latest)
- Archive backup feature
- Flatten output structure
- Smart year caching
- Improved error handling
- Code cleanup & optimization

### v4.0
- Enterprise modular architecture
- AI pattern recognition
- Custom templates
- Duplicate detection
- Rollback journaling
- Watch folder automation
- Webhook notifications

---

*Last Updated: August 2026*
