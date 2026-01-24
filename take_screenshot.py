#!/usr/bin/env python
"""
Simple screenshot utility for the game
Press Ctrl+C to exit, or just run it once to take a screenshot
"""

import time
from pathlib import Path
from datetime import datetime

try:
    import pyautogui
except ImportError:
    print("ERROR: pyautogui not installed!")
    print("Install it with: pip install pyautogui")
    exit(1)


def take_screenshot():
    """Take a screenshot and save it with timestamp"""
    # Create screenshots directory if it doesn't exist
    screenshots_dir = Path("screenshots")
    screenshots_dir.mkdir(exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = screenshots_dir / f"screenshot_{timestamp}.png"
    
    # Take screenshot
    try:
        screenshot = pyautogui.screenshot()
        screenshot.save(str(filename))
        print(f"✓ Screenshot saved: {filename}")
        return True
    except Exception as e:
        print(f"✗ Error taking screenshot: {e}")
        return False


def main():
    """Main function"""
    print("=" * 60)
    print("Game Screenshot Utility")
    print("=" * 60)
    print("\nUsage options:")
    print("1. Run once: python take_screenshot.py")
    print("2. Run in loop: python take_screenshot.py --loop")
    print("3. Press Ctrl+C to stop\n")
    
    import sys
    loop_mode = "--loop" in sys.argv
    
    if loop_mode:
        print("Loop mode: Taking screenshot every 5 seconds")
        print("Press Ctrl+C to stop\n")
        try:
            while True:
                take_screenshot()
                time.sleep(5)
        except KeyboardInterrupt:
            print("\n\nStopped by user")
    else:
        print("Taking single screenshot...\n")
        take_screenshot()


if __name__ == "__main__":
    main()
