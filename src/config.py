"""
Centralized Configuration Module for HandVision.
Holds application parameters, detection thresholds, UI colors, and mouse settings.
"""

import os
from dataclasses import dataclass, field
from typing import Tuple


@dataclass
class AppConfig:
    # Camera settings
    camera_index: int = 0
    frame_width: int = 1280
    frame_height: int = 720
    target_fps: int = 30
    mirror_camera: bool = True

    # MediaPipe Hand Tracking settings
    min_detection_confidence: float = 0.7
    min_tracking_confidence: float = 0.5
    num_hands: int = 2
    model_path: str = os.path.join("assets", "models", "hand_landmarker.task")

    # Feature Toggles
    virtual_mouse_enabled: bool = False
    gesture_control_enabled: bool = True
    system_control_enabled: bool = True

    # Virtual Mouse settings
    cursor_sensitivity: float = 1.5
    cursor_smoothing: float = 0.35  # Alpha for EMA smoothing (0.0 to 1.0)
    pinch_threshold_px: float = 38.0  # Pixel distance for pinch detection
    drag_hold_frames: int = 5  # Frames to hold pinch before starting drag

    # System Control settings
    system_cooldown: float = 1.2    # Seconds between OS hotkey actions (Close Tab, Open Explorer, etc.)
    scroll_sensitivity: float = 1.0 # Sensitivity multiplier for vertical scrolling
    default_explorer_dir: str = ""  # Optional custom directory path for File Explorer

    # Gesture settings
    gesture_cooldown: float = 1.5  # Seconds between screenshot triggers
    screenshot_dir: str = "screenshots"

    # UI Theme Palette (Modern Dark Theme)
    bg_dark: str = "#0F172A"       # Deep Slate
    card_bg: str = "#1E293B"       # Slate Card
    card_border: str = "#334155"   # Border accent
    accent_primary: str = "#38BDF8"# Cyan Blue
    accent_secondary: str = "#818CF8"# Indigo
    accent_success: str = "#4ADE80"# Green
    accent_warning: str = "#FACC15"# Amber / Yellow
    accent_danger: str = "#F87171" # Rose Red
    text_primary: str = "#F8FAFC"  # Pure White
    text_secondary: str = "#94A3B8"# Muted Grey

    # Colors for OpenCV Visualizations (BGR Format)
    cv_color_joint: Tuple[int, int, int] = (248, 189, 56)      # Vibrant Cyan BGR
    cv_color_bone: Tuple[int, int, int] = (248, 140, 129)      # Soft Indigo BGR
    cv_color_pinch: Tuple[int, int, int] = (80, 222, 74)       # Emerald Green BGR
    cv_color_cursor: Tuple[int, int, int] = (255, 100, 50)     # Bright Blue BGR

    def update(self, **kwargs):
        """Dynamically update settings."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
