"""
Multi-Threaded Camera Manager for HandVision.
Captures frames asynchronously from OpenCV VideoCapture to maintain smooth 30+ FPS UI rendering.
"""

import threading
import time
from typing import Optional, Tuple
import cv2
import numpy as np
from src.config import AppConfig


class CameraManager:
    """Manages OpenCV VideoCapture in a separate worker thread."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.cap: Optional[cv2.VideoCapture] = None
        self.running: bool = False
        self.thread: Optional[threading.Thread] = None

        self.latest_frame: Optional[np.ndarray] = None
        self.lock = threading.Lock()

        self.actual_width: int = config.frame_width
        self.actual_height: int = config.frame_height
        self.error_message: Optional[str] = None

    def start(self) -> bool:
        """Initialize camera and start capture worker thread."""
        if self.running:
            return True

        self.error_message = None
        try:
            self.cap = cv2.VideoCapture(self.config.camera_index, cv2.CAP_DSHOW)
            if not self.cap or not self.cap.isOpened():
                # Fallback to default backend if CAP_DSHOW fails
                self.cap = cv2.VideoCapture(self.config.camera_index)

            if not self.cap.isOpened():
                self.error_message = f"Cannot open camera index {self.config.camera_index}"
                return False

            # Set resolution requests
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.frame_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.frame_height)

            # Query actual hardware dimensions
            self.actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or self.config.frame_width
            self.actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or self.config.frame_height

            self.running = True
            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()
            return True

        except Exception as err:
            self.error_message = f"Camera initialization failed: {str(err)}"
            self.running = False
            return False

    def _capture_loop(self):
        """Worker thread loop reading camera frames."""
        while self.running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue

            if self.config.mirror_camera:
                frame = cv2.flip(frame, 1)

            with self.lock:
                self.latest_frame = frame.copy()

            # Prevent CPU hogging
            time.sleep(0.005)

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Retrieve latest captured frame."""
        with self.lock:
            if self.latest_frame is not None:
                return True, self.latest_frame.copy()

        # If no frame yet, generate a blank placeholder or error frame
        blank = np.zeros((self.actual_height, self.actual_width, 3), dtype=np.uint8)
        msg = self.error_message if self.error_message else "Camera Offline"
        cv2.putText(
            blank,
            msg,
            (40, self.actual_height // 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (100, 100, 255),
            2,
            cv2.LINE_AA,
        )
        return False, blank

    def stop(self):
        """Stop capture thread and release camera resources."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        self.thread = None

        if self.cap:
            self.cap.release()
            self.cap = None

        with self.lock:
            self.latest_frame = None

    def get_resolution(self) -> Tuple[int, int]:
        """Return actual camera resolution (width, height)."""
        return self.actual_width, self.actual_height
