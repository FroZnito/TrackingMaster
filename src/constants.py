"""
UI and visual constants for TrackingMaster.

All magic numbers for rendering, layout, and visual properties are defined here.
"""

# =============================================================================
# PANEL DIMENSIONS
# =============================================================================

# Info panel (top-left)
INFO_PANEL_WIDTH = 180
INFO_PANEL_MARGIN = 12
INFO_PANEL_PADDING = 14

# Debug panel
DEBUG_PANEL_WIDTH = 240
DEBUG_PANEL_HEIGHT = 200

# Finger panel
FINGER_PANEL_WIDTH = 180
FINGER_PANEL_HEIGHT = 180

# Threshold panel (debug mode)
THRESHOLD_PANEL_WIDTH = 200
THRESHOLD_PANEL_HEIGHT = 110

# Help window
HELP_WINDOW_WIDTH = 300
HELP_WINDOW_MAX_HEIGHT = 500

# Common
LINE_HEIGHT = 22
PANEL_CORNER_RADIUS = 10
SMALL_CORNER_RADIUS = 8

# =============================================================================
# FONT SIZES (OpenCV scale factor)
# =============================================================================

FONT_SIZE_TITLE = 0.5
FONT_SIZE_LARGE = 0.48
FONT_SIZE_MEDIUM = 0.44
FONT_SIZE_SMALL = 0.42
FONT_SIZE_TINY = 0.36

# Font thickness
FONT_THICKNESS_NORMAL = 1
FONT_THICKNESS_BOLD = 2

# =============================================================================
# OPACITIES
# =============================================================================

OPACITY_PANEL = 0.88
OPACITY_PANEL_SECONDARY = 0.85
OPACITY_DEBUG = 0.9
OPACITY_PAUSE = 0.95
OPACITY_PAUSE_MASK = 0.5
OPACITY_HELP = 0.6
OPACITY_NO_HANDS = 0.8
OPACITY_TOAST = 0.9

# =============================================================================
# HAND VALIDATION THRESHOLDS (for anti-face filtering)
# =============================================================================

# Distance threshold for hand matching between frames
HAND_MATCH_DISTANCE = 0.15

# Thumb must be laterally offset from finger line by at least this much
THUMB_LATERAL_OFFSET_MIN = 0.025

# Minimum finger direction coherence threshold
FINGER_DIRECTION_COHERENCE_MIN = 0.02

# Palm length validation bounds (as fraction of hand height)
PALM_LENGTH_MIN = 0.08
PALM_LENGTH_MAX = 0.4

# Wrist offset validation
WRIST_OFFSET_MAX = 0.04

# Finger tip spread validation
FINGER_TIP_SPREAD_MIN = 0.01

# =============================================================================
# GESTURE DETECTION THRESHOLDS
# =============================================================================

# Spread angle to differentiate PEACE from TWO
PEACE_SPREAD_MIN = 15  # degrees
TWO_SPREAD_MAX = 15    # degrees

# =============================================================================
# CONFIDENCE DISPLAY
# =============================================================================

CONFIDENCE_DOTS_COUNT = 5
CONFIDENCE_DOT_SIZE = 6
CONFIDENCE_BAR_WIDTH = 80

# =============================================================================
# TOAST NOTIFICATION
# =============================================================================

TOAST_DISPLAY_DURATION = 2.0  # seconds
TOAST_FADE_DURATION = 0.3     # seconds
TOAST_MIN_WIDTH = 200
TOAST_PADDING = 16

# =============================================================================
# LANDMARK DRAWING
# =============================================================================

LANDMARK_POINT_SIZE = 4
LANDMARK_LINE_THICKNESS = 2

# =============================================================================
# COLORS (BGR format for OpenCV)
# =============================================================================

# These are fallbacks - prefer using Theme class in overlay_renderer.py
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_RED = (0, 0, 255)
COLOR_BLUE = (255, 0, 0)
COLOR_YELLOW = (0, 255, 255)
COLOR_CYAN = (255, 255, 0)
COLOR_MAGENTA = (255, 0, 255)
