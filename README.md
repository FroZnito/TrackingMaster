# TrackingMaster

A comprehensive computer vision tracking system for hands, face, body, and activity recognition.

## Current Version: 0.1 - Foundation

Basic webcam access with real-time display and controls.

## Features (v0.1)

- Webcam video capture
- Real-time display with FPS counter
- Pause/Resume functionality
- Screenshot capture
- Camera error handling

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

## Project Structure

```
TrackingMaster/
├── main.py              # Entry point
├── src/
│   ├── __init__.py
│   └── camera.py        # Camera module
├── screenshots/         # Saved screenshots
├── requirements.txt
├── ROADMAP.md          # Development roadmap
└── README.md
```

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the complete development plan.

**Upcoming versions:**
- v0.2 - Hand Detection
- v0.3 - Finger Tracking
- v0.4 - Face Detection
- v0.5 - Head Pose Estimation
- ...and more!

## Requirements

- Python 3.10+
- Webcam

## License

MIT
