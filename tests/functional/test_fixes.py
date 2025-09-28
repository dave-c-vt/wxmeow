#!/usr/bin/env python3
"""
Test script to validate weather app fixes.

This script tests the three main issues that were reported:
1. Day weather description not changing when selecting different days
2. Plot of hourly temperature forecast not showing up
3. Blank weather icons on small screens

Run this script to test basic functionality of the weather app.
"""

import sys
import os
import re
from pathlib import Path

# Add the wxmeow package to the path
sys.path.insert(0, str(Path(__file__).parent))


def test_day_descriptions():
    """Test that day descriptions are properly generated with unique IDs."""
    print("Testing day weather descriptions...")

    try:
        from wxmeow.wx2json_noaa import wxmeow

        # Test with a known location
        test_location = "Boston"
        weather = wxmeow(test_location)

        # Check if day descriptions with proper IDs are generated
        html_content = weather.futuremeow

        # Look for day-description divs with IDs 0-4
        description_pattern = r'<div id="day-description-(\d)" class="day-description"'
        matches = re.findall(description_pattern, html_content)

        if len(matches) >= 5:
            print("✓ Day descriptions with unique IDs found")
            return True
        else:
            print(f"✗ Only {len(matches)} day descriptions found, expected 5")
            return False

    except Exception as e:
        print(f"✗ Error testing day descriptions: {str(e)}")
        return False


def test_chart_containers():
    """Test that chart containers are properly generated."""
    print("Testing chart containers...")

    try:
        from wxmeow.wx2json_noaa import wxmeow

        # Test with a known location
        test_location = "Boston"
        weather = wxmeow(test_location)

        # Check if chart containers are generated
        html_content = weather.futuremeow

        # Look for hourly chart containers with IDs 0-4
        chart_pattern = r'<div id="hourly-temperature-chart-(\d)" class="hourly-chart"'
        matches = re.findall(chart_pattern, html_content)

        if len(matches) >= 5:
            print("✓ Chart containers found")
            return True
        else:
            print(f"✗ Only {len(matches)} chart containers found, expected 5")
            return False

    except Exception as e:
        print(f"✗ Error testing chart containers: {str(e)}")
        return False


def test_chart_js_loading():
    """Test that Chart.js is properly loaded in the JavaScript."""
    print("Testing Chart.js loading...")

    try:
        from wxmeow.wx2json_noaa import wxmeow

        # Test with a known location
        test_location = "Boston"
        weather = wxmeow(test_location)

        # Check if Chart.js is loaded
        js_content = weather.js

        if "chart.js" in js_content.lower() or "chartjs" in js_content.lower():
            print("✓ Chart.js loading found in JavaScript")
            return True
        else:
            print("✗ Chart.js loading not found in JavaScript")
            return False

    except Exception as e:
        print(f"✗ Error testing Chart.js loading: {str(e)}")
        return False


def test_responsive_css():
    """Test that responsive CSS is present."""
    print("Testing responsive CSS...")

    try:
        # Check if styles.css has responsive rules
        styles_path = Path(__file__).parent / "wxmeow" / "static" / "styles.css"

        if not styles_path.exists():
            print("✗ styles.css file not found")
            return False

        with open(styles_path, "r") as f:
            css_content = f.read()

        # Look for media queries for responsive design
        media_queries = re.findall(r"@media\s*\([^)]+\)", css_content)
        weather_table_class = "weather-forecast-table" in css_content

        if len(media_queries) > 0 and weather_table_class:
            print("✓ Responsive CSS rules found")
            return True
        else:
            print("✗ Responsive CSS rules not found or incomplete")
            return False

    except Exception as e:
        print(f"✗ Error testing responsive CSS: {str(e)}")
        return False


def test_day_selector_onclick():
    """Test that day selectors have proper onclick handlers."""
    print("Testing day selector onclick handlers...")

    try:
        from wxmeow.wx2json_noaa import wxmeow

        # Test with a known location
        test_location = "Boston"
        weather = wxmeow(test_location)

        # Check if day selectors have onclick handlers
        html_content = weather.futuremeow

        # Look for day selectors with onclick handlers that include daySelected trigger
        onclick_pattern = r'onclick="[^"]*dayselected[^"]*"'
        matches = re.findall(onclick_pattern, html_content, re.IGNORECASE)

        if len(matches) >= 5:
            print("✓ Day selector onclick handlers found")
            return True
        else:
            print(f"✗ Only {len(matches)} onclick handlers found, expected 5")
            return False

    except Exception as e:
        print(f"✗ Error testing day selector onclick handlers: {str(e)}")
        return False


def test_weather_icon_css_classes():
    """Test that weather icons have proper CSS classes for responsive design."""
    print("Testing weather icon CSS classes...")

    try:
        from wxmeow.wx2json_noaa import wxmeow

        # Test with a known location
        test_location = "Boston"
        weather = wxmeow(test_location)

        # Check if weather icons have the proper classes
        html_content = weather.futuremeow

        # Look for weather-forecast-table class
        if 'class="weather-forecast-table"' in html_content:
            print("✓ Weather forecast table has responsive CSS class")
            return True
        else:
            print("✗ Weather forecast table missing responsive CSS class")
            return False

    except Exception as e:
        print(f"✗ Error testing weather icon CSS classes: {str(e)}")
        return False


def main():
    """Run all tests and report results."""
    print("=" * 60)
    print("Weather App Fix Validation Tests")
    print("=" * 60)

    tests = [
        test_day_descriptions,
        test_chart_containers,
        test_chart_js_loading,
        test_responsive_css,
        test_day_selector_onclick,
        test_weather_icon_css_classes,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {str(e)}")
            failed += 1
        print()

    print("=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed == 0:
        print("🎉 All tests passed! The weather app fixes should be working.")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
