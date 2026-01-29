#!/usr/bin/env python3
"""
Verification script to ensure simple theming is working correctly.
Run this after the theming revert to verify everything works.
"""

import os
import sys
from pathlib import Path

def check_file_exists(filepath, should_exist=True):
    """Check if a file exists or not."""
    exists = Path(filepath).exists()
    if should_exist and exists:
        print(f"✓ {filepath} exists")
        return True
    elif not should_exist and not exists:
        print(f"✓ {filepath} correctly removed")
        return True
    else:
        status = "missing" if should_exist else "still exists"
        print(f"❌ {filepath} {status}")
        return False

def check_file_content(filepath, should_contain, should_not_contain=None):
    """Check file content for specific strings."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        for item in should_contain:
            if item in content:
                print(f"✓ {filepath} contains '{item}'")
            else:
                print(f"❌ {filepath} missing '{item}'")
        
        if should_not_contain:
            for item in should_not_contain:
                if item not in content:
                    print(f"✓ {filepath} doesn't contain '{item}'")
                else:
                    print(f"❌ {filepath} still contains '{item}'")
    
    except FileNotFoundError:
        print(f"❌ {filepath} not found")

def main():
    print("=== Simple Theming Verification ===\n")
    
    # Check removed files
    print("1. Checking removed theme files:")
    check_file_exists("wxmeow/static/js/theme-switcher.js", False)
    print()
    
    # Check base template
    print("2. Checking base template:")
    check_file_content(
        "wxmeow/templates/base.html",
        should_contain=["temperature-chart.js", "^.^___/"],
        should_not_contain=["theme-toggle", "data-theme", "theme-switcher.js"]
    )
    print()
    
    # Check test templates
    print("3. Checking test templates:")
    check_file_content(
        "wxmeow/templates/test_autocomplete.html",
        should_contain=["autocomplete.js"],
        should_not_contain=["theme-switcher.js", "data-theme", "var(--"]
    )
    print()
    
    # Check styles
    print("4. Checking styles:")
    check_file_content(
        "wxmeow/static/styles.css",
        should_contain=[".hourly-chart", ".temperature-chart", "border-radius: 4px"],
        should_not_contain=["var(--", ":root", "--background-color"]
    )
    print()
    
    # Test app import
    print("5. Testing app import:")
    try:
        sys.path.insert(0, '.')
        from wxmeow import app
        from wxmeow.views.main import WEATHER_DESCRIPTIONS
        print("✓ App imports successfully")
        print(f"✓ Weather descriptions loaded: {len(WEATHER_DESCRIPTIONS)} items")
        print(f"✓ Sample descriptions: {WEATHER_DESCRIPTIONS[:3]}")
    except Exception as e:
        print(f"❌ Import error: {e}")
    
    print("\n=== Verification Complete ===")

if __name__ == "__main__":
    main()