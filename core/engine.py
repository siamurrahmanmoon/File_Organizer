"""
core/engine.py - Master Processing Engine for Smart File Organizer Pro.
"""

import os
import re
import time
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any, Callable

from config import OrganizerConfig, get_default_config
from core.security import SecurityValidator
from core.parser import SmartMediaParser
from core.template_engine import TemplateEngine
from core.duplicate_detector import DuplicateDetector
from core.filter_engine import FilterEngine
from core.quality_control import QualityController
from core.subtitle_manager import SubtitleManager
from core.rollback_manager import RollbackManager
from core.analytics import AnalyticsTracker
from core.notifier import Notifier
from utils.file_utils import (
    safe_move,
    safe_copy,
    get_unique_destination_path,
    safe_file_size,
    safe_exists,
    get_long_path,
)
from utils.metadata_extractor import extract_metadata_ffprobe
from utils.metadata_parser import get_smart_metadata, format_metadata_tags
from utils.logger_utils import setup_logger

logger = logging.getLogger("AnimeOrganizer")


class AnimeFileOrganizer:
    """
    Enterprise-grade, modular file organizer engine orchestrating all pipeline features:
    Metadata extraction, AI pattern parsing, custom templates, duplicate management,
    granular filtering, quality control, sidecar subtitles, journaling, and analytics.
    """

    def __init__(
        self,
        source_path: str,
        output_path: str,
        options: Optional[Dict[str, Any]] = None,
        config: Optional[OrganizerConfig] = None,
    ):
        if config:
            self.config = config
            if source_path:
                self.config.source_path = source_path
            if output_path:
                self.config.output_path = output_path
        else:
            self.config = get_default_config()
            self.config.source_path = source_path
            self.config.output_path = output_path
            if options:
                for k, v in options.items():
                    if hasattr(self.config, k):
                        setattr(self.config, k, v)

        self.source_path = Path(self.config.source_path)
        self.output_path = Path(self.config.output_path)
        self.options = options or self.config.to_dict()

        self.logger = setup_logger(
            log_to_file=self.options.get("create_log", True),
            log_dir=self.config.logs_path,
        )
        self.rollback_mgr = (
            RollbackManager(db_path=self.config.journal_db_path)
            if self.config.enable_rollback
            else None
        )
        self.duplicate_detector = (
            DuplicateDetector(quarantine_dir=self.config.quarantine_path)
            if self.config.enable_duplicates
            else None
        )
        self.analytics = (
            AnalyticsTracker(reports_dir=self.config.reports_path)
            if self.config.enable_analytics
            else None
        )

        self.progress_callback: Optional[Callable[[int, int, float], None]] = (
            self.options.get("progress_callback")
        )
        self.gui_input_callback = self.options.get("gui_input_callback")

        self.total_files = 0
        self.completed_files = 0
        self.processed_count = 0
        self.skipped_count = 0
        self.error_count = 0
        self.duplicate_count = 0
        self.processing_start_time = None
        self.skip_all_missing_years = False
        self.session_id = None

        self.year_pattern = re.compile(r"\b(19|20)\d{2}\b")
        self.video_extensions = set(self.config.video_extensions)

        if self.config.custom_extensions:
            ext_list = self.config.custom_extensions.split(",")
            self.video_extensions = {
                (
                    e.strip().lower()
                    if e.strip().startswith(".")
                    else f".{e.strip().lower()}"
                )
                for e in ext_list
                if e.strip()
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

    def plan_file_rename(
        self, file_path: Path, folder_year: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Runs the parsing and templating pipeline without moving the file.
        Returns complete analysis dictionary for preview / execution.
        """
        current_name = file_path.name
        parsed_info = SmartMediaParser.parse_filename(
            current_name, file_path.parent.name
        )

        # Year determination: fall back to all ancestors when the caller did
        # not already provide a folder year (for example, in preview mode).
        hierarchy_year = folder_year
        if not hierarchy_year and self.config.auto_folder_year:
            has_year, detected_year, detected_from = self.find_year_in_hierarchy(
                file_path.parent
            )
            if has_year:
                hierarchy_year = detected_year
                self.logger.info(
                    f"🔍 Auto-detected Year '{detected_year}' from: '{detected_from}'"
                )

        year_to_use = hierarchy_year or parsed_info.get("Year") or ""

        # Metadata extraction
        metadata_tags: Dict[str, Any] = {}
        if self.config.enable_metadata:
            meta_options = {
                k: v for k, v in self.options.items() if k.startswith("include_")
            }
            if any(meta_options.values()) or self.config.include_resolution:
                try:
                    raw_meta = extract_metadata_ffprobe(str(file_path))
                    if raw_meta:
                        metadata_tags = get_smart_metadata(str(file_path), raw_meta)
                except Exception as e:
                    self.logger.debug(f"Metadata probe notice for {current_name}: {e}")

        # Combine parsed info with stream metadata
        merged_context = dict(parsed_info)
        if year_to_use:
            merged_context["Year"] = year_to_use
        for k, v in metadata_tags.items():
            if v:
                merged_context[k] = v

        # Evaluate target name via TemplateEngine
        template_str = (
            self.config.naming_template
            or "{Title} ({Year}) [{Languages}] [{Resolution}] - S{Season}E{Episode}"
        )
        rendered_name = TemplateEngine.render(
            template_str, merged_context, extension=file_path.suffix
        )

        return {
            "source_path": file_path,
            "source_name": current_name,
            "target_name": rendered_name,
            "parsed_info": merged_context,
            "year": year_to_use,
            "has_existing_year": bool(parsed_info.get("Year")),
        }

    def process_file(
        self,
        file_path: Path,
        target_folder: Path,
        folder_year: Optional[str] = None,
        dry_run: bool = False,
    ) -> str:
        """Processes an individual video file through the complete pipeline."""
        current_name = file_path.name

        # 1. Quality Control
        if self.config.enable_quality_control and self.config.skip_incomplete_downloads:
            is_valid, reason = QualityController.check_file_integrity(file_path)
            if not is_valid:
                self.logger.warning(f"   ⚠️ Skipping {current_name}: {reason}")
                if self.analytics:
                    self.analytics.record_file(
                        current_name, "", "skipped", error_msg=reason
                    )
                self.skipped_count += 1
                return "skipped"

        # 2. Plan Rename & Parse Metadata
        plan = self.plan_file_rename(file_path, folder_year)
        parsed_info = plan["parsed_info"]
        year_to_use = plan["year"]
        new_name = plan["target_name"]

        # 3. Filtering Engine Check
        if self.config.enable_filters:
            passes_filter, filter_reason = FilterEngine.evaluate(
                file_path, parsed_info, self.config
            )
            if not passes_filter:
                self.logger.info(
                    f"   ⏭️ Filter Excluded ({current_name}): {filter_reason}"
                )
                if self.analytics:
                    self.analytics.record_file(
                        current_name, "", "skipped", error_msg=filter_reason
                    )
                self.skipped_count += 1
                return "filtered"

        # 4. Year Decision Tree & User Prompt if Missing
        if not year_to_use:
            if self.config.ask_user_input:
                if self.skip_all_missing_years:
                    self.skipped_count += 1
                    return "skipped"
                if self.gui_input_callback:
                    year_input = self.gui_input_callback(file_path.parent.name)
                else:
                    year_input = input(f"Enter year for {file_path.name}: ")

                if year_input == "skip_all":
                    self.skip_all_missing_years = True
                    self.skipped_count += 1
                    return "skipped"
                elif year_input and self.year_pattern.fullmatch(year_input.strip()):
                    year_to_use = year_input.strip()
                    parsed_info["Year"] = year_to_use
                    new_name = TemplateEngine.render(
                        self.config.naming_template,
                        parsed_info,
                        extension=file_path.suffix,
                    )
                else:
                    self.logger.info(f"   ⏭️ Skipped {current_name} (No year provided)")
                    self.skipped_count += 1
                    return "skipped"
            else:
                self.logger.info(f"   ⏭️ Skipped {current_name} (No year detected)")
                self.skipped_count += 1
                return "skipped"

        # 5. Duplicate Detection
        file_size = safe_file_size(file_path)
        file_hash = ""
        if self.config.enable_duplicates and self.duplicate_detector:
            file_hash = self.duplicate_detector.calculate_file_hash(
                file_path, algorithm=self.config.hash_algorithm
            )
            content_sig = self.duplicate_detector.get_content_signature(parsed_info)

            # Check if identical hash or signature exists
            is_dup = False
            if file_hash in self.duplicate_detector.hash_index:
                is_dup = True
            elif content_sig in self.duplicate_detector.signature_index:
                is_dup = True

            if is_dup:
                self.logger.warning(f"   🔍 Duplicate detected: {current_name}")
                self.duplicate_count += 1
                if self.config.duplicate_action == "quarantine" and not dry_run:
                    q_dest = self.duplicate_detector.quarantine_file(file_path)
                    self.logger.info(f"   📦 Moved duplicate to quarantine: {q_dest}")
                    if self.rollback_mgr and self.session_id:
                        self.rollback_mgr.log_operation(
                            self.session_id,
                            str(file_path),
                            str(q_dest),
                            "quarantine",
                            file_hash,
                        )
                    if self.analytics:
                        self.analytics.record_file(
                            current_name,
                            str(q_dest),
                            "duplicate",
                            file_size,
                            parsed_info,
                        )
                    return "duplicate"
                elif self.config.duplicate_action == "skip":
                    self.skipped_count += 1
                    return "duplicate"

            # Index this file
            if file_hash:
                self.duplicate_detector.hash_index.setdefault(file_hash, []).append(
                    file_path
                )
            self.duplicate_detector.signature_index.setdefault(content_sig, []).append(
                file_path
            )

        # 6. Execute Rename/Move or Dry Run
        target_path = target_folder / new_name
        if self.config.safe_mode and not dry_run:
            target_path = get_unique_destination_path(target_path)

        # Discover sidecar subtitles
        subtitles = []
        if self.config.enable_subtitles:
            subtitles = SubtitleManager.find_matching_subtitles(
                file_path, self.config.subtitle_extensions
            )

        if dry_run:
            self.logger.info(f"   🔍 [DRY RUN] Would rename to: {target_path.name}")
            if subtitles:
                self.logger.info(
                    f"      📄 Paired with {len(subtitles)} subtitle sidecar(s)"
                )
            self.processed_count += 1
            if self.analytics:
                self.analytics.record_file(
                    current_name, target_path.name, "success", file_size, parsed_info
                )
            return "dry_run"

        try:
            target_folder.mkdir(parents=True, exist_ok=True)
            if self.config.move_files:
                safe_move(str(file_path), str(target_path))
                op_type = "move"
            else:
                safe_copy(str(file_path), str(target_path))
                op_type = "copy"

            self.logger.info(f"   ✅ Renamed to: {target_path.name}")

            # Synchronize sidecar subtitles
            if subtitles:
                synced_subs = SubtitleManager.sync_subtitle_organization(
                    subtitles,
                    target_path.stem,
                    target_folder,
                    move_file=self.config.move_files,
                )
                self.logger.info(
                    f"      📄 Organized {len(synced_subs)} subtitle file(s)"
                )

            # Record in SQLite Rollback Journal
            if self.rollback_mgr and self.session_id:
                self.rollback_mgr.log_operation(
                    self.session_id,
                    str(file_path),
                    str(target_path),
                    op_type,
                    file_hash,
                )

            self.processed_count += 1
            if self.analytics:
                self.analytics.record_file(
                    current_name, target_path.name, "success", file_size, parsed_info
                )
            return "success"

        except Exception as e:
            self.logger.error(f"   ❌ Error moving {current_name}: {e}")
            self.error_count += 1
            if self.analytics:
                self.analytics.record_file(
                    current_name, "", "error", file_size, parsed_info, str(e)
                )
            return "error"

    def scan_and_process(self, dry_run: Optional[bool] = None) -> Dict[str, Any]:
        """Traverses the source directory and processes all matching media files."""
        if dry_run is None:
            dry_run = self.config.dry_run

        if not safe_exists(self.source_path):
            self.logger.error(f"❌ Source path does not exist: {self.source_path}")
            return {"error": "Source path does not exist"}

        # Collect files
        all_video_files: List[Tuple[Path, Path]] = []
        for root, _, files in os.walk(str(self.source_path)):
            root_path = Path(root)
            for f in files:
                if any(f.lower().endswith(ext) for ext in self.video_extensions):
                    all_video_files.append((root_path / f, root_path))
            if not self.config.process_subfolders:
                break

        self.total_files = len(all_video_files)
        self.completed_files = 0
        self.processing_start_time = time.time()

        self.logger.info(
            f"\n{'='*70}\n🚀 Found {self.total_files} media files to process.\n{'='*70}"
        )

        if self.analytics:
            self.analytics.reset()
            self.analytics.total_files = self.total_files

        if self.rollback_mgr and not dry_run:
            self.session_id = self.rollback_mgr.start_session(
                str(self.source_path), str(self.output_path), self.total_files
            )

        if self.progress_callback:
            self.progress_callback(0, self.total_files, self.processing_start_time)

        # Process each folder
        for file_path, folder_path in all_video_files:
            folder_has_year, folder_year, _ = (False, None, None)
            if self.config.auto_folder_year:
                folder_has_year, folder_year, _ = self.find_year_in_hierarchy(
                    folder_path
                )

            rel_path = (
                folder_path.relative_to(self.source_path)
                if self.config.process_subfolders
                else Path(folder_path.name)
            )
            target_folder = self.output_path / rel_path

            self.process_file(file_path, target_folder, folder_year, dry_run=dry_run)

            self.completed_files += 1
            if self.progress_callback:
                self.progress_callback(
                    self.completed_files, self.total_files, self.processing_start_time
                )

        # Complete session
        if self.rollback_mgr and self.session_id and not dry_run:
            self.rollback_mgr.complete_session(
                self.session_id, status="completed", error_count=self.error_count
            )

        summary = (
            self.analytics.get_summary()
            if self.analytics
            else {
                "processed": self.processed_count,
                "skipped": self.skipped_count,
                "duplicates": self.duplicate_count,
                "errors": self.error_count,
            }
        )

        # Auto export reports
        if self.analytics and not dry_run:
            self.analytics.export_csv()
            self.analytics.export_json()
            self.analytics.export_html()

        # Send Notifications
        if self.config.enable_notifications and not dry_run:
            Notifier.send_desktop_notification(
                "Anime Organizer Pro",
                f"Completed: {self.processed_count} processed, {self.skipped_count} skipped, {self.error_count} errors.",
            )
            if self.config.discord_webhook_url:
                Notifier.send_discord_webhook(self.config.discord_webhook_url, summary)
            if self.config.telegram_bot_token and self.config.telegram_chat_id:
                Notifier.send_telegram_message(
                    self.config.telegram_bot_token,
                    self.config.telegram_chat_id,
                    f"🎬 *Anime Organizer Pro Finished*\n✅ Processed: {self.processed_count}\n⏭️ Skipped: {self.skipped_count}\n❌ Errors: {self.error_count}",
                )

        return summary
