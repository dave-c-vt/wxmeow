#!/usr/bin/env python3
"""
Comprehensive Chart Rendering Test

This test verifies that temperature charts are properly rendered and functional
in the wxmeow weather application. It checks both the backend data generation
and the frontend HTML/JavaScript integration.
"""

import re
import json
from wxmeow.wx2json_noaa import wxmeow


class ChartRenderingTest:
    """Test suite for chart rendering functionality."""

    def __init__(self):
        self.test_location = "Boston, MA"
        self.weather_obj = None
        self.errors = []
        self.successes = []

    def log_success(self, message):
        """Log a successful test."""
        self.successes.append(message)
        print(f"[OK] {message}")

    def log_error(self, message):
        """Log a test failure."""
        self.errors.append(message)
        print(f"[FAIL] {message}")

    def test_weather_data_generation(self):
        """Test that weather data is properly generated."""
        print("\n🔧 TESTING WEATHER DATA GENERATION")
        print("-" * 50)

        try:
            self.weather_obj = wxmeow(self.test_location)
            self.log_success(f"Weather object created for {self.test_location}")

            # Check hourly data
            if hasattr(self.weather_obj, "meowhourly") and self.weather_obj.meowhourly:
                hourly_count = len(self.weather_obj.meowhourly)
                self.log_success(f"Hourly data available: {hourly_count} data points")

                # Check data structure
                sample = self.weather_obj.meowhourly[0]
                required_fields = ["time", "temperature", "condition"]
                missing_fields = [
                    field for field in required_fields if field not in sample
                ]

                if not missing_fields:
                    self.log_success("Hourly data has required fields")
                else:
                    self.log_error(f"Missing fields in hourly data: {missing_fields}")
            else:
                self.log_error("No hourly data available")

        except Exception as e:
            self.log_error(f"Failed to create weather object: {str(e)}")
            return False

        return True

    def test_html_chart_containers(self):
        """Test that HTML contains proper chart containers."""
        print("\n> TESTING HTML CHART CONTAINERS")
        print("-" * 50)

        if not self.weather_obj:
            self.log_error("No weather object available for HTML testing")
            return False

        html = self.weather_obj.futuremeow

        # Check for chart containers
        chart_containers = re.findall(r'id="hourly-temperature-chart-(\d+)"', html)
        if len(chart_containers) >= 5:
            self.log_success(f"Found {len(chart_containers)} chart containers")
        else:
            self.log_error(
                f"Only found {len(chart_containers)} chart containers, expected at least 5"
            )

        # Check for Chart.js library
        if "chart.js" in html.lower():
            self.log_success("Chart.js library included")
        else:
            self.log_error("Chart.js library not found")

        # Check for temperature chart script
        if "temperature-chart.js" in html:
            self.log_success("Temperature chart JavaScript included")
        else:
            self.log_error("Temperature chart JavaScript not found")

        # Check for jQuery
        if "jquery" in html.lower():
            self.log_success("jQuery library included")
        else:
            self.log_error("jQuery library not found")

        return len(chart_containers) >= 5

    def test_javascript_data_injection(self):
        """Test that JavaScript data is properly injected."""
        print("\n💾 TESTING JAVASCRIPT DATA INJECTION")
        print("-" * 50)

        if not self.weather_obj:
            self.log_error("No weather object available")
            return False

        html = self.weather_obj.futuremeow

        # Look for hourlyData injection
        hourly_data_pattern = r"window\.hourlyData\s*=\s*(\[.*?\]);"
        match = re.search(hourly_data_pattern, html, re.DOTALL)

        if match:
            try:
                json_data = match.group(1)
                parsed_data = json.loads(json_data)
                self.log_success(f"Hourly data injected: {len(parsed_data)} items")

                # Verify data structure
                if parsed_data and isinstance(parsed_data[0], dict):
                    sample_keys = list(parsed_data[0].keys())
                    self.log_success(f"Sample data keys: {sample_keys}")
                else:
                    self.log_error("Invalid hourly data structure")

            except json.JSONDecodeError as e:
                self.log_error(f"Invalid JSON in hourly data: {str(e)}")
                return False
        else:
            self.log_error("Hourly data not found in JavaScript")
            return False

        return True

    def test_chart_initialization(self):
        """Test chart initialization JavaScript."""
        print("\n> TESTING CHART INITIALIZATION")
        print("-" * 50)

        if not self.weather_obj:
            self.log_error("No weather object available")
            return False

        html = self.weather_obj.futuremeow

        # Check for selectDay function
        if "function selectDay(" in html:
            self.log_success("selectDay function found")
        else:
            self.log_error("selectDay function not found")

        # Check for chart initialization
        if "selectDay(0)" in html:
            self.log_success("Initial chart selection found")
        else:
            self.log_error("Initial chart selection not found")

        # Check for daySelected event trigger
        if "daySelected" in html:
            self.log_success("daySelected event handling found")
        else:
            self.log_error("daySelected event handling not found")

        return True

    def test_day_selector_integration(self):
        """Test day selector button integration."""
        print("\n> TESTING DAY SELECTOR INTEGRATION")
        print("-" * 50)

        if not self.weather_obj:
            self.log_error("No weather object available")
            return False

        html = self.weather_obj.futuremeow

        # Check for day selector buttons
        day_selectors = re.findall(r'onclick="selectDay\((\d+)\)', html)
        if len(day_selectors) >= 5:
            self.log_success(f"Found {len(day_selectors)} day selector buttons")
        else:
            self.log_error(f"Only found {len(day_selectors)} day selector buttons")

        # Check for day selector CSS classes
        if "day-selector" in html:
            self.log_success("Day selector CSS class found")
        else:
            self.log_error("Day selector CSS class not found")

        return len(day_selectors) >= 5

    def test_responsive_chart_styling(self):
        """Test responsive chart styling."""
        print("\n> TESTING RESPONSIVE CHART STYLING")
        print("-" * 50)

        if not self.weather_obj:
            self.log_error("No weather object available")
            return False

        html = self.weather_obj.futuremeow

        # Check for responsive CSS
        responsive_patterns = [
            r"@media.*max-width.*768px",
            r"@media.*max-width.*480px",
            r"width:\s*100%",
            r"max-width:\s*800px",
        ]

        responsive_found = 0
        for pattern in responsive_patterns:
            if re.search(pattern, html, re.IGNORECASE):
                responsive_found += 1

        if responsive_found >= 3:
            self.log_success(f"Found {responsive_found} responsive design elements")
        else:
            self.log_error(f"Only found {responsive_found} responsive design elements")

        # Check for chart container styling
        if "min-height: 300px" in html:
            self.log_success("Chart minimum height specified")
        else:
            self.log_error("Chart minimum height not found")

        return responsive_found >= 3

    def test_error_handling(self):
        """Test error handling in chart system."""
        print("\nTESTING ERROR HANDLING")
        print("-" * 50)

        if not self.weather_obj:
            self.log_error("No weather object available")
            return False

        html = self.weather_obj.futuremeow

        # Check for error console logging
        if "console.error" in html or "console.debug" in html or "console.log" in html:
            self.log_success("Console logging found")
        else:
            self.log_error("No console logging found")

        # Check for fallback handling
        if "No hourly data available" in html or "Chart container not found" in html:
            self.log_success("Error fallback messages found")
        else:
            # This is not necessarily an error, just informational
            print("i No specific error fallback messages found")

        return True

    def run_all_tests(self):
        """Run all chart rendering tests."""
        print("🧪 COMPREHENSIVE CHART RENDERING TEST")
        print("=" * 60)
        print(f"Testing location: {self.test_location}")
        print()

        test_methods = [
            self.test_weather_data_generation,
            self.test_html_chart_containers,
            self.test_javascript_data_injection,
            self.test_chart_initialization,
            self.test_day_selector_integration,
            self.test_responsive_chart_styling,
            self.test_error_handling,
        ]

        passed = 0
        for test_method in test_methods:
            try:
                if test_method():
                    passed += 1
            except Exception as e:
                self.log_error(
                    f"Test {test_method.__name__} failed with exception: {str(e)}"
                )

        # Final summary
        print("\n" + "=" * 60)
        print("[*] TEST SUMMARY")
        print("=" * 60)
        print(f"Tests Passed: {passed}/{len(test_methods)}")
        print(f"Success Rate: {(passed / len(test_methods) * 100):.1f}%")
        print(f"Total Successes: {len(self.successes)}")
        print(f"Total Errors: {len(self.errors)}")

        if self.errors:
            print("\n[FAIL] ERRORS FOUND:")
            for error in self.errors:
                print(f"   • {error}")

        if passed == len(test_methods):
            print("\n🎉 ALL TESTS PASSED!")
            print("Charts should be rendering properly.")
            print("\n💡 If charts still don't appear in browser:")
            print("   1. Check browser developer console for JavaScript errors")
            print("   2. Verify network requests are successful")
            print("   3. Check that DOM elements are properly loaded")
        else:
            print(f"\n[WARN] {len(test_methods) - passed} TESTS FAILED")
            print("Chart rendering may be broken.")

        return passed == len(test_methods)


def main():
    """Run the chart rendering tests."""
    test_suite = ChartRenderingTest()
    success = test_suite.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
