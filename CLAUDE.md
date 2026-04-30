# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TrackingMaster is a computer vision tracking system for hands, face, body, and activity recognition. Currently at **v0.3.1 - Finger Tracking** with real-time hand and finger tracking using MediaPipe, optimized with threading for high FPS.

### v0.3.1 Changes
- Thread-safe metrics in `ThreadedTracker` with dedicated `_stats_lock`
- Error handling in background processing thread
- Centralized configuration (`config.py`)
- Logging infrastructure (`src/logger.py`)
- UI constants extracted (`src/constants.py`)
- 17 gestures fully implemented (added: TWO, THREE, FOUR, LOSER, PINKY_UP, THUMB_INDEX_PINKY)
- Toast notifications for user feedback
- Latency stats in threading mode
- Dictionary validation to prevent KeyError crashes

## Commands

```bash
# Setup (Windows)
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Setup (Linux/Mac)
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run the application
python main.py
```

## Keyboard Controls

| Key | Action |
|-----|--------|
| Q / ESC | Quit |
| SPACE | Pause / Resume |
| S | Screenshot (saved to `screenshots/`) |
| I | Toggle info overlay |
| ? / / | Toggle help window |
| H | Toggle hand tracking |
| F | Toggle finger details panel |
| N | Toggle number detection |
| G | Toggle gesture detection |
| D | Toggle debug mode |
| R | Start/Stop recording (exports to `data/json/` and `data/csv/`) |
| T | Toggle threaded mode (performance) |
| [ / ] | Detection confidence -/+ |
| ; / ' | Tracking confidence -/+ |
| 1 / 2 | Finger curl threshold -/+ (debug mode) |
| 3 / 4 | Thumb curl threshold -/+ (debug mode) |
| 5 / 6 | Spread threshold -/+ (debug mode) |

## Architecture

```
TrackingMaster/
├── main.py              # Entry point with main loop
├── config.py            # Centralized configuration (dataclasses)
└── src/
    ├── camera.py           # Webcam management
    ├── hand_tracker.py     # MediaPipe hand detection
    ├── finger_tracker.py   # Finger analysis & gestures
    ├── threaded_tracker.py # Async processing (thread-safe)
    ├── overlay_renderer.py # Optimized UI rendering
    ├── logger.py           # Logging configuration
    └── constants.py        # UI constants & magic numbers
```

### Core Modules

- **main.py**: Entry point with main loop, keyboard handling, state management. Uses `FPSCounter` for smoothed FPS. Supports threaded and synchronous modes.

- **src/camera.py**: `Camera` class for webcam management.
  - DirectShow backend on Windows for faster init
  - Horizontal mirroring for natural display
  - Screenshot functionality (`screenshots/` folder)
  - `list_available_cameras()` with stderr suppression

- **src/hand_tracker.py**: `HandTracker` wrapping MediaPipe Hands.
  - Detects up to 2 hands with 21 landmarks each
  - `_is_valid_hand()` filters false positives (faces) using:
    - Thumb lateral offset from finger line
    - Wrist position validation
    - Finger direction coherence
    - Palm length validation
  - Temporal smoothing (`smoothing_factor=0.5`)
  - Hand persistence (`persistence_frames=5`)
  - `draw_landmarks()` method for threaded mode
  - Returns `HandData` dataclasses

- **src/finger_tracker.py**: `FingerTracker` for finger analysis.
  - **Dataclasses**: `FingerState`, `FingerConfidence`, `HandAnalysis`
  - Multi-criteria finger detection (5 criteria, need 3+ to validate)
  - Curl angle calculation per finger
  - Spread angle detection (for Peace vs Two differentiation)
  - **Gestures** (17): fist, open_hand, thumbs_up, thumbs_down, peace, two, pointing, ok, rock, three, four, gun, call_me, loser, pinky_up, thumb_index_pinky
  - **Adjustable thresholds**: curl, thumb_curl, spread
  - `TrackingDataRecorder` for JSON/CSV export
  - Temporal smoothing with history voting

- **src/threaded_tracker.py**: `ThreadedTracker` for async processing.
  - MediaPipe runs in background thread (~30 FPS)
  - Main thread stays at ~60 FPS for smooth rendering
  - Double buffering, automatic frame skipping
  - **Thread-safe metrics** with `_stats_lock` (v0.3.1)
  - **Error handling** in `_processing_loop()` - thread won't crash
  - **Latency tracking** (`latency_ms` in stats)
  - Performance stats (avg processing time, skip ratio)
  - Also includes `FrameSkipTracker` alternative

- **src/overlay_renderer.py**: `OverlayRenderer` for optimized UI.
  - Single-pass blending (one blend instead of many)
  - `Theme` class with consistent color palette
  - `_fill_rounded_rect()` for modern UI elements
  - **Toast notifications** via `_draw_toast()` (v0.3.1)
  - **Safe dictionary access** with `.get()` fallbacks
  - All panels: info, debug, finger, help, pause, no_hands, toast

- **config.py**: Centralized configuration (v0.3.1).
  - `CameraConfig`, `HandTrackingConfig`, `FingerTrackingConfig`
  - `ThreadingConfig`, `UIConfig`, `PathsConfig`
  - Global `config` instance with dataclass defaults

- **src/logger.py**: Logging infrastructure (v0.3.1).
  - `setup_logging()` with console and optional file output
  - `get_logger(name)` for module-specific loggers
  - Pre-configured: `get_camera_logger()`, `get_tracker_logger()`, etc.

- **src/constants.py**: UI and visual constants (v0.3.1).
  - Panel dimensions, font sizes, opacities
  - Hand validation thresholds
  - Gesture detection thresholds
  - Extracted magic numbers for maintainability

## Key Technical Details

- MediaPipe processes RGB; OpenCV captures BGR - conversion in `HandTracker.process()`
- Frames horizontally flipped in `Camera.read_frame()` for mirror display
- Threading: main thread renders, background thread processes MediaPipe
- Single-pass overlay: all UI drawn to buffer, one blend at end (3-5x faster)
- Data export: `data/json/` and `data/csv/` folders created automatically

## Performance Optimization

The app uses two key optimizations:

1. **Threaded Tracking**: MediaPipe (CPU intensive) runs in separate thread
2. **Single-Pass Rendering**: One overlay buffer + one blend instead of multiple copies

Toggle threading with [T] key to compare performance.

## Data Export

Recording ([R] key) exports to:
- `data/json/tracking_YYYYMMDD_HHMMSS.json` - Full data with metadata
- `data/csv/tracking_YYYYMMDD_HHMMSS.csv` - Flat format for analysis

## Current Status (v0.3.1 Complete)

Features implemented:
- [x] Finger state detection (extended/folded)
- [x] Multi-criteria validation with confidence scores
- [x] 17 gesture recognition (complete set)
- [x] Universal number detection (any fingers = count)
- [x] Debug mode with real-time threshold adjustment
- [x] Recording and export (JSON/CSV)
- [x] Threaded processing for high FPS
- [x] Optimized overlay rendering
- [x] Modern UI with Theme system
- [x] Thread-safe metrics (v0.3.1)
- [x] Error handling in threads (v0.3.1)
- [x] Centralized configuration (v0.3.1)
- [x] Logging infrastructure (v0.3.1)
- [x] Toast notifications for feedback (v0.3.1)
- [x] Latency tracking (v0.3.1)

## Next Version (v0.4 - Face Detection)

See ROADMAP.md. Will add:
- MediaPipe Face Mesh (468 landmarks)
- Face position tracking
- Bounding box
- Multi-face detection

## Code Conventions

- Dataclasses for data containers (`HandData`, `FingerState`, `HandAnalysis`)
- Type hints throughout
- BGR color format (OpenCV standard)
- Normalized coordinates (0-1) for landmarks
- All UI colors defined in `Theme` class
