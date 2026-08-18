"""
Utility & Helper Functions for HandVision.
Provides coordinate mapping, FPS calculation, distance math, and OpenCV drawing overlays.
"""

import math
import time
from typing import Tuple, List, Optional, Any
import cv2
import numpy as np
from src.config import AppConfig


class FPSCounter:
    """Calculates smoothed frames per second (FPS)."""

    def __init__(self, avg_window: int = 15):
        self.avg_window = avg_window
        self.frame_times: List[float] = []
        self.last_time = time.time()
        self.current_fps = 0.0

    def update(self) -> float:
        """Call on every frame update."""
        now = time.time()
        delta = now - self.last_time
        self.last_time = now

        if delta > 0:
            self.frame_times.append(delta)
            if len(self.frame_times) > self.avg_window:
                self.frame_times.pop(0)

            avg_delta = sum(self.frame_times) / len(self.frame_times)
            self.current_fps = 1.0 / avg_delta if avg_delta > 0 else 0.0

        return self.current_fps


def euclidean_distance_2d(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Calculate Euclidean distance between two 2D points."""
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def map_coordinates(
    x: float,
    y: float,
    src_width: int,
    src_height: int,
    dst_width: int,
    dst_height: int,
    margin_percent: float = 0.15,
) -> Tuple[int, int]:
    """
    Map coordinates from camera space to screen space.
    Applies a boundary margin so user does not need to stretch hand to frame edges.
    """
    margin_x = src_width * margin_percent
    margin_y = src_height * margin_percent

    usable_w = src_width - 2 * margin_x
    usable_h = src_height - 2 * margin_y

    # Clamp to usable region
    clamped_x = max(margin_x, min(src_width - margin_x, x))
    clamped_y = max(margin_y, min(src_height - margin_y, y))

    # Normalize 0.0 -> 1.0
    norm_x = (clamped_x - margin_x) / usable_w if usable_w > 0 else 0.5
    norm_y = (clamped_y - margin_y) / usable_h if usable_h > 0 else 0.5

    # Scale to screen resolution
    screen_x = int(norm_x * dst_width)
    screen_y = int(norm_y * dst_height)

    # Clamp to screen boundary
    screen_x = max(0, min(dst_width - 1, screen_x))
    screen_y = max(0, min(dst_height - 1, screen_y))

    return screen_x, screen_y


# Connections between hand landmarks (21 points)
HAND_CONNECTIONS = [
    # Wrist to Thumb
    (0, 1), (1, 2), (2, 3), (3, 4),
    # Wrist to Index
    (0, 5), (5, 6), (6, 7), (7, 8),
    # Index to Middle
    (5, 9), (9, 10), (10, 11), (11, 12),
    # Middle to Ring
    (9, 13), (13, 14), (14, 15), (15, 16),
    # Ring to Pinky
    (13, 17), (17, 18), (18, 19), (19, 20),
    # Wrist to Pinky base
    (0, 17)
]


def draw_styled_hand(
    frame: np.ndarray,
    landmarks_px: List[Tuple[int, int]],
    hand_label: str,
    confidence: float,
    gesture_name: str,
    pinch_distance: Optional[float] = None,
    config: Optional[AppConfig] = None
) -> np.ndarray:
    """
    Renders sleek, modern hand landmarks, skeletal connections, finger nodes,
    and pinch feedback on the OpenCV camera frame.
    """
    if config is None:
        config = AppConfig()

    h, w, _ = frame.shape

    # Draw Skeletal Lines
    for start_idx, end_idx in HAND_CONNECTIONS:
        if start_idx < len(landmarks_px) and end_idx < len(landmarks_px):
            pt1 = landmarks_px[start_idx]
            pt2 = landmarks_px[end_idx]
            cv2.line(frame, pt1, pt2, config.cv_color_bone, 2, cv2.LINE_AA)

    # Draw Landmark Joints
    for idx, (px, py) in enumerate(landmarks_px):
        # Fingertips (4, 8, 12, 16, 20) get larger accent dots
        if idx in [4, 8, 12, 16, 20]:
            cv2.circle(frame, (px, py), 7, config.cv_color_joint, -1, cv2.LINE_AA)
            cv2.circle(frame, (px, py), 9, (255, 255, 255), 1, cv2.LINE_AA)
        else:
            cv2.circle(frame, (px, py), 4, config.cv_color_bone, -1, cv2.LINE_AA)

    # Draw Bounding Box & Hand Label
    xs = [pt[0] for pt in landmarks_px]
    ys = [pt[1] for pt in landmarks_px]
    min_x, max_x = max(0, min(xs) - 15), min(w, max(xs) + 15)
    min_y, max_y = max(0, min(ys) - 15), min(h, max(ys) + 15)

    box_color = (100, 220, 100) if gesture_name != "UNKNOWN" else (180, 180, 180)
    cv2.rectangle(frame, (min_x, min_y), (max_x, max_y), box_color, 1, cv2.LINE_AA)

    label_str = f"{hand_label} ({int(confidence * 100)}%)"
    cv2.putText(
        frame,
        label_str,
        (min_x, max(20, min_y - 8)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        box_color,
        1,
        cv2.LINE_AA,
    )

    # Index Fingertip Cursor Indicator (Point 8)
    if len(landmarks_px) > 8:
        idx_pt = landmarks_px[8]
        cv2.circle(frame, idx_pt, 12, config.cv_color_cursor, 2, cv2.LINE_AA)
        cv2.circle(frame, idx_pt, 3, config.cv_color_cursor, -1, cv2.LINE_AA)

    # Pinch Indicator Line & Distance Banner
    if len(landmarks_px) > 8 and pinch_distance is not None:
        thumb_pt = landmarks_px[4]
        idx_pt = landmarks_px[8]

        line_color = config.cv_color_pinch if pinch_distance < config.pinch_threshold_px else (150, 150, 250)
        cv2.line(frame, thumb_pt, idx_pt, line_color, 2, cv2.LINE_AA)

        mid_x = (thumb_pt[0] + idx_pt[0]) // 2
        mid_y = (thumb_pt[1] + idx_pt[1]) // 2

        if pinch_distance < config.pinch_threshold_px:
            cv2.putText(
                frame,
                f"PINCH ACTIVE ({int(pinch_distance)}px)",
                (mid_x - 40, max(30, mid_y - 15)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                config.cv_color_pinch,
                2,
                cv2.LINE_AA,
            )

    return frame
