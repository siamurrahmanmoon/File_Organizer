import os
import re
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, List
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import time
import threading
import sys

# Import Modular Utils
from utils.ffmpeg_installer import ensure_ffmpeg, is_ffmpeg_installed, get_ffprobe_path
from utils.file_utils import safe_copy_and_remove
from utils.logger_utils import setup_logger
from utils.metadata_extractor import extract_metadata_ffprobe
from utils.metadata_parser import get_smart_metadata, format_metadata_tags


class AnimeFileOrganizer:
    """Advanced File Organizer with Smart Hierarchical Year Detection & Metadata Extraction"""

    def __init__(self, source_path: str, output_path: str, options: dict):
        self.source_path = Path(source_path)
        self.output_path = Path(output_path)
        self.options = options
        self.processed_count = 0
        self.skipped_count = 0
        self.error_count = 0
        self.progress_callback = options.get("progress_callback")
        self.total_files = 0
        self.completed_files = 0
        self.processing_start_time = None
        self.skip_all_missing_years = False

        self.logger = setup_logger(log_to_file=options.get("create_log"))
        self.logger.info(f"🚀 Organizer Started")
        self.logger.info(f"📂 Source: {self.source_path}")
        self.logger.info(f"📁 Output: {self.output_path}")

        self.year_pattern = re.compile(r"\b(19|20)\d{2}\b")
        self.video_extensions = {
            ".mp4",
            ".mkv",
            ".avi",
            ".mov",
            ".wmv",
            ".flv",
            ".webm",
            ".m4v",
            ".mpeg",
            ".mpg",
            ".ts",
            ".m2ts",
        }

        if options.get("custom_extensions"):
            ext_list = options["custom_extensions"].split(",")
            self.video_extensions = {
                (
                    ext.strip().lower()
                    if ext.strip().startswith(".")
                    else f".{ext.strip().lower()}"
                )
                for ext in ext_list
            }

    def contains_year(self, text: str) -> Tuple[bool, Optional[str]]:
        match = self.year_pattern.search(text)
        return (True, match.group(0)) if match else (False, None)

    def find_year_in_hierarchy(
        self, folder_path: Path
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        has_year, year = self.contains_year(folder_path.name)
        if has_year:
            return True, year, folder_path.name
        current = folder_path.parent
        while current != self.source_path.parent and current != current.parent:
            has_year, year = self.contains_year(current.name)
            if has_year:
                return True, year, current.name
            current = current.parent
        return False, None, None

    def clean_filename(self, filename: str) -> str:
        name = Path(filename).stem
        name = self.year_pattern.sub("", name).replace("_", " ")
        name = re.sub(r"[\[\]\(\)]+", " ", name)
        return re.sub(r"\s+", " ", name).strip()

    def format_output_name(
        self, filename: str, year: str, metadata_tags: str = ""
    ) -> str:
        """Formats the output filename with resolution metadata only."""
        original_name = Path(filename).stem
        language_match = re.search(r"\b(Hindi|English)\b", original_name, re.IGNORECASE)
        language = f" [{language_match.group(1).title()}]" if language_match else ""
        clean_name = self.clean_filename(filename)
        clean_name = re.sub(
            r"\b(?:Hindi|English)\b",
            "",
            clean_name,
            flags=re.IGNORECASE,
        )
        clean_name = re.sub(r"[-\s]?\d{3,4}[pP]\b", "", clean_name)
        clean_name = re.sub(
            r"\b(?:x264|x265|HEVC|AV1|AAC|FLAC|AC3|DTS|5\.1|7\.1|Stereo|Mono)\b",
            "",
            clean_name,
            flags=re.IGNORECASE,
        )
        clean_name = re.sub(
            r"\b\d+(\.\d+)?\s*(Kbps|Mbps)\b", "", clean_name, flags=re.IGNORECASE
        )
        clean_name = re.sub(
            r"\b\d+(\.\d+)?\s*fps\b", "", clean_name, flags=re.IGNORECASE
        )
        clean_name = re.sub(r"\s+", " ", clean_name).strip()

        episode_patterns = [
            (r"(\s*-?\s*S(\d{1,2})\s*E(\d{1,3}).*)$", "season_episode"),
            (r"(\s*-?\s*Episode\s*(\d{1,3}).*)$", "episode_only"),
            (r"(\s*-?\s*Ep\s*(\d{1,3}).*)$", "episode_only"),
            (r"(\s*-?\s*E(\d{1,3}).*)$", "episode_only"),
        ]
        suffix = ""
        title = clean_name
        for pattern, pattern_type in episode_patterns:
            suffix_match = re.search(pattern, clean_name, re.IGNORECASE)
            if suffix_match:
                full_match = suffix_match.group(1).strip().lstrip("-").strip()
                title = clean_name[: suffix_match.start()].strip()
                if pattern_type == "season_episode":
                    episode_match = re.search(
                        r"S(\d{1,2})\s*E(\d{1,3})", full_match, re.IGNORECASE
                    )
                    if episode_match:
                        suffix = (
                            f"S{int(episode_match.group(1)):02d}"
                            f"E{int(episode_match.group(2)):02d}"
                        )
                else:
                    episode_match = re.search(r"(\d{1,3})", full_match)
                    if episode_match:
                        suffix = f"E{int(episode_match.group(1)):02d}"
                break

        parts = [f"{title} ({year})"]
        if language:
            parts.append(language)
        if metadata_tags:
            resolution_match = re.search(
                r"\[(\d{3,4}p|4K)\]", metadata_tags, re.IGNORECASE
            )
            if resolution_match:
                parts.append(f" [{resolution_match.group(1)}]")
        if suffix:
            parts.append(f" - {suffix}")
        return "".join(parts)

    def get_files_safe(self, folder_path: Path) -> List[Path]:
        files = []
        try:
            for item_name in os.listdir(str(folder_path)):
                if any(
                    item_name.lower().endswith(ext) for ext in self.video_extensions
                ):
                    files.append(folder_path / item_name)
        except Exception as e:
            self.logger.error(f"❌ Error reading folder {folder_path.name}: {str(e)}")
        return files

    def process_folder(self, folder_path: Path, dry_run: bool = False):
        self.logger.info(f"\n{'='*70}\n📁 Scanning Folder: {folder_path.name}")
        folder_has_year, folder_year, source_folder_name = (False, None, None)

        if self.options.get("auto_folder_year"):
            folder_has_year, folder_year, source_folder_name = (
                self.find_year_in_hierarchy(folder_path)
            )
            if folder_has_year:
                self.logger.info(
                    f"🔍 Auto-detected Year '{folder_year}' from: '{source_folder_name}'"
                )

        files = self.get_files_safe(folder_path)
        if not files:
            self.logger.info(f"   ⚠️ No video files found")
            return

        target_folder = self.output_path / (
            folder_path.relative_to(self.source_path)
            if self.options.get("process_subfolders")
            else folder_path.name
        )
        if not dry_run:
            try:
                target_folder.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                self.logger.error(f"   ❌ Cannot create output folder: {str(e)}")
                return

        user_input_year = None
        for idx, file_path in enumerate(files, 1):
            try:
                current_name = file_path.name
                file_has_year, file_year = self.contains_year(current_name)

                if (
                    file_has_year
                    and self.options.get("skip_existing_year")
                    and not folder_has_year
                    and not self.options.get("ask_user_input")
                ):
                    self.logger.info(
                        f"   ⏭️ [{idx}/{len(files)}] Skipped (Already has year {file_year})"
                    )
                    self.skipped_count += 1
                    self.report_progress()
                    continue

                year_to_use = folder_year if folder_has_year else None

                if folder_has_year:
                    self.logger.info(
                        f"   ✅ [{idx}/{len(files)}] Applying hierarchy year ({year_to_use})"
                    )
                elif file_has_year:
                    year_to_use = file_year
                    self.logger.info(
                        f"   ✅ [{idx}/{len(files)}] Applying filename year ({year_to_use})"
                    )
                else:
                    if self.options.get("ask_user_input"):
                        if self.skip_all_missing_years:
                            self.logger.info(
                                f"   ⏭️ [{idx}/{len(files)}] Skipped (Skip All selected)"
                            )
                            self.skipped_count += 1
                            self.report_progress()
                            continue
                        if user_input_year is None:
                            gui_callback = self.options.get("gui_input_callback")
                            if gui_callback:
                                try:
                                    user_input_year = gui_callback(folder_path.name)
                                except Exception as e:
                                    self.logger.warning(
                                        f"   ⚠️ [{idx}/{len(files)}] Dialog error: {str(e)}"
                                    )
                                    user_input_year = None
                            else:
                                user_input_year = input("Enter year: ")

                        if user_input_year == "quit":
                            return "quit"
                        elif user_input_year == "skip_all":
                            self.skip_all_missing_years = True
                            self.logger.info(
                                f"   ⏭️ [{idx}/{len(files)}] Skip All activated"
                            )
                            user_input_year = None
                            self.skipped_count += 1
                            self.report_progress()
                            continue

                        if user_input_year is None or user_input_year == "":
                            self.logger.info(
                                f"   ⏭️ [{idx}/{len(files)}] Skipped (No year provided)"
                            )
                            self.skipped_count += 1
                            self.report_progress()
                            continue

                        year_to_use = user_input_year
                        self.logger.info(
                            f"   ✅ [{idx}/{len(files)}] Applying user year ({year_to_use})"
                        )
                    else:
                        self.logger.info(
                            f"   ⏭️ [{idx}/{len(files)}] Skipped "
                            "(No year found & user input disabled)"
                        )
                        self.skipped_count += 1
                        self.report_progress()
                        continue

                if not year_to_use:
                    self.logger.info(
                        f"   ⏭️ [{idx}/{len(files)}] Skipped (Year is None)"
                    )
                    self.skipped_count += 1
                    self.report_progress()
                    continue

                # 🧠 Smart Metadata Extraction
                metadata_tags_str = ""
                meta_options = {
                    k: v for k, v in self.options.items() if k.startswith("include_")
                }
                if any(meta_options.values()):
                    try:
                        raw_meta = extract_metadata_ffprobe(str(file_path))
                        parsed_meta = get_smart_metadata(str(file_path), raw_meta)
                        metadata_tags_str = format_metadata_tags(
                            parsed_meta, self.options
                        )
                    except Exception as e:
                        self.logger.warning(
                            f"   ⚠️ Metadata extraction failed: {str(e)}"
                        )

                ext = file_path.suffix
                new_name = f"{self.format_output_name(current_name, year_to_use, metadata_tags_str)}{ext}"
                new_path = target_folder / new_name

                if dry_run:
                    self.logger.info(f"   🔍 [DRY RUN] Would rename to: {new_name}")
                    self.processed_count += 1
                else:
                    try:
                        safe_copy_and_remove(str(file_path), str(new_path))
                        self.logger.info(f"   ✅ [{idx}/{len(files)}] Success")
                        self.processed_count += 1
                    except Exception as e:
                        self.logger.error(f"   ❌ [{idx}/{len(files)}] Error: {str(e)}")
                        self.error_count += 1
                self.report_progress()
            except Exception as e:
                self.logger.error(f"   ❌ Error processing {file_path.name}: {str(e)}")
                self.error_count += 1
                self.report_progress()

    def report_progress(self):
        self.completed_files += 1
        if self.progress_callback:
            try:
                self.progress_callback(
                    self.completed_files, self.total_files, self.processing_start_time
                )
            except:
                pass

    def scan_and_process(self, dry_run: bool = False):
        if not self.source_path.exists():
            self.logger.error(f"❌ Source path does not exist: {self.source_path}")
            return

        self.total_files = sum(
            1
            for r, _, f in os.walk(str(self.source_path))
            for file in f
            if file.lower().endswith(tuple(self.video_extensions))
        )
        self.processing_start_time = time.time()
        self.logger.info(f"📊 Total video files found: {self.total_files}")

        if self.total_files == 0:
            self.logger.warning(
                "⚠️ No supported video files found. Check the source folder "
                "and file extensions."
            )
            return

        if self.progress_callback:
            self.progress_callback(0, self.total_files, self.processing_start_time)

        for root, dirs, files in os.walk(str(self.source_path)):
            root_path = Path(root)
            if any(f.lower().endswith(tuple(self.video_extensions)) for f in files):
                if self.process_folder(root_path, dry_run) == "quit":
                    break
                if not self.options.get("process_subfolders"):
                    break


class AnimeOrganizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎬 Advanced File Organizer Pro (v4.0 - Metadata)")
        self.root.geometry("1150x950")
        self.organizer = None
        self.is_processing = False
        self.year_pattern = re.compile(r"\b(19|20)\d{2}\b")
        self.setup_ui()

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

        # Title
        ttk.Label(
            main_frame,
            text="🎬 Advanced File Organizer Pro V2",
            font=("Helvetica", 20, "bold"),
        ).grid(row=0, column=0, pady=10)

        # 🆕 FFmpeg Status Indicator
        self.ffmpeg_status_var = tk.StringVar()
        self.ffmpeg_status_label = ttk.Label(
            main_frame,
            textvariable=self.ffmpeg_status_var,
            font=("Helvetica", 10),
            foreground="gray",
        )
        self.ffmpeg_status_label.grid(row=0, column=0, pady=(0, 10), sticky=tk.S)
        self._update_ffmpeg_status()

        # Paths
        path_frame = ttk.LabelFrame(
            main_frame, text="📂 Folder Selection", padding="15"
        )
        path_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=10)
        path_frame.columnconfigure(1, weight=1)

        self.source_var = tk.StringVar(value=r"R:\Anime1")
        ttk.Entry(path_frame, textvariable=self.source_var, width=70).grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=5
        )
        ttk.Button(
            path_frame,
            text="📂 Browse",
            command=lambda: self.source_var.set(filedialog.askdirectory()),
        ).grid(row=0, column=2, padx=5)

        self.output_var = tk.StringVar(value=r"R:\Anime1_Organized")
        ttk.Entry(path_frame, textvariable=self.output_var, width=70).grid(
            row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5
        )
        ttk.Button(
            path_frame,
            text="📁 Browse",
            command=lambda: self.output_var.set(filedialog.askdirectory()),
        ).grid(row=1, column=2, padx=5)

        # Filters
        filters_frame = ttk.LabelFrame(
            main_frame, text="⚙️ Advanced Filters & Options", padding="15"
        )
        filters_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=10)

        self.dry_run_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            filters_frame, text="🔍 Dry Run (Preview only)", variable=self.dry_run_var
        ).grid(row=0, column=0, sticky=tk.W)
        self.auto_folder_year_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            filters_frame,
            text="🔍 Auto-detect year (Folder & Parents)",
            variable=self.auto_folder_year_var,
        ).grid(row=0, column=1, sticky=tk.W)
        self.process_subfolders_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            filters_frame,
            text="📂 Process all subfolders recursively",
            variable=self.process_subfolders_var,
        ).grid(row=1, column=0, sticky=tk.W)
        self.ask_user_input_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            filters_frame,
            text="❓ Ask user for year if not found",
            variable=self.ask_user_input_var,
        ).grid(row=1, column=1, sticky=tk.W)

        meta_frame = ttk.LabelFrame(
            main_frame, text="🧠 Smart Metadata Extraction", padding="15"
        )
        meta_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=10)
        meta_frame.columnconfigure(0, weight=1)

        self.include_res_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            meta_frame,
            text="Include Resolution (1080p, 720p, 4K)",
            variable=self.include_res_var,
        ).grid(row=0, column=0, sticky=tk.W, padx=10)
        ttk.Label(
            meta_frame,
            text="ℹ️ Only resolution will be included. Other metadata (codec, bitrate, etc.) will be removed.",
            font=("Helvetica", 8),
            foreground="gray",
        ).grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=4, column=0, pady=15)
        self.start_btn = ttk.Button(
            btn_frame, text="▶️ Start Processing", command=self.start_processing
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.install_ffmpeg_btn = ttk.Button(
            btn_frame, text="📥 Install FFmpeg", command=self._install_ffmpeg_gui
        )
        self.install_ffmpeg_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn = ttk.Button(
            btn_frame, text="⏹️ Stop", command=self.stop_processing, state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # Progress
        progress_frame = ttk.LabelFrame(main_frame, text="📊 Progress", padding="10")
        progress_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=10)
        progress_frame.columnconfigure(0, weight=1)
        self.progress_bar = ttk.Progressbar(
            progress_frame, mode="determinate", maximum=100, length=600
        )
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        self.status_var = tk.StringVar(
            value="✅ Ready - Configure options and click Start"
        )
        ttk.Label(
            progress_frame, textvariable=self.status_var, font=("Helvetica", 11, "bold")
        ).grid(row=1, column=0, sticky=tk.W)

        # Log
        log_frame = ttk.LabelFrame(main_frame, text="📋 Activity Log", padding="10")
        log_frame.grid(row=6, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.log_text = scrolledtext.ScrolledText(
            log_frame, height=15, width=120, wrap=tk.WORD, font=("Consolas", 9)
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.log_text.tag_configure("INFO", foreground="black")
        self.log_text.tag_configure("SUCCESS", foreground="green")
        self.log_text.tag_configure("WARNING", foreground="orange")
        self.log_text.tag_configure("ERROR", foreground="red")
        main_frame.rowconfigure(6, weight=1)

    def get_options(self) -> dict:
        return {
            "dry_run": self.dry_run_var.get(),
            "auto_folder_year": self.auto_folder_year_var.get(),
            "skip_existing_year": True,
            "ask_user_input": self.ask_user_input_var.get(),
            "process_subfolders": self.process_subfolders_var.get(),
            "create_log": True,
            "custom_extensions": "",
            "progress_callback": self.update_progress,
            "gui_input_callback": self.get_user_input_year_gui,
            "console_debug": False,
            "include_resolution": self.include_res_var.get(),
            "include_video_codec": False,
            "include_audio_codec": False,
            "include_audio_channels": False,
            "include_bitrate": False,
            "include_fps": False,
        }

    def start_processing(self):
        if self.is_processing:
            messagebox.showwarning("Warning", "Processing is already running!")
            return

        source_path = self.source_var.get()
        output_path = self.output_var.get()
        if not Path(source_path).exists():
            messagebox.showerror("Error", f"Source path does not exist:\n{source_path}")
            return

        options = self.get_options()

        metadata_keys = ["include_resolution"]
        if any(options.get(key) for key in metadata_keys) and not is_ffmpeg_installed():
            response = messagebox.askyesno(
                "FFmpeg Required",
                "You have enabled Smart Metadata Extraction, but FFmpeg is not installed.\n\n"
                "Would you like to auto-install FFmpeg now?\n"
                "(~100MB download, will be saved in local 'bin' folder)",
            )
            if response:
                self._install_ffmpeg_gui()
                return

            for key in metadata_keys:
                options[key] = False
            self.include_res_var.set(False)
            self.log_message(
                "⚠️ Metadata extraction disabled (FFmpeg not available)", "WARNING"
            )

        summary = f"""Processing Configuration:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📂 Source: {source_path}
📁 Output: {output_path}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 Dry Run: {'YES' if options['dry_run'] else 'NO'}
🎯 Auto Hierarchy Year: {'ON' if options['auto_folder_year'] else 'OFF'}
⏭️ Skip Existing Year: {'ON' if options['skip_existing_year'] else 'OFF'}
❓ Ask User Input: {'ON' if options['ask_user_input'] else 'OFF'}
📂 Process Subfolders: {'ON' if options['process_subfolders'] else 'OFF'}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        if not messagebox.askyesno("Confirm", summary + "\nStart processing?"):
            return

        self.is_processing = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_var.set("🔄 Processing started...")
        self.progress_bar.configure(value=0, maximum=100)
        self.log_text.delete(1.0, tk.END)
        self.log_message("=" * 70, "INFO")
        self.log_message("🎬 Advanced File Organizer Pro Started", "SUCCESS")
        self.log_message("=" * 70, "INFO")
        threading.Thread(target=self.run_processing, daemon=True).start()

    def _update_ffmpeg_status(self):
        """Updates the FFmpeg status label."""
        if is_ffmpeg_installed():
            path = get_ffprobe_path()
            self.ffmpeg_status_var.set(f"✅ FFprobe: {path}")
            self.ffmpeg_status_label.config(foreground="green")
        else:
            self.ffmpeg_status_var.set(
                "⚠️ FFmpeg not found (Will auto-install on first metadata use)"
            )
            self.ffmpeg_status_label.config(foreground="orange")

    def _install_ffmpeg_gui(self):
        """Downloads FFmpeg with GUI progress."""
        if self.is_processing:
            return
        if is_ffmpeg_installed():
            messagebox.showinfo("Info", "FFmpeg is already installed!")
            self._update_ffmpeg_status()
            return

        self.start_btn.config(state=tk.DISABLED)
        self.install_ffmpeg_btn.config(state=tk.DISABLED)
        self.status_var.set("📥 Downloading FFmpeg...")
        self.progress_bar.configure(value=0, maximum=100)
        self.log_message("📥 Starting FFmpeg auto-installation...", "INFO")

        def progress_cb(downloaded, total):
            percent = (downloaded / total) * 100 if total > 0 else 0
            self.root.after(0, lambda: self.progress_bar.configure(value=percent))
            self.root.after(
                0,
                lambda: self.status_var.set(
                    f"📥 Downloading FFmpeg... {percent:.1f}% "
                    f"({downloaded // 1024 // 1024}MB / {total // 1024 // 1024}MB)"
                ),
            )

        def worker():
            try:
                success = ensure_ffmpeg(progress_callback=progress_cb)
                self.root.after(0, lambda: self._ffmpeg_install_done(success))
            except Exception as error:
                self.root.after(0, lambda: self._ffmpeg_install_done(False, str(error)))

        threading.Thread(target=worker, daemon=True).start()

    def _ffmpeg_install_done(self, success: bool, error: str = ""):
        """Called when FFmpeg installation completes."""
        self.start_btn.config(state=tk.NORMAL)
        self.install_ffmpeg_btn.config(state=tk.NORMAL)
        if success:
            self.status_var.set("✅ FFmpeg installed successfully!")
            self.log_message("✅ FFmpeg installation complete!", "SUCCESS")
            messagebox.showinfo("Success", "FFmpeg has been installed successfully!")
        else:
            self.status_var.set("❌ FFmpeg installation failed")
            self.log_message(f"❌ FFmpeg installation failed: {error}", "ERROR")
            messagebox.showerror("Error", f"Failed to install FFmpeg:\n{error}")
        self._update_ffmpeg_status()

    def setup_logging(self, options: Optional[dict] = None):
        """Resets application logging before a processing run."""
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.info("🚀 Organizer Started")

    def _add_log_message(self, msg: str):
        """Thread-safe method to add log messages to the text widget."""
        try:
            if "✅" in msg or "Success" in msg:
                tag = "SUCCESS"
            elif "⚠️" in msg or "Skip" in msg or "No year" in msg:
                tag = "WARNING"
            elif "❌" in msg or "Error" in msg:
                tag = "ERROR"
            elif "🔍" in msg or "DRY RUN" in msg:
                tag = "INFO"
            else:
                tag = "INFO"

            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_text.insert(tk.END, f"[{timestamp}] ", "INFO")
            self.log_text.insert(tk.END, f"{msg}\n", tag)
            self.log_text.see(tk.END)
            self.log_text.update_idletasks()
        except Exception as e:
            print(f"Error adding log message: {e}")

    def log_message(self, message: str, tag: str = "INFO"):
        """Add a message to the log text widget."""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_text.insert(tk.END, f"[{timestamp}] ", "INFO")
            self.log_text.insert(tk.END, f"{message}\n", tag)
            self.log_text.see(tk.END)
            self.root.update_idletasks()
        except Exception as e:
            print(f"Error in log_message: {e}")

    def run_processing(self):
        try:
            source_path = self.source_var.get()
            output_path = self.output_var.get()
            options = self.get_options()

            self.root.after(0, lambda: self.log_text.delete(1.0, tk.END))
            self.setup_logging()
            self.organizer = AnimeFileOrganizer(source_path, output_path, options)

            class GUILogHandler(logging.Handler):
                def __init__(self, gui):
                    super().__init__()
                    self.gui = gui
                    self.setFormatter(logging.Formatter("%(message)s"))

                def emit(self, record):
                    try:
                        message = self.format(record)
                        self.gui.root.after(
                            0,
                            lambda msg=message: self.gui._add_log_message(msg),
                        )
                    except Exception as error:
                        print(f"Log handler error: {error}")

            for handler in self.organizer.logger.handlers[:]:
                self.organizer.logger.removeHandler(handler)

            root_logger = logging.getLogger()
            for handler in root_logger.handlers[:]:
                if isinstance(handler, logging.StreamHandler) and not isinstance(
                    handler, logging.FileHandler
                ):
                    root_logger.removeHandler(handler)
                    handler.close()

            gui_handler = GUILogHandler(self)
            self.organizer.logger.addHandler(gui_handler)

            if options.get("console_debug", False):
                console_handler = logging.StreamHandler()
                console_handler.setFormatter(logging.Formatter("%(message)s"))
                self.organizer.logger.addHandler(console_handler)

            self.organizer.scan_and_process(dry_run=options["dry_run"])
            self.root.after(0, self.finish_processing)
        except Exception as e:
            self.root.after(0, lambda: self.error_processing(str(e)))

    def finish_processing(self):
        self.is_processing = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_var.set("✅ Processing completed!")

    def update_progress(self, completed: int, total: int, start_time: float):
        percent = (completed / total) * 100 if total > 0 else 0
        self.root.after(0, lambda: self.progress_bar.configure(value=percent))
        self.root.after(
            0, lambda: self.status_var.set(f"🔄 {percent:.1f}% ({completed}/{total})")
        )

    def get_user_input_year_gui(self, folder_name: str) -> Optional[str]:
        """Get the release year from a GUI dialog in a worker-safe way."""
        result = {"year": None, "event": threading.Event()}

        def show_dialog():
            try:
                dialog = tk.Toplevel(self.root)
                dialog.title("Enter Release Year")
                dialog.geometry("450x180")
                dialog.transient(self.root)
                dialog.grab_set()
                dialog.lift()
                dialog.focus_force()
                dialog.attributes("-topmost", True)

                ttk.Label(
                    dialog,
                    text=f"Folder: {folder_name[:70]}...",
                    font=("Helvetica", 9),
                    wraplength=400,
                ).pack(pady=10, padx=10)

                year_var = tk.StringVar()
                year_frame = ttk.Frame(dialog)
                year_frame.pack(pady=10)
                ttk.Label(
                    year_frame, text="Enter Year:", font=("Helvetica", 10, "bold")
                ).pack(side=tk.LEFT, padx=5)
                year_entry = ttk.Entry(
                    year_frame, textvariable=year_var, width=15, font=("Helvetica", 12)
                )
                year_entry.pack(side=tk.LEFT, padx=5)
                year_entry.focus()

                dialog_result = {"year": None}

                def on_submit():
                    year = year_var.get().strip()
                    if year.lower() in ["skip", "s", ""]:
                        dialog_result["year"] = None
                    elif self.year_pattern.fullmatch(year):
                        dialog_result["year"] = year
                    else:
                        messagebox.showerror(
                            "Invalid Year",
                            "Please enter a valid year (e.g., 2006, 2024)\n"
                            "or leave empty to skip.",
                            parent=dialog,
                        )
                        return
                    dialog.destroy()

                def on_skip():
                    dialog_result["year"] = None
                    dialog.destroy()

                def on_skip_all():
                    dialog_result["year"] = "skip_all"
                    dialog.destroy()

                button_frame = ttk.Frame(dialog)
                button_frame.pack(pady=15)
                ttk.Button(
                    button_frame, text="Submit", command=on_submit, width=10
                ).pack(side=tk.LEFT, padx=5)
                ttk.Button(button_frame, text="Skip", command=on_skip, width=10).pack(
                    side=tk.LEFT, padx=5
                )
                ttk.Button(
                    button_frame, text="Skip All", command=on_skip_all, width=10
                ).pack(side=tk.LEFT, padx=5)

                def on_close():
                    dialog_result["year"] = None
                    dialog.destroy()

                dialog.protocol("WM_DELETE_WINDOW", on_close)
                year_entry.bind("<Return>", lambda event: on_submit())
                dialog.update_idletasks()
                width = dialog.winfo_width()
                height = dialog.winfo_height()
                x = (dialog.winfo_screenwidth() - width) // 2
                y = (dialog.winfo_screenheight() - height) // 2
                dialog.geometry(f"{width}x{height}+{x}+{y}")
                dialog.wait_window()
                result["year"] = dialog_result["year"]
            except Exception as e:
                print(f"Dialog error: {e}")
                result["year"] = None
            finally:
                result["event"].set()

        if threading.current_thread() is threading.main_thread():
            show_dialog()
        else:
            self.root.after(0, show_dialog)
            result["event"].wait()
        return result["year"]

    def stop_processing(self):
        self.is_processing = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

    def error_processing(self, err):
        self.is_processing = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)


def main():
    root = tk.Tk()
    app = AnimeOrganizerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
