"""
utils/metadata_extractor.py - Extracts streams and format metadata via ffprobe.
"""

import json
import logging
from typing import Dict, Any, Optional
from utils.ffmpeg_installer import run_ffprobe

logger = logging.getLogger("AnimeOrganizer")


def extract_metadata_ffprobe(file_path: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
    """
    Extracts complete JSON metadata including video, audio, and subtitle streams using ffprobe.
    """
    try:
        result = run_ffprobe(
            [
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                "-show_error",
                file_path,
            ],
            timeout=timeout,
        )

        if result is None:
            return None

        if result.returncode == 0 and result.stdout:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError as json_err:
                logger.warning(f"Failed to parse ffprobe JSON for {file_path}: {json_err}")
                return None
        else:
            if result.stderr:
                logger.warning(f"ffprobe warning for {file_path}: {result.stderr.strip()}")
            return None
    except Exception as e:
        logger.error(f"❌ Error executing ffprobe on {file_path}: {e}")
        return None
