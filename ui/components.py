"""
CustomTkinter UI Components & Settings Modal for HandVision.
Includes status card components, metrics displays, and interactive configuration dialogs.
"""

from typing import Callable, Dict, Any, Optional
import customtkinter as ctk
from src.config import AppConfig

# Configure CustomTkinter default appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class StatusCard(ctk.CTkFrame):
    """Reusable dark-styled card container with header title."""

    def __init__(
        self,
        master,
        title: str,
        config: AppConfig,
        **kwargs
    ):
        super().__init__(
            master,
            fg_color=config.card_bg,
            border_color=config.card_border,
            border_width=1,
            corner_radius=10,
            **kwargs
        )
        self.config = config

        # Card Title Header
        self.header = ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=config.accent_primary,
            anchor="w"
        )
        self.header.pack(fill="x", padx=14, pady=(10, 6))

        # Separator line
        self.sep = ctk.CTkFrame(self, height=1, fg_color=config.card_border)
        self.sep.pack(fill="x", padx=10, pady=(0, 8))

        # Content container
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=14, pady=(0, 10))


class KeyValueRow(ctk.CTkFrame):
    """Horizontal key-value metrics display row."""

    def __init__(self, master, label_text: str, default_val: str, config: AppConfig, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.label = ctk.CTkLabel(
            self,
            text=label_text,
            font=ctk.CTkFont(size=13),
            text_color=config.text_secondary,
            anchor="w"
        )
        self.label.pack(side="left", fill="x", expand=True)

        self.val_label = ctk.CTkLabel(
            self,
            text=default_val,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=config.text_primary,
            anchor="e"
        )
        self.val_label.pack(side="right")

    def set_value(self, text: str, color: Optional[str] = None):
        """Update value text and optional color."""
        self.val_label.configure(text=text)
        if color:
            self.val_label.configure(text_color=color)


class SettingsDialog(ctk.CTkToplevel):
    """Modal dialog for tweaking runtime configuration parameters."""

    def __init__(self, parent, config: AppConfig, on_save_callback: Callable):
        super().__init__(parent)
        self.config = config
        self.on_save_callback = on_save_callback

        self.title("HandVision Settings")
        self.geometry("450x580")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.configure(fg_color=config.bg_dark)

        # Header
        title_lbl = ctk.CTkLabel(
            self,
            text="Settings & Tuning",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=config.accent_primary
        )
        title_lbl.pack(pady=(15, 10))

        # Main scrollable frame
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=15, pady=5)

        # 1. Camera Index
        self.cam_idx_var = ctk.IntVar(value=config.camera_index)
        self._add_slider("Camera Index", self.scroll, self.cam_idx_var, 0, 3, is_int=True)

        # 2. Min Detection Confidence
        self.det_conf_var = ctk.DoubleVar(value=config.min_detection_confidence)
        self._add_slider("Min Detection Confidence", self.scroll, self.det_conf_var, 0.3, 0.95)

        # 3. Min Tracking Confidence
        self.track_conf_var = ctk.DoubleVar(value=config.min_tracking_confidence)
        self._add_slider("Min Tracking Confidence", self.scroll, self.track_conf_var, 0.3, 0.95)

        # 4. Cursor Sensitivity
        self.sens_var = ctk.DoubleVar(value=config.cursor_sensitivity)
        self._add_slider("Cursor Sensitivity", self.scroll, self.sens_var, 0.5, 3.0)

        # 5. Cursor Smoothing (Alpha)
        self.smooth_var = ctk.DoubleVar(value=config.cursor_smoothing)
        self._add_slider("Cursor Smoothing (Alpha)", self.scroll, self.smooth_var, 0.05, 0.9)

        # 6. Pinch Threshold (px)
        self.pinch_var = ctk.DoubleVar(value=config.pinch_threshold_px)
        self._add_slider("Pinch Threshold (px)", self.scroll, self.pinch_var, 20.0, 70.0)

        # 7. Gesture Cooldown (sec)
        self.cool_var = ctk.DoubleVar(value=config.gesture_cooldown)
        self._add_slider("Screenshot Cooldown (sec)", self.scroll, self.cool_var, 0.5, 3.5)

        # 8. System Action Cooldown (sec)
        self.sys_cool_var = ctk.DoubleVar(value=config.system_cooldown)
        self._add_slider("OS Action Cooldown (sec)", self.scroll, self.sys_cool_var, 0.5, 3.0)

        # 9. Scroll Sensitivity
        self.scroll_sens_var = ctk.DoubleVar(value=config.scroll_sensitivity)
        self._add_slider("Scroll Sensitivity", self.scroll, self.scroll_sens_var, 0.2, 3.0)

        # Save Button
        save_btn = ctk.CTkButton(
            self,
            text="Apply & Save Settings",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=config.accent_primary,
            hover_color="#0284C7",
            command=self._save
        )
        save_btn.pack(pady=15, padx=20, fill="x")

    def _add_slider(self, label_text: str, parent, variable, from_val, to_val, is_int: bool = False):
        frame = ctk.CTkFrame(parent, fg_color=self.config.card_bg, corner_radius=8)
        frame.pack(fill="x", pady=6, padx=5)

        val_lbl = ctk.CTkLabel(
            frame,
            text=f"{label_text}: {variable.get():.2f}" if not is_int else f"{label_text}: {variable.get()}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.config.text_primary
        )
        val_lbl.pack(anchor="w", padx=10, pady=(6, 2))

        def slider_cb(value):
            if is_int:
                variable.set(int(value))
                val_lbl.configure(text=f"{label_text}: {int(value)}")
            else:
                variable.set(round(value, 2))
                val_lbl.configure(text=f"{label_text}: {value:.2f}")

        slider = ctk.CTkSlider(
            frame,
            from_=from_val,
            to=to_val,
            command=slider_cb,
            button_color=self.config.accent_primary,
        )
        slider.set(variable.get())
        slider.pack(fill="x", padx=10, pady=(0, 8))

    def _save(self):
        new_settings = {
            "camera_index": int(self.cam_idx_var.get()),
            "min_detection_confidence": self.det_conf_var.get(),
            "min_tracking_confidence": self.track_conf_var.get(),
            "cursor_sensitivity": self.sens_var.get(),
            "cursor_smoothing": self.smooth_var.get(),
            "pinch_threshold_px": self.pinch_var.get(),
            "gesture_cooldown": self.cool_var.get(),
            "system_cooldown": self.sys_cool_var.get(),
            "scroll_sensitivity": self.scroll_sens_var.get(),
        }
        self.on_save_callback(new_settings)
        self.destroy()
