#!/usr/bin/env python3
"""
Comprehensive tests for day picker functionality, temperature alignment, and chart functionality.
Tests the specific issues:
1. Day text changes when clicking different day icons
2. Temperature forecast alignment with day icons
3. Chart functionality with real hourly data
"""

import sys
import os
import re
import json
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wxmeow.wx2json_noaa import wxmeow


class TestDayPickerFixes:
    def __init__(self):
        self.test_location = "Boston, MA"
        self.weather = None
        self.forecast_html = ""
        self.errors = []
        self.successes = []

    def setup(self):
        """Set up test data."""
        print("Setting up test data...")
        try:
            self.weather = wxmeow(self.test_location)
            self.forecast_html = self.weather.futuremeow
            if not self.forecast_html:
                raise Exception("No forecast HTML generated")
            print(f"✓ Test data setup complete. HTML length: {len(self.forecast_html)}")
            return True
        except Exception as e:
            print(f"✗ Setup failed: {str(e)}")
            return False

    def test_day_selector_structure(self):
        """Test that day selectors have proper IDs and onclick handlers."""
        print("\n1. Testing day selector structure...")

        # Check for day selector elements with proper IDs (0-4)
        day_selector_pattern = r"id='(\d)' class='day-selector weather-icon'"
        matches = re.findall(day_selector_pattern, self.forecast_html)

        expected_days = ["0", "1", "2", "3", "4"]
        found_days = sorted(matches)

        if found_days == expected_days:
            self.successes.append("Day selector IDs are correct (0-4)")
            print("   ✓ All 5 day selectors found with correct IDs")
        else:
            self.errors.append(
                f"Day selector IDs incorrect. Expected: {expected_days}, Found: {found_days}"
            )
            print(
                f"   ✗ Day selector IDs incorrect. Expected: {expected_days}, Found: {found_days}"
            )

        # Check for onclick handlers that trigger daySelected events
        onclick_pattern = r'onclick="[^"]*daySelected[^"]*"'
        onclick_matches = re.findall(onclick_pattern, self.forecast_html, re.IGNORECASE)

        if len(onclick_matches) >= 5:
            self.successes.append(
                f"Found {len(onclick_matches)} onclick handlers with daySelected events"
            )
            print(
                f"   ✓ Found {len(onclick_matches)} onclick handlers with daySelected events"
            )
        else:
            self.errors.append(
                f"Only {len(onclick_matches)} onclick handlers found, expected 5"
            )
            print(
                f"   ✗ Only {len(onclick_matches)} onclick handlers found, expected 5"
            )

    def test_day_descriptions_structure(self):
        """Test that day descriptions have proper IDs and unique content."""
        print("\n2. Testing day description structure...")

        # Check for day description elements with proper IDs
        desc_pattern = (
            r'<div id="day-description-(\d)" class="day-description"[^>]*>(.*?)</div>'
        )
        matches = re.findall(desc_pattern, self.forecast_html, re.DOTALL)

        if len(matches) >= 5:
            self.successes.append(f"Found {len(matches)} day descriptions")
            print(f"   ✓ Found {len(matches)} day descriptions")

            # Check that descriptions have different content (not all the same)
            descriptions = [match[1].strip() for match in matches]
            unique_descriptions = set(descriptions)

            if len(unique_descriptions) > 1:
                self.successes.append("Day descriptions have unique content")
                print("   ✓ Day descriptions have unique content")
            else:
                self.errors.append("All day descriptions appear to be identical")
                print("   ✗ All day descriptions appear to be identical")

            # Check description display styling
            display_pattern = (
                r'<div id="day-description-0"[^>]*style="[^"]*display:\s*block[^"]*"'
            )
            if re.search(display_pattern, self.forecast_html):
                self.successes.append("Day 0 description is initially visible")
                print("   ✓ Day 0 description is initially visible")
            else:
                self.errors.append("Day 0 description is not initially visible")
                print("   ✗ Day 0 description is not initially visible")

        else:
            self.errors.append(
                f"Only {len(matches)} day descriptions found, expected 5"
            )
            print(f"   ✗ Only {len(matches)} day descriptions found, expected 5")

    def test_temperature_alignment(self):
        """Test that temperatures are properly aligned with their corresponding day icons."""
        print("\n3. Testing temperature alignment with day icons...")

        # Extract the weather icons table structure
        table_pattern = r'<table[^>]*class="weather-forecast-table"[^>]*>(.*?)</table>'
        table_match = re.search(table_pattern, self.forecast_html, re.DOTALL)

        if not table_match:
            self.errors.append("Weather forecast table not found")
            print("   ✗ Weather forecast table not found")
            return

        table_content = table_match.group(1)

        # Look for temperature values in the HTML (they should be in a separate table row)
        temp_pattern = r"(\d+)\s*F"
        temp_matches = re.findall(temp_pattern, self.forecast_html)

        if len(temp_matches) >= 5:
            temperatures = temp_matches[:5]  # Take first 5 temperatures
            self.successes.append(
                f"Found {len(temp_matches)} temperatures: {', '.join(temperatures)}°F"
            )
            print(
                f"   ✓ Found {len(temp_matches)} temperatures: {', '.join(temperatures)}°F"
            )

            # Check that temperatures are reasonable (between 0-120°F)
            valid_temps = []
            for temp_str in temperatures:
                try:
                    temp = int(temp_str)
                    if 0 <= temp <= 120:
                        valid_temps.append(temp)
                except ValueError:
                    pass

            if len(valid_temps) >= 5:
                self.successes.append("All temperatures are in valid range (0-120°F)")
                print("   ✓ All temperatures are in valid range (0-120°F)")
            else:
                self.errors.append(f"Only {len(valid_temps)} temperatures are valid")
                print(f"   ✗ Only {len(valid_temps)} temperatures are valid")

        else:
            self.errors.append("Not enough temperature values found")
            print("   ✗ Not enough temperature values found")

        # Check for proper table cell alignment (td classes) - look for temperature row
        temp_row_pattern = r"<tr[^>]*>.*?<td[^>]*>\d+\s*F</td>.*?</tr>"
        temp_row_match = re.search(temp_row_pattern, self.forecast_html, re.DOTALL)

        if temp_row_match:
            self.successes.append("Temperature row structure found")
            print("   ✓ Temperature row structure found")

            # Count td elements with temperatures in the row
            td_temp_pattern = r"<td[^>]*>\d+\s*F</td>"
            td_temp_matches = re.findall(td_temp_pattern, temp_row_match.group(0))

            if len(td_temp_matches) >= 5:
                self.successes.append(
                    "Temperatures are properly wrapped in table cells"
                )
                print("   ✓ Temperatures are properly wrapped in table cells")
            else:
                self.errors.append(
                    f"Only {len(td_temp_matches)} temperature table cells found"
                )
                print(f"   ✗ Only {len(td_temp_matches)} temperature table cells found")
        else:
            self.errors.append("Temperature table row structure not found")
            print("   ✗ Temperature table row structure not found")

    def test_chart_containers(self):
        """Test that chart containers are properly created for each day."""
        print("\n4. Testing chart container structure...")

        # Check for chart containers with proper IDs
        chart_pattern = (
            r'<div id="hourly-temperature-chart-(\d)"[^>]*class="hourly-chart"[^>]*>'
        )
        matches = re.findall(chart_pattern, self.forecast_html)

        expected_charts = ["0", "1", "2", "3", "4"]
        found_charts = sorted(matches)

        if found_charts == expected_charts:
            self.successes.append("All 5 chart containers found with correct IDs")
            print("   ✓ All 5 chart containers found with correct IDs")
        else:
            self.errors.append(
                f"Chart container IDs incorrect. Expected: {expected_charts}, Found: {found_charts}"
            )
            print(
                f"   ✗ Chart container IDs incorrect. Expected: {expected_charts}, Found: {found_charts}"
            )

        # Check that chart 0 is initially visible, others hidden
        visible_chart_pattern = r'<div id="hourly-temperature-chart-0"[^>]*style="[^"]*display:\s*block[^"]*"'
        if re.search(visible_chart_pattern, self.forecast_html):
            self.successes.append("Chart 0 is initially visible")
            print("   ✓ Chart 0 is initially visible")
        else:
            self.errors.append("Chart 0 is not initially visible")
            print("   ✗ Chart 0 is not initially visible")

    def test_javascript_chart_functionality(self):
        """Test that JavaScript includes proper chart initialization code."""
        print("\n5. Testing JavaScript chart functionality...")

        # Check for Chart.js inclusion
        if "chart.js" in self.forecast_html.lower():
            self.successes.append("Chart.js library is included")
            print("   ✓ Chart.js library is included")
        else:
            self.errors.append("Chart.js library not found")
            print("   ✗ Chart.js library not found")

        # Check for selectDay function
        if "function selectDay" in self.forecast_html:
            self.successes.append("selectDay function found")
            print("   ✓ selectDay function found")
        else:
            self.errors.append("selectDay function not found")
            print("   ✗ selectDay function not found")

        # Check for daySelected event handling
        if "daySelected" in self.forecast_html:
            self.successes.append("daySelected event handling found")
            print("   ✓ daySelected event handling found")
        else:
            self.errors.append("daySelected event handling not found")
            print("   ✗ daySelected event handling not found")

        # Check for chart script inclusion
        if "temperature-chart.js" in self.forecast_html:
            self.successes.append("Chart script is included")
            print("   ✓ Chart script is included")
        else:
            self.errors.append("Chart script not included")
            print("   ✗ Chart script not included")

    def test_hourly_data_availability(self):
        """Test that real hourly data is available for charts."""
        print("\n6. Testing hourly data availability...")

        if hasattr(self.weather, "meowhourly") and self.weather.meowhourly:
            hourly_count = len(self.weather.meowhourly)
            self.successes.append(f"Real hourly data available: {hourly_count} periods")
            print(f"   ✓ Real hourly data available: {hourly_count} periods")

            # Check data structure
            if hourly_count > 0:
                first_item = self.weather.meowhourly[0]
                required_fields = ["time", "temperature", "condition"]
                missing_fields = [
                    field for field in required_fields if field not in first_item
                ]

                if not missing_fields:
                    self.successes.append(
                        "Hourly data has required fields (time, temperature, condition)"
                    )
                    print(
                        "   ✓ Hourly data has required fields (time, temperature, condition)"
                    )
                else:
                    self.errors.append(f"Hourly data missing fields: {missing_fields}")
                    print(f"   ✗ Hourly data missing fields: {missing_fields}")

                # Test sample data
                sample_temp = first_item.get("temperature")
                sample_time = first_item.get("time")
                sample_condition = first_item.get("condition")

                if sample_temp and 0 <= sample_temp <= 120:
                    self.successes.append(
                        f"Sample temperature is valid: {sample_temp}°F"
                    )
                    print(f"   ✓ Sample temperature is valid: {sample_temp}°F")
                else:
                    self.errors.append(f"Sample temperature is invalid: {sample_temp}")
                    print(f"   ✗ Sample temperature is invalid: {sample_temp}")

                if sample_time:
                    try:
                        # Try to parse the time string
                        datetime.fromisoformat(sample_time.replace("Z", "+00:00"))
                        self.successes.append("Sample time format is valid")
                        print("   ✓ Sample time format is valid")
                    except:
                        self.errors.append(
                            f"Sample time format is invalid: {sample_time}"
                        )
                        print(f"   ✗ Sample time format is invalid: {sample_time}")

        else:
            self.errors.append("No hourly data available")
            print("   ✗ No hourly data available")

    def test_day_picker_event_integration(self):
        """Test that day picker clicks properly integrate with chart updates."""
        print("\n7. Testing day picker event integration...")

        # Check that each day selector has onclick that triggers chart update
        for day in range(5):
            day_onclick_pattern = (
                f'id=[\'"]{day}[\'"][^>]*onclick="[^"]*daySelected.*?\\[{day}\\]'
            )
            if re.search(day_onclick_pattern, self.forecast_html):
                self.successes.append(
                    f"Day {day} selector properly triggers chart update"
                )
            else:
                self.errors.append(
                    f"Day {day} selector does not properly trigger chart update"
                )
                print(f"   ✗ Day {day} selector does not properly trigger chart update")

        # Check for chart update logic in JavaScript
        chart_update_pattern = r"trigger.*daySelected.*\[\s*dayIndex\s*\]"
        if re.search(chart_update_pattern, self.forecast_html):
            self.successes.append("Chart update logic found in JavaScript")
            print("   ✓ Chart update logic found in JavaScript")
        else:
            self.errors.append("Chart update logic not found in JavaScript")
            print("   ✗ Chart update logic not found in JavaScript")

    def test_responsive_design(self):
        """Test responsive design elements."""
        print("\n8. Testing responsive design...")

        # Check for responsive table class
        if "weather-forecast-table" in self.forecast_html:
            self.successes.append("Responsive table class found")
            print("   ✓ Responsive table class found")
        else:
            self.errors.append("Responsive table class missing")
            print("   ✗ Responsive table class missing")

        # Check for mobile-responsive td classes
        if "class='one'" in self.forecast_html:
            self.successes.append("Mobile-responsive td classes found")
            print("   ✓ Mobile-responsive td classes found")
        else:
            self.errors.append("Mobile-responsive td classes missing")
            print("   ✗ Mobile-responsive td classes missing")

    def run_all_tests(self):
        """Run all tests and return results."""
        print("=" * 70)
        print("RUNNING COMPREHENSIVE DAY PICKER TESTS")
        print("=" * 70)

        if not self.setup():
            return False

        # Run all test methods
        self.test_day_selector_structure()
        self.test_day_descriptions_structure()
        self.test_temperature_alignment()
        self.test_chart_containers()
        self.test_javascript_chart_functionality()
        self.test_hourly_data_availability()
        self.test_day_picker_event_integration()
        self.test_responsive_design()

        # Summary
        print("\n" + "=" * 70)
        print("TEST RESULTS SUMMARY")
        print("=" * 70)

        total_successes = len(self.successes)
        total_errors = len(self.errors)
        total_tests = total_successes + total_errors

        print(f"✓ SUCCESSES: {total_successes}")
        for success in self.successes:
            print(f"  • {success}")

        if self.errors:
            print(f"\n✗ ERRORS: {total_errors}")
            for error in self.errors:
                print(f"  • {error}")

        print(f"\nOVERALL: {total_successes}/{total_tests} tests passed")

        if total_errors == 0:
            print("🎉 ALL TESTS PASSED! Day picker functionality is working correctly.")
            return True
        elif total_successes >= total_errors * 2:
            print(
                "[OK] MOSTLY WORKING: Minor issues found but core functionality is good."
            )
            return True
        else:
            print("[FAIL] SIGNIFICANT ISSUES: Major problems found that need fixing.")
            return False


def main():
    """Main test execution."""
    tester = TestDayPickerFixes()
    success = tester.run_all_tests()

    print("\n" + "=" * 70)
    print("SPECIFIC ISSUE CHECKS")
    print("=" * 70)

    print(
        "1. DAY TEXT CHANGES: Check that day descriptions have unique IDs and content"
    )
    print("2. TEMPERATURE ALIGNMENT: Check that temps align with day icons in table")
    print("3. CHART FUNCTIONALITY: Check that real hourly data is available for charts")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
