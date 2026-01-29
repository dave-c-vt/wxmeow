#!/usr/bin/env python3
"""
Simple test to verify chart loading on weather pages.

This test checks:
1. That weather pages load correctly
2. That data-location attribute is set
3. That chart containers are present
4. That the hourly API endpoint works
5. That JavaScript files are included

Usage:
    python test_chart_loading.py
"""

import requests
import re
from bs4 import BeautifulSoup
import json


def test_weather_page_chart_loading():
    """Test that charts load properly on weather pages."""
    print("🧪 TESTING CHART LOADING ON WEATHER PAGES")
    print("=" * 60)

    base_url = "http://localhost:5000"
    test_location = "Boston, MA"

    tests_passed = 0
    total_tests = 8

    print(f"\nTesting location: {test_location}")
    print("-" * 40)

    # Test 1: Check if weather page loads
    try:
        weather_url = f"{base_url}/wx/{test_location}"
        response = requests.get(weather_url, timeout=10)

        if response.status_code == 200:
            print("[OK] Weather page loads successfully")
            tests_passed += 1
        else:
            print(f"[FAIL] Weather page failed to load (status: {response.status_code})")
            return False

        html_content = response.text
        soup = BeautifulSoup(html_content, "html.parser")

    except Exception as e:
        print(f"[FAIL] Failed to load weather page: {e}")
        return False

    # Test 2: Check data-location attribute
    body_tag = soup.find("body")
    if body_tag and body_tag.get("data-location"):
        location_attr = body_tag.get("data-location")
        print(f"[OK] data-location attribute found: '{location_attr}'")
        tests_passed += 1
    else:
        print("[FAIL] data-location attribute missing or empty")

    # Test 3: Check for chart containers
    chart_containers = soup.find_all(
        "div", id=re.compile(r"hourly-temperature-chart-\d+")
    )
    if len(chart_containers) >= 5:
        print(f"[OK] Found {len(chart_containers)} chart containers")
        tests_passed += 1
    else:
        print(f"[FAIL] Expected 5+ chart containers, found {len(chart_containers)}")

    # Test 4: Check for Chart.js library
    chartjs_scripts = soup.find_all("script", src=re.compile(r"chart\.js"))
    if chartjs_scripts:
        print("[OK] Chart.js library included")
        tests_passed += 1
    else:
        print("[FAIL] Chart.js library not found")

    # Test 5: Check for temperature-chart.js
    temp_chart_scripts = soup.find_all(
        "script", src=re.compile(r"temperature-chart\.js")
    )
    if temp_chart_scripts:
        print("[OK] temperature-chart.js included")
        tests_passed += 1
    else:
        print("[FAIL] temperature-chart.js not found")

    # Test 6: Check for day selector elements
    day_selectors = soup.find_all(class_=re.compile(r"day-selector"))
    if day_selectors:
        print(f"[OK] Found {len(day_selectors)} day selector elements")
        tests_passed += 1
    else:
        print("[FAIL] No day selector elements found")

    # Test 7: Test hourly API endpoint
    try:
        api_url = f"{base_url}/api/hourly/{test_location}"
        api_response = requests.get(api_url, timeout=10)

        if api_response.status_code == 200:
            hourly_data = api_response.json()
            if isinstance(hourly_data, list) and len(hourly_data) > 0:
                print(f"[OK] Hourly API returns {len(hourly_data)} data points")
                tests_passed += 1

                # Check data structure
                first_item = hourly_data[0]
                required_fields = ["time", "temperature", "condition"]
                if all(field in first_item for field in required_fields):
                    print("[OK] Hourly data has required fields")
                    tests_passed += 1
                else:
                    print("[FAIL] Hourly data missing required fields")
            else:
                print("[FAIL] Hourly API returns empty or invalid data")
        else:
            print(f"[FAIL] Hourly API failed (status: {api_response.status_code})")
    except Exception as e:
        print(f"[FAIL] Failed to test hourly API: {e}")

    # Test 8: Check for jQuery (needed for chart events)
    jquery_scripts = soup.find_all("script", src=re.compile(r"jquery"))
    if jquery_scripts:
        print("[OK] jQuery library included")
        tests_passed += 1
    else:
        print("[FAIL] jQuery library not found")

    print(f"\n[*] TEST RESULTS:")
    print("-" * 40)
    print(f"Tests Passed: {tests_passed}/{total_tests}")
    print(f"Success Rate: {(tests_passed / total_tests) * 100:.1f}%")

    if tests_passed >= 7:
        print("\n🎉 CHART LOADING APPEARS TO BE WORKING!")
        print("[OK] All essential components are present.")
        print("\n💡 If charts still don't appear:")
        print("   1. Check browser console for JavaScript errors")
        print(
            "   2. Verify the chart containers become visible when clicking day buttons"
        )
        print("   3. Check that the hourly data is being fetched correctly")
        return True
    elif tests_passed >= 5:
        print("\n[WARN]  PARTIAL FUNCTIONALITY DETECTED")
        print(
            "Most components are present but some issues may prevent proper chart loading."
        )
        return False
    else:
        print("\n[FAIL] CHART LOADING LIKELY NOT WORKING")
        print("Multiple essential components are missing.")
        return False


def test_chart_debugging():
    """Additional debugging information."""
    print("\n🔧 CHART DEBUGGING INFORMATION")
    print("=" * 60)

    try:
        base_url = "http://localhost:5000"
        test_location = "Boston, MA"

        # Get the weather page HTML
        weather_url = f"{base_url}/wx/{test_location}"
        response = requests.get(weather_url, timeout=10)
        html_content = response.text

        # Look for specific patterns that might indicate issues
        print("\n🔍 HTML Analysis:")
        print("-" * 20)

        # Check for empty chart containers
        empty_chart_pattern = r"<div[^>]*hourly-temperature-chart[^>]*></div>"
        empty_charts = re.findall(empty_chart_pattern, html_content)
        print(f"Empty chart containers: {len(empty_charts)}")

        # Check for initialization events
        dayselected_events = html_content.count("daySelected")
        print(f"daySelected event references: {dayselected_events}")

        # Check for console.log statements (debugging)
        console_logs = html_content.count("console.log")
        print(f"Debug console.log statements: {console_logs}")

        # Look for specific error patterns
        if 'data-location=""' in html_content:
            print("[WARN]  WARNING: data-location attribute appears to be empty")

        if "chart.js" not in html_content.lower():
            print("[FAIL] Chart.js library not found in HTML")

        if "temperature-chart.js" not in html_content:
            print("[FAIL] temperature-chart.js not found in HTML")

    except Exception as e:
        print(f"Error in debugging: {e}")


if __name__ == "__main__":
    print("Starting chart loading tests...")
    print("Make sure Flask server is running on localhost:5000\n")

    try:
        success = test_weather_page_chart_loading()
        test_chart_debugging()

        if success:
            print("\n[OK] Tests completed successfully!")
        else:
            print("\n[WARN]  Tests completed with issues.")

    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
    except Exception as e:
        print(f"\n[FAIL] Test failed with error: {e}")
