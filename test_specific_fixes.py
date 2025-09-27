#!/usr/bin/env python3
"""
Tests for specific UI and chart issues:
1. Chart showing multiple times instead of once per day selection
2. Chart missing proper x/y axis labels and precipitation data
3. Day forecast text not showing below weather icons
4. Temperature alignment issues with day icons
"""

import sys
import os
import re
import json
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wxmeow.wx2json_noaa import wxmeow
from wxmeow import create_app


class SpecificFixesTest:
    def __init__(self):
        self.test_location = "Boston, MA"
        self.weather = None
        self.forecast_html = ""
        self.app = None
        self.client = None
        self.errors = []
        self.successes = []

    def setup(self):
        """Set up test environment."""
        print("Setting up specific fixes test environment...")
        try:
            self.weather = wxmeow(self.test_location)
            self.forecast_html = self.weather.futuremeow
            self.app = create_app()
            self.client = self.app.test_client()

            if not self.forecast_html:
                raise Exception("No forecast HTML generated")

            print(f"✓ Setup complete. HTML length: {len(self.forecast_html)}")
            return True
        except Exception as e:
            print(f"✗ Setup failed: {str(e)}")
            return False

    def test_chart_display_logic(self):
        """Test that charts are shown one at a time, not multiple simultaneously."""
        print("\n1. Testing chart display logic...")

        # Find all chart containers
        chart_pattern = r'<div id="hourly-temperature-chart-(\d)" class="hourly-chart"[^>]*style="([^"]*)"'
        chart_matches = re.findall(chart_pattern, self.forecast_html)

        if len(chart_matches) >= 5:
            print(f"   Found {len(chart_matches)} chart containers")

            # Check initial display states
            visible_charts = []
            hidden_charts = []

            for day_id, style in chart_matches:
                if "display:block" in style or "display: block" in style:
                    visible_charts.append(day_id)
                elif "display:none" in style or "display: none" in style:
                    hidden_charts.append(day_id)

            # Only day 0 should be initially visible
            if len(visible_charts) == 1 and visible_charts[0] == "0":
                self.successes.append(f"Only chart 0 is initially visible")
                print("   ✓ Only chart 0 is initially visible")
            else:
                self.errors.append(
                    f"Multiple charts visible initially: {visible_charts}"
                )
                print(f"   ✗ Multiple charts visible initially: {visible_charts}")

            # Check that other charts are properly hidden
            expected_hidden = ["1", "2", "3", "4"]
            if set(hidden_charts) == set(expected_hidden):
                self.successes.append("Charts 1-4 are properly hidden")
                print("   ✓ Charts 1-4 are properly hidden")
            else:
                self.errors.append(
                    f"Hidden charts wrong. Expected: {expected_hidden}, Got: {hidden_charts}"
                )
                print(
                    f"   ✗ Hidden charts wrong. Expected: {expected_hidden}, Got: {hidden_charts}"
                )

        else:
            self.errors.append(
                f"Expected 5 chart containers, found {len(chart_matches)}"
            )
            print(f"   ✗ Expected 5 chart containers, found {len(chart_matches)}")

        # Test JavaScript chart switching logic
        if "Hide all day details and charts" in self.forecast_html:
            self.successes.append("Chart hiding logic found in JavaScript")
            print("   ✓ Chart hiding logic found in JavaScript")
        else:
            self.errors.append("Chart hiding logic missing from JavaScript")
            print("   ✗ Chart hiding logic missing from JavaScript")

    def test_chart_axis_and_precipitation(self):
        """Test that charts have proper axis labels and precipitation data."""
        print("\n2. Testing chart axis labels and precipitation data...")

        # Check for temperature axis label
        if "Temperature (°F)" in self.forecast_html:
            self.successes.append("Temperature axis label found")
            print("   ✓ Temperature axis label found")
        else:
            self.errors.append("Temperature axis label missing")
            print("   ✗ Temperature axis label missing")

        # Check for time axis label
        if '"Time"' in self.forecast_html:
            self.successes.append("Time axis label found")
            print("   ✓ Time axis label found")
        else:
            self.errors.append("Time axis label missing")
            print("   ✗ Time axis label missing")

        # Check if hourly data includes precipitation
        if self.weather.meowhourly:
            sample_data = self.weather.meowhourly[0]
            if "precip" in sample_data or "precipitation" in sample_data:
                self.successes.append("Precipitation data available in hourly data")
                print("   ✓ Precipitation data available in hourly data")

                # Check for multiple datasets in chart config
                if '"Precipitation (%)"' in self.forecast_html:
                    self.successes.append("Multiple chart datasets configured")
                    print("   ✓ Multiple chart datasets configured")
                else:
                    self.errors.append("Multiple chart datasets not configured")
                    print("   ✗ Multiple chart datasets not configured")
            else:
                self.errors.append("Precipitation data missing from hourly data")
                print("   ✗ Precipitation data missing from hourly data")
        else:
            self.errors.append("No hourly data available for testing")
            print("   ✗ No hourly data available for testing")

        # Check for chart styling and beauty
        chart_styling_indicators = [
            "tempGradient",
            "borderColor",
            "backgroundColor",
            "responsive: true",
            "animation:",
        ]

        found_styling = [
            indicator
            for indicator in chart_styling_indicators
            if indicator in self.forecast_html
        ]

        if len(found_styling) >= 3:
            self.successes.append(f"Chart styling elements found: {found_styling}")
            print(f"   ✓ Chart styling elements found: {found_styling}")
        else:
            self.errors.append(f"Insufficient chart styling. Found: {found_styling}")
            print(f"   ✗ Insufficient chart styling. Found: {found_styling}")

    def test_day_forecast_text_placement(self):
        """Test that day forecast text appears below the weather icons."""
        print("\n3. Testing day forecast text placement...")

        # Find the weather icons table
        table_pattern = r'<table[^>]*class="weather-forecast-table"[^>]*>(.*?)</table>'
        table_match = re.search(table_pattern, self.forecast_html, re.DOTALL)

        if table_match:
            self.successes.append("Weather forecast table found")
            print("   ✓ Weather forecast table found")

            table_content = table_match.group(0)
            table_end_pos = self.forecast_html.find(table_content) + len(table_content)

            # Check what comes immediately after the table
            after_table = self.forecast_html[table_end_pos : table_end_pos + 500]

            # Look for day descriptions immediately after the table
            desc_pattern = r'<div id="day-description-\d"'
            desc_match = re.search(desc_pattern, after_table)

            if desc_match:
                # Check if the description is visible immediately after table
                desc_position = desc_match.start()
                if desc_position < 200:  # Should be very close to table end
                    self.successes.append(
                        "Day description found immediately after icons table"
                    )
                    print("   ✓ Day description found immediately after icons table")
                else:
                    self.errors.append("Day description too far from icons table")
                    print("   ✗ Day description too far from icons table")
            else:
                self.errors.append("Day description not found after icons table")
                print("   ✗ Day description not found after icons table")

            # Check if day descriptions are properly structured for visibility
            visible_desc_pattern = (
                r'<div id="day-description-0"[^>]*style="[^"]*display:\s*block'
            )
            if re.search(visible_desc_pattern, self.forecast_html):
                self.successes.append("Day 0 description is initially visible")
                print("   ✓ Day 0 description is initially visible")
            else:
                self.errors.append("Day 0 description is not initially visible")
                print("   ✗ Day 0 description is not initially visible")

        else:
            self.errors.append("Weather forecast table not found")
            print("   ✗ Weather forecast table not found")

    def test_temperature_spacing_alignment(self):
        """Test temperature text spacing and vertical alignment with day icons."""
        print("\n4. Testing temperature spacing and alignment...")

        # Find the temperature row
        temp_row_pattern = (
            r"<tr[^>]*>.*?(\d+\s*F.*?\d+\s*F.*?\d+\s*F.*?\d+\s*F.*?\d+\s*F).*?</tr>"
        )
        temp_row_match = re.search(temp_row_pattern, self.forecast_html, re.DOTALL)

        if temp_row_match:
            temp_row_content = temp_row_match.group(1)
            self.successes.append("Temperature row found")
            print("   ✓ Temperature row found")

            # Check for proper table cell structure with spacing
            td_temp_pattern = r"<td[^>]*>\s*(\d+\s*F)\s*</td>"
            td_matches = re.findall(td_temp_pattern, temp_row_content)

            if len(td_matches) >= 5:
                self.successes.append(
                    f"Found {len(td_matches)} properly spaced temperature cells"
                )
                print(f"   ✓ Found {len(td_matches)} properly spaced temperature cells")
                print(f"      Temperatures: {', '.join(td_matches)}")
            else:
                self.errors.append(
                    f"Only {len(td_matches)} temperature cells found with proper spacing"
                )
                print(
                    f"   ✗ Only {len(td_matches)} temperature cells found with proper spacing"
                )

            # Check that temperatures are not all centered/adjacent
            if (
                "text-align:center" in temp_row_content
                or "text-align: center" in temp_row_content
            ):
                # This might be okay if they're in separate cells
                cell_count = temp_row_content.count("<td")
                if cell_count >= 5:
                    self.successes.append(
                        "Temperatures in separate table cells (centering is okay)"
                    )
                    print(
                        "   ✓ Temperatures in separate table cells (centering is okay)"
                    )
                else:
                    self.errors.append(
                        "Temperatures appear to be centered without proper cell separation"
                    )
                    print(
                        "   ✗ Temperatures appear to be centered without proper cell separation"
                    )
            else:
                self.successes.append("Temperature text alignment looks correct")
                print("   ✓ Temperature text alignment looks correct")

        else:
            self.errors.append("Temperature row with proper structure not found")
            print("   ✗ Temperature row with proper structure not found")

        # Test vertical alignment by checking table structure
        weather_icons_row = re.search(
            r"<tr[^>]*>.*?day-selector weather-icon.*?</tr>",
            self.forecast_html,
            re.DOTALL,
        )
        temp_row = re.search(
            r"<tr[^>]*>.*?\d+\s*F.*?</tr>", self.forecast_html, re.DOTALL
        )

        if weather_icons_row and temp_row:
            icons_pos = self.forecast_html.find(weather_icons_row.group(0))
            temp_pos = self.forecast_html.find(temp_row.group(0))

            if temp_pos > icons_pos and (temp_pos - icons_pos) < 2000:
                self.successes.append(
                    "Temperature row follows icons row in reasonable proximity"
                )
                print("   ✓ Temperature row follows icons row in reasonable proximity")
            else:
                self.errors.append(
                    "Temperature row not properly positioned relative to icons"
                )
                print("   ✗ Temperature row not properly positioned relative to icons")

        # Check for mobile responsive classes that might affect alignment
        mobile_class_pattern = r'class=["\'][^"\']*one[^"\']*["\']'
        mobile_matches = re.findall(mobile_class_pattern, self.forecast_html)

        if len(mobile_matches) >= 2:  # Should be some mobile-responsive cells
            self.successes.append("Mobile-responsive table classes found")
            print("   ✓ Mobile-responsive table classes found")
        else:
            self.errors.append("Mobile-responsive table classes missing")
            print("   ✗ Mobile-responsive table classes missing")

    def test_overall_layout_structure(self):
        """Test the overall layout structure for proper organization."""
        print("\n5. Testing overall layout structure...")

        # Expected order: Icons table -> Temperature row -> Day descriptions -> Charts
        structure_elements = [
            ("weather-forecast-table", "Weather icons table"),
            (r"\d+\s*F", "Temperature data"),
            (r'<div id="day-description-', "Day descriptions"),
            ("hourly-temperature-chart", "Chart containers"),
        ]

        positions = []
        for pattern, name in structure_elements:
            match = re.search(pattern, self.forecast_html)
            if match:
                positions.append((match.start(), name))
            else:
                self.errors.append(f"{name} not found in HTML")
                print(f"   ✗ {name} not found in HTML")

        # Check if elements are in correct order
        positions.sort(key=lambda x: x[0])
        expected_order = [
            "Weather icons table",
            "Temperature data",
            "Day descriptions",
            "Chart containers",
        ]
        actual_order = [name for _, name in positions]

        if actual_order == expected_order:
            self.successes.append("Page layout elements in correct order")
            print("   ✓ Page layout elements in correct order")
            for i, (pos, name) in enumerate(positions):
                print(f"      {i + 1}. {name} at position {pos}")
        else:
            self.errors.append(
                f"Layout order incorrect. Expected: {expected_order}, Got: {actual_order}"
            )
            print(
                f"   ✗ Layout order incorrect. Expected: {expected_order}, Got: {actual_order}"
            )

    def run_all_tests(self):
        """Run all specific fix tests."""
        print("=" * 80)
        print("TESTING SPECIFIC UI AND CHART FIXES")
        print("=" * 80)
        print(f"Testing location: {self.test_location}")
        print("=" * 80)

        if not self.setup():
            return False

        # Run all test methods
        self.test_chart_display_logic()
        self.test_chart_axis_and_precipitation()
        self.test_day_forecast_text_placement()
        self.test_temperature_spacing_alignment()
        self.test_overall_layout_structure()

        return self.show_results()

    def show_results(self):
        """Display test results."""
        print("\n" + "=" * 80)
        print("SPECIFIC FIXES TEST RESULTS")
        print("=" * 80)

        success_count = len(self.successes)
        error_count = len(self.errors)
        total_tests = success_count + error_count

        print(f"\n✓ SUCCESSES: {success_count}")
        for success in self.successes:
            print(f"  • {success}")

        if self.errors:
            print(f"\n✗ ERRORS: {error_count}")
            for error in self.errors:
                print(f"  • {error}")

        success_rate = (success_count / total_tests * 100) if total_tests > 0 else 0
        print(
            f"\nOVERALL: {success_count}/{total_tests} tests passed ({success_rate:.1f}%)"
        )

        print("\n" + "=" * 80)
        print("ISSUES TO FIX:")
        print("=" * 80)
        print("1. 📊 Chart should show one at a time, not multiple")
        print("2. 🎨 Chart needs proper axis labels and precipitation data")
        print("3. 📝 Day forecast text should appear below weather icons")
        print("4. 📐 Temperature alignment and spacing needs fixing")

        return success_rate >= 75


def main():
    """Run the specific fixes test."""
    tester = SpecificFixesTest()
    success = tester.run_all_tests()

    if success:
        print("\n🎯 READY FOR FIXES: Test suite identifies specific issues to address")
    else:
        print(
            "\n⚠️ CRITICAL ISSUES: Multiple problems found that need immediate attention"
        )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
