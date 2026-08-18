"""
Timestamped Screenshot Engine for HandVision.
Captures screen images safely with debounced cooldown timers.
"""

import os
import time
from datetime import datetime
from typing import Tuple, Optional
import pyautogui
from src.config import AppConfig


class ScreenshotManager:
    """Manages screenshot creation, file naming, and trigger cooldowns."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.last_screenshot_time: float = 0.0
        self.ensure_directory()

    def ensure_directory(self):
        """Ensure screenshots directory exists."""
        if not os.path.exists(self.config.screenshot_dir):
            os.makedirs(self.config.screenshot_dir, exist_ok=True)

    def trigger_screenshot(self) -> Tuple[bool, Optional[str]]:
        """
        Attempt to capture a screenshot if cooldown has passed.
        Returns (success, saved_file_path).
        """
        now = time.time()
        if (now - self.last_screenshot_time) < self.config.gesture_cooldown:
            return False, None  # Cooldown active

        self.ensure_directory()
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"screenshot_{timestamp}.png"
        filepath = os.path.join(self.config.screenshot_dir, filename)

        try:
            pyautogui.screenshot(filepath)
            self.last_screenshot_time = now
            return True, filepath
        except Exception as err:
            print(f"[Screenshot Error] {err}")
            return False, None
