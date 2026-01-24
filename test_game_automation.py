#!/usr/bin/env python
"""
Automated game testing script
- Launches game
- Waits for menu to load
- Clicks Play button or starts game programmatically
- Waits for gameplay
- Takes screenshot
- Saves for analysis
"""

import subprocess
import time
import sys
from pathlib import Path

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    print("Warning: pyautogui not available, install with: pip install pyautogui")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: PIL not available")


def take_screenshot(filename="screenshot.png"):
    """Take a screenshot of the screen"""
    if PYAUTOGUI_AVAILABLE:
        screenshot = pyautogui.screenshot()
        screenshot.save(filename)
        print(f"Screenshot saved to {filename}")
        return True
    else:
        print("Cannot take screenshot: pyautogui not available")
        return False


def find_and_click_play_button():
    """Try to find and click Play button"""
    if not PYAUTOGUI_AVAILABLE:
        return False
    
    try:
        # Look for Play button (green button in center)
        # This is a simple approach - might need image recognition
        # For now, try clicking center-bottom area where button should be
        screen_width, screen_height = pyautogui.size()
        
        # Play button is usually at (0, 0, -0.25) in normalized coords
        # On screen: center horizontally, slightly below center vertically
        x = screen_width // 2
        y = screen_height // 2 - 100  # Adjust based on your screen
        
        print(f"Attempting to click Play button at ({x}, {y})")
        pyautogui.click(x, y)
        return True
    except Exception as e:
        print(f"Error clicking Play button: {e}")
        return False


def main():
    """Main automation function"""
    print("=" * 60)
    print("Automated Game Testing")
    print("=" * 60)
    
    # Path to game
    game_script = Path("main.py")
    if not game_script.exists():
        print(f"Error: {game_script} not found!")
        return
    
    # Try to find venv Python
    venv_python = Path(".venv1/Scripts/python.exe")
    if venv_python.exists():
        python_exe = str(venv_python)
        print(f"   Using venv Python: {python_exe}")
    else:
        python_exe = sys.executable
        print(f"   Using system Python: {python_exe}")
    
    print(f"\n1. Launching game: {game_script}")
    print("   Using --auto-start flag for automatic gameplay start")
    
    # Start game process with auto-start
    # Don't redirect stdout/stderr for GUI applications - it can cause issues
    process = subprocess.Popen(
        [python_exe, str(game_script), "--auto-start", "--auto-start-delay", "5"],
        # Don't redirect output - let GUI app display normally
        cwd=str(Path.cwd())
    )
    
    # Timeline from logs:
    # 0s: Game starts
    # ~1s: Game initialized, menu shown (03:10:31,324)
    # ~12s: BrainLink timeout (03:10:42,510) 
    # ~13s: Auto-start triggers (timeout 8s + check 1s + delay 5s = ~14s from start)
    # ~14s: Game starting (03:10:43,422)
    # ~15s: Gameplay scene loaded
    
    print("   Waiting for game to load and show menu (3 seconds)...")
    time.sleep(3)  # Menu shows at ~1s, wait 2 more for stability
    
    print("\n2. Taking screenshot of main menu...")
    take_screenshot("screenshot_menu.png")
    
    print("\n3. Waiting for auto-start to trigger...")
    print("   (BrainLink timeout ~11s + auto-start delay 5s = ~16s total)")
    time.sleep(16)  # Wait for BrainLink timeout + auto-start delay + buffer
    
    print("\n4. Waiting for gameplay scene to fully load (2 seconds)...")
    time.sleep(2)  # Scene loads almost immediately, but wait for rendering
    
    print("\n5. Taking screenshot of gameplay...")
    take_screenshot("screenshot_gameplay.png")
    
    print("\n6. Closing game...")
    time.sleep(1)  # Brief pause before closing
    
    # Close game by sending Alt+F4 or closing window
    if PYAUTOGUI_AVAILABLE:
        try:
            # Press Alt+F4 to close window gracefully
            pyautogui.hotkey('alt', 'f4')
            time.sleep(1)
            # If that didn't work, try to terminate process
            if process.poll() is None:  # Process still running
                print("   Process still running, terminating...")
                process.terminate()
                time.sleep(1)
                if process.poll() is None:  # Still running
                    process.kill()
        except Exception as e:
            print(f"   Error closing window: {e}")
            # Fallback: terminate process
            try:
                process.terminate()
                time.sleep(1)
                if process.poll() is None:
                    process.kill()
            except:
                pass
    else:
        # No pyautogui, just terminate process
        try:
            process.terminate()
            time.sleep(1)
            if process.poll() is None:
                process.kill()
        except:
            pass
    
    print("\n7. Test complete!")
    print("   Screenshots saved:")
    print("   - screenshot_menu.png")
    print("   - screenshot_gameplay.png")
    
    return process


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
