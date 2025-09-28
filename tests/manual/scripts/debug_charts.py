#!/usr/bin/env python3
"""
Minimal debug script to test chart functionality step by step.
This will help identify where the chart system is breaking.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))


def test_basic_weather():
    """Test basic weather object creation"""
    print("🔧 TESTING BASIC WEATHER OBJECT")
    print("-" * 40)

    try:
        from wxmeow.wx2json_noaa import wxmeow

        w = wxmeow("Boston, MA")

        print(f"✅ Weather object created: {type(w)}")
        print(f"✅ Has meowhourly: {hasattr(w, 'meowhourly')}")

        if hasattr(w, "meowhourly"):
            hourly_len = len(w.meowhourly) if w.meowhourly else 0
            print(f"✅ Hourly data points: {hourly_len}")

            if hourly_len > 0:
                sample = w.meowhourly[0]
                print(f"✅ Sample data keys: {list(sample.keys())}")
                print(f"✅ Sample time: {sample.get('time', 'N/A')}")
                print(f"✅ Sample temp: {sample.get('temperature', 'N/A')}°F")
                return w

        return w

    except Exception as e:
        print(f"❌ Error creating weather object: {e}")
        import traceback

        print(traceback.format_exc())
        return None


def test_html_output(weather_obj):
    """Test HTML output generation"""
    print("\n🔧 TESTING HTML OUTPUT")
    print("-" * 40)

    if not weather_obj:
        print("❌ No weather object to test")
        return False

    try:
        html = weather_obj.futuremeow
        print(f"✅ HTML generated: {len(html)} characters")

        # Check for key elements
        chart_containers = html.count("hourly-temperature-chart")
        print(f"✅ Chart containers found: {chart_containers}")

        has_chartjs = "chart.js" in html.lower()
        print(f"✅ Chart.js included: {has_chartjs}")

        has_temp_script = "temperature-chart.js" in html
        print(f"✅ Temperature chart script: {has_temp_script}")

        # Look for temperature values
        import re

        temps = re.findall(r"(\d+)\s*F", html)
        print(
            f"✅ Temperature values found: {len(temps)} ({temps[:5] if temps else 'none'})"
        )

        return True

    except Exception as e:
        print(f"❌ Error generating HTML: {e}")
        import traceback

        print(traceback.format_exc())
        return False


def test_api_endpoint():
    """Test API endpoint functionality"""
    print("\n🔧 TESTING API ENDPOINT")
    print("-" * 40)

    try:
        from wxmeow import create_app

        app = create_app()

        with app.test_client() as client:
            response = client.get("/api/hourly/Boston,%20MA")
            print(f"✅ API status code: {response.status_code}")

            if response.status_code == 200:
                import json

                data = json.loads(response.data)
                print(f"✅ API data points: {len(data)}")

                if data and len(data) > 0:
                    sample = data[0]
                    print(f"✅ API sample time: {sample.get('time', 'N/A')}")
                    print(f"✅ API sample temp: {sample.get('temperature', 'N/A')}°F")
                    print(f"✅ API sample condition: {sample.get('condition', 'N/A')}")
                    return True
                else:
                    print("❌ API returned empty data")
                    return False
            else:
                print(f"❌ API error: {response.status_code}")
                print(f"Response: {response.data}")
                return False

    except Exception as e:
        print(f"❌ Error testing API: {e}")
        import traceback

        print(traceback.format_exc())
        return False


def test_javascript_file():
    """Test JavaScript file exists and is readable"""
    print("\n🔧 TESTING JAVASCRIPT FILE")
    print("-" * 40)

    js_paths = [
        "static/js/charts/temperature-chart.js",
        "wxmeow/static/js/charts/temperature-chart.js",
    ]

    for path in js_paths:
        try:
            if os.path.exists(path):
                with open(path, "r") as f:
                    content = f.read()
                    print(f"✅ Found JS file: {path} ({len(content)} chars)")

                    # Check for key functions
                    has_create_chart = "createTemperatureChart" in content
                    has_dom_ready = "DOMContentLoaded" in content
                    has_fetch = "fetch(" in content

                    print(f"   - createTemperatureChart: {has_create_chart}")
                    print(f"   - DOMContentLoaded: {has_dom_ready}")
                    print(f"   - fetch function: {has_fetch}")

                    return True
            else:
                print(f"❌ JS file not found: {path}")

        except Exception as e:
            print(f"❌ Error reading JS file {path}: {e}")

    return False


def main():
    """Run all debug tests"""
    print("🧪 CHART DEBUG SCRIPT")
    print("=" * 50)
    print("This script tests each component of the chart system")
    print("to identify where the issue is occurring.")
    print("=" * 50)

    # Test 1: Basic weather object
    weather_obj = test_basic_weather()

    # Test 2: HTML output
    html_ok = test_html_output(weather_obj)

    # Test 3: API endpoint
    api_ok = test_api_endpoint()

    # Test 4: JavaScript file
    js_ok = test_javascript_file()

    # Summary
    print("\n📋 DEBUG SUMMARY")
    print("=" * 50)
    print(f"Weather Object: {'✅' if weather_obj else '❌'}")
    print(f"HTML Output: {'✅' if html_ok else '❌'}")
    print(f"API Endpoint: {'✅' if api_ok else '❌'}")
    print(f"JavaScript File: {'✅' if js_ok else '❌'}")

    if all([weather_obj, html_ok, api_ok, js_ok]):
        print("\n🎉 ALL COMPONENTS WORKING!")
        print("The chart should display properly.")
        print("If it's still not working, check browser console for errors.")
    else:
        print("\n⚠️ ISSUES FOUND!")
        print("Fix the failing components above.")

    print("\n💡 NEXT STEPS:")
    print("1. Open the weather app in a browser")
    print("2. Open browser developer tools (F12)")
    print("3. Check the Console tab for JavaScript errors")
    print("4. Check the Network tab to see if files are loading")


if __name__ == "__main__":
    main()
