"""
core/security.py - Path traversal protection, Windows reserved names & filename sanitization.
"""

import re
import os
import sys
from pathlib import Path
from typing import Tuple

# Windows reserved device names
WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
}

# Illegal characters in Windows filenames
ILLEGAL_CHARS_PATTERN = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


class SecurityValidator:
    """Provides security checks and filename sanitization against vulnerabilities."""

    @staticmethod
    def sanitize_filename(filename: str, replace_with: str = "_") -> str:
        """
        Removes illegal characters and prevents Windows reserved names.
        """
        if not filename:
            return "unnamed_file"

        # 1. Replace illegal characters
        clean = ILLEGAL_CHARS_PATTERN.sub(replace_with, filename)

        # 2. Collapse whitespace
        clean = re.sub(r"\s+", " ", clean).strip(". ")

        # 3. Check for Windows reserved names
        stem = Path(clean).stem.upper()
        if stem in WINDOWS_RESERVED_NAMES:
            clean = f"Safe_{clean}"

        # 4. Limit filename length (Windows MAX_PATH limit is 260, filename max 255)
        if len(clean) > 240:
            ext = Path(clean).suffix
            stem_limit = 240 - len(ext)
            clean = clean[:stem_limit] + ext

        return clean or "unnamed_file"

    @staticmethod
    def sanitize_path(base_dir: Path, target_relative_path: str) -> Tuple[bool, Path]:
        """
        Prevents directory traversal attacks (e.g. `../../etc/passwd`).
        Ensures the resulting path is strictly within base_dir.
        """
        try:
            resolved_base = base_dir.resolve()
            # Normalize target
            target_clean = os.path.normpath(target_relative_path).lstrip("/\\")
            full_path = (resolved_base / target_clean).resolve()

            # Verify it starts with base directory
            is_safe = str(full_path).startswith(str(resolved_base))
            return is_safe, full_path
        except Exception:
            return False, base_dir

    @staticmethod
    def is_safe_path(path_str: str) -> bool:
        """Checks if a path string contains dangerous traversal indicators."""
        if not path_str:
            return False
        normalized = os.path.normpath(path_str)
        if ".." in normalized.split(os.sep):
            return False
        return True
