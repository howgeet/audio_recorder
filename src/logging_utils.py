"""Centralized logging setup for the Meeting Transcriber app."""

import logging
from pathlib import Path

from src.config import config


def setup_logging() -> Path:
    """Configure root logging to console and project log file.

    Returns:
        Absolute path to the configured log file.
    """
    project_root = Path(__file__).resolve().parent.parent
    configured = config.log_file
    log_path = configured if configured.is_absolute() else (project_root / configured)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    if getattr(root_logger, "_meeting_transcriber_logging_configured", False):
        return log_path

    root_logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)

    root_logger._meeting_transcriber_logging_configured = True
    logging.getLogger(__name__).info("Logging initialized. Log file: %s", log_path)
    return log_path
