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
        original_name = Path(filename).stem
        language_match = re.search(r"\b(Hindi|English)\b", original_name, re.IGNORECASE)
        clean_name = re.sub(
            r"\b(?:Hindi|English)\b",
            "",
            self.clean_filename(filename),
            flags=re.IGNORECASE,
        )
        clean_name = re.sub(r"\s+", " ", clean_name).strip()

        suffix_match = re.search(r"(\s*-?\s*S\d+\s*E\d+.*)$", clean_name, re.IGNORECASE)
        if suffix_match:
            title = clean_name[: suffix_match.start()].strip()
            suffix = suffix_match.group(1).strip().lstrip("-").strip()
        else:
            title = clean_name
            suffix = ""

        language = f" [{language_match.group(1).title()}]" if language_match else ""
        has_prefix = bool(language) or bool(metadata_tags)
        suffix_text = (
            f" - {suffix}"
            if has_prefix and suffix
            else (f" {suffix}" if suffix else "")
        )

        return f"{title} ({year}){language}{metadata_tags}{suffix_text}"

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

                if not year_to_use:
                    if self.options.get("ask_user_input"):
                        if self.skip_all_missing_years:
                            self.skipped_count += 1
                            self.report_progress()
                            continue
                        if user_input_year is None:
                            gui_callback = self.options.get("gui_input_callback")
                            user_input_year = (
                                gui_callback(folder_path.name)
                                if gui_callback
                                else input("Enter year: ")
                            )

                        if user_input_year == "quit":
                            return "quit"
                        elif user_input_year == "skip_all":
                            self.skip_all_missing_years = True
                            continue
                        year_to_use = user_input_year
                    else:
                        self.skipped_count += 1
                        self.report_progress()
                        continue

                # 🧠 Smart Metadata Extraction
                metadata_tags_str = ""
                meta_options = {
                    k: v for k, v in self.options.items() if k.startswith("include_")
                }
                if any(meta_options.values()):
                    raw_meta = extract_metadata_ffprobe(str(file_path))
                    parsed_meta = get_smart_metadata(str(file_path), raw_meta)
                    metadata_tags_str = format_metadata_tags(parsed_meta, self.options)

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
            text="🎬 Advanced File Organizer Pro",
            font=("Helvetica", 20, "bold"),
        ).grid(row=0, column=0, pady=10)

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

        # 🧠 Smart Metadata Extraction
        meta_frame = ttk.LabelFrame(
            main_frame,
            text="🧠 Smart Metadata Extraction (Requires FFprobe in PATH)",
            padding="15",
        )
        meta_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=10)
        meta_frame.columnconfigure(0, weight=1)
        meta_frame.columnconfigure(1, weight=1)

        self.include_res_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            meta_frame, text="Resolution (1080p, 4K)", variable=self.include_res_var
        ).grid(row=0, column=0, sticky=tk.W, padx=10)
        self.include_vcodec_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            meta_frame, text="Video Codec (x265, AV1)", variable=self.include_vcodec_var
        ).grid(row=0, column=1, sticky=tk.W, padx=10)
        self.include_acodec_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            meta_frame, text="Audio Codec (AAC, FLAC)", variable=self.include_acodec_var
        ).grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        self.include_achannels_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            meta_frame,
            text="Audio Channels (5.1, 7.1)",
            variable=self.include_achannels_var,
        ).grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)
        self.include_bitrate_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            meta_frame, text="Bitrate (Mbps)", variable=self.include_bitrate_var
        ).grid(row=2, column=0, sticky=tk.W, padx=10)
        self.include_fps_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            meta_frame, text="Frame Rate (24fps, 60fps)", variable=self.include_fps_var
        ).grid(row=2, column=1, sticky=tk.W, padx=10)

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=4, column=0, pady=15)
        self.start_btn = ttk.Button(
            btn_frame, text="▶️ Start Processing", command=self.start_processing
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)
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
        main_frame.rowconfigure(6, weight=1)

    def get_options(self) -> dict:
        return {
            "dry_run": self.dry_run_var.get(),
            "auto_folder_year": self.auto_folder_year_var.get(),
            "skip_existing_year": True,
            "ask_user_input": self.ask_user_input_var.get(),
            "process_subfolders": self.process_subfolders_var.get(),
            "create_log": True,
            "custom_extensions": ".mp4, .mkv, .avi",
            "progress_callback": self.update_progress,
            "gui_input_callback": self.get_user_input_year_gui,
            "include_resolution": self.include_res_var.get(),
            "include_video_codec": self.include_vcodec_var.get(),
            "include_audio_codec": self.include_acodec_var.get(),
            "include_audio_channels": self.include_achannels_var.get(),
            "include_bitrate": self.include_bitrate_var.get(),
            "include_fps": self.include_fps_var.get(),
        }

    def start_processing(self):
        if self.is_processing:
            return
        options = self.get_options()
        self.is_processing = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        threading.Thread(target=self.run_processing, daemon=True).start()

    def run_processing(self):
        try:
            self.organizer = AnimeFileOrganizer(
                self.source_var.get(), self.output_var.get(), self.get_options()
            )
            self.organizer.scan_and_process(dry_run=self.get_options()["dry_run"])
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
        # Simplified for brevity, returns None to skip if not implemented fully in GUI thread
        return None

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
