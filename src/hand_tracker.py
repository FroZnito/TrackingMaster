"""
TrackingMaster v0.2 - Hand Tracker Module
Hand detection and tracking with MediaPipe.
"""

import cv2
import mediapipe as mp
from dataclasses import dataclass, field
from collections import deque


@dataclass
class HandData:
    """Data for a detected hand."""
    landmarks: list  # List of 21 landmarks
    handedness: str  # "Left" or "Right"
    confidence: float  # Confidence score
    hand_id: int = -1  # Unique ID for tracking
    frames_since_seen: int = 0  # Frames since last detection


class HandTracker:
    """Class to detect and track hands with smoothing and stabilization."""

    def __init__(
        self,
        max_hands: int = 2,
        min_detection_confidence: float = 0.3,
        min_tracking_confidence: float = 0.3,
        model_complexity: int = 1,
        smoothing_factor: float = 0.5,
        persistence_frames: int = 5
    ):
        """
        Initialize hand tracker.

        Args:
            max_hands: Maximum number of hands to detect
            min_detection_confidence: Minimum confidence for detection
            min_tracking_confidence: Minimum confidence for tracking
            model_complexity: Model complexity (0 or 1). Higher = more accurate but slower
            smoothing_factor: Smoothing for landmarks (0 = no smoothing, 1 = max smoothing)
            persistence_frames: Frames to keep hand visible after losing detection
        """
        self.max_hands = max_hands
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.model_complexity = model_complexity
        self.smoothing_factor = smoothing_factor
        self.persistence_frames = persistence_frames

        # Initialize MediaPipe Hands
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            model_complexity=model_complexity,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )

        # Results from last processing
        self.results = None
        self.hands_data = []

        # Tracking state
        self._next_hand_id = 0
        self._tracked_hands = {}  # hand_id -> {landmarks, handedness, confidence, last_seen}
        self._landmark_history = {}  # hand_id -> deque of recent landmarks for smoothing

    def _get_hand_center(self, landmarks: list) -> tuple:
        """Get the center point of a hand from its landmarks."""
        x = sum(lm[0] for lm in landmarks) / len(landmarks)
        y = sum(lm[1] for lm in landmarks) / len(landmarks)
        return (x, y)

    def _landmarks_distance(self, lm1: list, lm2: list) -> float:
        """Calculate distance between two sets of landmarks."""
        c1 = self._get_hand_center(lm1)
        c2 = self._get_hand_center(lm2)
        return ((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2)**0.5

    def _match_hand_to_tracked(self, landmarks: list, handedness: str) -> int:
        """
        Match a detected hand to an existing tracked hand.

        Returns:
            hand_id if matched, -1 if new hand
        """
        best_match_id = -1
        best_distance = 0.15  # Maximum distance threshold for matching

        for hand_id, tracked in self._tracked_hands.items():
            # Prefer matching same handedness
            if tracked["handedness"] == handedness:
                dist = self._landmarks_distance(landmarks, tracked["landmarks"])
                if dist < best_distance:
                    best_distance = dist
                    best_match_id = hand_id

        # If no same-handedness match, try any hand (for crossed hands)
        if best_match_id == -1:
            for hand_id, tracked in self._tracked_hands.items():
                dist = self._landmarks_distance(landmarks, tracked["landmarks"])
                if dist < best_distance * 0.7:  # Stricter threshold for different handedness
                    best_distance = dist
                    best_match_id = hand_id

        return best_match_id

    def _smooth_landmarks(self, hand_id: int, new_landmarks: list) -> list:
        """
        Apply exponential smoothing to landmarks for fluid motion.

        Args:
            hand_id: The hand's tracking ID
            new_landmarks: New detected landmarks

        Returns:
            Smoothed landmarks
        """
        if self.smoothing_factor <= 0:
            return new_landmarks

        if hand_id not in self._landmark_history:
            self._landmark_history[hand_id] = new_landmarks
            return new_landmarks

        old_landmarks = self._landmark_history[hand_id]
        smoothed = []

        alpha = self.smoothing_factor
        for i in range(len(new_landmarks)):
            x = alpha * old_landmarks[i][0] + (1 - alpha) * new_landmarks[i][0]
            y = alpha * old_landmarks[i][1] + (1 - alpha) * new_landmarks[i][1]
            z = alpha * old_landmarks[i][2] + (1 - alpha) * new_landmarks[i][2]
            smoothed.append((x, y, z))

        self._landmark_history[hand_id] = smoothed
        return smoothed

    def _cleanup_lost_hands(self):
        """Remove hands that haven't been seen for too long."""
        to_remove = []
        for hand_id, tracked in self._tracked_hands.items():
            if tracked["frames_lost"] > self.persistence_frames:
                to_remove.append(hand_id)

        for hand_id in to_remove:
            del self._tracked_hands[hand_id]
            if hand_id in self._landmark_history:
                del self._landmark_history[hand_id]

    def _is_valid_hand(self, landmarks: list, confidence: float) -> bool:
        """
        Validate if detected landmarks form a valid hand shape.
        Strict anti-face filtering while accepting all hand poses.
        """
        if len(landmarks) != 21:
            return False

        # Indices
        WRIST, THUMB_CMC, THUMB_MCP, THUMB_TIP = 0, 1, 2, 4
        INDEX_MCP, INDEX_TIP = 5, 8
        MIDDLE_MCP, MIDDLE_TIP = 9, 12
        RING_MCP, RING_TIP = 13, 16
        PINKY_MCP, PINKY_TIP = 17, 20

        # Key points
        wrist = landmarks[WRIST]
        thumb_cmc = landmarks[THUMB_CMC]
        thumb_mcp = landmarks[THUMB_MCP]
        thumb_tip = landmarks[THUMB_TIP]
        index_mcp = landmarks[INDEX_MCP]
        middle_mcp = landmarks[MIDDLE_MCP]
        ring_mcp = landmarks[RING_MCP]
        pinky_mcp = landmarks[PINKY_MCP]

        index_tip = landmarks[INDEX_TIP]
        middle_tip = landmarks[MIDDLE_TIP]
        ring_tip = landmarks[RING_TIP]
        pinky_tip = landmarks[PINKY_TIP]

        tips = [index_tip, middle_tip, ring_tip, pinky_tip]
        mcps = [index_mcp, middle_mcp, ring_mcp, pinky_mcp]

        # Bounding box
        xs = [lm[0] for lm in landmarks]
        ys = [lm[1] for lm in landmarks]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        width = max_x - min_x
        height = max_y - min_y

        # === Basic size check ===
        if width < 0.03 or height < 0.03:
            return False

        # === ANTI-FACE 1: Thumb must be offset from finger line ===
        # (Only check if knuckle line is long enough - relaxed for fists)
        kx = index_mcp[0] - pinky_mcp[0]
        ky = index_mcp[1] - pinky_mcp[1]
        klen = (kx*kx + ky*ky)**0.5

        if klen > 0.025:  # Only check for open hands
            # Thumb CMC offset
            tx, ty = thumb_cmc[0] - pinky_mcp[0], thumb_cmc[1] - pinky_mcp[1]
            offset1 = abs(kx*ty - ky*tx) / klen

            # Thumb MCP offset
            tx, ty = thumb_mcp[0] - pinky_mcp[0], thumb_mcp[1] - pinky_mcp[1]
            offset2 = abs(kx*ty - ky*tx) / klen

            if max(offset1, offset2) < 0.02:
                return False

        # === ANTI-FACE 2: Wrist position check ===
        # For fists facing camera, wrist may appear centered
        # So we use a very relaxed check - only reject if wrist is exactly in the middle
        wrist_x_ratio = (wrist[0] - min_x) / width if width > 0 else 0.5
        wrist_y_ratio = (wrist[1] - min_y) / height if height > 0 else 0.5

        # Only reject if wrist is very centered on BOTH axes (likely a face)
        wrist_very_centered = (0.35 < wrist_x_ratio < 0.65 and 0.35 < wrist_y_ratio < 0.65)
        if wrist_very_centered:
            # Additional check: if hand is small, it might be a fist - allow it
            if width > 0.08 and height > 0.08:
                return False

        # === ANTI-FACE 3: Fingers direction (only for fully open hands) ===
        def finger_len(mcp, tip):
            return ((tip[0]-mcp[0])**2 + (tip[1]-mcp[1])**2)**0.5

        # Check finger lengths
        finger_lengths = [finger_len(mcp, tip) for mcp, tip in
                         [(index_mcp, index_tip), (middle_mcp, middle_tip),
                          (ring_mcp, ring_tip), (pinky_mcp, pinky_tip)]]

        # Only check direction coherence if ALL fingers are extended (fully open hand)
        # This allows poses like peace sign, pointing, etc.
        min_finger_len = min(finger_lengths)

        if min_finger_len > 0.04:  # All fingers extended
            def finger_dir(mcp, tip):
                dx, dy = tip[0] - mcp[0], tip[1] - mcp[1]
                length = (dx*dx + dy*dy)**0.5
                if length > 0.01:
                    return (dx/length, dy/length)
                return None

            dirs = []
            for mcp, tip in [(index_mcp, index_tip), (middle_mcp, middle_tip),
                             (ring_mcp, ring_tip), (pinky_mcp, pinky_tip)]:
                d = finger_dir(mcp, tip)
                if d:
                    dirs.append(d)

            if len(dirs) >= 3:
                coherent = 0
                total = 0
                for i in range(len(dirs)):
                    for j in range(i+1, len(dirs)):
                        dot = dirs[i][0]*dirs[j][0] + dirs[i][1]*dirs[j][1]
                        total += 1
                        if dot > 0.0:
                            coherent += 1

                if total > 0 and coherent < total * 0.4:
                    return False

        # === ANTI-FACE 4: Palm length check ===
        mcp_cx = sum(m[0] for m in mcps) / 4
        mcp_cy = sum(m[1] for m in mcps) / 4
        palm_len = ((wrist[0]-mcp_cx)**2 + (wrist[1]-mcp_cy)**2)**0.5

        if palm_len < 0.02:
            return False

        return True

    def process(self, frame) -> list:
        """
        Process a frame to detect hands with tracking and smoothing.

        Args:
            frame: BGR image from OpenCV

        Returns:
            List of HandData for each detected hand
        """
        # Convert BGR -> RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process image
        self.results = self.hands.process(rgb_frame)

        # Mark all tracked hands as potentially lost this frame
        for hand_id in self._tracked_hands:
            self._tracked_hands[hand_id]["frames_lost"] += 1

        # Process detected hands
        detected_hand_ids = set()

        if self.results.multi_hand_landmarks:
            for idx, hand_landmarks in enumerate(self.results.multi_hand_landmarks):
                # Get hand type (left/right)
                handedness = "Unknown"
                confidence = 0.0

                if self.results.multi_handedness:
                    hand_info = self.results.multi_handedness[idx]
                    handedness = hand_info.classification[0].label
                    confidence = hand_info.classification[0].score

                # Convert landmarks to list of tuples (x, y, z)
                landmarks = []
                for lm in hand_landmarks.landmark:
                    landmarks.append((lm.x, lm.y, lm.z))

                # Validate hand shape to filter false positives
                if not self._is_valid_hand(landmarks, confidence):
                    continue

                # Match to existing tracked hand or create new
                hand_id = self._match_hand_to_tracked(landmarks, handedness)

                if hand_id == -1:
                    # New hand
                    hand_id = self._next_hand_id
                    self._next_hand_id += 1

                # Apply smoothing
                smoothed_landmarks = self._smooth_landmarks(hand_id, landmarks)

                # Update tracking state
                self._tracked_hands[hand_id] = {
                    "landmarks": smoothed_landmarks,
                    "handedness": handedness,
                    "confidence": confidence,
                    "frames_lost": 0
                }
                detected_hand_ids.add(hand_id)

        # Build output list including persistent hands
        self.hands_data = []

        for hand_id, tracked in self._tracked_hands.items():
            # Include hands that are either currently detected or within persistence window
            if tracked["frames_lost"] <= self.persistence_frames:
                # Fade confidence for lost hands
                effective_confidence = tracked["confidence"]
                if tracked["frames_lost"] > 0:
                    fade = 1.0 - (tracked["frames_lost"] / (self.persistence_frames + 1))
                    effective_confidence *= fade

                self.hands_data.append(HandData(
                    landmarks=tracked["landmarks"],
                    handedness=tracked["handedness"],
                    confidence=effective_confidence,
                    hand_id=hand_id,
                    frames_since_seen=tracked["frames_lost"]
                ))

        # Cleanup old hands
        self._cleanup_lost_hands()

        return self.hands_data

    # Hand connections (same as MediaPipe)
    HAND_CONNECTIONS = [
        (0, 1), (1, 2), (2, 3), (3, 4),  # Thumb
        (0, 5), (5, 6), (6, 7), (7, 8),  # Index
        (0, 9), (9, 10), (10, 11), (11, 12),  # Middle
        (0, 13), (13, 14), (14, 15), (15, 16),  # Ring
        (0, 17), (17, 18), (18, 19), (19, 20),  # Pinky
        (5, 9), (9, 13), (13, 17)  # Palm
    ]

    def draw(self, frame, draw_landmarks: bool = True, draw_connections: bool = True) -> None:
        """
        Draw detected hands on frame using smoothed landmarks.

        Args:
            frame: Image to draw on
            draw_landmarks: Draw landmark points
            draw_connections: Draw connections between landmarks
        """
        if not self.hands_data:
            return

        for hand_data in self.hands_data:
            self.draw_landmarks(frame, hand_data.landmarks, hand_data.handedness,
                               draw_landmarks, draw_connections)

    def draw_landmarks(self, frame, landmarks: list, handedness: str = "Right",
                       draw_points: bool = True, draw_connections: bool = True) -> None:
        """
        Draw landmarks from a provided list (for threaded mode).

        Args:
            frame: Image to draw on
            landmarks: List of 21 (x, y, z) normalized landmarks
            handedness: "Left" or "Right"
            draw_points: Draw landmark points
            draw_connections: Draw connections between landmarks
        """
        if not landmarks or len(landmarks) != 21:
            return

        h, w = frame.shape[:2]

        # Color based on hand (left = blue, right = green)
        if handedness == "Right":
            landmark_color = (0, 255, 0)  # Green for right hand
            connection_color = (0, 200, 0)
        else:
            landmark_color = (255, 0, 0)  # Blue for left hand
            connection_color = (200, 0, 0)

        # Convert normalized landmarks to pixel coordinates
        points = []
        for lm in landmarks:
            px = int(lm[0] * w)
            py = int(lm[1] * h)
            points.append((px, py))

        # Draw connections
        if draw_connections:
            for start_idx, end_idx in self.HAND_CONNECTIONS:
                cv2.line(frame, points[start_idx], points[end_idx], connection_color, 2)

        # Draw landmarks
        if draw_points:
            for px, py in points:
                cv2.circle(frame, (px, py), 4, landmark_color, -1)
                cv2.circle(frame, (px, py), 5, connection_color, 1)

    def get_hand_count(self) -> int:
        """Return number of detected hands."""
        return len(self.hands_data)

    def get_hands_info(self) -> list:
        """
        Return information about detected hands.

        Returns:
            List of dictionaries with info for each hand
        """
        info = []
        for hand in self.hands_data:
            # MediaPipe detects hand based on anatomical shape (thumb position)
            # "Left" = left hand, "Right" = right hand
            display_hand = "Left" if hand.handedness == "Left" else "Right"
            info.append({
                "type": display_hand,
                "confidence": hand.confidence,
                "landmarks_count": len(hand.landmarks)
            })
        return info

    def reset_tracking(self):
        """Reset all tracking state. Useful when scene changes significantly."""
        self._tracked_hands.clear()
        self._landmark_history.clear()
        self._next_hand_id = 0
        self.hands_data = []

    def set_confidence(self, detection: float = None, tracking: float = None):
        """
        Update confidence thresholds (requires reinitializing MediaPipe).

        Args:
            detection: New detection threshold (0.0 - 1.0)
            tracking: New tracking threshold (0.0 - 1.0)
        """
        changed = False

        if detection is not None:
            detection = max(0.1, min(1.0, detection))
            if detection != self.min_detection_confidence:
                self.min_detection_confidence = detection
                changed = True

        if tracking is not None:
            tracking = max(0.1, min(1.0, tracking))
            if tracking != self.min_tracking_confidence:
                self.min_tracking_confidence = tracking
                changed = True

        if changed:
            # Reinitialize MediaPipe with new parameters
            self.hands.close()
            self.hands = self.mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=self.max_hands,
                model_complexity=self.model_complexity,
                min_detection_confidence=self.min_detection_confidence,
                min_tracking_confidence=self.min_tracking_confidence
            )
            # Reset tracking state when parameters change
            self.reset_tracking()

    def get_confidence(self) -> tuple:
        """
        Return current confidence thresholds.

        Returns:
            Tuple (detection_confidence, tracking_confidence)
        """
        return (self.min_detection_confidence, self.min_tracking_confidence)

    def release(self):
        """Release resources."""
        self.hands.close()


# Landmark names for reference
HAND_LANDMARKS = {
    0: "WRIST",
    1: "THUMB_CMC",
    2: "THUMB_MCP",
    3: "THUMB_IP",
    4: "THUMB_TIP",
    5: "INDEX_FINGER_MCP",
    6: "INDEX_FINGER_PIP",
    7: "INDEX_FINGER_DIP",
    8: "INDEX_FINGER_TIP",
    9: "MIDDLE_FINGER_MCP",
    10: "MIDDLE_FINGER_PIP",
    11: "MIDDLE_FINGER_DIP",
    12: "MIDDLE_FINGER_TIP",
    13: "RING_FINGER_MCP",
    14: "RING_FINGER_PIP",
    15: "RING_FINGER_DIP",
    16: "RING_FINGER_TIP",
    17: "PINKY_MCP",
    18: "PINKY_PIP",
    19: "PINKY_DIP",
    20: "PINKY_TIP"
}
