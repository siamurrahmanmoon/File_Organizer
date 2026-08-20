# utils/metadata_extractor.py
import subprocess
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("AnimeOrganizer")


def extract_metadata_ffprobe(file_path: str) -> Optional[Dict[str, Any]]:
    """Extracts metadata using ffprobe. Returns a dictionary or None if failed."""
    try:
        command = [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            file_path,
        ]
        result = subprocess.run(command, capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            logger.warning(f"ffprobe failed for {file_path}: {result.stderr}")
            return None
    except FileNotFoundError:
        logger.error(
            "❌ ffprobe not found. Please install FFmpeg and ensure it's in your PATH."
        )
        return None
    except subprocess.TimeoutExpired:
        logger.warning(f"⚠️ ffprobe timed out for {file_path}")
        return None
    except Exception as e:
        logger.error(f"❌ Error extracting metadata for {file_path}: {e}")
        return None
