"""
TrackingMaster v0.3.1 - Finger Tracking
Main entry point of the application.

Controls:
    Q / ESC  : Quit
    SPACE    : Pause / Resume
    S        : Screenshot
    I        : Toggle info overlay
    ? / /    : Toggle help window
    H        : Toggle hand tracking
    F        : Toggle finger tracking display
    N        : Toggle number detection
    G        : Toggle gesture detection
    D        : Toggle debug mode
    R        : Toggle recording (exports JSON/CSV on stop)
    [ / ]    : Adjust detection threshold (-/+)
    ; / '    : Adjust tracking threshold (-/+)
    1-6      : Debug threshold adjustments
"""

import cv2
import sys
import time
from collections import deque
from typing import Dict, List, Optional

from config import config
from src.camera import Camera, list_available_cameras
from src.hand_tracker import HandTracker
from src.finger_tracker import FingerTracker, TrackingDataRecorder
from src.overlay_renderer import OverlayRenderer
from src.logger import setup_logging

# Initialize logging
logger = setup_logging()

WINDOW_NAME = config.ui.window_name
FPS_SMOOTHING_WINDOW = config.ui.fps_smoothing_window


class FPSCounter:
    """Smoothed FPS counter using rolling average."""

    def __init__(self, window_size: int = 30):
        self.times: deque = deque(maxlen=window_size)
        self.last_time: float = time.perf_counter()

    def update(self) -> float:
        current_time = time.perf_counter()
        delta = current_time - self.last_time
        self.last_time = current_time
        if delta > 0:
            self.times.append(delta)
        if len(self.times) > 0:
            avg_delta = sum(self.times) / len(self.times)
            return 1.0 / avg_delta if avg_delta > 0 else 0.0
        return 0.0


def select_camera(cameras: List[Dict]) -> int:
    """Prompt user to select a camera."""
    valid_ids = [cam["id"] for cam in cameras]
    while True:
        try:
            if len(cameras) == 1:
                choice = input(f"\nInitialize camera {cameras[0]['id']}? (Y/n): ").strip().lower()
                if choice in ("", "y", "yes", "o", "oui"):
                    return cameras[0]["id"]
                elif choice in ("n", "no", "non"):
                    logger.info("Cancelled.")
                    sys.exit(0)
            else:
                selected_id = int(input(f"\nWhich camera? {valid_ids}: ").strip())
                if selected_id in valid_ids:
                    return selected_id
                logger.warning(f"Invalid. Options: {valid_ids}")
        except ValueError:
            logger.warning(f"Enter a number from {valid_ids}")
        except KeyboardInterrupt:
            logger.info("Cancelled.")
            sys.exit(0)


def create_toast(message: str) -> Dict:
    """Create a toast notification."""
    return {"message": message, "timestamp": time.time()}


def main():
    logger.info("=" * 50)
    logger.info("  TrackingMaster v0.3.1 - Finger Tracking")
    logger.info("=" * 50)

    # Camera setup
    logger.info("[1/4] Scanning cameras...")
    cameras = list_available_cameras()

    if not cameras:
        logger.error("No camera detected!")
        sys.exit(1)

    logger.info(f"{len(cameras)} camera(s) available:")
    for cam in cameras:
        logger.info(f"  [{cam['id']}] {cam['name']} - {cam['resolution']}")

    selected_id = select_camera(cameras)

    logger.info(f"[2/4] Initializing camera {selected_id}...")
    camera = Camera(camera_id=selected_id)
    if not camera.start():
        logger.error("Cannot open camera!")
        sys.exit(1)

    # Trackers setup
    logger.info("[3/4] Initializing trackers...")
    hand_tracker = HandTracker(max_hands=config.hand_tracking.max_hands)
    finger_tracker = FingerTracker(smoothing_frames=config.finger_tracking.smoothing_frames)
    data_recorder = TrackingDataRecorder()

    logger.info("  > Hand Tracker... OK")
    logger.info("  > Finger Tracker... OK")
    logger.info("  > Data Recorder... OK")

    # Overlay renderer
    logger.info("[4/4] Initializing renderer...")
    renderer = OverlayRenderer()
    logger.info("  > Overlay Renderer... OK")

    logger.info("Starting...")
    logger.info("Controls:")
    logger.info("  [Q/ESC] Quit  [SPACE] Pause  [S] Screenshot")
    logger.info("  [H] Hands  [F] Fingers  [N] Numbers  [G] Gestures")
    logger.info("  [D] Debug  [R] Record  [?] Help")
    logger.info("-" * 50)

    # State variables
    fps_counter = FPSCounter(FPS_SMOOTHING_WINDOW)
    show_info: bool = True
    show_help: bool = False
    hand_tracking_enabled: bool = True
    finger_display_enabled: bool = True
    number_detection_enabled: bool = True
    gesture_detection_enabled: bool = True
    current_toast: Optional[Dict] = None

    try:
        while True:
            success, frame = camera.read_frame()
            if not success:
                logger.error("Cannot read frame - camera may be disconnected")
                break

            fps = fps_counter.update()

            # Clear expired toast
            if current_toast and time.time() - current_toast["timestamp"] > 2.0:
                current_toast = None

            # Prepare render state
            render_state = {
                "fps": fps,
                "is_paused": camera.is_paused,
                "show_info": show_info,
                "show_help": show_help,
                "hand_tracking_enabled": hand_tracking_enabled,
                "finger_display_enabled": finger_display_enabled,
                "number_detection_enabled": number_detection_enabled,
                "gesture_detection_enabled": gesture_detection_enabled,
                "debug_mode": finger_tracker.debug_mode,
                "is_recording": data_recorder.is_recording,
                "record_frames": data_recorder.get_frame_count(),
                "thresholds": finger_tracker.get_thresholds(),
                "hands_info": [],
                "finger_data": [],
                "no_hands": False,
                "toast": current_toast,
            }

            # Process tracking (synchronous - no threading)
            if hand_tracking_enabled and not camera.is_paused:
                hands = hand_tracker.process(frame)
                hand_tracker.draw(frame)
                render_state["hands_info"] = hand_tracker.get_hands_info()

                if hands:
                    for hand in hands:
                        analysis = finger_tracker.analyze_hand(
                            hand.landmarks, hand.handedness, hand_id=hand.hand_id
                        )
                        curl_angles = finger_tracker.get_curl_angles(hand.landmarks)
                        spread_angles = finger_tracker.get_spread_angles(hand.landmarks)

                        gesture_to_show = analysis.gesture_name if gesture_detection_enabled else ""

                        finger_data = {
                            "hand_type": hand.handedness,
                            "landmarks": hand.landmarks,
                            "gesture": gesture_to_show,
                            "finger_count": analysis.finger_count,
                            "finger_states": analysis.finger_states.as_list(),
                            "confidence": analysis.confidence.as_dict(),
                            "curl_angles": curl_angles,
                            "spread_angles": spread_angles,
                            "analysis": analysis
                        }
                        render_state["finger_data"].append(finger_data)

                        if data_recorder.is_recording:
                            data_recorder.add_frame(hand.handedness, analysis, curl_angles)
                else:
                    render_state["no_hands"] = True

            elif hand_tracking_enabled:
                render_state["no_hands"] = True

            # Render overlays
            frame = renderer.render(frame, render_state)

            # Display
            cv2.imshow(WINDOW_NAME, frame)

            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q') or key == 27:
                logger.info("Closing...")
                break

            elif key == ord(' '):
                paused = camera.toggle_pause()
                status = 'Paused' if paused else 'Resumed'
                logger.info(status)
                current_toast = create_toast(status)

            elif key == ord('s'):
                filepath = camera.take_screenshot(camera.last_frame)
                if filepath:
                    logger.info(f"Screenshot: {filepath}")
                    current_toast = create_toast("Screenshot saved")

            elif key == ord('i'):
                show_info = not show_info

            elif key == ord('?') or key == ord('/'):
                show_help = not show_help

            elif key == ord('h'):
                hand_tracking_enabled = not hand_tracking_enabled
                status = f"Hand tracking: {'ON' if hand_tracking_enabled else 'OFF'}"
                logger.info(status)
                current_toast = create_toast(status)

            elif key == ord('f'):
                finger_display_enabled = not finger_display_enabled
                logger.info(f"Finger display: {'ON' if finger_display_enabled else 'OFF'}")

            elif key == ord('n'):
                number_detection_enabled = not number_detection_enabled
                status = f"Numbers: {'ON' if number_detection_enabled else 'OFF'}"
                logger.info(status)
                current_toast = create_toast(status)

            elif key == ord('g'):
                gesture_detection_enabled = not gesture_detection_enabled
                status = f"Gestures: {'ON' if gesture_detection_enabled else 'OFF'}"
                logger.info(status)
                current_toast = create_toast(status)

            elif key == ord('d'):
                debug = finger_tracker.toggle_debug_mode()
                status = f"Debug: {'ON' if debug else 'OFF'}"
                logger.info(status)
                current_toast = create_toast(status)

            elif key == ord('r'):
                is_now_recording = data_recorder.toggle_recording()
                if is_now_recording:
                    logger.info("Recording started...")
                    current_toast = create_toast("Recording started")
                else:
                    if data_recorder.get_frame_count() > 0:
                        json_path, csv_path = data_recorder.export_all()
                        logger.info(f"Recording stopped. Exported:")
                        logger.info(f"  JSON: {json_path}")
                        logger.info(f"  CSV: {csv_path}")
                        current_toast = create_toast("Recording saved")
                    else:
                        logger.info("Recording stopped (no data)")
                        current_toast = create_toast("Recording stopped")

            # Threshold adjustments
            elif key == ord('1'):
                new_val = finger_tracker.adjust_curl_threshold(-5)
                logger.info(f"Finger curl threshold: {new_val:.0f}")
                current_toast = create_toast(f"Finger curl: {new_val:.0f}")

            elif key == ord('2'):
                new_val = finger_tracker.adjust_curl_threshold(5)
                logger.info(f"Finger curl threshold: {new_val:.0f}")
                current_toast = create_toast(f"Finger curl: {new_val:.0f}")

            elif key == ord('3'):
                new_val = finger_tracker.adjust_thumb_curl_threshold(-5)
                logger.info(f"Thumb curl threshold: {new_val:.0f}")
                current_toast = create_toast(f"Thumb curl: {new_val:.0f}")

            elif key == ord('4'):
                new_val = finger_tracker.adjust_thumb_curl_threshold(5)
                logger.info(f"Thumb curl threshold: {new_val:.0f}")
                current_toast = create_toast(f"Thumb curl: {new_val:.0f}")

            elif key == ord('5'):
                new_val = finger_tracker.adjust_spread_threshold(-5)
                logger.info(f"Spread threshold: {new_val:.0f}")
                current_toast = create_toast(f"Spread: {new_val:.0f}")

            elif key == ord('6'):
                new_val = finger_tracker.adjust_spread_threshold(5)
                logger.info(f"Spread threshold: {new_val:.0f}")
                current_toast = create_toast(f"Spread: {new_val:.0f}")

            elif key == ord(']'):
                detection_conf, _ = hand_tracker.get_confidence()
                hand_tracker.set_confidence(detection=detection_conf + 0.05)
                d, _ = hand_tracker.get_confidence()
                logger.info(f"Detection: {d:.0%}")
                current_toast = create_toast(f"Detection: {d:.0%}")

            elif key == ord('['):
                detection_conf, _ = hand_tracker.get_confidence()
                hand_tracker.set_confidence(detection=detection_conf - 0.05)
                d, _ = hand_tracker.get_confidence()
                logger.info(f"Detection: {d:.0%}")
                current_toast = create_toast(f"Detection: {d:.0%}")

            elif key == ord("'"):
                _, tracking_conf = hand_tracker.get_confidence()
                hand_tracker.set_confidence(tracking=tracking_conf + 0.05)
                _, t = hand_tracker.get_confidence()
                logger.info(f"Tracking: {t:.0%}")
                current_toast = create_toast(f"Tracking: {t:.0%}")

            elif key == ord(';'):
                _, tracking_conf = hand_tracker.get_confidence()
                hand_tracker.set_confidence(tracking=tracking_conf - 0.05)
                _, t = hand_tracker.get_confidence()
                logger.info(f"Tracking: {t:.0%}")
                current_toast = create_toast(f"Tracking: {t:.0%}")

    except KeyboardInterrupt:
        logger.info("Interrupted")

    finally:
        logger.info("Shutting down...")

        if data_recorder.is_recording and data_recorder.get_frame_count() > 0:
            json_path, csv_path = data_recorder.export_all()
            logger.info(f"Auto-exported recording: {json_path}, {csv_path}")

        hand_tracker.release()
        camera.release()
        cv2.destroyAllWindows()
        logger.info("TrackingMaster closed.")


if __name__ == "__main__":
    main()
