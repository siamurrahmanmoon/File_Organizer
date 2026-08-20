"""
core/duplicate_detector.py - Intelligent Duplicate Detection & Quarantine System.
"""

import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from utils.file_utils import safe_move


RESOLUTION_RANKS = {
    "4K": 5,
    "2160p": 5,
    "1440p": 4,
    "1080p": 3,
    "720p": 2,
    "480p": 1,
    "360p": 0,
    "Unknown": 0,
}

CODEC_RANKS = {
    "AV1": 4,
    "x265": 3,
    "HEVC": 3,
    "x264": 2,
    "H264": 2,
    "XviD": 1,
    "DivX": 1,
}


class DuplicateDetector:
    """Detects identical or duplicate media files using hashing, size, and content similarity."""

    def __init__(self, quarantine_dir: str = "quarantine"):
        self.quarantine_dir = Path(quarantine_dir)
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)
        # Indexed by hash: hash -> List[filepath]
        self.hash_index: Dict[str, List[Path]] = {}
        # Indexed by content signature: "title_s01e05" -> List[filepath]
        self.signature_index: Dict[str, List[Path]] = {}

    @staticmethod
    def calculate_file_hash(file_path: Path, algorithm: str = "fast", chunk_size: int = 64 * 1024) -> str:
        """
        Calculates hash of a file.
        'fast': reads head (64KB), middle (64KB), and tail (64KB) along with file size.
        'sha256': full SHA-256 hash.
        'md5': full MD5 hash.
        """
        try:
            from utils.file_utils import safe_file_size, safe_open
            size = safe_file_size(file_path)
            if size == 0:
                return "empty_file_0"

            if algorithm == "fast":
                hasher = hashlib.md5()
                hasher.update(str(size).encode("utf-8"))
                with safe_open(file_path, "rb") as f:
                    # Head chunk
                    hasher.update(f.read(chunk_size))
                    # Middle chunk
                    if size > chunk_size * 2:
                        f.seek(size // 2)
                        hasher.update(f.read(chunk_size))
                    # Tail chunk
                    if size > chunk_size * 3:
                        f.seek(max(0, size - chunk_size))
                        hasher.update(f.read(chunk_size))
                return f"fast_{hasher.hexdigest()}"

            hasher = hashlib.sha256() if algorithm == "sha256" else hashlib.md5()
            with safe_open(file_path, "rb") as f:
                while chunk := f.read(chunk_size * 16):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return ""

    @staticmethod
    def get_content_signature(parsed_info: Dict[str, Any]) -> str:
        """Creates a unique content key based on Title + Season + Episode."""
        title = parsed_info.get("Title", "").lower().replace(" ", "")
        season = parsed_info.get("Season", "01")
        ep = parsed_info.get("Episode", "")
        m_type = parsed_info.get("MediaType", "Episode")
        if ep:
            return f"{title}_s{season}e{ep}_{m_type.lower()}"
        return f"{title}_{m_type.lower()}"

    @staticmethod
    def compare_quality(info1: Dict[str, Any], size1: int, info2: Dict[str, Any], size2: int) -> int:
        """
        Returns:
           1 if file1 is higher quality than file2
          -1 if file2 is higher quality than file1
           0 if quality is roughly equal
        """
        res1 = RESOLUTION_RANKS.get(info1.get("Resolution", "Unknown"), 0)
        res2 = RESOLUTION_RANKS.get(info2.get("Resolution", "Unknown"), 0)
        if res1 > res2:
            return 1
        elif res1 < res2:
            return -1

        codec1 = CODEC_RANKS.get(info1.get("VideoCodec", ""), 0)
        codec2 = CODEC_RANKS.get(info2.get("VideoCodec", ""), 0)
        if codec1 > codec2:
            return 1
        elif codec1 < codec2:
            return -1

        # Fallback to file size if resolution and codec are the same
        if size1 > size2 * 1.1:
            return 1
        elif size2 > size1 * 1.1:
            return -1

        return 0

    def quarantine_file(self, file_path: Path, reason: str = "duplicate") -> Optional[Path]:
        """Moves duplicate or corrupted file to the quarantine vault."""
        try:
            self.quarantine_dir.mkdir(parents=True, exist_ok=True)
            target = self.quarantine_dir / file_path.name
            # If target exists in quarantine, auto-increment
            stem = file_path.stem
            ext = file_path.suffix
            counter = 1
            while target.exists():
                target = self.quarantine_dir / f"{stem}_{counter}{ext}"
                counter += 1

            safe_move(str(file_path), str(target))
            return target
        except Exception:
            return None
