"""
ui/tabs/organize_tab.py - Main Organize Tab for folder selection, run controls & activity log.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path
from datetime import datetime
from typing import Callable, Dict, Any

from ui.widgets import PathSelector
from utils.ffmpeg_installer import is_ffmpeg_installed, get_ffprobe_path


class OrganizeTab(ttk.Frame):
    """Main tab for setting up paths, basic options, running organizer, and live activity log."""

    def __init__(self, parent, main_app, **kwargs):
        super().__init__(parent, padding="15", **kwargs)
        self.main_app = main_app

        self.columnconfigure(0, weight=1)
        self.rowconfigure(5, weight=1)

        self._build_header()
        self._build_paths_section()
        self._build_options_section()
        self._build_action_buttons()
        self._build_progress_section()
        self._build_log_section()

    def _build_header(self):
        header_frame = ttk.Frame(self)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        header_frame.columnconfigure(0, weight=1)

        title_lbl = ttk.Label(
            header_frame,
            text="🎬 Advanced File Organizer Pro",
            font=("Segoe UI", 16, "bold")
        )
        title_lbl.grid(row=0, column=0, sticky=tk.W)

        # Profile selection
        profile_frame = ttk.Frame(header_frame)
        profile_frame.grid(row=0, column=1, sticky=tk.E)

        ttk.Label(profile_frame, text="📑 Preset Profile: ", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        self.preset_combo = ttk.Combobox(
            profile_frame,
            values=["default", "plex_jellyfin", "anime_archival", "minimal_clean"],
            state="readonly",
            width=18
        )
        self.preset_combo.set("default")
        self.preset_combo.pack(side=tk.LEFT, padx=5)
        self.preset_combo.bind("<<ComboboxSelected>>", self._on_preset_change)

    def _build_paths_section(self):
        path_frame = ttk.LabelFrame(self, text="📂 Folder Selection", padding="12")
        path_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        path_frame.columnconfigure(0, weight=1)

        self.source_selector = PathSelector(
            path_frame,
            label_text="Source Directory: ",
            default_path=r"R:\Anime1",
            on_change=lambda path: self.main_app.on_source_change(path)
        )
        self.source_selector.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=4)

        self.output_selector = PathSelector(
            path_frame,
            label_text="Output Directory: ",
            default_path=r"R:\Anime1_Organized"
        )
        self.output_selector.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=4)

    def _build_options_section(self):
        opts_frame = ttk.LabelFrame(self, text="⚙️ Quick Options & Metadata", padding="12")
        opts_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        opts_frame.columnconfigure((0, 1, 2, 3), weight=1)

        self.dry_run_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts_frame, text="🔍 Dry Run (Simulate)", variable=self.dry_run_var).grid(row=0, column=0, sticky=tk.W, padx=5, pady=3)

        self.auto_folder_year_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts_frame, text="🎯 Auto Folder Year", variable=self.auto_folder_year_var).grid(row=0, column=1, sticky=tk.W, padx=5, pady=3)

        self.subfolders_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts_frame, text="📂 Recursive Subfolders", variable=self.subfolders_var).grid(row=0, column=2, sticky=tk.W, padx=5, pady=3)

        self.ask_user_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opts_frame, text="❓ Ask if Missing Year", variable=self.ask_user_var).grid(row=0, column=3, sticky=tk.W, padx=5, pady=3)

        # Metadata row
        self.inc_res_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts_frame, text="📺 Include Resolution", variable=self.inc_res_var).grid(row=1, column=0, sticky=tk.W, padx=5, pady=3)

        self.inc_codec_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opts_frame, text="🎞️ Include Video Codec", variable=self.inc_codec_var).grid(row=1, column=1, sticky=tk.W, padx=5, pady=3)

        self.inc_audio_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opts_frame, text="🔊 Include Audio Info", variable=self.inc_audio_var).grid(row=1, column=2, sticky=tk.W, padx=5, pady=3)

        self.inc_lang_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts_frame, text="🌍 Include Audio Language", variable=self.inc_lang_var).grid(row=1, column=3, sticky=tk.W, padx=5, pady=3)

    def _build_action_buttons(self):
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=3, column=0, pady=10)

        self.start_btn = ttk.Button(
            btn_frame,
            text="▶️ Start Processing",
            style="Accent.TButton",
            command=self.main_app.start_processing
        )
        self.start_btn.pack(side=tk.LEFT, padx=6)

        self.stop_btn = ttk.Button(
            btn_frame,
            text="⏹️ Stop",
            style="Danger.TButton",
            state=tk.DISABLED,
            command=self.main_app.stop_processing
        )
        self.stop_btn.pack(side=tk.LEFT, padx=6)

        self.ffmpeg_btn = ttk.Button(
            btn_frame,
            text="📥 Install FFmpeg",
            command=self.main_app.install_ffmpeg
        )
        self.ffmpeg_btn.pack(side=tk.LEFT, padx=6)

        self.preview_btn = ttk.Button(
            btn_frame,
            text="👁️ Open Diff Preview",
            command=lambda: self.main_app.switch_to_tab(1)
        )
        self.preview_btn.pack(side=tk.LEFT, padx=6)

    def _build_progress_section(self):
        prog_frame = ttk.LabelFrame(self, text="📊 Progress & Status", padding="10")
        prog_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=5)
        prog_frame.columnconfigure(0, weight=1)

        self.progress_bar = ttk.Progressbar(prog_frame, mode="determinate", maximum=100)
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=4)

        self.status_var = tk.StringVar(value="✅ Ready to scan files")
        self.status_lbl = ttk.Label(
            prog_frame,
            textvariable=self.status_var,
            font=("Segoe UI", 9, "bold")
        )
        self.status_lbl.grid(row=1, column=0, sticky=tk.W)

    def _build_log_section(self):
        log_frame = ttk.LabelFrame(self, text="📋 Activity Log", padding="8")
        log_frame.grid(row=5, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="#0f172a",
            fg="#f8fafc",
            insertbackground="#ffffff"
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Colored text tags
        self.log_text.tag_configure("INFO", foreground="#94a3b8")
        self.log_text.tag_configure("SUCCESS", foreground="#34d399")
        self.log_text.tag_configure("WARNING", foreground="#facc15")
        self.log_text.tag_configure("ERROR", foreground="#f87171")
        self.log_text.tag_configure("HIGHLIGHT", foreground="#38bdf8")

    def _on_preset_change(self, event=None):
        preset_name = self.preset_combo.get()
        self.main_app.load_preset(preset_name)

    def append_log(self, message: str, tag: str = "INFO"):
        """Adds timestamped entry to the activity log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] ", "INFO")
        self.log_text.insert(tk.END, f"{message}\n", tag)
        self.log_text.see(tk.END)

    def clear_log(self):
        self.log_text.delete(1.0, tk.END)
