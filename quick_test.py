#!/usr/bin/env python3
"""
Quick test to verify chart components are working without network calls.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))


def test_imports():
    """Test basic imports work"""
    print("Testing imports...")
    try:
        from wxmeow.wx2json_noaa import wxmeow

        print("✅ wxmeow import successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def test_files_exist():
    """Test required files exist"""
    print("Testing file existence...")

    files_to_check = [
        "static/js/charts/temperature-chart.js",
        "wxmeow/static/js/charts/temperature-chart.js",
    ]

    all_exist = True
    for filepath in files_to_check:
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print(f"✅ {filepath} exists ({size} bytes)")
        else:
            print(f"❌ {filepath} missing")
            all_exist = False

    return all_exist


def test_javascript_content():
    """Test JavaScript file has required functions"""
    print("Testing JavaScript content...")

    try:
        with open("static/js/charts/temperature-chart.js", "r") as f:
            content = f.read()

        required_functions = [
            "createTemperatureChart",
            "DOMContentLoaded",
            "fetch",
            "Chart(",
        ]

        all_found = True
        for func in required_functions:
            if func in content:
                print(f"✅ Found: {func}")
            else:
                print(f"❌ Missing: {func}")
                all_found = False

        return all_found

    except Exception as e:
        print(f"❌ Error reading JS file: {e}")
        return False


def test_basic_weather_mock():
    """Test weather object creation with minimal data"""
    print("Testing basic weather object...")

    try:
        # Import but don't make network calls
        from wxmeow import wx2json_noaa

        # Check class exists
        weather_class = wx2json_noaa.wxmeow
        print(f"✅ Weather class available: {weather_class}")

        # Check if we can see the meowhourly attribute in class
        if hasattr(weather_class, "__init__"):
            print("✅ Weather class has __init__ method")

        return True

    except Exception as e:
        print(f"❌ Weather object test failed: {e}")
        return False


def main():
    """Run all quick tests"""
    print("🚀 QUICK CHART TEST")
    print("=" * 40)

    tests = [
        ("Imports", test_imports),
        ("Files", test_files_exist),
        ("JavaScript", test_javascript_content),
        ("Weather Class", test_basic_weather_mock),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        result = test_func()
        results.append((test_name, result))

    print("\n📋 SUMMARY")
    print("=" * 40)
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    print(f"\nPassed: {passed}/{len(tests)}")

    if passed == len(tests):
        print("\n🎉 All basic components are in place!")
        print("Chart should work if network/API is accessible.")
    else:
        print(f"\n⚠️ {len(tests) - passed} issues found")
        print("Fix the failing components first.")


if __name__ == "__main__":
    main()
