# utils/logger_utils.py
import logging
from pathlib import Path
from datetime import datetime


def setup_logger(log_to_file: bool = False, log_dir: str = "logs") -> logging.Logger:
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    handlers = []
    if log_to_file:
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_path / f"organizer_{timestamp}.log"
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    handlers.append(logging.StreamHandler())

    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=handlers,
    )

    logger = logging.getLogger("AnimeOrganizer")
    return logger
