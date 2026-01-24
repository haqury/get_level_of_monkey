#!/usr/bin/env python
"""
Analyze screenshots to detect visual issues
"""

from PIL import Image
import os

def analyze_screenshot(filename):
    """Analyze screenshot for potential issues"""
    if not os.path.exists(filename):
        print(f"File not found: {filename}")
        return
    
    img = Image.open(filename)
    width, height = img.size
    print(f"\n{filename}:")
    print(f"  Size: {width}x{height}")
    
    # Check if image is mostly one color (indicates rendering issue)
    pixels = list(img.getdata())
    unique_colors = len(set(pixels[:1000]))  # Sample first 1000 pixels
    print(f"  Unique colors (sample): {unique_colors}")
    
    if unique_colors < 10:
        print("  WARNING: Very few colors detected - might be rendering issue")
    
    # Check for blank/white screen
    try:
        avg_brightness = sum(sum(img.getpixel((x, y))[:3])/3 
                            for x in range(0, width, 10) 
                            for y in range(0, height, 10)) / ((width//10) * (height//10))
        print(f"  Average brightness: {avg_brightness:.1f}/255")
        
        if avg_brightness > 240:
            print("  WARNING: Very bright screen - might be blank/white")
        elif avg_brightness < 10:
            print("  WARNING: Very dark screen - might be blank/black")
    except Exception as e:
        print(f"  Could not analyze brightness: {e}")

if __name__ == "__main__":
    print("Analyzing screenshots...")
    print("=" * 60)
    
    analyze_screenshot("screenshot_menu.png")
    analyze_screenshot("screenshot_gameplay.png")
    
    print("\n" + "=" * 60)
    print("Analysis complete!")
    print("\nNote: Full visual analysis requires manual inspection.")
