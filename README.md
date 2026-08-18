# HandVision v2.0 — AI-Powered Hand & Screen Visualization System

![HandVision Banner](https://img.shields.io/badge/HandVision-v2.0.0-38BDF8?style=for-the-badge)
![Python Version](https://img.shields.io/badge/Python-3.11%2B-blue?style=for-the-badge)
![OpenCV](https://img.shields.io/badge/OpenCV-5.0%2B-green?style=for-the-badge)
![MediaPipe](https://img.shields.io/badge/MediaPipe-Tasks-orange?style=for-the-badge)
![CustomTkinter](https://img.shields.io/badge/UI-CustomTkinter-indigo?style=for-the-badge)

**HandVision v2.0** is a real-time computer vision desktop application that transforms your standard webcam into a touchless hand tracking interface, virtual mouse, and **full OS System & Browser Controller**.

---

## 🌟 Key Features in v2.0

- 🌐 **Browser Tab Control**: Close active browser tabs or windows touchless using the `THREE_FINGERS` gesture (`Ctrl + W`).
- 📁 **File Explorer Launcher**: Instantly open Windows File Explorer or custom folders using the `FOUR_FINGERS` gesture (`Win + E`).
- 📜 **Vertical Screen Scroll**: Move pages and documents smoothly using the `TWO_FINGERS_SCROLL` gesture.
- 🔇 **Audio Mute Toggle**: Mute/unmute laptop system audio using the `THUMBS_DOWN` gesture.
- 🔀 **Application Window Switcher**: Switch active windows using the `OK_SIGN` gesture (`Alt + Tab`).
- 🎥 **Real-Time Multi-Threaded Camera**: 30+ FPS webcam capture, horizontal mirroring, and camera resolution queries.
- 🖐️ **21 Hand Landmark Tracking**: High-precision hand skeleton rendering using MediaPipe Tasks Vision (`HandLandmarker`) with offline model bundling.
- 🎯 **Finger State Evaluator**: Real-time detection of individual finger states (`OPEN` vs `CLOSED`) for Thumb, Index, Middle, Ring, and Pinky.
- 🖱️ **Virtual Mouse Engine**: Touchless screen control powered by Index fingertip navigation, Exponential Moving Average (EMA) tremor smoothing, pinch left-clicks, and drag-and-hold gestures.
- 📸 **Automatic Screenshot Capture**: Trigger timestamped full-screen captures (`screenshots/screenshot_YYYY-MM-DD_HH-MM-SS.png`) using the `VICTORY` gesture.
- 🎛️ **Modern Dark Dashboard**: Built with CustomTkinter featuring live status cards (`HAND STATUS`, `FINGER STATUS`, `GESTURE & ACTION`, `OS CONTROLS`, `SYSTEM METRICS`), bottom control bar, and interactive live tuning settings.
- 🛡️ **Safety & Emergency Controls**: Debouncing cooldowns (default 1.2s) prevent accidental trigger spamming. Hotkey `ESC` instantly disables Virtual Mouse and OS Control modes.

---

## 🖐️ Comprehensive Gesture & Action Reference

| Gesture | Hand Pose Description | System Action Triggered |
| :--- | :--- | :--- |
| **`THREE_FINGERS`** | Index + Middle + Ring open, Pinky & Thumb closed | **Close Current Browser Tab / Window (`Ctrl + W`)** |
| **`FOUR_FINGERS`** | Index + Middle + Ring + Pinky open, Thumb closed | **Open File Explorer / Folder (`Win + E`)** |
| **`TWO_FINGERS_SCROLL`** | Index + Middle open together | **Smooth Vertical Screen Scroll** (Hand movement up/down) |
| **`THUMBS_DOWN`** | Thumb pointing downwards, other fingers closed | **Toggle Mute System Audio (`Volume Mute`)** |
| **`OK_SIGN`** | Thumb + Index touching in circle, Middle/Ring/Pinky open | **Switch Active Application Window (`Alt + Tab`)** |
| **`OPEN_PALM`** | All 5 fingers extended | **Pause / Neutral State** |
| **`FIST`** | All fingers closed into a fist | **Stop current interaction / Release click** |
| **`POINT`** | Only Index finger open | **Enable Virtual Mouse Cursor Navigation** |
| **`PINCH`** | Thumb + Index tips close together ($<38\text{px}$) | **Mouse Left Click / Drag-and-Hold** |
| **`VICTORY`** | Index + Middle fingers open wide | **Capture Full-Screen Timestamped Screenshot** |
| **`THUMBS_UP`** | Thumb open while other fingers closed | **Confirm / Activate system command** |

---

## 📂 Project Architecture

```
HandVision/
├── main.py                     # Primary entry point
├── requirements.txt            # Package dependencies
├── README.md                   # System documentation
├── .gitignore                  # Git rules
├── run.bat                     # One-click Windows launcher
├── test_backend.py             # Backend unit test suite
├── test_gui.py                 # GUI integration test
├── test_v2_system.py          # v2.0 OS System & Gesture test suite
├── assets/
│   └── models/
│       └── hand_landmarker.task  # MediaPipe HandLandmarker model file
├── screenshots/
│   └── .gitkeep                 # Captured screenshots output directory
├── src/
│   ├── __init__.py
│   ├── camera.py              # Multi-threaded VideoCapture manager
│   ├── hand_tracker.py        # MediaPipe HandLandmarker wrapper
│   ├── gesture_recognizer.py  # Finger state & v2.0 gesture evaluator
│   ├── virtual_mouse.py       # Cursor navigation, EMA smoothing & pinch clicks
│   ├── system_controller.py   # OS System & Browser automation engine
│   ├── screenshot.py         # Timestamped screenshot engine
│   ├── config.py              # Centralized AppConfig settings & theme palette
│   └── utils.py               # Coordinate mapping, distance math & OpenCV overlay
└── ui/
    ├── __init__.py
    ├── dashboard.py           # CustomTkinter main GUI dashboard & update loop
    └── components.py          # Status cards, metric rows & settings modal
```

---

## ⚡ Quick Start & Installation

### 1. Launch via One-Click Script
Double-click `run.bat` inside the project folder:
`C:\Users\Vedant\.gemini\antigravity\scratch\HandVision\run.bat`

### 2. Or Launch via Terminal
```bash
cd C:\Users\Vedant\.gemini\antigravity\scratch\HandVision
python main.py
```

---

## ⚙️ Interactive Settings & Customization

Click the **⚙ Settings** button in the bottom control bar to tune parameters live:
- **Camera Index**: Switch between primary webcam (0) or external cameras (1, 2).
- **Min Detection Confidence**: Adjust tracking sensitivity (0.30 – 0.95).
- **Cursor Sensitivity**: Control virtual mouse movement speed (0.5 – 3.0).
- **Cursor Smoothing (Alpha)**: Adjust EMA smoothing filter (0.05 = super smooth, 0.90 = ultra responsive).
- **Pinch Threshold**: Set pixel distance threshold for pinch click activation (20px – 70px).
- **OS Action Cooldown**: Set safety delay between system actions like Close Tab or Open Explorer (0.5s – 3.0s).
- **Scroll Sensitivity**: Adjust webpage vertical scrolling speed (0.2 – 3.0).
