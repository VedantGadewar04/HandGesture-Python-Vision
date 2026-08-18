"""
OS System & Browser Automation Controller for HandVision.
Executes laptop & OS keyboard shortcuts (Close Tab, Open Explorer, Mute, Scroll, Switch App).
"""

import os
import subprocess
import time
from typing import Tuple, Optional
import pyautogui
from src.config import AppConfig

# Configure PyAutoGUI safety settings
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.001


class SystemController:
    """Manages OS hotkey shortcuts and screen scroll interactions with debouncing."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.last_action_time: float = 0.0
        self.prev_scroll_y: Optional[float] = None

    def _can_execute(self) -> bool:
        """Check if debouncing cooldown has elapsed."""
        now = time.time()
        if (now - self.last_action_time) >= self.config.system_cooldown:
            self.last_action_time = now
            return True
        return False

    def close_current_tab(self) -> Tuple[bool, str]:
        """Send Ctrl + W to close current active browser tab or window."""
        if not self._can_execute():
            return False, "Cooldown Active"

        try:
            pyautogui.hotkey('ctrl', 'w')
            return True, "Closed Browser Tab (Ctrl+W)"
        except Exception as err:
            return False, f"Failed: {err}"

    def open_file_explorer(self) -> Tuple[bool, str]:
        """Send Win + E or open specified directory in File Explorer."""
        if not self._can_execute():
            return False, "Cooldown Active"

        try:
            if self.config.default_explorer_dir and os.path.exists(self.config.default_explorer_dir):
                os.startfile(self.config.default_explorer_dir)
                return True, f"Opened Folder: {os.path.basename(self.config.default_explorer_dir)}"
            else:
                pyautogui.hotkey('win', 'e')
                return True, "Opened File Explorer (Win+E)"
        except Exception as err:
            return False, f"Failed: {err}"

    def toggle_mute_audio(self) -> Tuple[bool, str]:
        """Toggle system audio mute."""
        if not self._can_execute():
            return False, "Cooldown Active"

        try:
            pyautogui.press('volumemute')
            return True, "Toggled Audio Mute"
        except Exception as err:
            return False, f"Failed: {err}"

    def switch_active_window(self) -> Tuple[bool, str]:
        """Send Alt + Tab to switch active application window."""
        if not self._can_execute():
            return False, "Cooldown Active"

        try:
            pyautogui.hotkey('alt', 'tab')
            return True, "Switched Window (Alt+Tab)"
        except Exception as err:
            return False, f"Failed: {err}"

    def handle_scroll(self, index_y_norm: float) -> Tuple[bool, str]:
        """
        Calculates vertical hand displacement and scrolls the screen.
        """
        if self.prev_scroll_y is None:
            self.prev_scroll_y = index_y_norm
            return False, "Scroll Inactive"

        dy = self.prev_scroll_y - index_y_norm  # Moving UP -> positive dy -> scroll UP
        self.prev_scroll_y = index_y_norm

        # Deadzone threshold to avoid jitter
        if abs(dy) < 0.015:
            return False, "Scroll Deadzone"

        # Scale dy to PyAutoGUI scroll units (e.g., 100-300 units per scroll tick)
        scroll_units = int(dy * 2500 * self.config.scroll_sensitivity)
        try:
            pyautogui.scroll(scroll_units)
            direction = "UP" if scroll_units > 0 else "DOWN"
            return True, f"Scrolled {direction}"
        except Exception:
            return False, "Scroll Exception"

    def reset_scroll(self):
        """Reset continuous scroll tracking position."""
        self.prev_scroll_y = None
