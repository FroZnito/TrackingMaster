"""
TrackingMaster v0.3 - Finger Tracker Module
High-precision finger state detection, number counting, and gesture recognition.
With debug mode, confidence scores, and adjustable thresholds.
"""

import math
import json
import csv
import os
from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Optional, Tuple, List, Dict


class Gesture(Enum):
    """Recognized hand gestures (17 total as per ROADMAP)."""
    NONE = "none"
    FIST = "fist"
    OPEN_HAND = "open_hand"
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    PEACE = "peace"
    TWO = "two"  # Two fingers together (vs peace spread)
    POINTING = "pointing"
    OK = "ok"
    ROCK = "rock"
    THREE = "three"  # Three fingers extended
    FOUR = "four"  # Four fingers extended
    GUN = "gun"
    CALL_ME = "call_me"
    LOSER = "loser"  # L-shape (thumb + index at 90°)
    PINKY_UP = "pinky_up"  # Only pinky extended
    THUMB_INDEX_PINKY = "thumb_index_pinky"  # Thumb, index, pinky extended
    MIDDLE_FINGER = "middle_finger"


@dataclass
class FingerState:
    """State of all fingers on a hand."""
    thumb: bool
    index: bool
    middle: bool
    ring: bool
    pinky: bool

    def count_extended(self) -> int:
        return sum([self.thumb, self.index, self.middle, self.ring, self.pinky])

    def as_list(self) -> list:
        return [self.thumb, self.index, self.middle, self.ring, self.pinky]

    def as_tuple(self) -> tuple:
        return (self.thumb, self.index, self.middle, self.ring, self.pinky)

    def as_dict(self) -> dict:
        return {"thumb": self.thumb, "index": self.index, "middle": self.middle,
                "ring": self.ring, "pinky": self.pinky}


@dataclass
class FingerConfidence:
    """Confidence score for each finger (0-5 criteria met)."""
    thumb: int  # 0-5
    index: int  # 0-5
    middle: int  # 0-5
    ring: int  # 0-5
    pinky: int  # 0-5

    def as_dict(self) -> dict:
        return {"thumb": self.thumb, "index": self.index, "middle": self.middle,
                "ring": self.ring, "pinky": self.pinky}

    def as_percentages(self) -> dict:
        """Return confidence as percentages (0-100%)."""
        return {
            "thumb": self.thumb * 20,
            "index": self.index * 20,
            "middle": self.middle * 20,
            "ring": self.ring * 20,
            "pinky": self.pinky * 20
        }


@dataclass
class FingerDebugInfo:
    """Debug information for finger analysis."""
    curl_angles: Dict[str, float]  # Curl angle per finger
    confidence_scores: FingerConfidence
    finger_states: FingerState
    spread_angles: Dict[str, float]  # Spread between adjacent fingers
    thresholds: Dict[str, float]  # Current threshold values


@dataclass
class HandAnalysis:
    """Complete analysis of a hand."""
    finger_states: FingerState
    finger_count: int
    gesture: Gesture
    gesture_name: str
    confidence: FingerConfidence
    debug_info: Optional[FingerDebugInfo] = None


@dataclass
class TrackingFrame:
    """Single frame of tracking data for export."""
    timestamp: str
    frame_number: int
    hand_type: str
    finger_count: int
    finger_states: Dict[str, bool]
    gesture: str
    confidence: Dict[str, int]
    curl_angles: Dict[str, float]


class FingerTracker:
    """High-precision finger tracking with debug mode and adjustable thresholds."""

    # Landmark indices
    WRIST = 0
    THUMB_CMC, THUMB_MCP, THUMB_IP, THUMB_TIP = 1, 2, 3, 4
    INDEX_MCP, INDEX_PIP, INDEX_DIP, INDEX_TIP = 5, 6, 7, 8
    MIDDLE_MCP, MIDDLE_PIP, MIDDLE_DIP, MIDDLE_TIP = 9, 10, 11, 12
    RING_MCP, RING_PIP, RING_DIP, RING_TIP = 13, 14, 15, 16
    PINKY_MCP, PINKY_PIP, PINKY_DIP, PINKY_TIP = 17, 18, 19, 20

    def __init__(self, smoothing_frames: int = 3):
        self.smoothing_frames = smoothing_frames
        self._finger_history = {}
        self._count_history = {}

        # Adjustable thresholds
        self._curl_threshold = 70  # Degrees - finger curl threshold
        self._thumb_curl_threshold = 35  # Thumb curl threshold
        self._spread_threshold = 20  # Degrees for V-shape detection
        self._ok_distance = 0.07  # Distance for OK gesture

        # Threshold limits
        self._curl_min, self._curl_max = 40, 120
        self._thumb_curl_min, self._thumb_curl_max = 20, 60
        self._spread_min, self._spread_max = 10, 40

        # Debug mode
        self._debug_mode = False
        self._last_debug_info = {}

    # ===== THRESHOLD GETTERS/SETTERS =====

    @property
    def curl_threshold(self) -> float:
        return self._curl_threshold

    @curl_threshold.setter
    def curl_threshold(self, value: float):
        self._curl_threshold = max(self._curl_min, min(self._curl_max, value))

    @property
    def thumb_curl_threshold(self) -> float:
        return self._thumb_curl_threshold

    @thumb_curl_threshold.setter
    def thumb_curl_threshold(self, value: float):
        self._thumb_curl_threshold = max(self._thumb_curl_min, min(self._thumb_curl_max, value))

    @property
    def spread_threshold(self) -> float:
        return self._spread_threshold

    @spread_threshold.setter
    def spread_threshold(self, value: float):
        self._spread_threshold = max(self._spread_min, min(self._spread_max, value))

    def get_thresholds(self) -> Dict[str, float]:
        """Get all current thresholds."""
        return {
            "curl": self._curl_threshold,
            "thumb_curl": self._thumb_curl_threshold,
            "spread": self._spread_threshold,
            "ok_distance": self._ok_distance
        }

    def adjust_curl_threshold(self, delta: float) -> float:
        """Adjust curl threshold by delta. Returns new value."""
        self.curl_threshold = self._curl_threshold + delta
        return self._curl_threshold

    def adjust_thumb_curl_threshold(self, delta: float) -> float:
        """Adjust thumb curl threshold by delta. Returns new value."""
        self.thumb_curl_threshold = self._thumb_curl_threshold + delta
        return self._thumb_curl_threshold

    def adjust_spread_threshold(self, delta: float) -> float:
        """Adjust spread threshold by delta. Returns new value."""
        self.spread_threshold = self._spread_threshold + delta
        return self._spread_threshold

    # ===== DEBUG MODE =====

    @property
    def debug_mode(self) -> bool:
        return self._debug_mode

    @debug_mode.setter
    def debug_mode(self, value: bool):
        self._debug_mode = value

    def toggle_debug_mode(self) -> bool:
        self._debug_mode = not self._debug_mode
        return self._debug_mode

    def get_last_debug_info(self, hand_id: int = 0) -> Optional[FingerDebugInfo]:
        """Get last debug info for a hand."""
        return self._last_debug_info.get(hand_id)

    # ===== UTILITY FUNCTIONS =====

    def _dist(self, p1: tuple, p2: tuple) -> float:
        return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

    def _angle(self, v1: tuple, v2: tuple) -> float:
        dot = v1[0] * v2[0] + v1[1] * v2[1]
        mag1 = math.sqrt(v1[0]**2 + v1[1]**2)
        mag2 = math.sqrt(v2[0]**2 + v2[1]**2)
        if mag1 < 0.001 or mag2 < 0.001:
            return 0
        cos_a = max(-1, min(1, dot / (mag1 * mag2)))
        return math.degrees(math.acos(cos_a))

    def _finger_curl(self, lm: list, mcp: int, pip: int, dip: int, tip: int) -> float:
        v1 = (lm[pip][0] - lm[mcp][0], lm[pip][1] - lm[mcp][1])
        v2 = (lm[dip][0] - lm[pip][0], lm[dip][1] - lm[pip][1])
        v3 = (lm[tip][0] - lm[dip][0], lm[tip][1] - lm[dip][1])
        return self._angle(v1, v2) + self._angle(v2, v3)

    def _thumb_curl(self, lm: list) -> float:
        v1 = (lm[self.THUMB_MCP][0] - lm[self.THUMB_CMC][0],
              lm[self.THUMB_MCP][1] - lm[self.THUMB_CMC][1])
        v2 = (lm[self.THUMB_IP][0] - lm[self.THUMB_MCP][0],
              lm[self.THUMB_IP][1] - lm[self.THUMB_MCP][1])
        v3 = (lm[self.THUMB_TIP][0] - lm[self.THUMB_IP][0],
              lm[self.THUMB_TIP][1] - lm[self.THUMB_IP][1])
        return self._angle(v1, v2) + self._angle(v2, v3)

    def _get_finger_spread(self, lm: list, tip1: int, mcp1: int, tip2: int, mcp2: int) -> float:
        v1 = (lm[tip1][0] - lm[mcp1][0], lm[tip1][1] - lm[mcp1][1])
        v2 = (lm[tip2][0] - lm[mcp2][0], lm[tip2][1] - lm[mcp2][1])
        return self._angle(v1, v2)

    # ===== FINGER DETECTION WITH CONFIDENCE =====

    def _is_thumb_extended_with_confidence(self, lm: list, handedness: str) -> Tuple[bool, int]:
        """Returns (is_extended, confidence_score 0-5)."""
        thumb_tip = lm[self.THUMB_TIP]
        thumb_ip = lm[self.THUMB_IP]
        thumb_mcp = lm[self.THUMB_MCP]
        index_mcp = lm[self.INDEX_MCP]
        middle_mcp = lm[self.MIDDLE_MCP]
        wrist = lm[self.WRIST]

        scores = []

        # 1. Curl angle
        curl = self._thumb_curl(lm)
        is_straight = curl < self._thumb_curl_threshold
        scores.append(is_straight)

        # 2. Thumb tip distance from palm
        palm_x = (wrist[0] + middle_mcp[0]) / 2
        palm_y = (wrist[1] + middle_mcp[1]) / 2
        tip_to_palm = self._dist(thumb_tip, (palm_x, palm_y))
        mcp_to_palm = self._dist(thumb_mcp, (palm_x, palm_y))
        extended_from_palm = tip_to_palm > mcp_to_palm * 1.05
        scores.append(extended_from_palm)

        # 3. Lateral position
        if handedness == "Right":
            lateral_ok = thumb_tip[0] < index_mcp[0]
        else:
            lateral_ok = thumb_tip[0] > index_mcp[0]
        scores.append(lateral_ok)

        # 4. Not curled into palm
        tip_to_middle = self._dist(thumb_tip, middle_mcp)
        not_curled = tip_to_middle > 0.05
        scores.append(not_curled)

        # 5. Tip farther from wrist than IP
        tip_to_wrist = self._dist(thumb_tip, wrist)
        ip_to_wrist = self._dist(thumb_ip, wrist)
        tip_extended = tip_to_wrist > ip_to_wrist * 0.95
        scores.append(tip_extended)

        confidence = sum(scores)
        is_extended = confidence >= 3

        return is_extended, confidence

    def _is_finger_extended_with_confidence(self, lm: list, mcp: int, pip: int, dip: int, tip: int) -> Tuple[bool, int]:
        """Returns (is_extended, confidence_score 0-5)."""
        tip_pos = lm[tip]
        pip_pos = lm[pip]
        mcp_pos = lm[mcp]
        dip_pos = lm[dip]
        wrist = lm[self.WRIST]

        scores = []

        # 1. Curl angle
        curl = self._finger_curl(lm, mcp, pip, dip, tip)
        is_straight = curl < self._curl_threshold
        scores.append(is_straight)

        # 2. Tip above PIP
        tip_above_pip = tip_pos[1] < pip_pos[1]
        scores.append(tip_above_pip)

        # 3. Straightness ratio
        direct_dist = self._dist(mcp_pos, tip_pos)
        seg_sum = (self._dist(mcp_pos, pip_pos) +
                   self._dist(pip_pos, dip_pos) +
                   self._dist(dip_pos, tip_pos))
        straightness = direct_dist / seg_sum if seg_sum > 0.001 else 0
        is_geom_straight = straightness > 0.82
        scores.append(is_geom_straight)

        # 4. Tip farther from wrist than PIP
        tip_to_wrist = self._dist(tip_pos, wrist)
        pip_to_wrist = self._dist(pip_pos, wrist)
        tip_farther = tip_to_wrist > pip_to_wrist * 0.98
        scores.append(tip_farther)

        # 5. DIP above PIP
        dip_above_pip = dip_pos[1] < pip_pos[1] + 0.02
        scores.append(dip_above_pip)

        confidence = sum(scores)
        is_extended = confidence >= 3

        return is_extended, confidence

    def get_finger_states_with_confidence(self, landmarks: list, handedness: str = "Right") -> Tuple[FingerState, FingerConfidence]:
        """Get finger states and confidence scores."""
        if len(landmarks) != 21:
            return (FingerState(False, False, False, False, False),
                    FingerConfidence(0, 0, 0, 0, 0))

        thumb_ext, thumb_conf = self._is_thumb_extended_with_confidence(landmarks, handedness)
        index_ext, index_conf = self._is_finger_extended_with_confidence(
            landmarks, self.INDEX_MCP, self.INDEX_PIP, self.INDEX_DIP, self.INDEX_TIP)
        middle_ext, middle_conf = self._is_finger_extended_with_confidence(
            landmarks, self.MIDDLE_MCP, self.MIDDLE_PIP, self.MIDDLE_DIP, self.MIDDLE_TIP)
        ring_ext, ring_conf = self._is_finger_extended_with_confidence(
            landmarks, self.RING_MCP, self.RING_PIP, self.RING_DIP, self.RING_TIP)
        pinky_ext, pinky_conf = self._is_finger_extended_with_confidence(
            landmarks, self.PINKY_MCP, self.PINKY_PIP, self.PINKY_DIP, self.PINKY_TIP)

        states = FingerState(thumb_ext, index_ext, middle_ext, ring_ext, pinky_ext)
        confidence = FingerConfidence(thumb_conf, index_conf, middle_conf, ring_conf, pinky_conf)

        return states, confidence

    def get_finger_states(self, landmarks: list, handedness: str = "Right") -> FingerState:
        """Get finger states (backward compatible)."""
        states, _ = self.get_finger_states_with_confidence(landmarks, handedness)
        return states

    def get_curl_angles(self, landmarks: list) -> Dict[str, float]:
        """Get curl angles for all fingers."""
        if len(landmarks) != 21:
            return {"thumb": 0, "index": 0, "middle": 0, "ring": 0, "pinky": 0}

        return {
            "thumb": round(self._thumb_curl(landmarks), 1),
            "index": round(self._finger_curl(landmarks, self.INDEX_MCP, self.INDEX_PIP,
                                              self.INDEX_DIP, self.INDEX_TIP), 1),
            "middle": round(self._finger_curl(landmarks, self.MIDDLE_MCP, self.MIDDLE_PIP,
                                               self.MIDDLE_DIP, self.MIDDLE_TIP), 1),
            "ring": round(self._finger_curl(landmarks, self.RING_MCP, self.RING_PIP,
                                             self.RING_DIP, self.RING_TIP), 1),
            "pinky": round(self._finger_curl(landmarks, self.PINKY_MCP, self.PINKY_PIP,
                                              self.PINKY_DIP, self.PINKY_TIP), 1)
        }

    def get_spread_angles(self, landmarks: list) -> Dict[str, float]:
        """Get spread angles between adjacent fingers."""
        if len(landmarks) != 21:
            return {"index_middle": 0, "middle_ring": 0, "ring_pinky": 0}

        return {
            "index_middle": round(self._get_finger_spread(
                landmarks, self.INDEX_TIP, self.INDEX_MCP, self.MIDDLE_TIP, self.MIDDLE_MCP), 1),
            "middle_ring": round(self._get_finger_spread(
                landmarks, self.MIDDLE_TIP, self.MIDDLE_MCP, self.RING_TIP, self.RING_MCP), 1),
            "ring_pinky": round(self._get_finger_spread(
                landmarks, self.RING_TIP, self.RING_MCP, self.PINKY_TIP, self.PINKY_MCP), 1)
        }

    def get_finger_states_smoothed(self, landmarks: list, handedness: str, hand_id: int) -> FingerState:
        """Get finger states with temporal smoothing."""
        current = self.get_finger_states(landmarks, handedness)

        if hand_id not in self._finger_history:
            self._finger_history[hand_id] = deque(maxlen=self.smoothing_frames)

        self._finger_history[hand_id].append(current)

        if len(self._finger_history[hand_id]) < 2:
            return current

        history = list(self._finger_history[hand_id])
        threshold = len(history) / 2

        return FingerState(
            thumb=sum(1 for s in history if s.thumb) > threshold,
            index=sum(1 for s in history if s.index) > threshold,
            middle=sum(1 for s in history if s.middle) > threshold,
            ring=sum(1 for s in history if s.ring) > threshold,
            pinky=sum(1 for s in history if s.pinky) > threshold
        )

    def count_fingers(self, landmarks: list, handedness: str = "Right") -> int:
        state = self.get_finger_states(landmarks, handedness)
        return state.count_extended()

    def recognize_gesture(self, landmarks: list, handedness: str = "Right") -> Gesture:
        """Recognize special gesture patterns (17 gestures)."""
        if len(landmarks) != 21:
            return Gesture.NONE

        state = self.get_finger_states(landmarks, handedness)
        pattern = state.as_tuple()
        count = state.count_extended()

        thumb_tip = landmarks[self.THUMB_TIP]
        thumb_mcp = landmarks[self.THUMB_MCP]
        index_tip = landmarks[self.INDEX_TIP]

        thumb_up = thumb_tip[1] < thumb_mcp[1] - 0.03
        thumb_down = thumb_tip[1] > thumb_mcp[1] + 0.03
        thumb_index_dist = self._dist(thumb_tip, index_tip)

        index_middle_spread = self._get_finger_spread(
            landmarks, self.INDEX_TIP, self.INDEX_MCP, self.MIDDLE_TIP, self.MIDDLE_MCP)

        # Count-based gestures
        if count == 0:
            return Gesture.FIST
        if count == 5:
            return Gesture.OPEN_HAND

        # Single finger gestures
        if pattern == (True, False, False, False, False):
            return Gesture.THUMBS_UP if thumb_up else (Gesture.THUMBS_DOWN if thumb_down else Gesture.THUMBS_UP)

        if pattern == (False, True, False, False, False):
            return Gesture.POINTING
        if pattern == (False, False, True, False, False):
            return Gesture.MIDDLE_FINGER
        if pattern == (False, False, False, False, True):
            return Gesture.PINKY_UP

        # Two finger gestures
        if pattern == (False, True, True, False, False):
            # Peace vs Two: differentiated by spread angle
            if index_middle_spread > self._spread_threshold:
                return Gesture.PEACE
            else:
                return Gesture.TWO

        if pattern == (True, True, False, False, False):
            # Check for L-shape (Loser) vs Gun
            # Loser: thumb and index form roughly 90 degree angle
            thumb_vec = (thumb_tip[0] - thumb_mcp[0], thumb_tip[1] - thumb_mcp[1])
            index_vec = (index_tip[0] - landmarks[self.INDEX_MCP][0],
                        index_tip[1] - landmarks[self.INDEX_MCP][1])
            angle = self._angle(thumb_vec, index_vec)
            if 70 < angle < 110:
                return Gesture.LOSER
            return Gesture.GUN

        if pattern == (True, False, False, False, True):
            return Gesture.CALL_ME

        # Three finger gestures
        if pattern == (False, True, True, True, False):
            return Gesture.THREE

        # Rock gestures (index + pinky, with or without thumb)
        if pattern == (False, True, False, False, True):
            return Gesture.ROCK
        if pattern == (True, True, False, False, True):
            return Gesture.THUMB_INDEX_PINKY

        # Four finger gestures
        if pattern == (False, True, True, True, True):
            return Gesture.FOUR

        # OK gesture (special case - requires distance check)
        if thumb_index_dist < self._ok_distance and state.middle and state.ring and state.pinky:
            return Gesture.OK

        return Gesture.NONE

    def get_gesture_name(self, gesture: Gesture) -> str:
        names = {
            Gesture.NONE: "",
            Gesture.FIST: "Fist",
            Gesture.OPEN_HAND: "Open Hand",
            Gesture.THUMBS_UP: "Thumbs Up",
            Gesture.THUMBS_DOWN: "Thumbs Down",
            Gesture.PEACE: "Peace",
            Gesture.TWO: "Two",
            Gesture.POINTING: "Pointing",
            Gesture.OK: "OK",
            Gesture.ROCK: "Rock",
            Gesture.THREE: "Three",
            Gesture.FOUR: "Four",
            Gesture.GUN: "Gun",
            Gesture.CALL_ME: "Call Me",
            Gesture.LOSER: "Loser",
            Gesture.PINKY_UP: "Pinky Up",
            Gesture.THUMB_INDEX_PINKY: "Rock On",
            Gesture.MIDDLE_FINGER: "Middle Finger"
        }
        return names.get(gesture, "")

    def analyze_hand(self, landmarks: list, handedness: str, hand_id: int = 0) -> HandAnalysis:
        """Complete analysis of a single hand with debug info."""
        if len(landmarks) != 21:
            return HandAnalysis(
                finger_states=FingerState(False, False, False, False, False),
                finger_count=0, gesture=Gesture.NONE, gesture_name="",
                confidence=FingerConfidence(0, 0, 0, 0, 0), debug_info=None
            )

        # Get states with confidence
        states, confidence = self.get_finger_states_with_confidence(landmarks, handedness)

        # Apply smoothing
        smoothed_states = self.get_finger_states_smoothed(landmarks, handedness, hand_id)
        count = smoothed_states.count_extended()

        gesture = self.recognize_gesture(landmarks, handedness)
        gesture_name = self.get_gesture_name(gesture)

        # Build debug info if enabled
        debug_info = None
        if self._debug_mode:
            debug_info = FingerDebugInfo(
                curl_angles=self.get_curl_angles(landmarks),
                confidence_scores=confidence,
                finger_states=states,
                spread_angles=self.get_spread_angles(landmarks),
                thresholds=self.get_thresholds()
            )
            self._last_debug_info[hand_id] = debug_info

        return HandAnalysis(
            finger_states=smoothed_states,
            finger_count=count,
            gesture=gesture,
            gesture_name=gesture_name,
            confidence=confidence,
            debug_info=debug_info
        )

    def clear_history(self, hand_id: int = None):
        if hand_id is None:
            self._finger_history.clear()
            self._count_history.clear()
        else:
            self._finger_history.pop(hand_id, None)
            self._count_history.pop(hand_id, None)


class TwoHandNumberRecognizer:
    """Combines two hands to form a two-digit number."""

    def __init__(self, right_handed: bool = True):
        self.right_handed = right_handed
        self._history = deque(maxlen=5)

    def get_combined_number(self, right_count: int, left_count: int) -> Optional[int]:
        if right_count == 0 and left_count == 0:
            return None

        if self.right_handed:
            first, second = right_count, left_count
        else:
            first, second = left_count, right_count

        combined = first * 10 + second
        self._history.append(combined)

        if len(self._history) >= 2:
            from collections import Counter
            counts = Counter(self._history).most_common(1)
            # Safe access: check if Counter returned any results
            if counts:
                return counts[0][0]
        return combined

    def get_number_string(self, right_count: int, left_count: int) -> str:
        combined = self.get_combined_number(right_count, left_count)
        if combined is None:
            return "00"
        return f"{right_count}{left_count}" if self.right_handed else f"{left_count}{right_count}"

    def clear_history(self):
        self._history.clear()


class TrackingDataRecorder:
    """Records tracking data for export to JSON/CSV in organized folders."""

    # Base directories
    DATA_DIR = "data"
    JSON_DIR = "data/json"
    CSV_DIR = "data/csv"

    def __init__(self):
        self.is_recording = False
        self.frames: List[TrackingFrame] = []
        self.start_time: Optional[datetime] = None
        self.frame_counter = 0
        self._ensure_directories()

    def _ensure_directories(self):
        """Create data directories if they don't exist."""
        for directory in [self.DATA_DIR, self.JSON_DIR, self.CSV_DIR]:
            if not os.path.exists(directory):
                os.makedirs(directory)

    def start_recording(self):
        """Start a new recording session."""
        self._ensure_directories()
        self.is_recording = True
        self.frames = []
        self.start_time = datetime.now()
        self.frame_counter = 0

    def stop_recording(self):
        """Stop recording."""
        self.is_recording = False

    def toggle_recording(self) -> bool:
        """Toggle recording state. Returns new state."""
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()
        return self.is_recording

    def add_frame(self, hand_type: str, analysis: HandAnalysis, curl_angles: Dict[str, float]):
        """Add a frame of tracking data."""
        if not self.is_recording:
            return

        frame = TrackingFrame(
            timestamp=datetime.now().isoformat(),
            frame_number=self.frame_counter,
            hand_type=hand_type,
            finger_count=analysis.finger_count,
            finger_states=analysis.finger_states.as_dict(),
            gesture=analysis.gesture_name or "none",
            confidence=analysis.confidence.as_dict(),
            curl_angles=curl_angles
        )
        self.frames.append(frame)
        self.frame_counter += 1

    def get_frame_count(self) -> int:
        """Get number of recorded frames."""
        return len(self.frames)

    def export_json(self, filename: str = None) -> str:
        """Export recording to JSON file in data/json/."""
        self._ensure_directories()

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tracking_{timestamp}.json"

        filepath = os.path.join(self.JSON_DIR, filename)

        data = {
            "recording_start": self.start_time.isoformat() if self.start_time else None,
            "recording_end": datetime.now().isoformat(),
            "total_frames": len(self.frames),
            "frames": [asdict(f) for f in self.frames]
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return filepath

    def export_csv(self, filename: str = None) -> str:
        """Export recording to CSV file in data/csv/."""
        self._ensure_directories()

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tracking_{timestamp}.csv"

        filepath = os.path.join(self.CSV_DIR, filename)

        if not self.frames:
            return filepath

        fieldnames = [
            'timestamp', 'frame_number', 'hand_type', 'finger_count', 'gesture',
            'thumb_state', 'index_state', 'middle_state', 'ring_state', 'pinky_state',
            'thumb_conf', 'index_conf', 'middle_conf', 'ring_conf', 'pinky_conf',
            'thumb_curl', 'index_curl', 'middle_curl', 'ring_curl', 'pinky_curl'
        ]

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for frame in self.frames:
                row = {
                    'timestamp': frame.timestamp,
                    'frame_number': frame.frame_number,
                    'hand_type': frame.hand_type,
                    'finger_count': frame.finger_count,
                    'gesture': frame.gesture,
                    'thumb_state': frame.finger_states.get('thumb', False),
                    'index_state': frame.finger_states.get('index', False),
                    'middle_state': frame.finger_states.get('middle', False),
                    'ring_state': frame.finger_states.get('ring', False),
                    'pinky_state': frame.finger_states.get('pinky', False),
                    'thumb_conf': frame.confidence.get('thumb', 0),
                    'index_conf': frame.confidence.get('index', 0),
                    'middle_conf': frame.confidence.get('middle', 0),
                    'ring_conf': frame.confidence.get('ring', 0),
                    'pinky_conf': frame.confidence.get('pinky', 0),
                    'thumb_curl': frame.curl_angles.get('thumb', 0),
                    'index_curl': frame.curl_angles.get('index', 0),
                    'middle_curl': frame.curl_angles.get('middle', 0),
                    'ring_curl': frame.curl_angles.get('ring', 0),
                    'pinky_curl': frame.curl_angles.get('pinky', 0)
                }
                writer.writerow(row)

        return filepath

    def export_all(self, base_name: str = None) -> Tuple[str, str]:
        """Export to both JSON and CSV. Returns (json_path, csv_path)."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not base_name:
            base_name = f"tracking_{timestamp}"

        json_path = self.export_json(f"{base_name}.json")
        csv_path = self.export_csv(f"{base_name}.csv")

        return json_path, csv_path


# Finger names for reference
FINGER_NAMES = {0: "Thumb", 1: "Index", 2: "Middle", 3: "Ring", 4: "Pinky"}
