# Anime Organizer Pro v4.1

Enterprise-grade, AI-powered anime & media file organizer with GUI and CLI interfaces.

## Quick Start

### Option 1: Run from Source (Python)
```bash
# First time setup
python -m venv venv
venv\Scripts\pip install -r requirements.txt

# Run GUI
python organizer.py

# Run CLI
python cli.py -s "R:\Anime" -o "R:\Organized" --execute
```

### Option 2: Build Windows EXE
```bash
# Run setup script (installs deps + builds EXE)
setup_and_build.bat
```

### Option 3: Install on Another PC
1. Run `dist_package.bat` to create distribution package
2. Copy the folder to target PC
3. Run `Install.bat`

## Features

- Smart file renaming with anime metadata
- Duplicate detection and quarantine
- Custom naming templates
- Batch processing with progress tracking
- Rollback/Undo support
- Archive backup
- Watch folder automation
- Discord/Telegram notifications

## Project Structure

```
filenameedit/
├── organizer.py          # Main GUI entry point
├── cli.py                # CLI entry point
├── config.py             # Configuration & feature toggles
├── core/                 # Core processing engine
├── ui/                   # GUI components
├── utils/                # Utility functions
├── presets/              # JSON preset profiles
├── dist/                 # Built executables
├── setup_and_build.bat   # Build script
├── dist_package.bat      # Distribution package builder
└── install.bat           # System installer
```

## System Requirements

- Windows 10/11
- Python 3.10+ (for source execution)
- 4 GB RAM recommended
- FFmpeg (for metadata extraction)

## License

This software is provided as-is for personal use.

---

*Version 4.1 - August 2026*
