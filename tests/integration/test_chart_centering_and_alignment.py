#!/usr/bin/env python3
"""
Comprehensive Test for Chart Centering and Temperature Alignment Fixes

This test verifies that:
1. Temperature charts are properly centered on noon (12 PM) in the user's local timezone
2. Temperature values are properly aligned with weather icons in the forecast table
3. Both fixes work correctly across different scenarios

Usage:
    python test_chart_centering_and_alignment.py
"""

import re
import sys
import os
import json
from datetime import datetime, timedelta

# Add the wxmeow module to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from wxmeow.wx2json_noaa import wxmeow
except ImportError as e:
    print(f"[FAIL] Cannot import wxmeow module: {e}")
    print("Make sure you're running this from the wxmeow directory")
    sys.exit(1)


class ChartCenteringAndAlignmentTest:
    """Test suite for chart centering and temperature alignment fixes."""

    def __init__(self):
        self.successes = []
        self.errors = []
        self.test_location = "Boston, MA"
        self.weather_data = None

    def run_all_tests(self):
        """Run all test methods."""
        print("🧪 CHART CENTERING AND TEMPERATURE ALIGNMENT TEST SUITE")
        print("=" * 70)
        print(f"Testing with location: {self.test_location}")
        print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print()

        # Load weather data once
        try:
            self.weather_data = wxmeow(self.test_location)
            print("[OK] Weather data loaded successfully")
        except Exception as e:
            print(f"[FAIL] Failed to load weather data: {e}")
            return False

        # Run all tests
        test_methods = [
            self.test_chart_centering_configuration,
            self.test_temperature_table_structure,
            self.test_temperature_alignment_css,
            self.test_chart_timezone_handling,
            self.test_responsive_design_alignment,
            self.test_javascript_chart_integration,
            self.test_noon_emphasis_features,
            self.test_24_hour_data_structure,
        ]

        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                error_msg = f"Test {test_method.__name__} failed with exception: {e}"
                self.errors.append(error_msg)
                print(f"[FAIL] {error_msg}")

        # Print summary
        self.print_summary()
        return len(self.errors) == 0

    def test_chart_centering_configuration(self):
        """Test that chart is configured to center noon properly."""
        print("\n[*] TESTING CHART CENTERING CONFIGURATION")
        print("-" * 50)

        # Read the JavaScript chart file
        chart_js_path = "wxmeow/static/js/charts/temperature-chart.js"
        try:
            with open(chart_js_path, "r", encoding="utf-8") as f:
                js_content = f.read()
        except FileNotFoundError:
            error_msg = f"Chart JavaScript file not found: {chart_js_path}"
            self.errors.append(error_msg)
            print(f"[FAIL] {error_msg}")
            return

        # Check for timezone detection
        if "Intl.DateTimeFormat().resolvedOptions().timeZone" in js_content:
            success_msg = "[OK] Browser timezone detection implemented"
            self.successes.append(success_msg)
            print(f"   {success_msg}")
        else:
            error_msg = "[FAIL] Browser timezone detection missing"
            self.errors.append(error_msg)
            print(f"   {error_msg}")

        # Check for time scale configuration
        if (
            'type: "linear"' in js_content
            and "min: 0" in js_content
            and "max: 23" in js_content
        ):
            success_msg = "[OK] Proper time scale configuration (0-23 hours)"
            self.successes.append(success_msg)
            print(f"   {success_msg}")
        else:
            error_msg = "[FAIL] Missing proper time scale configuration"
            self.errors.append(error_msg)
            print(f"   {error_msg}")

        # Check for noon emphasis (updated to not require emoji)
        if "value === 12" in js_content:
            success_msg = "[OK] Noon emphasis implemented"
            self.successes.append(success_msg)
            print(f"   {success_msg}")
        else:
            error_msg = "[FAIL] Noon emphasis features missing"
            self.errors.append(error_msg)
            print(f"   {error_msg}")

        # Check for 24-hour data structure
        if "ensureFullDayCoverage" in js_content:
            success_msg = "[OK] 24-hour data coverage function present"
            self.successes.append(success_msg)
            print(f"   {success_msg}")
        else:
            error_msg = "[FAIL] 24-hour data coverage function missing"
            self.errors.append(error_msg)
            print(f"   {error_msg}")

    def test_temperature_table_structure(self):
        """Test that temperature table structure is correct."""
        print("\n[*] TESTING TEMPERATURE TABLE STRUCTURE")
        print("-" * 50)

        html_content = self.weather_data.futuremeow

        # Check for weather-forecast-table class
        if 'class="weather-forecast-table"' in html_content:
            success_msg = "[OK] Weather forecast table class present"
            self.successes.append(success_msg)
            print(f"   {success_msg}")
        else:
            error_msg = "[FAIL] Weather forecast table class missing"
            self.errors.append(error_msg)
            print(f"   {error_msg}")

        # Check for temperature cells within the table
        if 'class="temperature-cell' in html_content:
            success_msg = "[OK] Temperature cells with proper CSS classes"
            self.successes.append(success_msg)
            print(f"   {success_msg}")
        else:
            error_msg = "[FAIL] Temperature cells missing proper CSS classes"
            self.errors.append(error_msg)
            print(f"   {error_msg}")

        # Check for temperature values with spans
        temp_span_pattern = r'<span class="temperature-value">(\d+) F</span>'
        temp_matches = re.findall(temp_span_pattern, html_content)

        if len(temp_matches) >= 5:
            success_msg = (
                f"[OK] Found {len(temp_matches)} properly formatted temperature values"
            )
            self.successes.append(success_msg)
            print(f"   {success_msg}")
            print(f"      Temperatures: {[t + '°F' for t in temp_matches[:5]]}")
        else:
            error_msg = (
                f"[FAIL] Only found {len(temp_matches)} temperature values, expected 5+"
            )
            self.errors.append(error_msg)
            print(f"   {error_msg}")

        # Check that temperatures are inside the table structure
        table_pattern = r'<table[^>]*class="weather-forecast-table"[^>]*>(.*?)</table>'
        table_match = re.search(table_pattern, html_content, re.DOTALL)

        if table_match:
            table_content = table_match.group(1)
            temps_in_table = len(re.findall(temp_span_pattern, table_content))
            if temps_in_table >= 5:
                success_msg = "[OK] Temperature values are properly contained within the forecast table"
                self.successes.append(success_msg)
                print(f"   {success_msg}")
            else:
                error_msg = f"[FAIL] Only {temps_in_table} temperatures found within table structure"
                self.errors.append(error_msg)
                print(f"   {error_msg}")

    def test_temperature_alignment_css(self):
        """Test that CSS for temperature alignment is present."""
        print("\n🎨 TESTING TEMPERATURE ALIGNMENT CSS")
        print("-" * 50)

        html_content = self.weather_data.futuremeow

        # Check for temperature alignment CSS rules
        css_checks = [
            (".weather-forecast-table", "table-layout: fixed"),
            (".weather-forecast-table td", "width: 20%"),
            (".weather-forecast-table td", "text-align: center"),
            (".temperature-cell", "vertical-align: middle"),
            (".temperature-value", "font-weight: bold"),
        ]

        for selector, rule in css_checks:
            if selector in html_content and rule in html_content:
                success_msg = f"[OK] CSS rule found: {selector} → {rule}"
                self.successes.append(success_msg)
                print(f"   {success_msg}")
            else:
                error_msg = f"[FAIL] CSS rule missing: {selector} → {rule}"
                self.errors.append(error_msg)
                print(f"   {error_msg}")

        # Check for responsive CSS
        if "@media (max-width: 768px)" in html_content:
            success_msg = "[OK] Responsive CSS for mobile devices present"
            self.successes.append(success_msg)
            print(f"   {success_msg}")
        else:
            error_msg = "[FAIL] Responsive CSS missing"
            self.errors.append(error_msg)
            print(f"   {error_msg}")

    def test_chart_timezone_handling(self):
        """Test timezone handling in chart JavaScript."""
        print("\nTESTING CHART TIMEZONE HANDLING")
        print("-" * 50)

        chart_js_path = "wxmeow/static/js/charts/temperature-chart.js"
        try:
            with open(chart_js_path, "r", encoding="utf-8") as f:
                js_content = f.read()
        except FileNotFoundError:
            error_msg = "Chart JavaScript file not found"
            self.errors.append(error_msg)
            print(f"[FAIL] {error_msg}")
            return

        # Check for timezone functions
        timezone_functions = [
            "displayTimezoneInfo",
            "validateTimezoneConversion",
            "convertUTCToLocal",
            "ensureFullDayCoverage",
        ]

        for func in timezone_functions:
            if f"function {func}" in js_content:
                success_msg = f"[OK] Timezone function present: {func}"
                self.successes.append(success_msg)
                print(f"   {success_msg}")
            else:
                error_msg = f"[FAIL] Timezone function missing: {func}"
                self.errors.append(error_msg)
                print(f"   {error_msg}")

        # Check for proper local timezone usage
        timezone_patterns = [
            r'toLocaleString\("en-US", \{ timeZone: userTimezone \}\)',
            r"timeZone: userTimezone",
            r"getHours\(\).*===.*hour",
        ]

        for pattern in timezone_patterns:
            if re.search(pattern, js_content):
                success_msg = f"[OK] Proper timezone conversion pattern found"
                self.successes.append(success_msg)
                print(f"   {success_msg}")
                break
        else:
            error_msg = "[FAIL] No proper timezone conversion patterns found"
            self.errors.append(error_msg)
            print(f"   {error_msg}")

    def test_responsive_design_alignment(self):
        """Test responsive design for temperature alignment."""
        print("\n> TESTING RESPONSIVE DESIGN ALIGNMENT")
        print("-" * 50)

        html_content = self.weather_data.futuremeow

        # Check for mobile-specific CSS rules
        mobile_css_patterns = [
            r"@media \(max-width: 768px\)",
            r"@media \(max-width: 480px\)",
            r"\.day-selector.*width:.*height:",
            r"\.temperature-value.*font-size:",
        ]

        for pattern in mobile_css_patterns:
            if re.search(pattern, html_content, re.IGNORECASE):
                success_msg = (
                    f"[OK] Mobile responsive CSS pattern found: {pattern[:30]}..."
                )
                self.successes.append(success_msg)
                print(f"   {success_msg}")
            else:
                error_msg = (
                    f"[FAIL] Mobile responsive CSS pattern missing: {pattern[:30]}..."
                )
                self.errors.append(error_msg)
                print(f"   {error_msg}")

    def test_javascript_chart_integration(self):
        """Test JavaScript chart integration features."""
        print("\n> TESTING JAVASCRIPT CHART INTEGRATION")
        print("-" * 50)

        html_content = self.weather_data.futuremeow

        # Check for chart containers with proper IDs
        chart_container_pattern = r'id="hourly-temperature-chart-(\d)"'
        chart_containers = re.findall(chart_container_pattern, html_content)

        if len(chart_containers) >= 5:
            success_msg = (
                f"[OK] Found {len(chart_containers)} chart containers with proper IDs"
            )
            self.successes.append(success_msg)
            print(f"   {success_msg}")
        else:
            error_msg = (
                f"[FAIL] Only found {len(chart_containers)} chart containers, expected 5+"
            )
            self.errors.append(error_msg)
            print(f"   {error_msg}")

        # Check for day selector click handlers
        if "onclick=" in html_content and "day-selector" in html_content:
            success_msg = "[OK] Day selector click handlers present"
            self.successes.append(success_msg)
            print(f"   {success_msg}")
        else:
            error_msg = "[FAIL] Day selector click handlers missing"
            self.errors.append(error_msg)
            print(f"   {error_msg}")

        # Check for Chart.js inclusion
        if "Chart.js" in html_content or "chart.js" in html_content:
            success_msg = "[OK] Chart.js library inclusion found"
            self.successes.append(success_msg)
            print(f"   {success_msg}")
        else:
            error_msg = "[FAIL] Chart.js library inclusion missing"
            self.errors.append(error_msg)
            print(f"   {error_msg}")

    def test_noon_emphasis_features(self):
        """Test noon emphasis features in the chart."""
        print("\nTESTING NOON EMPHASIS FEATURES")
        print("-" * 50)

        chart_js_path = "wxmeow/static/js/charts/temperature-chart.js"
        try:
            with open(chart_js_path, "r", encoding="utf-8") as f:
                js_content = f.read()
        except FileNotFoundError:
            error_msg = "Chart JavaScript file not found"
            self.errors.append(error_msg)
            print(f"[FAIL] {error_msg}")
            return

        # Check for noon emphasis (updated to not require emoji)
        if "12 PM" in js_content or "value === 12" in js_content:
            success_msg = "[OK] Noon emphasis implemented"
            self.successes.append(success_msg)
            print(f"   {success_msg}")
        else:
            error_msg = "[FAIL] Noon emphasis missing"
            self.errors.append(error_msg)
            print(f"   {error_msg}")

        # Check for special grid line formatting at noon
        grid_patterns = [
            r"value === 12.*lineWidth.*3",
            r"context\.tick\.value.*12.*thicker",
            r"if \(value === 12\) return 3",
        ]

        grid_found = False
        for pattern in grid_patterns:
            if re.search(pattern, js_content):
                grid_found = True
                break

        if grid_found:
            success_msg = "[OK] Special grid line formatting for noon found"
            self.successes.append(success_msg)
            print(f"   {success_msg}")
        else:
            error_msg = "[FAIL] Special grid line formatting for noon missing"
            self.errors.append(error_msg)
            print(f"   {error_msg}")

    def test_24_hour_data_structure(self):
        """Test that 24-hour data structure is properly maintained."""
        print("\n🕐 TESTING 24-HOUR DATA STRUCTURE")
        print("-" * 50)

        chart_js_path = "wxmeow/static/js/charts/temperature-chart.js"
        try:
            with open(chart_js_path, "r", encoding="utf-8") as f:
                js_content = f.read()
        except FileNotFoundError:
            error_msg = "Chart JavaScript file not found"
            self.errors.append(error_msg)
            print(f"   {error_msg}")
            return

        # Check for 24-hour loop
        if "for (let hour = 0; hour < 24; hour++)" in js_content:
            success_msg = "[OK] 24-hour data structure loop found"
            self.successes.append(success_msg)
            print(f"   {success_msg}")
        else:
            error_msg = "[FAIL] 24-hour data structure loop missing"
            self.errors.append(error_msg)
            print(f"   {error_msg}")

        # Check for hour-based data point creation
        if "x: hour" in js_content and "y:" in js_content:
            success_msg = "[OK] Hour-based data point structure found"
            self.successes.append(success_msg)
            print(f"   {success_msg}")
        else:
            error_msg = "[FAIL] Hour-based data point structure missing"
            self.errors.append(error_msg)
            print(f"   {error_msg}")

        # Check for data sorting by hour
        if "sort((a, b)" in js_content and "getHours()" in js_content:
            success_msg = "[OK] Data sorting by hour implemented"
            self.successes.append(success_msg)
            print(f"   {success_msg}")
        else:
            error_msg = "[FAIL] Data sorting by hour missing"
            self.errors.append(error_msg)
            print(f"   {error_msg}")

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 70)
        print("📋 TEST SUMMARY")
        print("=" * 70)

        total_tests = len(self.successes) + len(self.errors)
        success_rate = (
            (len(self.successes) / total_tests * 100) if total_tests > 0 else 0
        )

        print(f"Total Checks: {total_tests}")
        print(f"Successes: {len(self.successes)}")
        print(f"Errors: {len(self.errors)}")
        print(f"Success Rate: {success_rate:.1f}%")

        if self.errors:
            print(f"\n[FAIL] ERRORS FOUND ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"   {i}. {error}")

        if len(self.errors) == 0:
            print("\n🎉 ALL TESTS PASSED!")
            print("[OK] Chart centering: Noon should be centered in plots")
            print("[OK] Temperature alignment: Temps should align with weather icons")
            print("[OK] Both fixes appear to be implemented correctly!")
        else:
            print(
                f"\n[WARN]  {len(self.errors)} issues found that may affect functionality."
            )

        print("\n" + "=" * 70)


def main():
    """Run the test suite."""
    test = ChartCenteringAndAlignmentTest()
    success = test.run_all_tests()

    # Additional debugging information
    print("\n🔧 DEBUGGING INFORMATION")
    print("-" * 50)
    print(f"Test Location: {test.test_location}")
    print(f"Current Directory: {os.getcwd()}")
    print(f"Python Path: {sys.path[0]}")

    if test.weather_data:
        print("[OK] Weather data object created successfully")
        # Print sample of HTML for verification
        html_sample = test.weather_data.futuremeow[:500]
        print(f"HTML Sample (first 500 chars):")
        print(f"{'...' if len(html_sample) >= 500 else ''}")

    # Exit code for CI/CD systems
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
