"""
TrackingMaster v0.2 - Hand Detection
Main entry point of the application.

Controls:
    Q / ESC  : Quit
    SPACE    : Pause / Resume
    S        : Screenshot
    I        : Toggle info overlay
    H        : Toggle hand tracking
    [ / ]    : Adjust detection threshold (-/+)
    ; / '    : Adjust tracking threshold (-/+)
"""

import cv2
import sys
import time
from collections import deque
from src.camera import Camera, list_available_cameras
from src.hand_tracker import HandTracker


# Configuration
WINDOW_NAME = "TrackingMaster v0.2"
DEFAULT_CAMERA = 0
FPS_SMOOTHING_WINDOW = 30  # Nombre de frames pour la moyenne glissante


class FPSCounter:
    """Compteur de FPS avec moyenne glissante."""

    def __init__(self, window_size: int = 30):
        self.window_size = window_size
        self.times = deque(maxlen=window_size)
        self.last_time = time.time()

    def update(self) -> float:
        """Met à jour et retourne le FPS lissé."""
        current_time = time.time()
        delta = current_time - self.last_time
        self.last_time = current_time

        if delta > 0:
            self.times.append(delta)

        if len(self.times) > 0:
            avg_delta = sum(self.times) / len(self.times)
            return 1.0 / avg_delta if avg_delta > 0 else 0.0
        return 0.0


def draw_info_overlay(
    frame,
    fps: float,
    is_paused: bool,
    show_info: bool,
    hand_tracking_enabled: bool = True,
    hands_info: list = None,
    detection_conf: float = 0.7,
    tracking_conf: float = 0.5
):
    """Draw information overlay on the frame."""
    if not show_info:
        return frame

    height, width = frame.shape[:2]

    # Information lines
    info_lines = [
        f"FPS: {fps:.1f}",
        f"Resolution: {width}x{height}",
        f"Status: {'PAUSED' if is_paused else 'RUNNING'}",
        f"Hand Tracking: {'ON' if hand_tracking_enabled else 'OFF'}"
    ]

    # Add confidence thresholds
    if hand_tracking_enabled:
        info_lines.append(f"Detection: {detection_conf:.0%} [/]")
        info_lines.append(f"Tracking: {tracking_conf:.0%} [;']")

    # Add detected hands info
    if hand_tracking_enabled and hands_info:
        info_lines.append(f"Hands detected: {len(hands_info)}")
        for hand in hands_info:
            info_lines.append(f"  {hand['type']} ({hand['confidence']*100:.0f}%)")
    elif hand_tracking_enabled:
        info_lines.append("Hands detected: 0")

    # Controls
    info_lines.append("")
    info_lines.append("[H] Hands  [I] Info  [S] Shot")

    # Calculate background size
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.55
    thickness = 1
    padding = 15
    line_height = 22

    # Find max text width
    max_width = 0
    for line in info_lines:
        (text_width, _), _ = cv2.getTextSize(line, font, font_scale, thickness)
        max_width = max(max_width, text_width)

    # Rectangle dimensions
    rect_width = max_width + padding * 2
    rect_height = len(info_lines) * line_height + padding * 2 - 5

    # Semi-transparent background
    overlay = frame.copy()
    cv2.rectangle(overlay, (10, 10), (10 + rect_width, 10 + rect_height), (0, 0, 0), -1)
    frame = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)

    # Draw text
    y_offset = 10 + padding + 12
    for line in info_lines:
        if "PAUSED" in line:
            color = (0, 255, 255)  # Yellow
        elif "RUNNING" in line:
            color = (0, 255, 0)  # Green
        elif "ON" in line and "Hand" in line:
            color = (0, 255, 0)  # Green
        elif "OFF" in line and "Hand" in line:
            color = (0, 0, 255)  # Red
        elif "Right" in line:
            color = (0, 255, 0)  # Green
        elif "Left" in line:
            color = (255, 0, 0)  # Blue
        elif "Detection:" in line or "Tracking:" in line:
            color = (200, 200, 200)  # Light gray
        else:
            color = (255, 255, 255)  # White

        cv2.putText(
            frame, line,
            (10 + padding, y_offset),
            font, font_scale, color, thickness, cv2.LINE_AA
        )
        y_offset += line_height

    return frame


def draw_no_hands_indicator(frame):
    """Display visual indicator when no hands are detected."""
    height, width = frame.shape[:2]

    # Text at bottom center
    text = "No hands detected"
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.7
    thickness = 2

    (text_width, text_height), _ = cv2.getTextSize(text, font, font_scale, thickness)

    # Centered position at bottom
    x = (width - text_width) // 2
    y = height - 30

    # Semi-transparent background
    padding = 10
    overlay = frame.copy()
    cv2.rectangle(
        overlay,
        (x - padding, y - text_height - padding),
        (x + text_width + padding, y + padding),
        (0, 0, 100), -1
    )
    frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)

    # Text
    cv2.putText(
        frame, text,
        (x, y),
        font, font_scale, (100, 100, 255), thickness, cv2.LINE_AA
    )

    return frame


def draw_pause_indicator(frame):
    """Display pause indicator at center."""
    height, width = frame.shape[:2]
    center_x, center_y = width // 2, height // 2

    # Icône pause (deux barres)
    bar_width = 20
    bar_height = 60
    gap = 20

    cv2.rectangle(
        frame,
        (center_x - gap - bar_width, center_y - bar_height // 2),
        (center_x - gap, center_y + bar_height // 2),
        (255, 255, 255), -1
    )
    cv2.rectangle(
        frame,
        (center_x + gap, center_y - bar_height // 2),
        (center_x + gap + bar_width, center_y + bar_height // 2),
        (255, 255, 255), -1
    )

    return frame


def select_camera(cameras: list) -> int:
    """
    Allow user to select a camera.

    Args:
        cameras: List of available cameras

    Returns:
        Selected camera ID, or -1 if cancelled
    """
    valid_ids = [cam["id"] for cam in cameras]

    while True:
        try:
            if len(cameras) == 1:
                cam = cameras[0]
                choice = input(f"\nInitialize camera {cam['id']}? (Y/n): ").strip().lower()
                if choice in ("", "y", "yes", "o", "oui"):
                    return cam["id"]
                elif choice in ("n", "no", "non"):
                    print("Cancelled.")
                    sys.exit(0)
                else:
                    print("Answer Y (yes) or N (no)")
            else:
                choice = input(f"\nWhich camera to initialize? {valid_ids}: ").strip()
                selected_id = int(choice)

                if selected_id in valid_ids:
                    return selected_id
                else:
                    print(f"Invalid choice. Options: {valid_ids}")
        except ValueError:
            print(f"Enter a number from {valid_ids}")
        except KeyboardInterrupt:
            print("\nCancelled.")
            sys.exit(0)


def main():
    """Main function."""
    print("=" * 50)
    print("  TrackingMaster v0.2 - Hand Detection")
    print("=" * 50)

    # Scan available cameras
    print("\n[1/4] Scanning cameras...")
    cameras = list_available_cameras()

    if not cameras:
        print("  ERROR: No camera detected!")
        print("  Make sure your webcam is connected and not used by another application.")
        sys.exit(1)

    print(f"\n  {len(cameras)} camera(s) available:")
    for cam in cameras:
        print(f"    [{cam['id']}] {cam['name']}")
        print(f"        Resolution: {cam['resolution']} | FPS: {cam['fps']:.0f} | Backend: {cam['backend']}")

    # Camera selection
    selected_id = select_camera(cameras)

    # Initialize selected camera
    print(f"\n[2/4] Initializing camera {selected_id}...")
    camera = Camera(camera_id=selected_id)

    if not camera.start():
        print(f"  ERROR: Cannot open camera {selected_id}!")
        sys.exit(1)

    resolution = camera.get_resolution()

    # Initialize hand tracker
    print(f"\n[3/4] Initializing Hand Tracker...")
    hand_tracker = HandTracker(max_hands=2)
    print(f"  > MediaPipe Hands loaded... OK")
    print(f"  > Detecting up to 2 hands")

    print(f"\n[4/4] Starting...")
    print(f"  Camera ready: {resolution[0]}x{resolution[1]}")
    print("\nControls:")
    print("  Q / ESC  : Quit")
    print("  SPACE    : Pause / Resume")
    print("  S        : Screenshot")
    print("  I        : Toggle info overlay")
    print("  H        : Toggle hand tracking")
    print("  [ / ]    : Detection threshold (-/+ 5%)")
    print("  ; / '    : Tracking threshold (-/+ 5%)")
    print("-" * 50)

    # Variables
    fps_counter = FPSCounter(FPS_SMOOTHING_WINDOW)
    show_info = True
    hand_tracking_enabled = True

    try:
        while True:
            # Lire une frame
            success, frame = camera.read_frame()

            if not success:
                print("ERROR: Cannot read frame")
                break

            # Calculer le FPS (lissé)
            fps = fps_counter.update()

            # Tracking des mains
            hands_info = []
            if hand_tracking_enabled and not camera.is_paused:
                hand_tracker.process(frame)
                hand_tracker.draw(frame)
                hands_info = hand_tracker.get_hands_info()

            # Récupérer les seuils actuels
            detection_conf, tracking_conf = hand_tracker.get_confidence()

            # Dessiner les overlays
            frame = draw_info_overlay(
                frame, fps, camera.is_paused, show_info,
                hand_tracking_enabled, hands_info,
                detection_conf, tracking_conf
            )

            # Indicateur aucune main détectée
            if hand_tracking_enabled and not hands_info and not camera.is_paused:
                frame = draw_no_hands_indicator(frame)

            if camera.is_paused:
                frame = draw_pause_indicator(frame)

            # Afficher la frame
            cv2.imshow(WINDOW_NAME, frame)

            # Gérer les entrées clavier
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q') or key == 27:  # Q or ESC
                print("\nClosing...")
                break

            elif key == ord(' '):  # SPACE
                paused = camera.toggle_pause()
                print(f"{'Paused' if paused else 'Resumed'}")

            elif key == ord('s'):  # S
                filepath = camera.take_screenshot(camera.last_frame)
                if filepath:
                    print(f"Screenshot saved: {filepath}")

            elif key == ord('i'):  # I
                show_info = not show_info

            elif key == ord('h'):  # H
                hand_tracking_enabled = not hand_tracking_enabled
                print(f"Hand tracking: {'enabled' if hand_tracking_enabled else 'disabled'}")

            elif key == ord(']'):  # ] (increase detection)
                new_val = detection_conf + 0.05
                hand_tracker.set_confidence(detection=new_val)
                d, _ = hand_tracker.get_confidence()
                print(f"Detection threshold: {d:.0%}")

            elif key == ord('['):  # [ (decrease detection)
                new_val = detection_conf - 0.05
                hand_tracker.set_confidence(detection=new_val)
                d, _ = hand_tracker.get_confidence()
                print(f"Detection threshold: {d:.0%}")

            elif key == ord("'"):  # ' (increase tracking)
                new_val = tracking_conf + 0.05
                hand_tracker.set_confidence(tracking=new_val)
                _, t = hand_tracker.get_confidence()
                print(f"Tracking threshold: {t:.0%}")

            elif key == ord(';'):  # ; (decrease tracking)
                new_val = tracking_conf - 0.05
                hand_tracker.set_confidence(tracking=new_val)
                _, t = hand_tracker.get_confidence()
                print(f"Tracking threshold: {t:.0%}")

    except KeyboardInterrupt:
        print("\nInterrupted by user")

    finally:
        # Cleanup
        hand_tracker.release()
        camera.release()
        cv2.destroyAllWindows()
        print("TrackingMaster closed.")


if __name__ == "__main__":
    main()
