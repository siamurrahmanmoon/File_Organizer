"""
ui/tabs/help_tab.py - Built-in User Documentation, Syntax Cheatsheets & FAQ.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext

HELP_DOCUMENTATION = """
================================================================================
🎬 SMART FILE ORGANIZER PRO - COMPLETE USER GUIDE & REFERENCE
================================================================================

1. 🎯 SMART HIERARCHICAL YEAR DETECTION
--------------------------------------------------------------------------------
The organizer follows a strict decision hierarchy:
  1. Checks if the video filename contains a valid release year (e.g. 2006, 2024).
  2. If missing, checks the parent folder name (and ancestor folders).
  3. If still missing and 'Ask User' is enabled, prompts via dialog.
  4. Otherwise skips the file safely without destructive changes.

2. 🏷️ CUSTOM NAMING TEMPLATE SYNTAX
--------------------------------------------------------------------------------
You can compose any naming format using tokens:
  • {Title}          - Cleaned Anime / Show title
  • {Year}           - 4-digit release year (e.g. 2024)
  • {Season}         - Season number (01)
  • {Episode}        - Episode number (05)
  • {EpisodeRange}   - Multi-episode marker (E01-E04)
  • {Resolution}     - Resolution (1080p, 720p, 4K)
  • {Codec}          - Video Codec (x265, x264, AV1)
  • {AudioCodec}     - Audio Codec (AAC, FLAC, AC3)
  • {AudioChannels}  - Surround/Stereo (5.1, Stereo, 7.1)
  • {AudioLang}      - Audio language (Japanese, English, Hindi)
  • {Group}          - Release group ([SubsPlease], [Erai-raws])
  • {Type}           - Media type (Movie, OVA, Special, Episode)

Example Templates:
  • Standard:  {Title} ({Year}) [{Resolution}] - S{Season}E{Episode}
  • Scene:     [{Group}] {Title} - {Episode} [{Resolution}] [{Codec}]
  • Jellyfin:  {Title} ({Year})/Season {Season:02d}/{Title} - S{Season:02d}E{Episode:02d}

3. 🔍 INTELLIGENT DUPLICATE DETECTION
--------------------------------------------------------------------------------
  • Fast Partial Hash: Inspects head (64KB), middle (64KB), and tail (64KB) chunks.
  • Exact SHA-256 / MD5: Full byte verification.
  • Safe Quarantine: Moves duplicates to the 'quarantine/' folder without data loss.

4. 🔄 1-CLICK ROLLBACK & UNDO
--------------------------------------------------------------------------------
Every file move is recorded in SQLite ('logs/operations_journal.db').
Open the 'Rollback' tab at any time, pick a session, and click 'Undo' to restore
all files back to their exact original locations.

5. 🛠️ WINDOWS EXECUTABLE COMPILATION (.EXE)
--------------------------------------------------------------------------------
To compile a standalone .exe with PyInstaller:
  pip install pyinstaller
  pyinstaller --noconfirm --onefile --windowed --name "AnimeOrganizerPro" --icon=icon.ico organizer.py
================================================================================
"""


class HelpTab(ttk.Frame):
    """Built-in documentation and template syntax reference."""

    def __init__(self, parent, main_app, **kwargs):
        super().__init__(parent, padding="15", **kwargs)
        self.main_app = main_app

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        help_text = scrolledtext.ScrolledText(
            self,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#0f172a",
            fg="#f8fafc",
            padx=15,
            pady=15
        )
        help_text.insert(tk.END, HELP_DOCUMENTATION.strip())
        help_text.config(state=tk.DISABLED)
        help_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
