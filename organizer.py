import os
import re
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, List
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import time
import threading
import sys


# Windows Long Path Support Helper
def get_long_path(path: str) -> str:
    """Adds \\?\ prefix to support paths longer than 260 characters on Windows."""
    if sys.platform == "win32" and not path.startswith("\\\\?\\"):
        path = path.replace("/", "\\")
        return f"\\\\?\\{path}"
    return path


class AnimeFileOrganizer:
    """Advanced File Organizer with Smart Hierarchical Year Detection"""

    def __init__(self, source_path: str, output_path: str, options: dict):
        self.source_path = Path(source_path)
        self.output_path = Path(output_path)
        self.options = options

        self.processed_count = 0
        self.skipped_count = 0
        self.error_count = 0
        self.log_file = None

        self.progress_callback = options.get("progress_callback")
        self.total_files = 0
        self.completed_files = 0
        self.processing_start_time = None
        self.skip_all_missing_years = False

        self.setup_logging()

        # Regex patterns
        self.year_pattern = re.compile(r"\b(19|20)\d{2}\b")

        # Default video extensions
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
            ".mpe",
            ".3gp",
            ".3g2",
            ".ts",
            ".m2ts",
            ".mts",
            ".vob",
            ".ogv",
            ".rm",
            ".rmvb",
            ".asf",
            ".f4v",
        }

        # Filter extensions if specified
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

    def setup_logging(self):
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        if self.options.get("create_log"):
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.log_file = log_dir / f"organizer_{timestamp}.log"
            logging.basicConfig(
                level=logging.INFO,
                format="%(message)s",
                handlers=[
                    logging.FileHandler(self.log_file, encoding="utf-8"),
                    logging.StreamHandler(),
                ],
            )
        else:
            logging.basicConfig(
                level=logging.INFO,
                format="%(message)s",
                handlers=[logging.StreamHandler()],
            )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f" Organizer Started")
        self.logger.info(f" Source: {self.source_path}")
        self.logger.info(f"📁 Output: {self.output_path}")

    def contains_year(self, text: str) -> Tuple[bool, Optional[str]]:
        match = self.year_pattern.search(text)
        if match:
            return True, match.group(0)
        return False, None

    def find_year_in_hierarchy(
        self, folder_path: Path
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Checks the folder and its parents up to the source root to find a year."""
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
        name = self.year_pattern.sub("", name)
        name = name.replace("_", " ")
        name = re.sub(r"[\[\]\(\)]+", " ", name)
        name = re.sub(r"\s+", " ", name).strip()
        return name

    def format_output_name(self, filename: str, year: str) -> str:
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
        suffix_text = f" -{suffix}" if language and suffix else ""
        if not language and suffix:
            suffix_text = f" {suffix}"
        return f"{title} ({year}){language}{suffix_text}"

    def get_files_safe(self, folder_path: Path) -> List[Path]:
        files = []
        try:
            for item_name in os.listdir(str(folder_path)):
                item_lower = item_name.lower()
                if any(item_lower.endswith(ext) for ext in self.video_extensions):
                    files.append(folder_path / item_name)
        except Exception as e:
            self.logger.error(f"❌ Error reading folder {folder_path.name}: {str(e)}")
        return files

    def process_folder(self, folder_path: Path, dry_run: bool = False):
        self.logger.info(f"\n{'='*70}")
        self.logger.info(f"📁 Scanning Folder: {folder_path.name}")

        folder_has_year = False
        folder_year = None
        source_folder_name = None

        if self.options.get("auto_folder_year"):
            folder_has_year, folder_year, source_folder_name = (
                self.find_year_in_hierarchy(folder_path)
            )
            if folder_has_year:
                self.logger.info(
                    f" Auto-detected Year '{folder_year}' from parent folder: '{source_folder_name}'"
                )
            else:
                self.logger.info(f"⚠️ No year found in folder hierarchy.")
        else:
            self.logger.info(f"️ Auto folder year detection disabled")

        files = self.get_files_safe(folder_path)
        if not files:
            self.logger.info(f"   ️ No video files found")
            return

        self.logger.info(f"   📊 Found {len(files)} video file(s)")

        if self.options.get("process_subfolders"):
            try:
                rel_path = folder_path.relative_to(self.source_path)
                target_folder = self.output_path / rel_path
            except ValueError:
                target_folder = self.output_path / folder_path.name
        else:
            target_folder = self.output_path

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

                if folder_has_year:
                    year_to_use = folder_year
                    self.logger.info(
                        f"   ✅ [{idx}/{len(files)}] Applying hierarchy year ({year_to_use})"
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
                            # ✅ FIX: Use the callback from options instead of calling a non-existent method
                            gui_callback = self.options.get("gui_input_callback")
                            if gui_callback:
                                user_input_year = gui_callback(folder_path.name)
                            else:
                                user_input_year = self.get_user_input_year(
                                    folder_path.name
                                )

                        if user_input_year == "quit":
                            return "quit"
                        elif user_input_year == "skip_all":
                            self.skip_all_missing_years = True
                            user_input_year = None

                        if user_input_year is None:
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
                            f"   ⏭️ [{idx}/{len(files)}] Skipped (No year & input disabled)"
                        )
                        self.skipped_count += 1
                        self.report_progress()
                        continue

                ext = file_path.suffix
                new_name = f"{self.format_output_name(current_name, year_to_use)}{ext}"
                new_path = target_folder / new_name

                if dry_run:
                    self.logger.info(f"   🔍 [DRY RUN] Would rename to: {new_name}")
                    self.processed_count += 1
                else:
                    try:
                        src_long = get_long_path(str(file_path))
                        dst_long = get_long_path(str(new_path))
                        shutil.copy2(src_long, dst_long)
                        os.remove(src_long)
                        self.logger.info(f"   ✅ [{idx}/{len(files)}] Success")
                        self.processed_count += 1
                    except Exception as e:
                        self.logger.error(f"   ❌ [{idx}/{len(files)}] Error: {str(e)}")
                        self.error_count += 1

                self.report_progress()
            except Exception as e:
                self.logger.error(f"    Error processing {file_path.name}: {str(e)}")
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

    def get_user_input_year(self, folder_name: str) -> Optional[str]:
        print(f"\n{'='*70}")
        print(f"📂 Folder: {folder_name}")
        year = input("Enter release year (or 'skip' / 'quit'): ").strip()
        if year.lower() in ["skip", "s", ""]:
            return None
        elif year.lower() in ["quit", "q", "exit"]:
            return "quit"
        elif self.year_pattern.fullmatch(year):
            return year
        return None

    def scan_and_process(self, dry_run: bool = False):
        if not self.source_path.exists():
            self.logger.error(f"❌ Source path does not exist: {self.source_path}")
            return
        if not dry_run:
            try:
                self.output_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                self.logger.error(f" Cannot create output directory: {str(e)}")
                return

        self.logger.info(f"📂 Output will be saved to: {self.output_path}")

        self.total_files = 0
        self.completed_files = 0
        self.skip_all_missing_years = False
        self.processing_start_time = time.time()

        try:
            for root, dirs, files in os.walk(str(self.source_path)):
                for file_name in files:
                    if file_name.lower().endswith(tuple(self.video_extensions)):
                        self.total_files += 1
        except Exception as e:
            self.logger.error(f"❌ Error counting files: {str(e)}")

        self.logger.info(f"📊 Total video files found: {self.total_files}")
        if self.progress_callback:
            self.progress_callback(0, self.total_files, self.processing_start_time)

        folders_processed = 0
        try:
            for root, dirs, files in os.walk(str(self.source_path)):
                root_path = Path(root)
                has_videos = any(
                    f.lower().endswith(tuple(self.video_extensions)) for f in files
                )
                if not has_videos:
                    continue
                result = self.process_folder(root_path, dry_run)
                if result == "quit":
                    break
                folders_processed += 1
                if not self.options.get("process_subfolders"):
                    break
        except Exception as e:
            self.logger.error(f"❌ Error during scan: {str(e)}")

        self.print_summary(folders_processed)

    def print_summary(self, folders_processed: int):
        summary = f"""
{'='*70}
 FINAL SUMMARY
{'='*70}
✅ Folders Scanned  : {folders_processed}
📝 Files Renamed    : {self.processed_count}
️  Files Skipped    : {self.skipped_count}
❌ Errors           : {self.error_count}
{'='*70}
"""
        self.logger.info(summary)


class AnimeOrganizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎬 Advanced File Organizer Pro (v3.1)")
        self.root.geometry("1100x850")
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

        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=10)
        ttk.Label(
            title_frame,
            text="🎬 Advanced File Organizer Pro",
            font=("Helvetica", 20, "bold"),
        ).pack(side=tk.LEFT)
        ttk.Label(
            title_frame,
            text="v3.1 (GUI Input Fix)",
            font=("Helvetica", 10),
            foreground="gray",
        ).pack(side=tk.LEFT, padx=10)

        path_frame = ttk.LabelFrame(main_frame, text=" Folder Selection", padding="15")
        path_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=10)
        path_frame.columnconfigure(1, weight=1)

        ttk.Label(
            path_frame, text="Source Folder:", font=("Helvetica", 10, "bold")
        ).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.source_var = tk.StringVar(value=r"R:\Anime1")
        ttk.Entry(path_frame, textvariable=self.source_var, width=70).grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5
        )
        ttk.Button(path_frame, text="📂 Browse", command=self.browse_source).grid(
            row=0, column=2, padx=5
        )

        ttk.Label(
            path_frame, text="Output Folder:", font=("Helvetica", 10, "bold")
        ).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.output_var = tk.StringVar(value=r"R:\Anime1_Organized")
        ttk.Entry(path_frame, textvariable=self.output_var, width=70).grid(
            row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5
        )
        ttk.Button(path_frame, text="📁 Browse", command=self.browse_output).grid(
            row=1, column=2, padx=5
        )

        filters_frame = ttk.LabelFrame(
            main_frame, text="⚙️ Advanced Filters & Options", padding="15"
        )
        filters_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=10)
        filters_frame.columnconfigure(0, weight=1)
        filters_frame.columnconfigure(1, weight=1)

        col1_frame = ttk.Frame(filters_frame)
        col1_frame.grid(row=0, column=0, sticky=tk.W, padx=10)
        self.dry_run_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            col1_frame, text="🔍 Dry Run (Preview only)", variable=self.dry_run_var
        ).pack(anchor=tk.W, pady=3)
        self.auto_folder_year_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            col1_frame,
            text=" Auto-detect year (Folder & Parents)",
            variable=self.auto_folder_year_var,
        ).pack(anchor=tk.W, pady=3)
        self.skip_existing_year_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            col1_frame,
            text="⏭️ Skip files that already have year",
            variable=self.skip_existing_year_var,
        ).pack(anchor=tk.W, pady=3)
        self.ask_user_input_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            col1_frame,
            text="❓ Ask user for year if not found",
            variable=self.ask_user_input_var,
        ).pack(anchor=tk.W, pady=3)

        col2_frame = ttk.Frame(filters_frame)
        col2_frame.grid(row=0, column=1, sticky=tk.W, padx=10)
        self.process_subfolders_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            col2_frame,
            text="📂 Process all subfolders recursively",
            variable=self.process_subfolders_var,
        ).pack(anchor=tk.W, pady=3)
        self.create_log_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            col2_frame, text="📄 Create detailed log file", variable=self.create_log_var
        ).pack(anchor=tk.W, pady=3)
        self.auto_close_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            col2_frame,
            text="🚪 Auto-close after completion",
            variable=self.auto_close_var,
        ).pack(anchor=tk.W, pady=3)

        ext_frame = ttk.Frame(filters_frame)
        ext_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        ttk.Label(
            ext_frame,
            text="Custom Extensions (comma-separated):",
            font=("Helvetica", 9),
        ).pack(side=tk.LEFT)
        self.extensions_var = tk.StringVar(value=".mp4, .mkv, .avi")
        ttk.Entry(ext_frame, textvariable=self.extensions_var, width=60).pack(
            side=tk.LEFT, padx=5
        )

        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=3, column=0, pady=15)
        self.start_btn = ttk.Button(
            btn_frame, text="▶️ Start Processing", command=self.start_processing
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn = ttk.Button(
            btn_frame, text="⏹️ Stop", command=self.stop_processing, state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑️ Clear Log", command=self.clear_log).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(btn_frame, text="📂 Open Output", command=self.open_output).pack(
            side=tk.LEFT, padx=5
        )

        progress_frame = ttk.LabelFrame(main_frame, text=" Progress", padding="10")
        progress_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=10)
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

        log_frame = ttk.LabelFrame(main_frame, text="📋 Activity Log", padding="10")
        log_frame.grid(row=5, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.log_text = scrolledtext.ScrolledText(
            log_frame, height=18, width=120, wrap=tk.WORD, font=("Consolas", 9)
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.log_text.tag_config("INFO", foreground="gray")
        self.log_text.tag_config("SUCCESS", foreground="green")
        self.log_text.tag_config("WARNING", foreground="orange")
        self.log_text.tag_config("ERROR", foreground="red")
        main_frame.rowconfigure(5, weight=1)

    def browse_source(self):
        path = filedialog.askdirectory(initialdir="R:\\", title="Select Source Folder")
        if path:
            self.source_var.set(path)

    def browse_output(self):
        path = filedialog.askdirectory(initialdir="R:\\", title="Select Output Folder")
        if path:
            self.output_var.set(path)

    def log_message(self, message: str, tag="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] ", "INFO")
        self.log_text.insert(tk.END, f"{message}\n", tag)
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def clear_log(self):
        self.log_text.delete(1.0, tk.END)

    def open_output(self):
        output_path = self.output_var.get()
        if Path(output_path).exists():
            os.startfile(output_path)
        else:
            messagebox.showinfo("Info", "Output folder doesn't exist yet")

    def get_user_input_year_gui(self, folder_name: str) -> Optional[str]:
        """Get the release year from a GUI dialog."""
        result = {"year": None}
        dialog_ready = threading.Event()

        def show_dialog():
            dialog = tk.Toplevel(self.root)
            dialog.title("Enter Release Year")
            dialog.geometry("400x150")
            dialog.transient(self.root)
            dialog.grab_set()

            ttk.Label(
                dialog, text=f"Folder: {folder_name[:60]}...", font=("Helvetica", 9)
            ).pack(pady=10, padx=10)

            year_var = tk.StringVar()
            year_entry = ttk.Entry(
                dialog, textvariable=year_var, width=20, font=("Helvetica", 12)
            )
            year_entry.pack(pady=5)
            year_entry.focus()

            def on_submit():
                year = year_var.get().strip()
                if year.lower() in ["skip", "s", ""]:
                    result["year"] = None
                elif self.year_pattern.fullmatch(year):
                    result["year"] = year
                else:
                    messagebox.showerror(
                        "Invalid",
                        "Please enter a valid year (e.g., 2006, 2024) or 'skip'",
                        parent=dialog,
                    )
                    return
                dialog.destroy()

            def on_skip():
                result["year"] = None
                dialog.destroy()

            def on_skip_all():
                result["year"] = "skip_all"
                dialog.destroy()

            btn_frame = ttk.Frame(dialog)
            btn_frame.pack(pady=10)
            ttk.Button(btn_frame, text="Submit", command=on_submit).pack(
                side=tk.LEFT, padx=5
            )
            ttk.Button(btn_frame, text="Skip", command=on_skip).pack(
                side=tk.LEFT, padx=5
            )
            ttk.Button(btn_frame, text="Skip All", command=on_skip_all).pack(
                side=tk.LEFT, padx=5
            )

            dialog.protocol("WM_DELETE_WINDOW", on_skip)
            dialog.wait_window()
            dialog_ready.set()

        if threading.current_thread() is threading.main_thread():
            show_dialog()
        else:
            self.root.after(0, show_dialog)
            dialog_ready.wait()

        return result["year"]

    def get_options(self) -> dict:
        return {
            "dry_run": self.dry_run_var.get(),
            "auto_folder_year": self.auto_folder_year_var.get(),
            "skip_existing_year": self.skip_existing_year_var.get(),
            "ask_user_input": self.ask_user_input_var.get(),
            "process_subfolders": self.process_subfolders_var.get(),
            "create_log": self.create_log_var.get(),
            "auto_close": self.auto_close_var.get(),
            "custom_extensions": self.extensions_var.get(),
            "progress_callback": self.update_progress,
            "gui_input_callback": self.get_user_input_year_gui,
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

        thread = threading.Thread(target=self.run_processing, daemon=True)
        thread.start()

    def run_processing(self):
        try:
            source_path = self.source_var.get()
            output_path = self.output_var.get()
            options = self.get_options()
            self.organizer = AnimeFileOrganizer(source_path, output_path, options)

            class GUILogHandler(logging.Handler):
                def __init__(self, gui):
                    super().__init__()
                    self.gui = gui

                def emit(self, record):
                    try:
                        msg = self.format(record)
                        if "✅" in msg or "Success" in msg:
                            self.gui.log_message(msg, "SUCCESS")
                        elif "⚠️" in msg or "Skip" in msg:
                            self.gui.log_message(msg, "WARNING")
                        elif "❌" in msg or "Error" in msg:
                            self.gui.log_message(msg, "ERROR")
                        else:
                            self.gui.log_message(msg, "INFO")
                    except:
                        pass

            handler = GUILogHandler(self)
            handler.setFormatter(logging.Formatter("%(message)s"))
            self.organizer.logger.addHandler(handler)
            self.organizer.scan_and_process(dry_run=options["dry_run"])
            self.root.after(0, self.finish_processing)
        except Exception as e:
            self.root.after(0, lambda: self.error_processing(str(e)))

    def finish_processing(self):
        self.is_processing = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.progress_bar.configure(value=100)
        self.status_var.set("✅ Processing completed!")
        if self.organizer:
            msg = (
                f"✅ Folders: {self.organizer.processed_count} | "
                f"📝 Renamed: {self.organizer.processed_count} | "
                f"️ Skipped: {self.organizer.skipped_count} | "
                f"❌ Errors: {self.organizer.error_count}"
            )
            self.log_message("=" * 70, "INFO")
            self.log_message(msg, "SUCCESS")
            messagebox.showinfo("✅ Complete!", f"Processing finished!\n\n{msg}")
            if self.auto_close_var.get():
                self.root.after(2000, self.root.destroy)

    def update_progress(self, completed: int, total: int, start_time: float):
        try:
            if total > 0:
                percent = (completed / total) * 100
            else:
                percent = 0
            elapsed = max(time.time() - start_time, 0) if start_time else 0
            if completed > 0 and elapsed > 0:
                remaining = elapsed * (total - completed) / completed
                eta_text = self.format_duration(remaining)
            else:
                eta_text = "calculating..."
            self.root.after(
                0,
                self.apply_progress_update,
                completed,
                total,
                percent,
                self.format_duration(elapsed),
                eta_text,
            )
        except:
            pass

    def apply_progress_update(
        self,
        completed: int,
        total: int,
        percent: float,
        elapsed_text: str,
        eta_text: str,
    ):
        try:
            self.progress_bar.configure(value=percent)
            self.status_var.set(
                f"🔄 {percent:.1f}% ({completed}/{total}) | Elapsed: {elapsed_text} | Remaining: {eta_text}"
            )
        except:
            pass

    @staticmethod
    def format_duration(seconds: float) -> str:
        total_seconds = max(0, int(seconds))
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def error_processing(self, err):
        self.is_processing = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.progress_bar.configure(value=0)
        self.status_var.set("❌ Error occurred")
        self.log_message(f"❌ Error: {err}", "ERROR")
        messagebox.showerror("Error", f"An error occurred:\n{err}")

    def stop_processing(self):
        self.is_processing = False
        self.status_var.set("⏹️ Stopped by user")
        self.log_message("⏹️ Processing stopped by user", "WARNING")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)


_instance_mutex = None


def acquire_single_instance() -> bool:
    global _instance_mutex

    if sys.platform != "win32":
        return True

    from ctypes import windll

    _instance_mutex = windll.kernel32.CreateMutexW(
        None, False, "AnimeOrganizerPro_SingleInstance"
    )
    if not _instance_mutex:
        return True

    if windll.kernel32.GetLastError() == 183:
        windll.kernel32.CloseHandle(_instance_mutex)
        _instance_mutex = None
        return False

    return True


def main():
    if not acquire_single_instance():
        root = tk.Tk()
        root.withdraw()
        messagebox.showwarning(
            "Already Running",
            "Anime Organizer Pro is already running. Please use the existing window.",
        )
        root.destroy()
        return

    root = tk.Tk()
    try:
        from ctypes import windll

        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    app = AnimeOrganizerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
