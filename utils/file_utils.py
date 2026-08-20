# utils/file_utils.py
import sys
import os
import shutil


def get_long_path(path: str) -> str:
    """Adds \\?\ prefix to support paths longer than 260 characters on Windows."""
    if sys.platform == "win32" and not path.startswith("\\\\?\\"):
        path = path.replace("/", "\\")
        return f"\\\\?\\{path}"
    return path


def safe_copy_and_remove(src: str, dst: str):
    """Safely copies a file and removes the original, handling long paths."""
    src_long = get_long_path(src)
    dst_long = get_long_path(dst)
    os.makedirs(os.path.dirname(dst_long), exist_ok=True)
    shutil.copy2(src_long, dst_long)
    os.remove(src_long)
