"""
HandVision Application Entry Point.
AI-Powered Hand & Screen Visualization System.
"""

import sys
import os

# Add project root directory to python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import AppConfig
from ui.dashboard import HandVisionDashboard


def main():
    """Application main entry point."""
    print("=" * 60)
    print(" HandVision — AI-Powered Hand & Screen Visualization System")
    print("=" * 60)
    print("Initializing HandVision Dashboard...")
    print("Press ESC key inside the window to immediately stop virtual mouse.")

    try:
        config = AppConfig()
        app = HandVisionDashboard(config)
        app.mainloop()
    except KeyboardInterrupt:
        print("\nApplication stopped by user.")
    except Exception as err:
        print(f"\n[Fatal Error] {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
