"""
Virtual Mouse Controller for HandVision.
Maps hand cursor positions to screen space with EMA smoothing, pinch clicking, and drag controls.
"""

import time
from typing import Tuple, Optional
import pyautogui
from src.config import AppConfig
from src.gesture_recognizer import GestureResult
from src.hand_tracker import HandData
from src.utils import map_coordinates

# Configure PyAutoGUI safety settings
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.001


class VirtualMouseController:
    """Controls mouse cursor and clicks using hand tracking input."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.screen_width, self.screen_height = pyautogui.size()

        # Smoothed Cursor State
        self.prev_screen_x: float = self.screen_width / 2.0
        self.prev_screen_y: float = self.screen_height / 2.0

        # Click & Drag States
        self.is_dragging: bool = False
        self.pinch_start_time: Optional[float] = None
        self.last_click_time: float = 0.0
        self.click_cooldown_sec: float = 0.35  # Debounce delay between distinct clicks

    def update(
        self,
        hand: HandData,
        gesture: GestureResult,
        camera_res: Tuple[int, int]
    ):
        """
        Process current hand landmark position and gesture state to update cursor.
        """
        if not self.config.virtual_mouse_enabled or len(hand.landmarks_px) < 9:
            self._release_mouse_if_held()
            return

        cam_w, cam_h = camera_res
        index_pt = hand.landmarks_px[8]  # Index Fingertip

        # Map camera ROI to screen coordinates
        raw_screen_x, raw_screen_y = map_coordinates(
            index_pt[0],
            index_pt[1],
            cam_w,
            cam_h,
            self.screen_width,
            self.screen_height,
            margin_percent=0.15,
        )

        # Exponential Moving Average (EMA) Smoothing
        alpha = self.config.cursor_smoothing
        smooth_x = alpha * raw_screen_x + (1 - alpha) * self.prev_screen_x
        smooth_y = alpha * raw_screen_y + (1 - alpha) * self.prev_screen_y

        self.prev_screen_x = smooth_x
        self.prev_screen_y = smooth_y

        target_x = int(smooth_x)
        target_y = int(smooth_y)

        # Move Cursor if POINT, PINCH, or OPEN_PALM
        try:
            pyautogui.moveTo(target_x, target_y, _pause=False)
        except Exception:
            pass  # Suppress out-of-bounds GUI exceptions safely

        now = time.time()

        # Pinch Action Handling (Click & Drag)
        if gesture.gesture_name == "PINCH":
            if self.pinch_start_time is None:
                self.pinch_start_time = now

            pinch_duration = now - self.pinch_start_time

            # If pinch held for longer than 0.2s -> initiate DRAG
            if pinch_duration > 0.20 and not self.is_dragging:
                try:
                    pyautogui.mouseDown(button='left', _pause=False)
                    self.is_dragging = True
                except Exception:
                    pass

        else:
            # Pinch released
            if self.pinch_start_time is not None:
                pinch_duration = now - self.pinch_start_time

                if self.is_dragging:
                    try:
                        pyautogui.mouseUp(button='left', _pause=False)
                    except Exception:
                        pass
                    self.is_dragging = False

                elif pinch_duration < 0.20 and (now - self.last_click_time) > self.click_cooldown_sec:
                    # Short pinch -> Left Click
                    try:
                        pyautogui.click(button='left', _pause=False)
                        self.last_click_time = now
                    except Exception:
                        pass

                self.pinch_start_time = None

    def _release_mouse_if_held(self):
        """Cleanly release mouse button if hand tracking is lost while dragging."""
        if self.is_dragging:
            try:
                pyautogui.mouseUp(button='left', _pause=False)
            except Exception:
                pass
            self.is_dragging = False
        self.pinch_start_time = None
