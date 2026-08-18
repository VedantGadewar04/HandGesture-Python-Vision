"""
HandVision Backend Verification & Unit Test Suite.
Tests camera, hand tracker, gesture recognizer, virtual mouse, and utils.
"""

import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import AppConfig
from src.utils import map_coordinates, euclidean_distance_2d, FPSCounter
from src.hand_tracker import HandTracker, HandData
from src.gesture_recognizer import GestureRecognizer, detect_finger_states
from src.virtual_mouse import VirtualMouseController
from src.screenshot import ScreenshotManager


def test_utils():
    print("[1/5] Testing Utils & Math Helpers...")
    d = euclidean_distance_2d((0, 0), (3, 4))
    assert d == 5.0, f"Expected 5.0, got {d}"

    sx, sy = map_coordinates(320, 240, 640, 480, 1920, 1080)
    assert 0 <= sx <= 1920 and 0 <= sy <= 1080, f"Out of bounds mapping: {sx}, {sy}"

    fps = FPSCounter()
    fps.update()
    print("[OK] Utils Passed.")


def test_hand_tracker():
    print("[2/5] Testing MediaPipe Hand Tracker...")
    config = AppConfig()
    tracker = HandTracker(config)

    # Test processing a dummy image
    dummy_bgr = np.zeros((720, 1280, 3), dtype=np.uint8)
    hands = tracker.process_frame(dummy_bgr)
    assert isinstance(hands, list), "Expected list of hands"
    tracker.close()
    print("[OK] Hand Tracker Passed.")


def test_gesture_recognizer():
    print("[3/5] Testing Gesture Recognizer...")
    recognizer = GestureRecognizer(pinch_threshold_px=38.0)

    # Create synthetic hand data for POINT gesture (Index OPEN, others CLOSED)
    norm_lms = [(0.5, 0.5, 0.0)] * 21
    # Index tip (8) above PIP (6) -> OPEN
    norm_lms[8] = (0.5, 0.2, 0.0)
    norm_lms[6] = (0.5, 0.4, 0.0)

    # Middle, Ring, Pinky tips below PIP -> CLOSED
    norm_lms[12] = (0.6, 0.6, 0.0)
    norm_lms[10] = (0.6, 0.5, 0.0)
    norm_lms[16] = (0.7, 0.6, 0.0)
    norm_lms[14] = (0.7, 0.5, 0.0)
    norm_lms[20] = (0.8, 0.6, 0.0)
    norm_lms[18] = (0.8, 0.5, 0.0)

    px_lms = [(int(x * 1280), int(y * 720)) for x, y, z in norm_lms]

    dummy_hand = HandData(
        landmarks_norm=norm_lms,
        landmarks_px=px_lms,
        handedness="Right",
        confidence=0.95,
        bbox=(100, 100, 500, 500)
    )

    res = recognizer.recognize(dummy_hand)
    print(f"Recognized gesture: {res.gesture_name}, Action: {res.action_description}")
    assert res.gesture_name == "POINT", f"Expected POINT, got {res.gesture_name}"
    print("[OK] Gesture Recognizer Passed.")


def test_screenshot_manager():
    print("[4/5] Testing Screenshot Manager...")
    config = AppConfig()
    mgr = ScreenshotManager(config)
    print("[OK] Screenshot Manager Initialized.")


def test_virtual_mouse():
    print("[5/5] Testing Virtual Mouse Controller...")
    config = AppConfig()
    vm = VirtualMouseController(config)
    assert vm.screen_width > 0 and vm.screen_height > 0
    print("[OK] Virtual Mouse Controller Initialized.")


if __name__ == "__main__":
    test_utils()
    test_hand_tracker()
    test_gesture_recognizer()
    test_screenshot_manager()
    test_virtual_mouse()
    print("\n" + "=" * 50)
    print(" ALL BACKEND UNIT TESTS PASSED SUCCESSFULLY! ")
    print("=" * 50)
