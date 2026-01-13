"""
TrackingMaster v0.2 - Camera Module
Webcam access and basic controls management.
"""

import cv2
import sys
from datetime import datetime
from pathlib import Path


class Camera:
    """Class to manage webcam access and controls."""

    def __init__(self, camera_id: int = 0, width: int = 1280, height: int = 720):
        """
        Initialize camera.

        Args:
            camera_id: Camera ID (0 = default camera)
            width: Capture width
            height: Capture height
        """
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.cap = None
        self.is_paused = False
        self.last_frame = None
        self.screenshot_dir = Path("screenshots")

    def start(self, verbose: bool = True) -> bool:
        """
        Start video capture.

        Args:
            verbose: Display progress messages

        Returns:
            True if camera opened successfully, False otherwise.
        """
        # Use DirectShow on Windows for faster initialization
        if sys.platform == "win32":
            self.cap = cv2.VideoCapture(self.camera_id, cv2.CAP_DSHOW)
        else:
            self.cap = cv2.VideoCapture(self.camera_id)

        if not self.cap.isOpened():
            return False

        if verbose:
            print(f"  > Connecting to camera {self.camera_id}... OK")

        # Reduce buffer for less latency
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Configure resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        # Set target FPS
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        if verbose:
            actual_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            print(f"  > Setting resolution {actual_w}x{actual_h}... OK")

        # Check and create screenshots folder if needed
        if verbose:
            print(f"  > Checking folder '{self.screenshot_dir}'...", end=" ")

        if self.screenshot_dir.exists():
            if verbose:
                print("exists")
        else:
            self.screenshot_dir.mkdir(exist_ok=True)
            if verbose:
                print("created")

        # Read first frame to warm up camera
        if verbose:
            print(f"  > Warming up camera...", end=" ")
        self.cap.read()
        if verbose:
            print("OK")

        return True

    def read_frame(self):
        """
        Read a frame from the camera.

        Returns:
            tuple: (success, frame) - success is boolean, frame is the image
        """
        if self.cap is None:
            return False, None

        if self.is_paused and self.last_frame is not None:
            return True, self.last_frame

        success, frame = self.cap.read()

        if success:
            # Horizontal mirror for natural display
            frame = cv2.flip(frame, 1)
            self.last_frame = frame

        return success, frame

    def toggle_pause(self):
        """Toggle between pause and play."""
        self.is_paused = not self.is_paused
        return self.is_paused

    def take_screenshot(self, frame) -> str:
        """
        Take a screenshot.

        Args:
            frame: The image to save

        Returns:
            The path of the saved file
        """
        if frame is None:
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.screenshot_dir / f"screenshot_{timestamp}.png"
        cv2.imwrite(str(filename), frame)
        return str(filename)

    def get_fps(self) -> float:
        """Return the camera FPS."""
        if self.cap is None:
            return 0.0
        return self.cap.get(cv2.CAP_PROP_FPS)

    def get_resolution(self) -> tuple:
        """Return current resolution (width, height)."""
        if self.cap is None:
            return (0, 0)
        return (
            int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        )

    def release(self):
        """Release camera resources."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None


class CameraError(Exception):
    """Custom exception for camera errors."""
    pass


def get_camera_names_windows() -> list:
    """
    Get camera names on Windows via pygrabber (DirectShow).

    Returns:
        List of camera names in order
    """
    names = []

    # Use pygrabber to get DirectShow names
    try:
        from pygrabber.dshow_graph import FilterGraph

        graph = FilterGraph()
        devices = graph.get_input_devices()
        names = list(devices.values())

        if names:
            return names
    except ImportError:
        pass  # pygrabber not installed
    except Exception:
        pass

    # Fallback: generic names
    return names


def list_available_cameras(max_cameras: int = 3, target_width: int = 1280, target_height: int = 720) -> list:
    """
    List available cameras on the system.

    Args:
        max_cameras: Maximum number of cameras to test
        target_width: Target width to test capabilities
        target_height: Target height to test capabilities

    Returns:
        List of dictionaries with info for each available camera
    """
    import os

    available = []

    # Get camera names on Windows
    camera_names_list = []
    if sys.platform == "win32":
        camera_names_list = get_camera_names_windows()

    # Save and redirect stderr at OS level
    stderr_fd = sys.stderr.fileno()
    old_stderr_fd = os.dup(stderr_fd)

    try:
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, stderr_fd)
        os.close(devnull)

        camera_index = 0
        for i in range(max_cameras):
            if sys.platform == "win32":
                cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            else:
                cap = cv2.VideoCapture(i)

            if cap.isOpened():
                # Configure target resolution to get actual capabilities
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, target_width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, target_height)
                cap.set(cv2.CAP_PROP_FPS, 30)

                # Read a frame to activate the settings
                cap.read()

                # Get actual info
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                backend = cap.getBackendName()

                # Use real name if available
                if camera_index < len(camera_names_list):
                    name = camera_names_list[camera_index]
                else:
                    name = f"Camera {i}"

                available.append({
                    "id": i,
                    "name": name,
                    "resolution": f"{width}x{height}",
                    "fps": fps if fps > 0 else 30.0,
                    "backend": backend
                })
                cap.release()
                camera_index += 1
    finally:
        # Restore stderr
        os.dup2(old_stderr_fd, stderr_fd)
        os.close(old_stderr_fd)

    return available
