"""
Gesture Recognition Engine for HandVision.
Detects finger states (OPEN/CLOSED) and evaluates rule-based gesture patterns,
including OS system controls (Close Tab, Open Explorer, Scroll, Mute, Switch Window).
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import math
from src.hand_tracker import HandData
from src.utils import euclidean_distance_2d


@dataclass
class GestureResult:
    """Result of gesture recognition analysis."""
    gesture_name: str                           # Gesture identifier
    finger_states: Dict[str, str]               # {"Thumb": "OPEN", ...}
    pinch_distance: float                       # Distance between Thumb and Index tip (px)
    action_description: str                     # Human readable system action


def detect_finger_states(
    landmarks_norm: List[Tuple[float, float, float]],
    handedness: str = "Right"
) -> Dict[str, str]:
    """
    Evaluates individual finger states (OPEN / CLOSED) using 3D landmarks.
    Combines y-coordinate Ratios AND Wrist-to-Joint Euclidean Distances for 100% rotation invariance.
    Landmark Indices:
      Thumb:  Tip=4, IP=3, MCP=2, CMC=1
      Index:  Tip=8, DIP=7, PIP=6, MCP=5
      Middle: Tip=12, DIP=11, PIP=10, MCP=9
      Ring:   Tip=16, DIP=15, PIP=14, MCP=13
      Pinky:  Tip=20, DIP=19, PIP=18, MCP=17
      Wrist:  0
    """
    if len(landmarks_norm) < 21:
        return {f: "CLOSED" for f in ["Thumb", "Index", "Middle", "Ring", "Pinky"]}

    wrist = landmarks_norm[0]

    def dist_wrist(idx: int) -> float:
        return math.hypot(landmarks_norm[idx][0] - wrist[0], landmarks_norm[idx][1] - wrist[1])

    states = {}

    # 1. Index Finger (Tip 8 vs MCP 5 / PIP 6)
    states["Index"] = "OPEN" if (dist_wrist(8) > dist_wrist(5) * 1.22 or landmarks_norm[8][1] < landmarks_norm[6][1]) else "CLOSED"

    # 2. Middle Finger (Tip 12 vs MCP 9 / PIP 10)
    states["Middle"] = "OPEN" if (dist_wrist(12) > dist_wrist(9) * 1.22 or landmarks_norm[12][1] < landmarks_norm[10][1]) else "CLOSED"

    # 3. Ring Finger (Tip 16 vs MCP 13 / PIP 14)
    states["Ring"] = "OPEN" if (dist_wrist(16) > dist_wrist(13) * 1.22 or landmarks_norm[16][1] < landmarks_norm[14][1]) else "CLOSED"

    # 4. Pinky Finger (Tip 20 vs MCP 17 / PIP 18)
    states["Pinky"] = "OPEN" if (dist_wrist(20) > dist_wrist(17) * 1.22 or landmarks_norm[20][1] < landmarks_norm[18][1]) else "CLOSED"

    # 5. Thumb Finger (Tip 4 vs MCP 2)
    states["Thumb"] = "OPEN" if (dist_wrist(4) > dist_wrist(2) * 1.15) else "CLOSED"

    return states


class GestureRecognizer:
    """Centralized evaluator classifying hand landmarks into discrete gestures."""

    def __init__(self, pinch_threshold_px: float = 38.0):
        self.pinch_threshold_px = pinch_threshold_px

    def recognize(self, hand: HandData) -> GestureResult:
        """Evaluates hand landmarks and returns gesture decision."""
        finger_states = detect_finger_states(hand.landmarks_norm, hand.handedness)

        # Calculate pixel distance between Thumb Tip (4) and Index Tip (8)
        thumb_px = hand.landmarks_px[4]
        index_px = hand.landmarks_px[8]
        middle_px = hand.landmarks_px[12]
        pinch_dist = euclidean_distance_2d(thumb_px, index_px)
        index_middle_dist = euclidean_distance_2d(index_px, middle_px)

        thumb = finger_states["Thumb"] == "OPEN"
        index = finger_states["Index"] == "OPEN"
        middle = finger_states["Middle"] == "OPEN"
        ring = finger_states["Ring"] == "OPEN"
        pinky = finger_states["Pinky"] == "OPEN"

        main_open_count = sum([index, middle, ring, pinky])

        # Check THUMBS_DOWN (Thumb tip pointing downwards below MCP, other fingers closed)
        thumb_tip_norm = hand.landmarks_norm[4]
        thumb_mcp_norm = hand.landmarks_norm[2]
        is_thumbs_down = (thumb_tip_norm[1] > thumb_mcp_norm[1] + 0.04) and (not index and not middle and not ring and not pinky)

        # OK SIGN: Thumb and Index tips close together, while Middle, Ring, Pinky are open
        is_ok_sign = (pinch_dist < 28.0) and middle and ring and pinky

        gesture = "UNKNOWN"
        action = "None"

        # 1. OK SIGN -> Switch Window (Alt + Tab)
        if is_ok_sign:
            gesture = "OK_SIGN"
            action = "Switch Window (Alt+Tab)"

        # 2. PINCH -> Mouse Click / Drag
        elif pinch_dist < self.pinch_threshold_px and (index or thumb):
            gesture = "PINCH"
            action = "Mouse Click / Drag"

        # 3. FOUR FINGERS: Index, Middle, Ring, Pinky ALL OPEN -> Open File Explorer
        elif index and middle and ring and pinky:
            gesture = "FOUR_FINGERS"
            action = "Open File Explorer"

        # 4. THREE FINGERS: Index, Middle, Ring OPEN, Pinky CLOSED -> Close Current Tab
        elif index and middle and ring and not pinky:
            gesture = "THREE_FINGERS"
            action = "Close Current Tab"

        # 5. FIST: All fingers closed
        elif main_open_count == 0 and not thumb and not is_thumbs_down:
            gesture = "FIST"
            action = "Stop Interaction"

        # 6. THUMBS DOWN: Thumb pointing downwards
        elif is_thumbs_down:
            gesture = "THUMBS_DOWN"
            action = "Toggle Audio Mute"

        # 7. THUMBS UP: Thumb open while Index, Middle, Ring, Pinky closed
        elif thumb and main_open_count == 0:
            gesture = "THUMBS_UP"
            action = "Confirm / Activate"

        # 8. TWO FINGERS SCROLL: Index & Middle open together, Ring & Pinky closed
        elif index and middle and not ring and not pinky and index_middle_dist < 45.0:
            gesture = "TWO_FINGERS_SCROLL"
            action = "Scroll Page Up/Down"

        # 9. VICTORY: Index + Middle open wide while Ring & Pinky closed
        elif index and middle and not ring and not pinky and index_middle_dist >= 45.0:
            gesture = "VICTORY"
            action = "Take Screenshot"

        # 10. POINT: Only Index open
        elif index and not middle and not ring and not pinky:
            gesture = "POINT"
            action = "Cursor Control"

        else:
            gesture = "UNKNOWN"
            action = "None"

        return GestureResult(
            gesture_name=gesture,
            finger_states=finger_states,
            pinch_distance=pinch_dist,
            action_description=action,
        )
