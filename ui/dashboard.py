"""
Main Dashboard Application Window for HandVision v2.0.
Assembles live video view, status cards grid, control bar, and real-time processing loop with OS controls.
"""

import os
import sys
import time
from typing import Optional
import cv2
from PIL import Image
import customtkinter as ctk

from src.config import AppConfig
from src.camera import CameraManager
from src.hand_tracker import HandTracker, HandData
from src.gesture_recognizer import GestureRecognizer, GestureResult
from src.virtual_mouse import VirtualMouseController
from src.screenshot import ScreenshotManager
from src.system_controller import SystemController
from src.utils import FPSCounter, draw_styled_hand
from ui.components import StatusCard, KeyValueRow, SettingsDialog


class HandVisionDashboard(ctk.CTk):
    """Main Application GUI Window and Processing Master Loop."""

    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config

        # Main Window Setup
        self.title("HandVision v2.0 — AI Touchless Hand & OS Screen Controller")
        self.geometry("1320x840")
        self.minsize(1150, 720)
        self.configure(fg_color=config.bg_dark)

        # Core Backend Subsystems
        self.camera = CameraManager(config)
        self.tracker: Optional[HandTracker] = None
        self.gesture_engine = GestureRecognizer(config.pinch_threshold_px)
        self.mouse_controller = VirtualMouseController(config)
        self.screenshot_mgr = ScreenshotManager(config)
        self.sys_controller = SystemController(config)
        self.fps_counter = FPSCounter()

        # UI Toast Notification Timer
        self.toast_msg: Optional[str] = None
        self.toast_end_time: float = 0.0

        # Build GUI Layout
        self._build_header()
        self._build_main_body()
        self._build_bottom_controls()

        # Bind Hotkeys
        self.bind("<Escape>", lambda e: self.emergency_stop())

        # Protocol Handler for Close Button
        self.protocol("WM_DELETE_WINDOW", self.safe_exit)

        # Initialize Hand Tracker
        try:
            self.tracker = HandTracker(config)
        except Exception as err:
            self._show_toast(f"Tracker Error: {err}", duration=5.0)

        # Auto-start Camera on launch
        self.start_camera()

        # Kickoff main processing loop
        self.after(15, self._main_loop)

    def _build_header(self):
        """Top Header Banner."""
        header_frame = ctk.CTkFrame(self, fg_color=self.config.card_bg, height=60, corner_radius=0)
        header_frame.pack(fill="x", side="top", padx=0, pady=0)

        # Title Text
        title_lbl = ctk.CTkLabel(
            header_frame,
            text="HandVision v2.0",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=self.config.accent_primary
        )
        title_lbl.pack(side="left", padx=(20, 10), pady=12)

        # Subtitle
        sub_lbl = ctk.CTkLabel(
            header_frame,
            text="AI-Powered Touchless OS & Screen Controller",
            font=ctk.CTkFont(size=14),
            text_color=self.config.text_secondary
        )
        sub_lbl.pack(side="left", pady=12)

        # Right Status Badge
        self.badge_lbl = ctk.CTkLabel(
            header_frame,
            text="● SYSTEM OFFLINE",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=self.config.accent_danger
        )
        self.badge_lbl.pack(side="right", padx=20, pady=12)

    def _build_main_body(self):
        """Build Main Split Body (Left Video Feed, Right Status Cards)."""
        body_frame = ctk.CTkFrame(self, fg_color="transparent")
        body_frame.pack(fill="both", expand=True, padx=15, pady=12)

        # LEFT PANEL: Video Display
        left_panel = ctk.CTkFrame(
            body_frame,
            fg_color=self.config.card_bg,
            border_color=self.config.card_border,
            border_width=1,
            corner_radius=12
        )
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.video_label = ctk.CTkLabel(left_panel, text="Initializing Camera Feed...", text_color=self.config.text_secondary)
        self.video_label.pack(fill="both", expand=True, padx=8, pady=8)

        # RIGHT PANEL: Status Cards Stack
        right_panel = ctk.CTkFrame(body_frame, fg_color="transparent", width=340)
        right_panel.pack(side="right", fill="y", padx=(0, 0))
        right_panel.pack_propagate(False)

        # 1. HAND STATUS Card
        self.hand_card = StatusCard(right_panel, "HAND STATUS", self.config)
        self.hand_card.pack(fill="x", pady=(0, 8))

        self.row_hand_detected = KeyValueRow(self.hand_card.content_frame, "Hand Detected:", "NO", self.config)
        self.row_hand_detected.pack(fill="x", pady=1)

        self.row_hand_label = KeyValueRow(self.hand_card.content_frame, "Hand:", "None", self.config)
        self.row_hand_label.pack(fill="x", pady=1)

        self.row_confidence = KeyValueRow(self.hand_card.content_frame, "Confidence:", "0%", self.config)
        self.row_confidence.pack(fill="x", pady=1)

        # 2. FINGER STATUS Card
        self.finger_card = StatusCard(right_panel, "FINGER STATUS", self.config)
        self.finger_card.pack(fill="x", pady=(0, 8))

        self.finger_rows = {}
        for finger in ["Thumb", "Index", "Middle", "Ring", "Pinky"]:
            r = KeyValueRow(self.finger_card.content_frame, f"{finger}:", "CLOSED", self.config)
            r.pack(fill="x", pady=1)
            self.finger_rows[finger] = r

        # 3. GESTURE & ACTION Card
        self.gesture_card = StatusCard(right_panel, "GESTURE & ACTION", self.config)
        self.gesture_card.pack(fill="x", pady=(0, 8))

        self.row_gesture = KeyValueRow(self.gesture_card.content_frame, "Gesture:", "UNKNOWN", self.config)
        self.row_gesture.pack(fill="x", pady=1)

        self.row_action = KeyValueRow(self.gesture_card.content_frame, "Action:", "Pause / Neutral", self.config)
        self.row_action.pack(fill="x", pady=1)

        # 4. OS CONTROL STATUS Card
        self.os_card = StatusCard(right_panel, "OS CONTROLS", self.config)
        self.os_card.pack(fill="x", pady=(0, 8))

        self.row_os_status = KeyValueRow(self.os_card.content_frame, "OS Automation:", "ACTIVE", self.config)
        self.row_os_status.pack(fill="x", pady=1)

        self.row_os_last = KeyValueRow(self.os_card.content_frame, "Last OS Event:", "None", self.config)
        self.row_os_last.pack(fill="x", pady=1)

        # 5. SYSTEM METRICS Card
        self.sys_card = StatusCard(right_panel, "SYSTEM METRICS", self.config)
        self.sys_card.pack(fill="x")

        self.row_fps = KeyValueRow(self.sys_card.content_frame, "FPS:", "0.0", self.config)
        self.row_fps.pack(fill="x", pady=1)

        self.row_resolution = KeyValueRow(self.sys_card.content_frame, "Camera:", "0x0", self.config)
        self.row_resolution.pack(fill="x", pady=1)

        self.row_vmouse = KeyValueRow(self.sys_card.content_frame, "Virtual Mouse:", "DISABLED", self.config)
        self.row_vmouse.pack(fill="x", pady=1)

    def _build_bottom_controls(self):
        """Bottom Action Control Bar."""
        bar = ctk.CTkFrame(self, fg_color=self.config.card_bg, height=65, corner_radius=0)
        bar.pack(fill="x", side="bottom", padx=0, pady=0)

        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=15, pady=10)

        # Start Camera Button
        self.btn_start = ctk.CTkButton(
            inner,
            text="Start Camera",
            font=ctk.CTkFont(weight="bold"),
            fg_color=self.config.accent_success,
            hover_color="#16A34A",
            width=100,
            command=self.start_camera
        )
        self.btn_start.pack(side="left", padx=4)

        # Stop Camera Button
        self.btn_stop = ctk.CTkButton(
            inner,
            text="Stop Camera",
            font=ctk.CTkFont(weight="bold"),
            fg_color=self.config.accent_danger,
            hover_color="#DC2626",
            width=100,
            command=self.stop_camera
        )
        self.btn_stop.pack(side="left", padx=4)

        # Virtual Mouse Toggle Button
        self.btn_vmouse = ctk.CTkButton(
            inner,
            text="Virtual Mouse: OFF",
            font=ctk.CTkFont(weight="bold"),
            fg_color="#334155",
            hover_color="#475569",
            width=140,
            command=self.toggle_virtual_mouse
        )
        self.btn_vmouse.pack(side="left", padx=6)

        # OS Control Toggle Button
        self.btn_os_control = ctk.CTkButton(
            inner,
            text="OS Control: ON",
            font=ctk.CTkFont(weight="bold"),
            fg_color=self.config.accent_secondary,
            hover_color="#6366F1",
            width=130,
            command=self.toggle_os_control
        )
        self.btn_os_control.pack(side="left", padx=6)

        # Manual Screenshot Button
        self.btn_shot = ctk.CTkButton(
            inner,
            text="📷 Screenshot",
            font=ctk.CTkFont(weight="bold"),
            fg_color="#475569",
            hover_color="#64748B",
            width=110,
            command=self.take_screenshot
        )
        self.btn_shot.pack(side="left", padx=4)

        # Settings Button
        self.btn_settings = ctk.CTkButton(
            inner,
            text="⚙ Settings",
            font=ctk.CTkFont(weight="bold"),
            fg_color="#475569",
            hover_color="#64748B",
            width=90,
            command=self.open_settings
        )
        self.btn_settings.pack(side="right", padx=4)

        # Exit Button
        self.btn_exit = ctk.CTkButton(
            inner,
            text="Exit App (ESC)",
            font=ctk.CTkFont(weight="bold"),
            fg_color="#991B1B",
            hover_color="#7F1D1D",
            width=110,
            command=self.safe_exit
        )
        self.btn_exit.pack(side="right", padx=4)

    def start_camera(self):
        """Start video camera stream."""
        if self.camera.start():
            self.badge_lbl.configure(text="● ONLINE", text_color=self.config.accent_success)
            w, h = self.camera.get_resolution()
            self.row_resolution.set_value(f"{w}x{h}")
            self._show_toast("Camera Started Successfully", duration=2.0)
        else:
            self.badge_lbl.configure(text="● ERROR", text_color=self.config.accent_danger)
            self._show_toast(f"Camera Error: {self.camera.error_message}", duration=4.0)

    def stop_camera(self):
        """Stop video camera stream."""
        self.camera.stop()
        self.badge_lbl.configure(text="● STOPPED", text_color=self.config.accent_warning)
        self.row_hand_detected.set_value("NO", self.config.accent_danger)
        self._show_toast("Camera Stopped", duration=2.0)

    def toggle_virtual_mouse(self):
        """Toggle Virtual Mouse mode."""
        self.config.virtual_mouse_enabled = not self.config.virtual_mouse_enabled
        if self.config.virtual_mouse_enabled:
            self.btn_vmouse.configure(text="Virtual Mouse: ON", fg_color=self.config.accent_primary)
            self.row_vmouse.set_value("ENABLED", self.config.accent_success)
            self._show_toast("Virtual Mouse Activated! Move Index Finger.", duration=3.0)
        else:
            self.btn_vmouse.configure(text="Virtual Mouse: OFF", fg_color="#334155")
            self.row_vmouse.set_value("DISABLED", self.config.text_secondary)
            self._show_toast("Virtual Mouse Disabled", duration=2.0)

    def toggle_os_control(self):
        """Toggle OS Control mode."""
        self.config.system_control_enabled = not self.config.system_control_enabled
        if self.config.system_control_enabled:
            self.btn_os_control.configure(text="OS Control: ON", fg_color=self.config.accent_secondary)
            self.row_os_status.set_value("ACTIVE", self.config.accent_success)
            self._show_toast("OS Control Enabled (Close Tab, Open Explorer, Mute, Alt-Tab)", duration=3.0)
        else:
            self.btn_os_control.configure(text="OS Control: OFF", fg_color="#334155")
            self.row_os_status.set_value("DISABLED", self.config.text_secondary)
            self._show_toast("OS Control Disabled", duration=2.0)

    def emergency_stop(self):
        """Emergency ESC hotkey handler: instantly disables virtual mouse & OS controls."""
        self.config.virtual_mouse_enabled = False
        self.config.system_control_enabled = False
        self.btn_vmouse.configure(text="Virtual Mouse: OFF", fg_color="#334155")
        self.btn_os_control.configure(text="OS Control: OFF", fg_color="#334155")
        self.row_vmouse.set_value("DISABLED", self.config.text_secondary)
        self.row_os_status.set_value("DISABLED", self.config.text_secondary)
        self._show_toast("EMERGENCY STOP: Mouse & OS Controls Disabled!", duration=3.0)

    def take_screenshot(self):
        """Manual screenshot trigger."""
        success, path = self.screenshot_mgr.trigger_screenshot()
        if success and path:
            basename = os.path.basename(path)
            self._show_toast(f"Screenshot Saved: {basename}", duration=3.5)
        else:
            self._show_toast("Screenshot Cooldown Active...", duration=1.5)

    def open_settings(self):
        """Open settings modal."""
        def apply_changes(new_settings):
            self.config.update(**new_settings)
            self.gesture_engine.pinch_threshold_px = self.config.pinch_threshold_px
            if self.tracker:
                self.tracker.close()
                self.tracker = HandTracker(self.config)
            self._show_toast("Settings Applied Successfully", duration=2.5)

        SettingsDialog(self, self.config, apply_changes)

    def _show_toast(self, message: str, duration: float = 3.0):
        """Set floating toast overlay banner on video feed."""
        self.toast_msg = message
        self.toast_end_time = time.time() + duration

    def _main_loop(self):
        """Real-time processing loop executed every 15ms."""
        fps = self.fps_counter.update()
        self.row_fps.set_value(f"{fps:.1f}")

        ret, frame = self.camera.read()

        if ret and frame is not None:
            cam_res = self.camera.get_resolution()

            # Process Hand Tracking
            hands: list[HandData] = []
            if self.tracker:
                hands = self.tracker.process_frame(frame)

            if hands:
                hand = hands[0]  # Primary hand

                # Gesture Evaluation
                gesture_res: GestureResult = self.gesture_engine.recognize(hand)

                # Update Virtual Mouse
                if self.config.virtual_mouse_enabled:
                    self.mouse_controller.update(hand, gesture_res, cam_res)

                # OS Controls Evaluation
                if self.config.system_control_enabled:
                    # 1. Close Browser Tab (THREE FINGERS)
                    if gesture_res.gesture_name == "THREE_FINGERS":
                        ok, msg = self.sys_controller.close_current_tab()
                        if ok:
                            self.row_os_last.set_value("Close Tab", self.config.accent_primary)
                            self._show_toast(f"🌐 {msg}", duration=3.0)

                    # 2. Open File Explorer (FOUR FINGERS)
                    elif gesture_res.gesture_name == "FOUR_FINGERS":
                        ok, msg = self.sys_controller.open_file_explorer()
                        if ok:
                            self.row_os_last.set_value("Open Explorer", self.config.accent_primary)
                            self._show_toast(f"📁 {msg}", duration=3.0)

                    # 3. Toggle Mute Audio (THUMBS DOWN)
                    elif gesture_res.gesture_name == "THUMBS_DOWN":
                        ok, msg = self.sys_controller.toggle_mute_audio()
                        if ok:
                            self.row_os_last.set_value("Mute Audio", self.config.accent_warning)
                            self._show_toast(f"🔇 {msg}", duration=3.0)

                    # 4. Switch Window (OK SIGN)
                    elif gesture_res.gesture_name == "OK_SIGN":
                        ok, msg = self.sys_controller.switch_active_window()
                        if ok:
                            self.row_os_last.set_value("Switch Window", self.config.accent_secondary)
                            self._show_toast(f"🔀 {msg}", duration=3.0)

                    # 5. Dynamic Screen Scroll (TWO FINGERS SCROLL)
                    elif gesture_res.gesture_name == "TWO_FINGERS_SCROLL":
                        index_y_norm = hand.landmarks_norm[8][1]
                        ok, msg = self.sys_controller.handle_scroll(index_y_norm)
                        if ok:
                            self.row_os_last.set_value("Scroll Screen", self.config.accent_primary)
                    else:
                        self.sys_controller.reset_scroll()

                # Screenshot Gesture Trigger (VICTORY)
                if self.config.gesture_control_enabled and gesture_res.gesture_name == "VICTORY":
                    success, path = self.screenshot_mgr.trigger_screenshot()
                    if success and path:
                        self._show_toast(f"📷 Screenshot Saved: {os.path.basename(path)}", duration=3.0)

                # Render Visualizations on Frame
                frame = draw_styled_hand(
                    frame,
                    hand.landmarks_px,
                    hand.handedness,
                    hand.confidence,
                    gesture_res.gesture_name,
                    gesture_res.pinch_distance,
                    self.config
                )

                # Update UI Dashboard Panels
                self.row_hand_detected.set_value("YES", self.config.accent_success)
                self.row_hand_label.set_value(hand.handedness)
                self.row_confidence.set_value(f"{int(hand.confidence * 100)}%")

                for f_name, f_state in gesture_res.finger_states.items():
                    color = self.config.accent_success if f_state == "OPEN" else self.config.text_secondary
                    self.finger_rows[f_name].set_value(f_state, color)

                self.row_gesture.set_value(gesture_res.gesture_name, self.config.accent_primary)
                self.row_action.set_value(gesture_res.action_description, self.config.accent_secondary)

            else:
                # No hand detected
                self.row_hand_detected.set_value("NO", self.config.accent_danger)
                self.row_hand_label.set_value("None")
                self.row_confidence.set_value("0%")
                self.row_gesture.set_value("UNKNOWN")
                self.row_action.set_value("None")
                for f_row in self.finger_rows.values():
                    f_row.set_value("CLOSED", self.config.text_secondary)

                self.mouse_controller._release_mouse_if_held()
                self.sys_controller.reset_scroll()

        # Render Toast Overlay on Frame if active
        if self.toast_msg and time.time() < self.toast_end_time:
            cv2.rectangle(frame, (10, 10), (frame.shape[1] - 10, 50), (30, 30, 30), -1)
            cv2.putText(
                frame,
                self.toast_msg,
                (20, 38),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (50, 220, 255),
                2,
                cv2.LINE_AA
            )

        # Convert OpenCV BGR Frame -> CTkImage for CustomTkinter
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_frame)

        # Scale image to fit label dimensions
        lbl_w = max(100, self.video_label.winfo_width())
        lbl_h = max(100, self.video_label.winfo_height())
        ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(lbl_w, lbl_h))

        self.video_label.configure(image=ctk_img, text="")

        # Schedule next update tick
        self.after(15, self._main_loop)

    def safe_exit(self):
        """Graceful shutdown of camera, virtual mouse, and window."""
        self.stop_camera()
        if self.tracker:
            self.tracker.close()
        self.destroy()
        sys.exit(0)
