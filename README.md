# TrackingMaster

A comprehensive computer vision tracking system for hands, face, body, and activity recognition.

## Current Version: 0.3.1 - Finger Tracking

Real-time hand and finger tracking with MediaPipe, optimized with threading for high performance.

## Features

### Hand Tracking
- Up to 2 hands detected simultaneously
- 21 landmarks per hand with connections
- Left/Right hand detection with confidence scores
- Anti-face filtering (prevents false positives)
- Temporal smoothing for stable tracking

### Finger Detection
- Per-finger state detection (extended/folded)
- Multi-criteria validation with confidence scores (0-5)
- Curl angle calculation for each finger
- Spread angle detection between fingers

### Gesture Recognition (17 gestures)
- Basic: Fist, Open Hand
- Thumbs: Thumbs Up, Thumbs Down
- Pointing: Pointing, Middle Finger
- V-signs: Peace (spread), Two (together)
- Numbers: Three, Four
- Special: OK, Rock, Gun, Call Me, Loser, Pinky Up, Rock On

### Number Detection
- Universal finger counting (0-5 per hand)
- Two-hand number recognition (00-55)
- Real-time display

### Performance
- Threaded tracking (MediaPipe in background thread)
- Single-pass overlay rendering (3-5x faster)
- 60+ FPS main thread, 30 FPS processing

### Data Export
- JSON export with full metadata
- CSV export for analysis
- Automatic folder organization

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/TrackingMaster.git
cd TrackingMaster

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

### Controls

| Key | Action |
|-----|--------|
| `Q` / `ESC` | Quit |
| `SPACE` | Pause / Resume |
| `S` | Take screenshot |
| `I` | Toggle info overlay |
| `?` / `/` | Toggle help window |
| `H` | Toggle hand tracking |
| `F` | Toggle finger display panel |
| `N` | Toggle number detection |
| `G` | Toggle gesture detection |
| `D` | Toggle debug mode |
| `R` | Start/Stop recording |
| `T` | Toggle threaded mode |
| `[` / `]` | Detection confidence -/+ |
| `;` / `'` | Tracking confidence -/+ |

### Debug Mode Keys (when D is active)
| Key | Action |
|-----|--------|
| `1` / `2` | Finger curl threshold -/+ |
| `3` / `4` | Thumb curl threshold -/+ |
| `5` / `6` | Spread threshold -/+ |

## Project Structure

```
TrackingMaster/
├── main.py                 # Entry point
├── config.py               # Centralized configuration
├── src/
│   ├── __init__.py
│   ├── camera.py           # Camera module
│   ├── hand_tracker.py     # Hand tracking (MediaPipe)
│   ├── finger_tracker.py   # Finger analysis & gestures
│   ├── threaded_tracker.py # Async processing
│   ├── overlay_renderer.py # Optimized UI rendering
│   ├── logger.py           # Logging configuration
│   └── constants.py        # UI constants
├── screenshots/            # Saved screenshots
├── data/
│   ├── json/              # JSON exports
│   └── csv/               # CSV exports
├── logs/                   # Log files
├── requirements.txt
├── ROADMAP.md
├── CLAUDE.md
└── README.md
```

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the complete development plan.

**Completed:**
- v0.1 - Foundation
- v0.2 - Hand Detection
- v0.3 - Finger Tracking
- v0.3.1 - Bug fixes, logging, config, 17 gestures

**Next:**
- v0.4 - Face Detection (MediaPipe Face Mesh)

## Requirements

- Python 3.10+
- Webcam
- Windows/Linux/Mac

## License

MIT
