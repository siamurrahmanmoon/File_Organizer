"""
core/subtitle_manager.py - Sidecar Subtitle Detection & Synchronized Organization.
"""

import os
from pathlib import Path
from typing import List, Dict, Tuple
from utils.file_utils import safe_move, safe_copy

DEFAULT_SUB_EXTENSIONS = {".srt", ".ass", ".ssa", ".vtt", ".sub", ".idx"}


class SubtitleManager:
    """Finds and synchronizes sidecar subtitle files when organizing videos."""

    @staticmethod
    def find_matching_subtitles(
        video_path: Path,
        sub_extensions: set = None
    ) -> List[Path]:
        """
        Finds all subtitle files associated with a video file in the same folder.
        Matches exact stem or prefix matches like "Movie.en.srt", "Movie.forced.ass".
        """
        if sub_extensions is None:
            sub_extensions = DEFAULT_SUB_EXTENSIONS

        parent = video_path.parent
        video_stem = video_path.stem
        matching_subs = []

        try:
            for item in parent.iterdir():
                if item.is_file() and item.suffix.lower() in sub_extensions:
                    sub_name = item.name
                    # Match exact stem: VideoName.srt
                    if item.stem == video_stem:
                        matching_subs.append(item)
                    # Match prefix with language tags: VideoName.en.srt, VideoName.ja.ass
                    elif sub_name.startswith(video_stem + ".") or sub_name.startswith(video_stem + " ["):
                        matching_subs.append(item)
        except Exception:
            pass

        return matching_subs

    @staticmethod
    def sync_subtitle_organization(
        matching_subs: List[Path],
        new_video_stem: str,
        target_folder: Path,
        move_file: bool = True
    ) -> List[Tuple[Path, Path]]:
        """
        Moves/copies matching sidecar subtitles to target folder with synchronized naming.
        Preserves language suffixes (e.g. '.en.srt' -> 'NewName.en.srt').
        Returns list of (source_sub, destination_sub).
        """
        results = []
        target_folder.mkdir(parents=True, exist_ok=True)

        for sub in matching_subs:
            try:
                sub_ext = sub.suffix
                # Check for intermediate language code e.g. .en.srt
                parts = sub.name.split(".")
                lang_suffix = ""
                if len(parts) >= 3:
                    lang_tag = parts[-2]
                    if len(lang_tag) <= 5 and not lang_tag.isdigit():
                        lang_suffix = f".{lang_tag}"

                new_sub_name = f"{new_video_stem}{lang_suffix}{sub_ext}"
                dest_sub = target_folder / new_sub_name

                if move_file:
                    safe_move(str(sub), str(dest_sub))
                else:
                    safe_copy(str(sub), str(dest_sub))

                results.append((sub, dest_sub))
            except Exception:
                pass

        return results
