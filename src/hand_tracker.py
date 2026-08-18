"""
Hand Tracking Pipeline for HandVision using MediaPipe HandLandmarker.
Extracts 21 3D hand landmarks, handedness classification, confidence scores, and pixel positions.
"""

import os
from dataclasses import dataclass
from typing import List, Tuple, Optional
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from src.config import AppConfig


@dataclass
class HandData:
    """Structured result for a single detected hand."""
    landmarks_norm: List[Tuple[float, float, float]]  # Normalized (x, y, z)
    landmarks_px: List[Tuple[int, int]]               # Pixel (x, y)
    handedness: str                                    # "Right" or "Left"
    confidence: float                                  # Detection confidence (0.0 to 1.0)
    bbox: Tuple[int, int, int, int]                   # (min_x, min_y, max_x, max_y)


class HandTracker:
    """Wrapper around MediaPipe HandLandmarker for high-performance detection."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.detector: Optional[vision.HandLandmarker] = None
        self._init_detector()

    def _init_detector(self):
        """Initialize MediaPipe HandLandmarker task detector."""
        model_path = self.config.model_path
        if not os.path.isabs(model_path):
            model_path = os.path.abspath(model_path)

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"MediaPipe model file not found at: {model_path}")

        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_hands=self.config.num_hands,
            min_hand_detection_confidence=self.config.min_detection_confidence,
            min_hand_presence_confidence=self.config.min_tracking_confidence,
        )
        self.detector = vision.HandLandmarker.create_from_options(options)

    def process_frame(self, frame_bgr: np.ndarray) -> List[HandData]:
        """
        Process BGR OpenCV image frame and return list of HandData objects.
        """
        if self.detector is None or frame_bgr is None:
            return []

        h, w, _ = frame_bgr.shape
        rgb_frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        result = self.detector.detect(mp_image)
        if not result or not result.hand_landmarks:
            return []

        hands_list: List[HandData] = []

        for hand_idx, hand_landmarks in enumerate(result.hand_landmarks):
            # Extract Handedness label & score
            handedness_label = "Right"
            confidence = 0.90
            if result.handedness and hand_idx < len(result.handedness):
                cat = result.handedness[hand_idx][0]
                handedness_label = cat.category_name
                confidence = float(cat.score)

            landmarks_norm: List[Tuple[float, float, float]] = []
            landmarks_px: List[Tuple[int, int]] = []

            for lm in hand_landmarks:
                landmarks_norm.append((lm.x, lm.y, lm.z))
                px = max(0, min(w - 1, int(lm.x * w)))
                py = max(0, min(h - 1, int(lm.y * h)))
                landmarks_px.append((px, py))

            # Bounding box calculation
            xs = [pt[0] for pt in landmarks_px]
            ys = [pt[1] for pt in landmarks_px]
            bbox = (min(xs), min(ys), max(xs), max(ys))

            hands_list.append(
                HandData(
                    landmarks_norm=landmarks_norm,
                    landmarks_px=landmarks_px,
                    handedness=handedness_label,
                    confidence=confidence,
                    bbox=bbox,
                )
            )

        return hands_list

    def close(self):
        """Clean up MediaPipe resources."""
        if self.detector:
            self.detector.close()
            self.detector = None
