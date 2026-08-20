"""
core/quality_control.py - Video Quality Control & File Integrity Verification.
"""

from pathlib import Path
from typing import Tuple
from utils.ffmpeg_installer import run_ffprobe
from utils.file_utils import safe_file_size, safe_exists, get_long_path

INCOMPLETE_EXTENSIONS = {".part", ".crdownload", ".!qb", ".tmp", ".downloading"}


class QualityController:
    """Performs integrity checks and detects corrupted or incomplete video files."""

    @staticmethod
    def check_file_integrity(file_path: Path, deep_probe: bool = False) -> Tuple[bool, str]:
        """
        Validates file integrity:
        1. Checks for incomplete download extension markers (.part, .crdownload, etc.)
        2. Checks if file is 0 bytes or unreadable
        3. Optional ffprobe stream probe to detect broken container headers.
        """
        name_lower = file_path.name.lower()

        # 1. Incomplete download check
        for inc_ext in INCOMPLETE_EXTENSIONS:
            if name_lower.endswith(inc_ext) or f"{inc_ext}." in name_lower:
                return False, f"Incomplete download detected (contains {inc_ext})"

        if not safe_exists(file_path):
            return False, "File path does not exist on disk"

        try:
            size = safe_file_size(file_path)
            if size == 0:
                return False, "File is completely empty (0 bytes)"
        except Exception as e:
            return False, f"Cannot read file stat: {e}"

        # 2. Deep ffprobe stream check if requested
        if deep_probe:
            try:
                res = run_ffprobe(
                    [
                        "-v", "error",
                        "-select_streams", "v:0",
                        "-show_entries", "stream=codec_name,width,height",
                        "-of", "csv=p=0",
                        get_long_path(str(file_path))
                    ],
                    timeout=10
                )
                if res and res.returncode != 0:
                    return False, f"Stream corruption: {res.stderr.strip()[:100]}"
            except Exception as e:
                return False, f"Probe error: {e}"

        return True, "Valid"
