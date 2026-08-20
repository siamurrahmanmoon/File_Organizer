# utils/metadata_extractor.py
import json
import logging
from typing import Dict, Any, Optional
from utils.ffmpeg_installer import run_ffprobe

logger = logging.getLogger("AnimeOrganizer")


def extract_metadata_ffprobe(file_path: str) -> Optional[Dict[str, Any]]:
    """Extracts metadata using ffprobe (local or system)."""
    try:
        result = run_ffprobe(
            [
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                file_path,
            ],
            timeout=30,
        )

        if result is None:
            logger.error("❌ ffprobe not available. Please install FFmpeg.")
            return None

        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            logger.warning(f"ffprobe failed for {file_path}: {result.stderr}")
            return None
    except Exception as e:
        logger.error(f"❌ Error extracting metadata for {file_path}: {e}")
        return None
