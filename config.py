"""
Centralized configuration for TrackingMaster.

All configurable parameters are defined here as dataclasses.
Modify these values to customize application behavior without changing code.
"""

from dataclasses import dataclass, field
from typing import Tuple


@dataclass
class CameraConfig:
    """Camera capture settings."""
    width: int = 1280
    height: int = 720
    fps: int = 30
    buffer_size: int = 1
    max_cameras_scan: int = 3


@dataclass
class HandTrackingConfig:
    """MediaPipe hand tracking settings."""
    max_hands: int = 2
    model_complexity: int = 1
    detection_confidence: float = 0.3
    tracking_confidence: float = 0.3
    smoothing_factor: float = 0.5
    persistence_frames: int = 5


@dataclass
class FingerTrackingConfig:
    """Finger detection and gesture settings."""
    smoothing_frames: int = 3
    curl_threshold: int = 70
    thumb_curl_threshold: int = 35
    spread_threshold: int = 20
    ok_distance: float = 0.07

    # Threshold adjustment limits
    curl_range: Tuple[int, int] = (40, 120)
    thumb_curl_range: Tuple[int, int] = (20, 60)
    spread_range: Tuple[int, int] = (10, 40)

    # Adjustment step size
    threshold_step: int = 5


@dataclass
class ThreadingConfig:
    """Threaded processing settings."""
    target_fps: int = 30
    processing_history_size: int = 30
    thread_timeout: float = 1.0


@dataclass
class UIConfig:
    """User interface settings."""
    window_name: str = "TrackingMaster v0.3.1"
    fps_smoothing_window: int = 30
    toast_duration: float = 2.0  # seconds


@dataclass
class PathsConfig:
    """File paths configuration."""
    screenshots_dir: str = "screenshots"
    data_json_dir: str = "data/json"
    data_csv_dir: str = "data/csv"
    logs_dir: str = "logs"


@dataclass
class AppConfig:
    """Main application configuration container."""
    camera: CameraConfig = field(default_factory=CameraConfig)
    hand_tracking: HandTrackingConfig = field(default_factory=HandTrackingConfig)
    finger_tracking: FingerTrackingConfig = field(default_factory=FingerTrackingConfig)
    threading: ThreadingConfig = field(default_factory=ThreadingConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    paths: PathsConfig = field(default_factory=PathsConfig)


# Global configuration instance
config = AppConfig()
