"""
ui/main_window.py - Main Application Window Hosting Notebook Tabs & Background Threads.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import os
import re
from pathlib import Path
from typing import Optional, Dict, Any

from config import OrganizerConfig, get_default_config
from core.engine import AnimeFileOrganizer
from core.profiles_manager import ProfilesManager
from utils.ffmpeg_installer import ensure_ffmpeg, is_ffmpeg_installed
from ui.theme import ModernTheme
from ui.tabs.organize_tab import OrganizeTab
from ui.tabs.preview_tab import PreviewTab
from ui.tabs.template_tab import TemplateTab
from ui.tabs.filter_tab import FilterTab
from ui.tabs.duplicate_tab import DuplicateTab
from ui.tabs.rollback_tab import RollbackTab
from ui.tabs.analytics_tab import AnalyticsTab
from ui.tabs.watch_tab import WatchTab
from ui.tabs.help_tab import HelpTab


class AnimeOrganizerGUI:
    """Main application controller hosting all GUI tabs and orchestrating background execution."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("🎬 Smart File Organizer Pro (v4.0 - Enterprise)")
        self.root.geometry("1200x920")
        self.root.minsize(950, 700)

        # Apply Modern Aesthetic Theme
        ModernTheme.apply_theme(self.root)

        self.profiles_mgr = ProfilesManager()
        self.config = get_default_config()
        self.organizer: Optional[AnimeFileOrganizer] = None
        self.is_processing = False
        self.year_pattern = re.compile(r"\b(19|20)\d{2}\b")

        self._build_main_ui()

    def _build_main_ui(self):
        # Configure root grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Main Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Instantiate Tabs
        self.organize_tab = OrganizeTab(self.notebook, self)
        self.preview_tab = PreviewTab(self.notebook, self)
        self.template_tab = TemplateTab(self.notebook, self)
        self.filter_tab = FilterTab(self.notebook, self)
        self.duplicate_tab = DuplicateTab(self.notebook, self)
        self.rollback_tab = RollbackTab(self.notebook, self)
        self.analytics_tab = AnalyticsTab(self.notebook, self)
        self.watch_tab = WatchTab(self.notebook, self)
        self.help_tab = HelpTab(self.notebook, self)

        # Add tabs to notebook
        self.notebook.add(self.organize_tab, text="📂 Organize")
        self.notebook.add(self.preview_tab, text="👁️ Diff Preview")
        self.notebook.add(self.template_tab, text="📝 Templates")
        self.notebook.add(self.filter_tab, text="⚙️ Filters")
        self.notebook.add(self.duplicate_tab, text="🔍 Duplicates")
        self.notebook.add(self.rollback_tab, text="🔄 Rollback")
        self.notebook.add(self.analytics_tab, text="📊 Analytics")
        self.notebook.add(self.watch_tab, text="⚡ Automation")
        self.notebook.add(self.help_tab, text="📚 Help")

    def switch_to_tab(self, index: int):
        self.notebook.select(index)

    def on_source_change(self, new_source: str):
        if new_source:
            out_candidate = f"{new_source}_Organized"
            self.organize_tab.output_selector.set(out_candidate)

    def get_source_path(self) -> str:
        return self.organize_tab.source_selector.get()

    def get_output_path(self) -> str:
        return self.organize_tab.output_selector.get()

    def sync_config_from_ui(self) -> OrganizerConfig:
        """Reads all settings across all tabs into the runtime OrganizerConfig."""
        self.config.source_path = self.get_source_path()
        self.config.output_path = self.get_output_path()
        self.config.dry_run = self.organize_tab.dry_run_var.get()
        self.config.auto_folder_year = self.organize_tab.auto_folder_year_var.get()
        self.config.process_subfolders = self.organize_tab.subfolders_var.get()
        self.config.flatten_output_structure = self.organize_tab.flatten_output_var.get()
        self.config.archive_source_files = self.organize_tab.archive_source_var.get()
        self.config.archive_path = self.organize_tab.archive_selector.get()
        self.config.ask_user_input = self.organize_tab.ask_user_var.get()

        # Metadata
        self.config.include_resolution = self.organize_tab.inc_res_var.get()
        self.config.include_video_codec = self.organize_tab.inc_codec_var.get()
        self.config.include_audio_codec = self.organize_tab.inc_audio_var.get()
        self.config.include_audio_language = self.organize_tab.inc_lang_var.get()

        # Template
        self.config.naming_template = self.template_tab.template_var.get()

        # Filters
        self.config.min_file_size_mb = self.filter_tab.min_size_var.get()
        self.config.max_file_size_mb = self.filter_tab.max_size_var.get()
        self.config.min_year = self.filter_tab.min_year_var.get()
        self.config.max_year = self.filter_tab.max_year_var.get()
        if self.filter_tab.enable_custom_regex_var.get():
            self.config.custom_regex_filter = self.filter_tab.regex_pattern_var.get().strip()
        else:
            self.config.custom_regex_filter = ""
        self.config.resolution_whitelist = [r for r, v in self.filter_tab.res_vars.items() if v.get()]
        self.config.codec_whitelist = [c for c, v in self.filter_tab.codec_vars.items() if v.get()]

        # Duplicates
        self.config.enable_duplicates = self.duplicate_tab.enable_dups_var.get()
        self.config.hash_algorithm = self.duplicate_tab.hash_algo_combo.get().split()[0]
        self.config.duplicate_action = self.duplicate_tab.dup_action_combo.get().split()[0]

        # Webhooks
        self.config.discord_webhook_url = self.watch_tab.discord_url_var.get().strip()
        self.config.telegram_bot_token = self.watch_tab.tg_token_var.get().strip()
        self.config.telegram_chat_id = self.watch_tab.tg_chat_var.get().strip()

        return self.config

    def load_preset(self, name: str):
        preset = self.profiles_mgr.load_preset(name)
        if not preset:
            return

        self.config = preset
        self.organize_tab.dry_run_var.set(preset.dry_run)
        self.organize_tab.auto_folder_year_var.set(preset.auto_folder_year)
        self.organize_tab.subfolders_var.set(preset.process_subfolders)
        self.organize_tab.flatten_output_var.set(getattr(preset, 'flatten_output_structure', False))
        self.organize_tab.archive_source_var.set(getattr(preset, 'archive_source_files', False))
        if getattr(preset, 'archive_path', ''):
            self.organize_tab.archive_selector.set(preset.archive_path)
        self.organize_tab.ask_user_var.set(preset.ask_user_input)

        self.organize_tab.inc_res_var.set(preset.include_resolution)
        self.organize_tab.inc_codec_var.set(preset.include_video_codec)
        self.organize_tab.inc_audio_var.set(preset.include_audio_codec)
        self.organize_tab.inc_lang_var.set(preset.include_audio_language)

        if preset.naming_template:
            self.template_tab.template_var.set(preset.naming_template)

        self.organize_tab.append_log(f"📑 Preset profile loaded: '{name}'", "HIGHLIGHT")

    def get_organizer_instance(self) -> AnimeFileOrganizer:
        cfg = self.sync_config_from_ui()
        opts = cfg.to_dict()
        opts["progress_callback"] = self.update_progress
        opts["gui_input_callback"] = self.get_user_input_year_gui
        return AnimeFileOrganizer(cfg.source_path, cfg.output_path, options=opts, config=cfg)

    def start_processing(self):
        if self.is_processing:
            messagebox.showwarning("Warning", "Processing is already running!")
            return

        source_path = self.get_source_path()
        output_path = self.get_output_path()

        if not source_path or not Path(source_path).exists():
            messagebox.showerror("Error", f"Source path does not exist:\n{source_path}")
            return

        cfg = self.sync_config_from_ui()

        # Check FFmpeg if metadata requested
        if (cfg.include_resolution or cfg.include_video_codec or cfg.include_audio_codec) and not is_ffmpeg_installed():
            if messagebox.askyesno("FFmpeg Required", "Metadata extraction is enabled, but FFmpeg is not installed.\n\nWould you like to install FFmpeg now?"):
                self.install_ffmpeg()
                return

        if not messagebox.askyesno(
            "Confirm Run",
            f"Start organizing files?\n\n📂 Source: {source_path}\n📁 Output: {output_path}\n🔍 Dry Run: {'YES' if cfg.dry_run else 'NO'}"
        ):
            return

        self.is_processing = True
        self.organize_tab.start_btn.config(state=tk.DISABLED)
        self.organize_tab.stop_btn.config(state=tk.NORMAL)
        self.organize_tab.status_var.set("🔄 Processing started...")
        self.organize_tab.progress_bar.configure(value=0, maximum=100)
        self.organize_tab.clear_log()
        self.organize_tab.append_log("=" * 70, "INFO")
        self.organize_tab.append_log("🚀 Advanced File Organizer Pro Started", "SUCCESS")
        self.organize_tab.append_log("=" * 70, "INFO")

        threading.Thread(target=self._run_worker, daemon=True).start()

    def _run_worker(self):
        try:
            self.organizer = self.get_organizer_instance()

            # Redirect logger to GUI
            import logging
            class GUILogHandler(logging.Handler):
                def __init__(self, app):
                    super().__init__()
                    self.app = app

                def emit(self, record):
                    try:
                        msg = self.format(record)
                        tag = "INFO"
                        if "✅" in msg or "Success" in msg:
                            tag = "SUCCESS"
                        elif "⚠️" in msg or "Skip" in msg or "warning" in msg.lower():
                            tag = "WARNING"
                        elif "❌" in msg or "error" in msg.lower():
                            tag = "ERROR"
                        elif "🔍" in msg or "DRY RUN" in msg:
                            tag = "HIGHLIGHT"
                        self.app.root.after(0, lambda m=msg, t=tag: self.app.organize_tab.append_log(m, t))
                    except Exception:
                        pass

            gui_handler = GUILogHandler(self)
            self.organizer.logger.addHandler(gui_handler)

            summary = self.organizer.scan_and_process()
            self.root.after(0, lambda: self._finish_processing(summary))

        except Exception as e:
            self.root.after(0, lambda: self._error_processing(str(e)))

    def _finish_processing(self, summary: Dict[str, Any]):
        self.is_processing = False
        self.organize_tab.start_btn.config(state=tk.NORMAL)
        self.organize_tab.stop_btn.config(state=tk.DISABLED)
        self.organize_tab.status_var.set("✅ Processing completed!")
        self.organize_tab.append_log(
            f"\n🎉 Finished! Processed: {summary.get('processed', 0)} | Skipped: {summary.get('skipped', 0)} | Errors: {summary.get('errors', 0)}",
            "SUCCESS"
        )
        self.analytics_tab.update_metrics(summary)
        self.rollback_tab.refresh_history()

    def _error_processing(self, err_msg: str):
        self.is_processing = False
        self.organize_tab.start_btn.config(state=tk.NORMAL)
        self.organize_tab.stop_btn.config(state=tk.DISABLED)
        self.organize_tab.status_var.set("❌ Processing encountered an error")
        self.organize_tab.append_log(f"❌ Error: {err_msg}", "ERROR")

    def stop_processing(self):
        self.is_processing = False
        self.organize_tab.start_btn.config(state=tk.NORMAL)
        self.organize_tab.stop_btn.config(state=tk.DISABLED)
        self.organize_tab.status_var.set("⏹️ Processing stopped by user.")

    def update_progress(self, completed: int, total: int, start_time: float):
        percent = (completed / total) * 100 if total > 0 else 0
        self.root.after(0, lambda: self.organize_tab.progress_bar.configure(value=percent))
        self.root.after(
            0, lambda: self.organize_tab.status_var.set(f"🔄 Processing: {percent:.1f}% ({completed}/{total})")
        )

    def install_ffmpeg(self):
        """Downloads FFmpeg with live GUI progress."""
        if self.is_processing:
            return

        self.organize_tab.start_btn.config(state=tk.DISABLED)
        self.organize_tab.ffmpeg_btn.config(state=tk.DISABLED)
        self.organize_tab.status_var.set("📥 Downloading FFmpeg...")
        self.organize_tab.progress_bar.configure(value=0, maximum=100)
        self.organize_tab.append_log("📥 Starting FFmpeg auto-installation...", "HIGHLIGHT")

        def progress_cb(downloaded, total):
            percent = (downloaded / total) * 100 if total > 0 else 0
            self.root.after(0, lambda: self.organize_tab.progress_bar.configure(value=percent))
            self.root.after(
                0,
                lambda: self.organize_tab.status_var.set(
                    f"📥 Downloading FFmpeg... {percent:.1f}% ({downloaded // 1024 // 1024}MB / {total // 1024 // 1024}MB)"
                )
            )

        def worker():
            try:
                success = ensure_ffmpeg(progress_callback=progress_cb)
                self.root.after(0, lambda: self._ffmpeg_done(success))
            except Exception as e:
                self.root.after(0, lambda: self._ffmpeg_done(False, str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _ffmpeg_done(self, success: bool, error: str = ""):
        self.organize_tab.start_btn.config(state=tk.NORMAL)
        self.organize_tab.ffmpeg_btn.config(state=tk.NORMAL)
        if success:
            self.organize_tab.status_var.set("✅ FFmpeg installed successfully!")
            self.organize_tab.append_log("✅ FFmpeg installation complete!", "SUCCESS")
            messagebox.showinfo("Success", "FFmpeg has been installed successfully!")
        else:
            self.organize_tab.status_var.set("❌ FFmpeg installation failed")
            self.organize_tab.append_log(f"❌ FFmpeg installation failed: {error}", "ERROR")
            messagebox.showerror("Error", f"Failed to install FFmpeg:\n{error}")

    def get_user_input_year_gui(self, anime_title: str) -> Optional[str]:
        """Thread-safe dialog asking for release year with anime title display."""
        result = {"year": None, "event": threading.Event()}

        def show_dialog():
            try:
                dialog = tk.Toplevel(self.root)
                dialog.title("🎬 Enter Release Year")
                dialog.geometry("550x200")
                dialog.transient(self.root)
                dialog.grab_set()
                dialog.attributes("-topmost", True)

                # Anime Title Label
                ttk.Label(dialog, text="Anime Title:", font=("Segoe UI", 9, "bold")).pack(pady=(15, 5))

                title_text = tk.Text(dialog, wrap=tk.WORD, height=2, font=("Segoe UI", 10),
                                    bg="#f0f0f0", relief="flat", padx=10, pady=5)
                title_text.insert("1.0", anime_title)
                title_text.config(state="disabled")
                title_text.pack(pady=5, padx=10, fill=tk.X)

                # Year Entry
                year_frame = ttk.Frame(dialog)
                year_frame.pack(pady=10)
                ttk.Label(year_frame, text="Enter Year: ", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)

                year_var = tk.StringVar()
                year_entry = ttk.Entry(year_frame, textvariable=year_var, width=12, font=("Segoe UI", 11))
                year_entry.pack(side=tk.LEFT, padx=5)
                year_entry.focus()

                def on_submit():
                    y = year_var.get().strip()
                    if not y or self.year_pattern.fullmatch(y):
                        result["year"] = y or None
                        dialog.destroy()
                    else:
                        messagebox.showerror("Invalid Year", "Please enter a valid 4-digit year (e.g. 2024).", parent=dialog)

                def on_skip():
                    result["year"] = None
                    dialog.destroy()

                def on_skip_all():
                    result["year"] = "skip_all"
                    dialog.destroy()

                # Bind Enter key
                year_entry.bind("<Return>", lambda e: on_submit())

                btn_f = ttk.Frame(dialog)
                btn_f.pack(pady=10)
                ttk.Button(btn_f, text="Submit", style="Accent.TButton", command=on_submit).pack(side=tk.LEFT, padx=5)
                ttk.Button(btn_f, text="Skip", command=on_skip).pack(side=tk.LEFT, padx=5)
                ttk.Button(btn_f, text="Skip All", command=on_skip_all).pack(side=tk.LEFT, padx=5)

                dialog.protocol("WM_DELETE_WINDOW", on_skip)
                dialog.wait_window()
            finally:
                result["event"].set()

        if threading.current_thread() is threading.main_thread():
            show_dialog()
        else:
            self.root.after(0, show_dialog)
            result["event"].wait()

        return result["year"]
