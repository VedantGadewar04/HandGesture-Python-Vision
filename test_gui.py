"""
GUI Integration Verification Script for HandVision.
Launches HandVisionDashboard, runs loop for 2 seconds, and exits safely.
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import AppConfig
from ui.dashboard import HandVisionDashboard


def main():
    print("[1/2] Initializing HandVision Dashboard UI...")
    config = AppConfig()
    app = HandVisionDashboard(config)

    # Let UI update for 2000 milliseconds
    start_time = time.time()

    def check_loop():
        if time.time() - start_time > 2.0:
            print("[2/2] UI Loop execution verified cleanly for 2.0 seconds!")
            app.destroy()
            print("=== GUI INTEGRATION TEST PASSED SUCCESSFULLY! ===")
            sys.exit(0)
        else:
            app.after(100, check_loop)

    app.after(100, check_loop)
    app.mainloop()


if __name__ == "__main__":
    main()
