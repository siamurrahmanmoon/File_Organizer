# utils/ffmpeg_installer.py
import os
import sys
import shutil
import subprocess
import zipfile
import urllib.request
import logging
from pathlib import Path
from typing import Optional, Callable, Tuple

logger = logging.getLogger("AnimeOrganizer")

# Local bin directory (no PATH modification needed)
BIN_DIR = Path(__file__).parent.parent / "bin"
FFPROBE_PATH: Optional[Path] = None


def get_executable_name(name: str) -> str:
    """Returns executable name with .exe on Windows."""
    if sys.platform == "win32":
        return f"{name}.exe"
    return name


def get_ffprobe_path() -> Optional[Path]:
    """Returns the path to ffprobe (local bin first, then system PATH)."""
    global FFPROBE_PATH
    if FFPROBE_PATH and FFPROBE_PATH.exists():
        return FFPROBE_PATH

    # 1. Check local bin directory
    local_ffprobe = BIN_DIR / get_executable_name("ffprobe")
    if local_ffprobe.exists():
        FFPROBE_PATH = local_ffprobe
        return local_ffprobe

    # 2. Check system PATH
    system_ffprobe = shutil.which("ffprobe")
    if system_ffprobe:
        FFPROBE_PATH = Path(system_ffprobe)
        return FFPROBE_PATH

    return None


def is_ffmpeg_installed() -> bool:
    """Checks if ffprobe is available (locally or in PATH)."""
    return get_ffprobe_path() is not None


def get_download_url() -> Tuple[str, str]:
    """Returns (download_url, zip_filename) based on the platform."""
    if sys.platform == "win32":
        return (
            "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
            "ffmpeg-win64.zip",
        )
    elif sys.platform == "darwin":
        return ("https://evermeet.cx/ffmpeg/getrelease/zip", "ffmpeg-macos.zip")
    else:  # Linux
        return (
            "https://johnvansickle.com/ffmpeg/builds/ffmpeg-release-amd64-static.tar.xz",
            "ffmpeg-linux.tar.xz",
        )


def download_ffmpeg(
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> bool:
    """Downloads and extracts FFmpeg to the local bin directory."""
    try:
        url, zip_name = get_download_url()
        BIN_DIR.mkdir(parents=True, exist_ok=True)
        zip_path = BIN_DIR / zip_name

        logger.info(f"📥 Downloading FFmpeg from {url}...")

        # Download with progress
        req = urllib.request.Request(url, headers={"User-Agent": "AnimeOrganizer/1.0"})
        with urllib.request.urlopen(req, timeout=60) as response:
            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0
            chunk_size = 64 * 1024  # 64KB chunks

            with open(zip_path, "wb") as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total_size > 0:
                        progress_callback(downloaded, total_size)

        logger.info(f"✅ Download complete: {zip_path.name}")

        # Extract
        logger.info("📦 Extracting FFmpeg...")
        if zip_name.endswith(".zip"):
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(BIN_DIR)
        else:
            import tarfile

            with tarfile.open(zip_path, "r:xz") as tf:
                tf.extractall(BIN_DIR)

        # Find extracted folder and move executables to BIN_DIR
        _organize_extracted_files()

        # Cleanup zip
        try:
            zip_path.unlink()
        except Exception as e:
            logger.warning(f"⚠️ Could not delete zip file: {e}")

        # Verify installation
        if get_ffprobe_path():
            logger.info(f"✅ FFmpeg installed successfully at: {BIN_DIR}")
            return True
        else:
            logger.error("❌ FFmpeg extraction succeeded but ffprobe not found")
            return False

    except urllib.error.URLError as e:
        logger.error(f"❌ Network error downloading FFmpeg: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error installing FFmpeg: {e}")
        return False


def _organize_extracted_files():
    """Moves ffprobe/ffmpeg executables to the root of BIN_DIR."""
    exe_names = ["ffprobe", "ffmpeg"]
    if sys.platform == "win32":
        exe_names = [f"{n}.exe" for n in exe_names]

    # Search recursively for the executables
    for exe_name in exe_names:
        found = False
        for root, _, files in os.walk(BIN_DIR):
            if exe_name in files:
                src = Path(root) / exe_name
                dst = BIN_DIR / exe_name
                if src != dst:
                    try:
                        shutil.move(str(src), str(dst))
                        found = True
                    except Exception as e:
                        logger.warning(f"⚠️ Could not move {exe_name}: {e}")
                else:
                    found = True
                break

        # Clean up empty extracted folders
        if found:
            for item in BIN_DIR.iterdir():
                if item.is_dir() and item.name != "__pycache__":
                    try:
                        shutil.rmtree(item)
                    except Exception:
                        pass


def ensure_ffmpeg(
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> bool:
    """Main entry point: ensures FFmpeg is installed, downloads if needed."""
    if is_ffmpeg_installed():
        logger.info(f"✅ FFmpeg found at: {get_ffprobe_path()}")
        return True

    logger.info("⚠️ FFmpeg/FFprobe not found. Attempting auto-installation...")
    return download_ffmpeg(progress_callback)


def run_ffprobe(args: list, timeout: int = 15) -> Optional[subprocess.CompletedProcess]:
    """Runs ffprobe with the local/system path."""
    ffprobe = get_ffprobe_path()
    if not ffprobe:
        return None

    try:
        cmd = [str(ffprobe)] + args
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except Exception as e:
        logger.error(f"❌ ffprobe execution error: {e}")
        return None
