"""
core/filter_engine.py - Multi-Criteria Media Filtering Engine.
"""

import re
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from config import OrganizerConfig


class FilterEngine:
    """Evaluates whether a media file matches configured filter rules."""

    @staticmethod
    def evaluate(
        file_path: Path,
        parsed_info: Dict[str, Any],
        config: OrganizerConfig
    ) -> Tuple[bool, str]:
        """
        Tests file against all active filters in config.
        Returns (True, "OK") if it passes, or (False, "Reason for skip").
        """
        if not config.enable_filters:
            return True, "OK"

        try:
            from utils.file_utils import safe_file_size
            file_size_bytes = safe_file_size(file_path)
            file_size_mb = file_size_bytes / (1024 * 1024)
        except Exception:
            file_size_mb = 0.0

        # 1. File Size Filter
        if config.min_file_size_mb > 0 and file_size_mb < config.min_file_size_mb:
            return False, f"File size ({file_size_mb:.1f} MB) is below minimum ({config.min_file_size_mb} MB)"

        if config.max_file_size_mb > 0 and file_size_mb > config.max_file_size_mb:
            return False, f"File size ({file_size_mb:.1f} MB) exceeds maximum ({config.max_file_size_mb} MB)"

        # 2. Resolution Whitelist
        if config.resolution_whitelist:
            res = parsed_info.get("Resolution", "").upper()
            whitelist_upper = [r.upper() for r in config.resolution_whitelist]
            if res and res not in whitelist_upper:
                return False, f"Resolution '{res}' not in allowed list ({', '.join(config.resolution_whitelist)})"

        # 3. Codec Whitelist
        if config.codec_whitelist:
            codec = parsed_info.get("VideoCodec", "").upper()
            codec_whitelist_upper = [c.upper() for c in config.codec_whitelist]
            if codec and codec not in codec_whitelist_upper:
                return False, f"Codec '{codec}' not in allowed list ({', '.join(config.codec_whitelist)})"

        # 4. Release Group Filter
        if config.release_group_filter:
            group = parsed_info.get("ReleaseGroup", "")
            target_groups = [g.strip().lower() for g in config.release_group_filter.split(",") if g.strip()]
            if target_groups and group.lower() not in target_groups:
                return False, f"Release group '{group}' does not match filter ({config.release_group_filter})"

        # 5. Language Filter
        if config.language_filter:
            file_langs = [lang.lower() for lang in parsed_info.get("Languages", [])]
            required_langs = [l.strip().lower() for l in config.language_filter]
            if file_langs and not any(req in file_langs for req in required_langs):
                return False, f"File languages ({', '.join(parsed_info.get('Languages', []))}) do not contain required ({', '.join(config.language_filter)})"

        # 6. Year Range Filter
        year_str = parsed_info.get("Year", "")
        if year_str and year_str.isdigit():
            year_int = int(year_str)
            if not (config.min_year <= year_int <= config.max_year):
                return False, f"Year {year_int} out of range ({config.min_year}-{config.max_year})"

        # 7. Custom Regex Filter
        if config.custom_regex_filter:
            try:
                if not re.search(config.custom_regex_filter, file_path.name, re.IGNORECASE):
                    return False, f"Filename did not match custom regex: {config.custom_regex_filter}"
            except re.error as e:
                return False, f"Invalid custom regex pattern: {e}"

        return True, "OK"
