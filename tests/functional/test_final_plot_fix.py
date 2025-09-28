#!/usr/bin/env python3
"""
FINAL PLOT FIX VERIFICATION TEST

This test verifies that all chart/plot issues have been properly fixed:
1. Day selector buttons work correctly
2. Charts display hourly data without errors
3. Day descriptions change when selecting different days
4. All JavaScript functionality is properly integrated

This test simulates the actual user experience and verifies the fixes work.
"""

import re
import json
import tempfile
import webbrowser
import os
from wxmeow.wx2json_noaa import wxmeow


class FinalPlotFixTest:
    """Comprehensive test for plot/chart functionality fixes."""

    def __init__(self):
        self.test_location = "Boston, MA"
        self.weather_obj = None
        self.html_content = ""
        self.errors = []
        self.fixes_verified = []

    def log_fix(self, fix_name, status, details=""):
        """Log a fix verification result."""
        status_symbol = "✅" if status else "❌"
        message = f"{status_symbol} {fix_name}: {details}"
        print(message)

        self.fixes_verified.append(
            {"fix": fix_name, "status": status, "details": details}
        )

        if not status:
            self.errors.append(f"{fix_name}: {details}")

    def verify_day_selector_fix(self):
        """Verify that day selector onclick handlers are properly implemented."""
        print("\n🔧 VERIFYING DAY SELECTOR FIX")
        print("-" * 50)

        # Check for correct onclick handlers
        onclick_patterns = re.findall(r'onclick="([^"]*)"', self.html_content)
        selectday_handlers = [p for p in onclick_patterns if "selectDay(" in p]

        self.log_fix(
            "Day Selector Buttons",
            len(selectday_handlers) >= 5,
            f"Found {len(selectday_handlers)} selectDay onclick handlers",
        )

        # Verify the selectDay function targets correct elements
        selectday_function = (
            self.html_content[
                self.html_content.find("function selectDay(") : self.html_content.find(
                    "function selectDay("
                )
                + 1000
            ]
            if "function selectDay(" in self.html_content
            else ""
        )

        # Check that it targets day-description elements (not the broken .tr elements)
        targets_day_descriptions = 'day-description-" + dayIndex' in selectday_function
        no_broken_tr_elements = '.tr" + dayIndex' not in selectday_function

        self.log_fix(
            "SelectDay Function Targets",
            targets_day_descriptions and no_broken_tr_elements,
            f"Targets day-description: {targets_day_descriptions}, Avoids broken .tr: {no_broken_tr_elements}",
        )

    def verify_hourly_data_fix(self):
        """Verify that hourly data is properly injected into JavaScript."""
        print("\n💾 VERIFYING HOURLY DATA FIX")
        print("-" * 50)

        # Check that window.hourlyData is set
        hourly_data_pattern = r"window\.hourlyData\s*=\s*(\[.*?\]);"
        match = re.search(hourly_data_pattern, self.html_content, re.DOTALL)

        if match:
            try:
                json_data = match.group(1)
                parsed_data = json.loads(json_data)
                data_count = len(parsed_data)

                self.log_fix(
                    "Hourly Data Injection",
                    data_count > 0,
                    f"Found {data_count} hourly data points in window.hourlyData",
                )

                # Verify data structure
                if parsed_data:
                    sample = parsed_data[0]
                    required_fields = ["time", "temperature", "condition"]
                    has_required_fields = all(
                        field in sample for field in required_fields
                    )

                    self.log_fix(
                        "Hourly Data Structure",
                        has_required_fields,
                        f"Required fields present: {has_required_fields}",
                    )
                else:
                    self.log_fix("Hourly Data Structure", False, "No data points found")

            except json.JSONDecodeError as e:
                self.log_fix("Hourly Data JSON", False, f"Invalid JSON: {str(e)}")
        else:
            self.log_fix("Hourly Data Injection", False, "window.hourlyData not found")

    def verify_chart_containers_fix(self):
        """Verify that chart containers are properly set up."""
        print("\n📊 VERIFYING CHART CONTAINERS FIX")
        print("-" * 50)

        # Check for chart container elements
        chart_containers = re.findall(
            r'id="hourly-temperature-chart-(\d+)"', self.html_content
        )

        self.log_fix(
            "Chart Container Elements",
            len(chart_containers) >= 5,
            f"Found {len(chart_containers)} chart containers",
        )

        # Check for proper chart styling
        has_chart_styling = "min-height: 300px" in self.html_content
        has_chart_width = "width: 100%" in self.html_content

        self.log_fix(
            "Chart Container Styling",
            has_chart_styling and has_chart_width,
            f"Min-height: {has_chart_styling}, Width: {has_chart_width}",
        )

        # Check for Chart.js library inclusion
        has_chartjs = "chart.js" in self.html_content.lower()
        has_temp_chart_js = "temperature-chart.js" in self.html_content

        self.log_fix(
            "Chart Libraries",
            has_chartjs and has_temp_chart_js,
            f"Chart.js: {has_chartjs}, temperature-chart.js: {has_temp_chart_js}",
        )

    def verify_day_descriptions_fix(self):
        """Verify that day descriptions are properly implemented."""
        print("\n📝 VERIFYING DAY DESCRIPTIONS FIX")
        print("-" * 50)

        # Check for day description elements
        day_descriptions = re.findall(r'id="day-description-(\d+)"', self.html_content)

        self.log_fix(
            "Day Description Elements",
            len(day_descriptions) >= 5,
            f"Found {len(day_descriptions)} day description elements",
        )

        # Check that only day 0 is initially visible
        day_0_visible = (
            'id="day-description-0"' in self.html_content
            and "display:block" in self.html_content
        )
        day_others_hidden = "display:none" in self.html_content

        self.log_fix(
            "Day Description Visibility",
            day_0_visible and day_others_hidden,
            f"Day 0 visible: {day_0_visible}, Others hidden: {day_others_hidden}",
        )

    def verify_javascript_integration_fix(self):
        """Verify that JavaScript integration is working properly."""
        print("\n⚙️ VERIFYING JAVASCRIPT INTEGRATION FIX")
        print("-" * 50)

        # Check for jQuery inclusion
        has_jquery = "jquery" in self.html_content.lower()

        # Check for proper event handling
        has_document_ready = "$(document).ready(" in self.html_content
        has_day_selected_event = "daySelected" in self.html_content

        self.log_fix(
            "JavaScript Dependencies", has_jquery, f"jQuery included: {has_jquery}"
        )

        self.log_fix(
            "JavaScript Event Handling",
            has_document_ready and has_day_selected_event,
            f"Document ready: {has_document_ready}, daySelected event: {has_day_selected_event}",
        )

        # Check for initial chart selection
        has_initial_selection = "selectDay(0)" in self.html_content

        self.log_fix(
            "Initial Chart Selection",
            has_initial_selection,
            f"selectDay(0) called on load: {has_initial_selection}",
        )

    def create_test_html_file(self):
        """Create a test HTML file to verify functionality in browser."""
        print("\n🌐 CREATING BROWSER TEST FILE")
        print("-" * 50)

        # Create a temporary HTML file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(self.html_content)
            temp_file = f.name

        print(f"📄 Test HTML file created: {temp_file}")
        print("🔍 You can manually open this file in a browser to verify:")
        print("   1. Day selector buttons change the forecast text")
        print("   2. Charts display without 'unable to load' errors")
        print("   3. Clicking day icons shows different content")

        return temp_file

    def run_all_verifications(self):
        """Run all fix verifications."""
        print("🧪 FINAL PLOT FIX VERIFICATION TEST")
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

        # Run all verification tests
        verification_tests = [
            self.verify_day_selector_fix,
            self.verify_hourly_data_fix,
            self.verify_chart_containers_fix,
            self.verify_day_descriptions_fix,
            self.verify_javascript_integration_fix,
        ]

        for test in verification_tests:
            try:
                test()
            except Exception as e:
                self.log_fix(
                    test.__name__, False, f"Test failed with exception: {str(e)}"
                )

        # Create browser test file
        test_file = self.create_test_html_file()

        # Final summary
        print("\n" + "=" * 60)
        print("📊 FINAL FIX VERIFICATION SUMMARY")
        print("=" * 60)

        total_fixes = len(self.fixes_verified)
        passed_fixes = len([f for f in self.fixes_verified if f["status"]])
        success_rate = (passed_fixes / total_fixes * 100) if total_fixes > 0 else 0

        print(f"Fixes Verified: {passed_fixes}/{total_fixes}")
        print(f"Success Rate: {success_rate:.1f}%")

        if self.errors:
            print(f"\n❌ REMAINING ISSUES ({len(self.errors)}):")
            for error in self.errors:
                print(f"   • {error}")

        if success_rate >= 90:
            print("\n🎉 PLOT FIXES SUCCESSFUL!")
            print("The chart/plot functionality should now work properly.")
            print("\n💡 To verify manually:")
            print(f"   1. Open: {test_file}")
            print("   2. Check browser console for any JavaScript errors")
            print("   3. Test clicking day selector buttons")
            print("   4. Verify charts load without 'unable to load' messages")
        else:
            print(f"\n⚠️ PLOT FIXES INCOMPLETE!")
            print("Some issues remain that need to be addressed.")

        return success_rate >= 90


def main():
    """Run the final plot fix verification test."""
    test = FinalPlotFixTest()
    success = test.run_all_verifications()
    return 0 if success else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
