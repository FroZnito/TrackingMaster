"""
Logging configuration for TrackingMaster.

Provides a centralized logging setup with console output.
Designed for minimal performance impact.
"""

import logging
import sys
from typing import Optional

# Cache the logger to avoid repeated setup
_logger: Optional[logging.Logger] = None


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """
    Set up and configure the TrackingMaster logger.

    Args:
        level: Logging level (default: INFO)

    Returns:
        Configured logger instance
    """
    global _logger

    if _logger is not None:
        return _logger

    logger = logging.getLogger("TrackingMaster")
    logger.setLevel(level)

    # Avoid adding handlers multiple times
    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    _logger = logger
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Optional submodule name (e.g., "camera", "tracker")

    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f"TrackingMaster.{name}")
    return logging.getLogger("TrackingMaster")


# Pre-configured loggers for each module
def get_camera_logger() -> logging.Logger:
    """Get logger for camera module."""
    return get_logger("camera")


def get_tracker_logger() -> logging.Logger:
    """Get logger for hand tracker module."""
    return get_logger("tracker")


def get_finger_logger() -> logging.Logger:
    """Get logger for finger tracker module."""
    return get_logger("finger")


def get_thread_logger() -> logging.Logger:
    """Get logger for threaded tracker module."""
    return get_logger("thread")


def get_overlay_logger() -> logging.Logger:
    """Get logger for overlay renderer module."""
    return get_logger("overlay")
