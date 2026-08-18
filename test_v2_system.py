"""
HandVision v2.0 OS & Gesture Verification Test Suite.
Verifies THREE_FINGERS, FOUR_FINGERS, OK_SIGN, THUMBS_DOWN, TWO_FINGERS_SCROLL, and SystemController.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import AppConfig
from src.hand_tracker import HandData
from src.gesture_recognizer import GestureRecognizer
from src.system_controller import SystemController


def make_synthetic_hand(
    index_open=False,
    middle_open=False,
    ring_open=False,
    pinky_open=False,
    thumb_open=False,
    thumb_index_dist_px=100.0,
    index_middle_dist_px=100.0,
    thumbs_down=False
):
    # Wrist at (0.5, 0.8)
    norm_lms = [(0.5, 0.8, 0.0)] * 21

    # MCPs at y = 0.5
    norm_lms[5] = (0.4, 0.5, 0.0)
    norm_lms[9] = (0.5, 0.5, 0.0)
    norm_lms[13] = (0.6, 0.5, 0.0)
    norm_lms[17] = (0.7, 0.5, 0.0)
    norm_lms[2] = (0.3, 0.6, 0.0)

    # PIPs at y = 0.4
    norm_lms[6] = (0.4, 0.4, 0.0)
    norm_lms[10] = (0.5, 0.4, 0.0)
    norm_lms[14] = (0.6, 0.4, 0.0)
    norm_lms[18] = (0.7, 0.4, 0.0)
    norm_lms[3] = (0.25, 0.6, 0.0)

    # Tips (Open -> y = 0.1, Closed -> y = 0.55)
    norm_lms[8] = (0.4, 0.1 if index_open else 0.55, 0.0)
    norm_lms[12] = (0.5, 0.1 if middle_open else 0.55, 0.0)
    norm_lms[16] = (0.6, 0.1 if ring_open else 0.55, 0.0)
    norm_lms[20] = (0.7, 0.1 if pinky_open else 0.55, 0.0)

    if thumbs_down:
        norm_lms[4] = (0.3, 0.85, 0.0)  # Below MCP & Wrist
    elif thumb_open:
        norm_lms[4] = (0.1, 0.4, 0.0)   # Stretched open
    else:
        norm_lms[4] = (0.35, 0.55, 0.0)

    px_lms = [(int(x * 1280), int(y * 720)) for x, y, z in norm_lms]

    # Override Thumb & Index tip px distance
    px_lms[4] = (200, 200)
    px_lms[8] = (int(200 + thumb_index_dist_px), 200)
    px_lms[12] = (int(200 + thumb_index_dist_px + index_middle_dist_px), 200)

    return HandData(
        landmarks_norm=norm_lms,
        landmarks_px=px_lms,
        handedness="Right",
        confidence=0.95,
        bbox=(100, 100, 500, 500)
    )


def test_v2_gestures():
    print("[1/2] Testing v2.0 Gesture Classification...")
    rec = GestureRecognizer(pinch_threshold_px=38.0)

    # 1. THREE_FINGERS
    hand3 = make_synthetic_hand(index_open=True, middle_open=True, ring_open=True, pinky_open=False, thumb_open=False)
    g3 = rec.recognize(hand3)
    assert g3.gesture_name == "THREE_FINGERS", f"Expected THREE_FINGERS, got {g3.gesture_name}"

    # 2. FOUR_FINGERS
    hand4 = make_synthetic_hand(index_open=True, middle_open=True, ring_open=True, pinky_open=True, thumb_open=False)
    g4 = rec.recognize(hand4)
    assert g4.gesture_name == "FOUR_FINGERS", f"Expected FOUR_FINGERS, got {g4.gesture_name}"

    # 3. OK_SIGN
    hand_ok = make_synthetic_hand(index_open=True, middle_open=True, ring_open=True, pinky_open=True, thumb_open=True, thumb_index_dist_px=15.0)
    g_ok = rec.recognize(hand_ok)
    assert g_ok.gesture_name == "OK_SIGN", f"Expected OK_SIGN, got {g_ok.gesture_name}"

    # 4. THUMBS_DOWN
    hand_td = make_synthetic_hand(thumbs_down=True)
    g_td = rec.recognize(hand_td)
    assert g_td.gesture_name == "THUMBS_DOWN", f"Expected THUMBS_DOWN, got {g_td.gesture_name}"

    # 5. TWO_FINGERS_SCROLL
    hand_sc = make_synthetic_hand(index_open=True, middle_open=True, ring_open=False, pinky_open=False, thumb_open=False, index_middle_dist_px=25.0)
    g_sc = rec.recognize(hand_sc)
    assert g_sc.gesture_name == "TWO_FINGERS_SCROLL", f"Expected TWO_FINGERS_SCROLL, got {g_sc.gesture_name}"

    print("[OK] All v2.0 Gesture Recognition Tests Passed Successfully!")


def test_system_controller():
    print("[2/2] Testing SystemController Initializer & Cooldowns...")
    config = AppConfig()
    sc = SystemController(config)
    assert sc._can_execute() == True
    assert sc._can_execute() == False  # Debounced by cooldown
    print("[OK] SystemController Tests Passed Successfully!")


if __name__ == "__main__":
    test_v2_gestures()
    test_system_controller()
    print("\n==================================================")
    print(" ALL V2.0 SYSTEM & GESTURE TESTS PASSED! ")
    print("==================================================")
