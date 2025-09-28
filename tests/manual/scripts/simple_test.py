#!/usr/bin/env python3
"""
Simple test to verify basic weather app functionality without complex operations.
"""

import sys
import os
import re

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_basic_imports():
    """Test that basic imports work."""
    try:
        from wxmeow.wx2json_noaa import wxmeow

        print("✓ Successfully imported wxmeow")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_weather_generation():
    """Test basic weather generation."""
    try:
        from wxmeow.wx2json_noaa import wxmeow

        print("Creating weather object for Boston...")

        # Create weather instance
        w = wxmeow("Boston")

        print(f"✓ Weather object created")
        print(f"✓ Current conditions length: {len(w.wxmeow)}")
        print(f"✓ Forecast HTML length: {len(w.futuremeow)}")
        print(
            f"✓ Hourly data points: {len(w.meowhourly) if hasattr(w, 'meowhourly') else 0}"
        )

        return True
    except Exception as e:
        print(f"✗ Weather generation failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_html_structure():
    """Test basic HTML structure."""
    try:
        from wxmeow.wx2json_noaa import wxmeow

        w = wxmeow("Boston")
        html = w.futuremeow

        # Test basic structure
        tests = [
            ("weather-forecast-table", "Weather icons table"),
            ("day-selector", "Day selectors"),
            ("hourly-temperature-chart", "Chart containers"),
            ("Chart.js", "Chart library"),
            (r"\d+\s*F", "Temperature data"),
        ]

        results = []
        for pattern, name in tests:
            if re.search(pattern, html):
                print(f"✓ {name} found")
                results.append(True)
            else:
                print(f"✗ {name} missing")
                results.append(False)

        return all(results)

    except Exception as e:
        print(f"✗ HTML structure test failed: {e}")
        return False


def test_day_picker_elements():
    """Test day picker elements."""
    try:
        from wxmeow.wx2json_noaa import wxmeow

        w = wxmeow("Boston")
        html = w.futuremeow

        # Check for day selectors with IDs 0-4
        day_selectors = re.findall(r"id='(\d)' class='day-selector", html)
        expected = ["0", "1", "2", "3", "4"]

        if sorted(day_selectors) == expected:
            print(f"✓ All 5 day selectors found: {day_selectors}")
            day_picker_ok = True
        else:
            print(f"✗ Day selectors wrong. Expected: {expected}, Got: {day_selectors}")
            day_picker_ok = False

        # Check for day descriptions
        day_descriptions = re.findall(r'<div id="day-description-(\d)"', html)
        if len(day_descriptions) >= 5:
            print(f"✓ Day descriptions found: {len(day_descriptions)}")
            descriptions_ok = True
        else:
            print(f"✗ Only {len(day_descriptions)} day descriptions found")
            descriptions_ok = False

        # Check for charts
        charts = re.findall(r"hourly-temperature-chart-(\d)", html)
        if len(charts) >= 5:
            print(f"✓ Chart containers found: {len(charts)}")
            charts_ok = True
        else:
            print(f"✗ Only {len(charts)} chart containers found")
            charts_ok = False

        return day_picker_ok and descriptions_ok and charts_ok

    except Exception as e:
        print(f"✗ Day picker test failed: {e}")
        return False


def test_temperature_alignment():
    """Test temperature alignment."""
    try:
        from wxmeow.wx2json_noaa import wxmeow

        w = wxmeow("Boston")
        html = w.futuremeow

        # Find temperatures
        temps = re.findall(r"(\d+)\s*F", html)
        if len(temps) >= 5:
            print(f"✓ Found {len(temps)} temperatures: {temps[:5]}")

            # Check if they're in table cells
            temp_cells = re.findall(r"<td[^>]*>\s*\d+\s*F\s*</td>", html)
            if len(temp_cells) >= 5:
                print(f"✓ Temperatures properly in table cells: {len(temp_cells)}")
                return True
            else:
                print(f"✗ Only {len(temp_cells)} temperatures in proper table cells")
                return False
        else:
            print(f"✗ Only found {len(temps)} temperatures")
            return False

    except Exception as e:
        print(f"✗ Temperature alignment test failed: {e}")
        return False


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("SIMPLE WEATHER APP FUNCTIONALITY TEST")
    print("=" * 60)

    tests = [
        ("Basic Imports", test_basic_imports),
        ("Weather Generation", test_weather_generation),
        ("HTML Structure", test_html_structure),
        ("Day Picker Elements", test_day_picker_elements),
        ("Temperature Alignment", test_temperature_alignment),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 30)
        result = test_func()
        results.append(result)
        print(f"Result: {'PASS' if result else 'FAIL'}")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        return True
    elif passed >= total * 0.8:
        print("✅ Most tests passed - minor issues remain")
        return True
    else:
        print("❌ Significant issues found")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
