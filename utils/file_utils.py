"""
utils/file_utils.py - Cross-platform file operations with long path (>260 chars) & collision protection.
"""

import sys
import os
import shutil
from pathlib import Path
from typing import Tuple, Any, Optional


def get_long_path(path: Any) -> str:
    """
    Adds \\?\\ prefix to support paths longer than 260 characters on Windows.
    Handles relative paths, UNC network shares, and already formatted paths.
    """
    path_str = str(path)
    if sys.platform != "win32":
        return path_str

    if path_str.startswith("\\\\?\\"):
        return path_str

    abs_path = os.path.abspath(path_str)
    if abs_path.startswith("\\\\?\\"):
        return abs_path

    # UNC path format: \\server\share -> \\?\UNC\server\share
    if abs_path.startswith("\\\\"):
        return f"\\\\?\\UNC\\{abs_path[2:]}"

    return f"\\\\?\\{abs_path}"


def safe_stat(path: Any) -> os.stat_result:
    """Returns os.stat with Windows long path support (>260 chars)."""
    return os.stat(get_long_path(path))


def safe_file_size(path: Any) -> int:
    """Returns file size in bytes with Windows long path support."""
    try:
        return safe_stat(path).st_size
    except Exception:
        return 0


def safe_exists(path: Any) -> bool:
    """Checks if file or folder exists with Windows long path support."""
    try:
        return os.path.exists(get_long_path(path))
    except Exception:
        return False


def safe_open(path: Any, mode: str = "r", **kwargs):
    """Opens a file with Windows long path support."""
    return open(get_long_path(path), mode, **kwargs)


def get_unique_destination_path(target_path: Path) -> Path:
    """
    If the target file already exists, appends _1, _2, etc. to prevent accidental overwrites.
    """
    if not safe_exists(target_path):
        return target_path

    parent = target_path.parent
    stem = target_path.stem
    suffix = target_path.suffix
    counter = 1

    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if not safe_exists(candidate):
            return candidate
        counter += 1


def safe_copy(src: Any, dst: Any):
    """Safely copies a file, creating parent directories if needed."""
    src_long = get_long_path(src)
    dst_long = get_long_path(dst)
    dst_parent = os.path.dirname(dst_long)
    if dst_parent:
        os.makedirs(dst_parent, exist_ok=True)
    shutil.copy2(src_long, dst_long)


def safe_move(src: Any, dst: Any):
    """Safely moves a file across drives or directories, handling long paths."""
    src_long = get_long_path(src)
    dst_long = get_long_path(dst)
    dst_parent = os.path.dirname(dst_long)
    if dst_parent:
        os.makedirs(dst_parent, exist_ok=True)
    try:
        shutil.move(src_long, dst_long)
    except Exception:
        # Fallback to copy + remove for cross-device moves
        shutil.copy2(src_long, dst_long)
        os.remove(src_long)


def safe_delete(path: Any) -> bool:
    """Safely deletes a file if it exists."""
    try:
        p = get_long_path(path)
        if os.path.isfile(p):
            os.remove(p)
            return True
        elif os.path.isdir(p):
            shutil.rmtree(p)
            return True
    except Exception:
        pass
    return False
