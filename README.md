# TrackingMaster

A comprehensive computer vision tracking system for hands, face, body, and activity recognition.

## Current Version: 0.2 - Hand Detection

Real-time hand tracking with MediaPipe.

## Features

- Webcam video capture with camera selection
- **Hand tracking with MediaPipe** (up to 2 hands)
- Detection of left/right hand with confidence score
- 21 landmarks per hand with connections
- Real-time display with FPS counter
- Pause/Resume functionality
- Screenshot capture
- Toggle hand tracking on/off

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
| `H` | Toggle hand tracking |

## Project Structure

```
TrackingMaster/
├── main.py              # Entry point
├── src/
│   ├── __init__.py
│   ├── camera.py        # Camera module
│   └── hand_tracker.py  # Hand tracking module
├── screenshots/         # Saved screenshots
├── requirements.txt
├── ROADMAP.md          # Development roadmap
└── README.md
```

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the complete development plan.

**Completed:**
- v0.1 - Foundation
- v0.2 - Hand Detection

**Upcoming versions:**
- v0.3 - Finger Tracking
- v0.4 - Face Detection
- v0.5 - Head Pose Estimation
- ...and more!

## Requirements

- Python 3.10+
- Webcam

## License

MIT
