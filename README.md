# HandTracking

HandTracking is a Flask + OpenCV + MediaPipe hand gesture controller. It streams an annotated camera feed in the browser, tracks hand coordinates, and uses pinch gestures to move windows.

## Features

- Live browser camera preview with gesture, coordinate, velocity, and target-window readouts
- MediaPipe hand landmark tracking
- Pinch-to-grab window movement
- Velocity-sensitive movement for fast hand jerks
- Deadzone, smoothing, damping, and gesture hysteresis for steadier control
- Platform split for macOS and Windows window-management code

## Setup

Use Python 3.11 if possible.

```bash
cd HandTracking
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python download_model.py
```

## Run

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

Do not open `templates/index.html` directly. The page needs the Flask backend routes for status, camera control, and video streaming.

## macOS Notes

Allow these permissions when prompted:

- Camera access for your Python or terminal app
- Accessibility access in System Settings > Privacy & Security > Accessibility

For best window movement, use a normal non-fullscreen app window. Some macOS/browser windows may reject Accessibility repositioning.

## Gesture Controls

- Open palm: release the window
- Pinch: grab the active/target window
- Fast pinch movement: apply velocity gain for larger travel

The app includes a controller-style deadzone and smoothing to reduce jitter.

## Model File

`hand_landmarker.task` is intentionally ignored by git. Run `python download_model.py` to download it locally.

