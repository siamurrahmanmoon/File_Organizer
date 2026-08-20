"""
utils/logger_utils.py - Centralized multi-target logging system.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List


class InMemoryLogHandler(logging.Handler):
    """Stores recent log messages in memory for UI viewing and export."""
    def __init__(self, max_messages: int = 1000):
        super().__init__()
        self.max_messages = max_messages
        self.messages: List[str] = []

    def emit(self, record):
        try:
            msg = self.format(record)
            self.messages.append(msg)
            if len(self.messages) > self.max_messages:
                self.messages.pop(0)
        except Exception:
            pass

    def get_logs(self) -> str:
        return "\n".join(self.messages)

    def clear(self):
        self.messages.clear()


GLOBAL_IN_MEMORY_HANDLER = InMemoryLogHandler()


def setup_logger(log_to_file: bool = False, log_dir: str = "logs", log_level: int = logging.INFO) -> logging.Logger:
    """Configures the root and application logger."""
    logger = logging.getLogger("AnimeOrganizer")
    logger.setLevel(log_level)
    logger.handlers.clear()

    formatter = logging.Formatter("%(message)s")

    if log_to_file:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_path / f"organizer_{timestamp}.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s"))
        file_handler.setLevel(log_level)
        logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(log_level)
    logger.addHandler(stream_handler)

    GLOBAL_IN_MEMORY_HANDLER.setFormatter(formatter)
    GLOBAL_IN_MEMORY_HANDLER.setLevel(log_level)
    if GLOBAL_IN_MEMORY_HANDLER not in logger.handlers:
        logger.addHandler(GLOBAL_IN_MEMORY_HANDLER)

    return logger
