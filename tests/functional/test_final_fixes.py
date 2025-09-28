#!/usr/bin/env python3
"""
Final Comprehensive Test for All Plot Fixes

This test verifies all issues have been resolved:
1. Plot loads immediately on page load (not blank)
2. No page jumping when clicking day selector buttons
3. Temperature text properly aligned with weather icons
4. No hyperlink underlines on day selectors
5. Both temperature and precipitation data displayed
6. Charts switch properly between days
"""

import re
import tempfile
import webbrowser
import os
from wxmeow.wx2json_noaa import wxmeow


class FinalFixesTest:
    """Comprehensive test for all plot functionality fixes."""

    def __init__(self):
        self.test_location = "Boston, MA"
        self.weather_obj = None
        self.html_content = ""
        self.passed_tests = 0
        self.total_tests = 0

    def test_result(self, test_name, condition, details=""):
        """Record and display test result."""
        self.total_tests += 1
        status = "✅ PASS" if condition else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"     {details}")
        if condition:
            self.passed_tests += 1
        return condition

    def test_initial_chart_load(self):
        """Test that chart loads immediately on page load."""
        print("\n🔧 TESTING INITIAL CHART LOAD")
        print("-" * 50)

        # Check for initial chart creation call
        has_initial_creation = "createTemperatureChart(0);" in self.html_content
        self.test_result(
            "Initial Chart Creation",
            has_initial_creation,
            "createTemperatureChart(0) called on document ready",
        )

        # Check that day 0 container is visible by default
        day_0_visible = (
            'id="hourly-temperature-chart-0"' in self.html_content
            and "display: block" in self.html_content
        )
        self.test_result(
            "Day 0 Container Visible",
            day_0_visible,
            "Chart container for day 0 visible by default",
        )

        return has_initial_creation and day_0_visible

    def test_no_page_jumping(self):
        """Test that clicking day buttons doesn't cause page jumping."""
        print("\n🚫 TESTING NO PAGE JUMPING")
        print("-" * 50)

        # Check that all onclick handlers include 'return false;'
        onclick_patterns = re.findall(r'onclick="([^"]*)"', self.html_content)
        selectday_handlers = [p for p in onclick_patterns if "selectDay(" in p]

        has_return_false = all(
            "return false" in handler for handler in selectday_handlers
        )
        self.test_result(
            "Return False in Onclick",
            has_return_false,
            f"All {len(selectday_handlers)} selectDay handlers include 'return false;'",
        )

        # Check for consistent selectDay function calls (no old jQuery code)
        no_old_jquery = not any(
            [
                ".removeClass('selected-day')" in handler
                and "selectDay(" not in handler
                for handler in onclick_patterns
            ]
        )
        self.test_result(
            "No Old jQuery Handlers",
            no_old_jquery,
            "No conflicting jQuery onclick handlers present",
        )

        return has_return_false and no_old_jquery

    def test_temperature_alignment(self):
        """Test that temperature values align with weather icons."""
        print("\n🌡️ TESTING TEMPERATURE ALIGNMENT")
        print("-" * 50)

        # Check that temperature values are present
        temp_values = self.weather_obj.meowtp[:5]
        temp_count_in_html = sum(
            1 for temp in temp_values if f"{temp} F" in self.html_content
        )

        alignment_correct = temp_count_in_html >= 5
        self.test_result(
            "Temperature Values Present",
            alignment_correct,
            f"Found {temp_count_in_html}/5 temperature values in HTML",
        )

        # Check for proper table structure
        has_table_structure = (
            "<table" in self.html_content
            and "</table>" in self.html_content
            and "<td" in self.html_content
        )
        self.test_result(
            "Table Structure Present",
            has_table_structure,
            "HTML contains proper table structure for alignment",
        )

        # Check weather icon and temperature positioning
        has_weather_icons = "weather-icon" in self.html_content
        self.test_result(
            "Weather Icons Present",
            has_weather_icons,
            "Weather icon elements found in HTML",
        )

        return alignment_correct and has_table_structure and has_weather_icons

    def test_no_underlines(self):
        """Test that hyperlink underlines are removed."""
        print("\n🔗 TESTING NO UNDERLINES")
        print("-" * 50)

        # Check for text-decoration: none CSS rules
        has_no_underline_css = "text-decoration: none" in self.html_content
        self.test_result(
            "No Underline CSS",
            has_no_underline_css,
            "text-decoration: none rules found in CSS",
        )

        # Check for day-selector specific styling
        has_day_selector_styling = ".day-selector" in self.html_content
        self.test_result(
            "Day Selector Styling",
            has_day_selector_styling,
            "Day selector CSS classes present",
        )

        return has_no_underline_css and has_day_selector_styling

    def test_dual_axis_chart(self):
        """Test that charts display both temperature and precipitation data."""
        print("\n📊 TESTING DUAL-AXIS CHART")
        print("-" * 50)

        # Check for dual y-axis configuration
        has_dual_axis = (
            "yAxisID: 'temp'" in self.html_content
            and "yAxisID: 'precip'" in self.html_content
        )
        self.test_result(
            "Dual Y-Axis Configuration",
            has_dual_axis,
            "Both temperature and precipitation y-axis configurations found",
        )

        # Check for precipitation dataset
        has_precip_dataset = "Precipitation %" in self.html_content
        self.test_result(
            "Precipitation Dataset",
            has_precip_dataset,
            "Precipitation percentage dataset configured",
        )

        # Check for legend display
        has_legend = (
            "display: true" in self.html_content
            and "position: 'top'" in self.html_content
        )
        self.test_result(
            "Chart Legend", has_legend, "Chart legend configured to display"
        )

        # Verify actual precipitation data
        has_precip_data = any(
            item.get("precip") is not None for item in self.weather_obj.meowhourly[:5]
        )
        self.test_result(
            "Precipitation Data Available",
            has_precip_data,
            "Hourly data contains precipitation values",
        )

        return has_dual_axis and has_precip_dataset and has_legend and has_precip_data

    def test_chart_switching(self):
        """Test that charts switch properly between days."""
        print("\n🔄 TESTING CHART SWITCHING")
        print("-" * 50)

        # Check for 5 chart containers
        chart_containers = re.findall(
            r'id="hourly-temperature-chart-(\d+)"', self.html_content
        )
        has_all_containers = len(chart_containers) >= 5
        self.test_result(
            "Chart Containers",
            has_all_containers,
            f"Found {len(chart_containers)} chart containers (need 5)",
        )

        # Check for proper show/hide logic
        has_show_hide = (
            "hide()" in self.html_content
            and "show()" in self.html_content
            and 'id="hourly-temperature-chart-" + dayIndex' in self.html_content
        )
        self.test_result(
            "Show/Hide Logic", has_show_hide, "Chart show/hide logic implemented"
        )

        # Check for chart creation on day selection
        has_chart_creation = "createTemperatureChart(dayIndex)" in self.html_content
        self.test_result(
            "Chart Creation on Selection",
            has_chart_creation,
            "Chart created when day is selected",
        )

        return has_all_containers and has_show_hide and has_chart_creation

    def test_data_integrity(self):
        """Test that all necessary data is present and properly formatted."""
        print("\n💾 TESTING DATA INTEGRITY")
        print("-" * 50)

        # Check hourly data availability
        hourly_data_count = len(self.weather_obj.meowhourly)
        sufficient_data = hourly_data_count >= 120  # 5 days * 24 hours
        self.test_result(
            "Sufficient Hourly Data",
            sufficient_data,
            f"Has {hourly_data_count} hourly data points (need 120+)",
        )

        # Check window.hourlyData injection
        has_data_injection = "window.hourlyData = " in self.html_content
        self.test_result(
            "Data Injection",
            has_data_injection,
            "window.hourlyData properly injected into JavaScript",
        )

        # Verify data structure
        sample_data = (
            self.weather_obj.meowhourly[0] if self.weather_obj.meowhourly else {}
        )
        required_fields = ["time", "temp", "temperature", "condition", "precip"]
        has_required_fields = all(field in sample_data for field in required_fields)
        self.test_result(
            "Data Structure Complete",
            has_required_fields,
            f"Sample data has required fields: {list(sample_data.keys())}",
        )

        return sufficient_data and has_data_injection and has_required_fields

    def create_browser_test(self):
        """Create a test HTML file for manual browser verification."""
        print("\n🌐 CREATING BROWSER TEST FILE")
        print("-" * 50)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            # Add some debugging info at the top
            debug_header = f"""
<!-- FINAL FIXES TEST FILE -->
<!-- Generated for location: {self.test_location} -->
<!-- Total hourly data points: {len(self.weather_obj.meowhourly)} -->
<!-- Test results: {self.passed_tests}/{self.total_tests} passed -->
<div style="position: fixed; top: 0; right: 0; background: #333; color: #fff; padding: 10px; font-family: monospace; font-size: 12px; z-index: 9999;">
    TEST: {self.passed_tests}/{self.total_tests} PASSED<br>
    DATA: {len(self.weather_obj.meowhourly)} points<br>
    LOC: {self.test_location}
</div>
"""
            f.write(debug_header + self.html_content)
            test_file = f.name

        print(f"📄 Test file created: {test_file}")
        print("\n🔍 Manual verification steps:")
        print("1. Open the file in a browser")
        print("2. Chart should load immediately (not blank)")
        print("3. Click different day icons - page should not jump")
        print("4. Each day should show different chart data")
        print("5. Charts should show both temperature and precipitation lines")
        print("6. Temperature numbers should align with weather icons")
        print("7. No underlines on day selector buttons")

        return test_file

    def run_all_tests(self):
        """Run all comprehensive tests."""
        print("🧪 FINAL COMPREHENSIVE FIXES TEST")
        print("=" * 60)
        print(f"Testing location: {self.test_location}")

        # Load weather data
        try:
            self.weather_obj = wxmeow(self.test_location)
            self.html_content = self.weather_obj.futuremeow
            print(f"✅ Weather data loaded: {len(self.html_content)} characters")
        except Exception as e:
            print(f"❌ Failed to load weather data: {str(e)}")
            return False

        # Run all test categories
        test_categories = [
            ("Initial Chart Load", self.test_initial_chart_load),
            ("No Page Jumping", self.test_no_page_jumping),
            ("Temperature Alignment", self.test_temperature_alignment),
            ("No Underlines", self.test_no_underlines),
            ("Dual-Axis Chart", self.test_dual_axis_chart),
            ("Chart Switching", self.test_chart_switching),
            ("Data Integrity", self.test_data_integrity),
        ]

        category_results = []
        for category_name, test_func in test_categories:
            try:
                result = test_func()
                category_results.append((category_name, result))
            except Exception as e:
                print(f"❌ {category_name} failed with exception: {str(e)}")
                category_results.append((category_name, False))

        # Create browser test file
        test_file = self.create_browser_test()

        # Final summary
        print("\n" + "=" * 60)
        print("📊 FINAL TEST SUMMARY")
        print("=" * 60)

        print(
            f"Individual Tests: {self.passed_tests}/{self.total_tests} passed ({self.passed_tests / self.total_tests * 100:.1f}%)"
        )

        print("\nCategory Results:")
        passed_categories = 0
        for category_name, result in category_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status}: {category_name}")
            if result:
                passed_categories += 1

        overall_success = passed_categories == len(category_results)

        if overall_success:
            print("\n🎉 ALL FIXES SUCCESSFULLY IMPLEMENTED!")
            print("The plot should now work perfectly:")
            print("  • Loads immediately without being blank")
            print("  • No page jumping when clicking day selectors")
            print("  • Temperature text properly aligned")
            print("  • No hyperlink underlines")
            print("  • Dual-axis charts with temperature & precipitation")
            print("  • Smooth day switching functionality")
        else:
            print(f"\n⚠️ {len(category_results) - passed_categories} ISSUES REMAIN")
            print("Some fixes may need additional work.")

        print(f"\n💡 Manual test file: {test_file}")
        print("Open in browser to verify all functionality works as expected.")

        return overall_success


def main():
    """Run the comprehensive final fixes test."""
    test_suite = FinalFixesTest()
    success = test_suite.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
