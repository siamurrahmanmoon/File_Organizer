"""
core/watch_folder.py - Background Automated Watch Folder & Scheduler Service.
"""

import time
import threading
from pathlib import Path
from typing import Callable, Optional, Set, Dict
import logging

logger = logging.getLogger("AnimeOrganizer")


class WatchFolderService:
    """
    Monitors a folder continuously in the background.
    Detects new video files, verifies write stability (no change in size for N sec),
    and triggers organizer callback.
    """

    def __init__(
        self,
        watch_path: str,
        process_callback: Callable[[Path], None],
        video_extensions: Set[str],
        poll_interval: int = 10,
        stability_wait: int = 5
    ):
        self.watch_path = Path(watch_path)
        self.process_callback = process_callback
        self.video_extensions = video_extensions
        self.poll_interval = poll_interval
        self.stability_wait = stability_wait
        self.is_running = False
        self._thread: Optional[threading.Thread] = None
        # Maps file path -> last observed (size, timestamp)
        self._tracked_files: Dict[Path, tuple] = {}

    def start(self):
        """Starts the background monitoring thread."""
        if self.is_running:
            return
        self.is_running = True
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()
        logger.info(f"👀 Watch Folder started on: {self.watch_path}")

    def stop(self):
        """Stops monitoring."""
        self.is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("⏹️ Watch Folder stopped.")

    def _watch_loop(self):
        while self.is_running:
            try:
                if self.watch_path.exists():
                    current_time = time.time()
                    for item in self.watch_path.iterdir():
                        if not self.is_running:
                            break
                        if item.is_file() and item.suffix.lower() in self.video_extensions:
                            try:
                                curr_size = item.stat().st_size
                                if item not in self._tracked_files:
                                    # First time seen
                                    self._tracked_files[item] = (curr_size, current_time)
                                else:
                                    last_size, first_seen = self._tracked_files[item]
                                    if curr_size != last_size:
                                        # Still being written to
                                        self._tracked_files[item] = (curr_size, current_time)
                                    else:
                                        # Size is stable, check if stability_wait passed
                                        if current_time - first_seen >= self.stability_wait:
                                            # File is completely written, trigger process
                                            del self._tracked_files[item]
                                            logger.info(f"✨ Auto-processing stabilized file: {item.name}")
                                            self.process_callback(item)
                            except Exception:
                                pass
            except Exception as e:
                logger.warning(f"Error in watch loop: {e}")

            time.sleep(self.poll_interval)
