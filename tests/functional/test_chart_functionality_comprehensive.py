#!/usr/bin/env python3
"""
Comprehensive tests for wxmeow chart functionality.

This test suite verifies that all chart-related issues are properly fixed:
1. Temperature and precipitation data display correctly
2. Day selection works without page scrolling or data loss
3. Temperature alignment matches day weather icons

Usage:
    python -m pytest tests/functional/test_chart_functionality_comprehensive.py -v
    python tests/functional/test_chart_functionality_comprehensive.py
"""

import sys
import os
import time
import unittest
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Add project root to path
project_root = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(project_root))

# Import the Flask app
try:
    from wxmeow import create_app
except ImportError as e:
    print(f"Error importing Flask app: {e}")
    sys.exit(1)


class ChartFunctionalityTest(unittest.TestCase):
    """Comprehensive functional tests for wxmeow chart functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment and start Flask app."""
        # Set up Chrome driver options
        cls.chrome_options = Options()
        cls.chrome_options.add_argument("--headless")
        cls.chrome_options.add_argument("--no-sandbox")
        cls.chrome_options.add_argument("--disable-dev-shm-usage")
        cls.chrome_options.add_argument("--disable-gpu")
        cls.chrome_options.add_argument("--window-size=1920,1080")

        # Create Flask app in testing mode
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.app.config["DEBUG"] = False

        # Start Flask test server
        import threading

        cls.server_thread = threading.Thread(
            target=cls.app.run,
            kwargs={
                "host": "127.0.0.1",
                "port": 5555,
                "debug": False,
                "use_reloader": False,
            },
        )
        cls.server_thread.daemon = True
        cls.server_thread.start()

        # Wait for server to start
        time.sleep(2)

        cls.base_url = "http://127.0.0.1:5555"
        cls.test_location = "Boston, MA"

    def setUp(self):
        """Set up individual test."""
        self.driver = webdriver.Chrome(options=self.chrome_options)
        self.driver.implicitly_wait(10)
        self.wait = WebDriverWait(self.driver, 20)

    def tearDown(self):
        """Clean up after each test."""
        if hasattr(self, "driver"):
            self.driver.quit()

    def test_01_temperature_and_precipitation_display_on_load(self):
        """
        Test Issue 1: Verify temperature and precipitation both display correctly on page load.

        Expected: Both temperature and precipitation datasets should be visible in the initial chart.
        """
        print("\n🧪 Testing Issue 1: Temperature and precipitation display on load")

        # Navigate to weather page
        weather_url = f"{self.base_url}/wx/{self.test_location}"
        self.driver.get(weather_url)

        # Wait for page to load completely
        self.wait.until(
            EC.presence_of_element_located((By.ID, "hourly-temperature-chart-0"))
        )
        time.sleep(3)  # Allow charts to initialize

        # Check that chart container is present and visible
        chart_container = self.driver.find_element(By.ID, "hourly-temperature-chart-0")
        self.assertTrue(
            chart_container.is_displayed(), "Chart container should be visible"
        )

        # Check for canvas element (Chart.js creates this)
        canvas_elements = self.driver.find_elements(By.TAG_NAME, "canvas")
        self.assertGreater(
            len(canvas_elements), 0, "Should have at least one canvas element"
        )

        # Execute JavaScript to check chart data
        chart_data_script = """
            if (typeof charts !== 'undefined' && charts[0]) {
                const chart = charts[0];
                const datasets = chart.data.datasets;
                return {
                    datasetCount: datasets.length,
                    hasTemperature: datasets.some(ds => ds.label && ds.label.includes('Temperature')),
                    hasPrecipitation: datasets.some(ds => ds.label && ds.label.includes('Precipitation')),
                    temperatureData: datasets.find(ds => ds.label && ds.label.includes('Temperature'))?.data || [],
                    precipitationData: datasets.find(ds => ds.label && ds.label.includes('Precipitation'))?.data || []
                };
            }
            return { error: 'Charts not found or not initialized' };
        """

        chart_info = self.driver.execute_script(chart_data_script)

        # Verify chart has both temperature and precipitation data
        if "error" not in chart_info:
            self.assertGreaterEqual(
                chart_info["datasetCount"],
                1,
                "Should have at least temperature dataset",
            )
            self.assertTrue(
                chart_info["hasTemperature"], "Should have temperature data"
            )

            # If precipitation data exists, it should be visible
            if chart_info["hasPrecipitation"]:
                self.assertGreater(
                    len(chart_info["precipitationData"]),
                    0,
                    "Precipitation dataset should have data points",
                )
                print("✅ Both temperature and precipitation data found")
            else:
                print(
                    "⚠️  Only temperature data found (may be normal if no precipitation)"
                )
        else:
            self.fail(f"Chart initialization failed: {chart_info.get('error')}")

    def test_02_day_selection_no_scrolling_no_data_loss(self):
        """
        Test Issue 2: Verify day selection works without page scrolling and data loss.

        Expected: Clicking day icons should not scroll page and should maintain chart data.
        """
        print("\n🧪 Testing Issue 2: Day selection without scrolling/data loss")

        # Navigate to weather page
        weather_url = f"{self.base_url}/wx/{self.test_location}"
        self.driver.get(weather_url)

        # Wait for page to load and initial chart to appear
        self.wait.until(
            EC.presence_of_element_located((By.ID, "hourly-temperature-chart-0"))
        )
        time.sleep(3)

        # Record initial scroll position
        initial_scroll_position = self.driver.execute_script(
            "return window.pageYOffset;"
        )

        # Find day selector elements
        day_selectors = self.driver.find_elements(By.CSS_SELECTOR, ".day-selector")
        self.assertGreaterEqual(
            len(day_selectors), 5, "Should have at least 5 day selectors"
        )

        # Test clicking different days
        for day_index in [1, 2, 3, 4, 0]:  # Test days 1-4, then back to 0
            print(f"   Testing day {day_index} selection...")

            # Click the day selector
            day_selector = self.driver.find_element(By.ID, str(day_index))
            self.driver.execute_script("arguments[0].click();", day_selector)

            # Wait for chart to update
            time.sleep(2)

            # Check scroll position hasn't changed significantly
            current_scroll_position = self.driver.execute_script(
                "return window.pageYOffset;"
            )
            scroll_diff = abs(current_scroll_position - initial_scroll_position)
            self.assertLess(
                scroll_diff,
                50,
                f"Page should not scroll significantly when clicking day {day_index}",
            )

            # Verify the correct chart container is visible
            active_chart = self.driver.find_element(
                By.ID, f"hourly-temperature-chart-{day_index}"
            )
            self.assertTrue(
                active_chart.is_displayed(), f"Chart {day_index} should be visible"
            )

            # Check for error messages
            error_text = active_chart.text.lower()
            error_indicators = ["no data", "no hourly data", "error", "failed"]
            has_error = any(indicator in error_text for indicator in error_indicators)

            if has_error:
                print(f"⚠️  Day {day_index} shows error: {error_text}")
                # Don't fail immediately - collect all results
            else:
                print(f"✅ Day {day_index} loaded successfully")

            # Verify chart data exists
            chart_check_script = f"""
                if (typeof charts !== 'undefined' && charts[{day_index}]) {{
                    const chart = charts[{day_index}];
                    const datasets = chart.data.datasets;
                    return {{
                        hasData: datasets.length > 0 && datasets[0].data.length > 0,
                        datasetCount: datasets.length,
                        dataPoints: datasets[0].data.length
                    }};
                }}
                return {{ hasData: false, error: 'Chart not found' }};
            """

            chart_data = self.driver.execute_script(chart_check_script)
            if day_index <= 2:  # First 3 days should typically have data
                self.assertTrue(
                    chart_data.get("hasData", False),
                    f"Day {day_index} should have chart data",
                )

    def test_03_temperature_alignment_with_day_icons(self):
        """
        Test Issue 3: Verify temperatures align correctly with day weather icons.

        Expected: Temperature values should be positioned directly under their corresponding day icons.
        """
        print("\n🧪 Testing Issue 3: Temperature alignment with day icons")

        # Navigate to weather page
        weather_url = f"{self.base_url}/wx/{self.test_location}"
        self.driver.get(weather_url)

        # Wait for page to load
        self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".day-selector"))
        )
        time.sleep(2)

        # Get positions of weather icons and temperature values
        icon_positions = []
        temp_positions = []

        # Find all day selector icons
        day_selectors = self.driver.find_elements(By.CSS_SELECTOR, ".day-selector")
        for i, selector in enumerate(day_selectors[:5]):  # Check first 5 days
            location = selector.location
            size = selector.size
            center_x = location["x"] + size["width"] / 2
            icon_positions.append(
                {
                    "day": i,
                    "center_x": center_x,
                    "left": location["x"],
                    "right": location["x"] + size["width"],
                }
            )

        # Find temperature elements - they should be in the same table structure
        # Look for temperature text in table cells
        temp_script = """
            const tempElements = [];
            const rows = document.querySelectorAll('tr');

            rows.forEach(row => {
                const cells = row.querySelectorAll('td');
                if (cells.length >= 5) {
                    // Check if this row contains temperature data
                    const cellTexts = Array.from(cells).map(cell => cell.textContent.trim());
                    const hasTemp = cellTexts.some(text => text.includes('F') || text.includes('°'));

                    if (hasTemp) {
                        cells.forEach((cell, index) => {
                            if (index < 5 && (cell.textContent.includes('F') || cell.textContent.includes('°'))) {
                                const rect = cell.getBoundingClientRect();
                                tempElements.push({
                                    day: index,
                                    centerX: rect.left + rect.width / 2,
                                    left: rect.left,
                                    right: rect.right,
                                    text: cell.textContent.trim()
                                });
                            }
                        });
                    }
                }
            });

            return tempElements;
        """

        temp_elements = self.driver.execute_script(temp_script)

        # Verify we found temperature elements
        self.assertGreaterEqual(
            len(temp_elements), 3, "Should find at least 3 temperature elements"
        )

        # Check alignment between icons and temperatures
        alignment_tolerance = 50  # pixels - allow some tolerance for alignment
        aligned_count = 0

        for icon_pos in icon_positions[: len(temp_elements)]:
            day = icon_pos["day"]
            icon_center = icon_pos["center_x"]

            # Find corresponding temperature
            temp_pos = next((t for t in temp_elements if t["day"] == day), None)
            if temp_pos:
                temp_center = temp_pos["centerX"]
                alignment_diff = abs(icon_center - temp_center)

                print(
                    f"   Day {day}: Icon center {icon_center:.1f}px, Temp center {temp_center:.1f}px, "
                    f"Diff: {alignment_diff:.1f}px"
                )

                if alignment_diff <= alignment_tolerance:
                    aligned_count += 1
                    print(f"   ✅ Day {day} alignment OK")
                else:
                    print(f"   ⚠️  Day {day} alignment off by {alignment_diff:.1f}px")

        # At least 80% of elements should be properly aligned
        min_aligned = max(1, int(len(icon_positions) * 0.8))
        self.assertGreaterEqual(
            aligned_count,
            min_aligned,
            f"At least {min_aligned} out of {len(icon_positions)} elements should be aligned",
        )

    def test_04_integration_all_issues_together(self):
        """
        Integration test: Verify all three issues work together correctly.

        Tests the complete user workflow with all fixes applied.
        """
        print("\n🧪 Testing Integration: All issues working together")

        # Navigate to weather page
        weather_url = f"{self.base_url}/wx/{self.test_location}"
        self.driver.get(weather_url)

        # Wait for initial load
        self.wait.until(
            EC.presence_of_element_located((By.ID, "hourly-temperature-chart-0"))
        )
        time.sleep(3)

        # Track scroll position throughout
        initial_scroll = self.driver.execute_script("return window.pageYOffset;")

        issues_found = []

        # Test 1: Initial chart load
        try:
            chart_info = self.driver.execute_script("""
                if (typeof charts !== 'undefined' && charts[0]) {
                    return {
                        hasChart: true,
                        datasetCount: charts[0].data.datasets.length,
                        hasData: charts[0].data.datasets[0].data.length > 0
                    };
                }
                return { hasChart: false };
            """)

            if not chart_info.get("hasChart") or not chart_info.get("hasData"):
                issues_found.append("Initial chart failed to load with data")
        except Exception as e:
            issues_found.append(f"Initial chart load error: {str(e)}")

        # Test 2: Day switching workflow
        for day in [1, 2, 0]:  # Switch between days
            try:
                # Click day selector
                day_selector = self.driver.find_element(By.ID, str(day))
                self.driver.execute_script("arguments[0].click();", day_selector)
                time.sleep(2)

                # Check scroll position
                current_scroll = self.driver.execute_script(
                    "return window.pageYOffset;"
                )
                if abs(current_scroll - initial_scroll) > 50:
                    issues_found.append(f"Page scrolled when selecting day {day}")

                # Check chart visibility
                chart_container = self.driver.find_element(
                    By.ID, f"hourly-temperature-chart-{day}"
                )
                if not chart_container.is_displayed():
                    issues_found.append(f"Chart {day} not visible after selection")

                # Check for error messages
                if "no data" in chart_container.text.lower():
                    issues_found.append(f"Day {day} shows 'no data' error")

            except Exception as e:
                issues_found.append(f"Day {day} selection failed: {str(e)}")

        # Test 3: Temperature alignment check
        try:
            alignment_script = """
                const icons = document.querySelectorAll('.day-selector');
                const iconPositions = Array.from(icons).slice(0, 5).map((icon, i) => {
                    const rect = icon.getBoundingClientRect();
                    return rect.left + rect.width / 2;
                });

                const tempCells = document.querySelectorAll('td');
                const tempPositions = [];
                tempCells.forEach((cell, i) => {
                    if (cell.textContent.includes('F') && tempPositions.length < 5) {
                        const rect = cell.getBoundingClientRect();
                        tempPositions.push(rect.left + rect.width / 2);
                    }
                });

                const alignmentDiffs = iconPositions.map((iconX, i) => {
                    const tempX = tempPositions[i];
                    return tempX ? Math.abs(iconX - tempX) : 999;
                });

                return {
                    iconCount: iconPositions.length,
                    tempCount: tempPositions.length,
                    maxDiff: Math.max(...alignmentDiffs),
                    avgDiff: alignmentDiffs.reduce((a, b) => a + b, 0) / alignmentDiffs.length
                };
            """

            alignment_data = self.driver.execute_script(alignment_script)
            if alignment_data["maxDiff"] > 100:  # More than 100px off
                issues_found.append(
                    f"Temperature alignment off by {alignment_data['maxDiff']:.1f}px"
                )

        except Exception as e:
            issues_found.append(f"Alignment check failed: {str(e)}")

        # Report results
        if issues_found:
            print("\n❌ Issues found in integration test:")
            for issue in issues_found:
                print(f"   - {issue}")
            self.fail(f"Integration test failed with {len(issues_found)} issues")
        else:
            print("\n✅ Integration test passed - all issues resolved")

    def test_05_chart_data_persistence_across_days(self):
        """
        Test that chart data persists correctly when switching between days.

        Verifies that data doesn't disappear when switching days.
        """
        print("\n🧪 Testing chart data persistence across day switches")

        # Navigate to weather page
        weather_url = f"{self.base_url}/wx/{self.test_location}"
        self.driver.get(weather_url)

        # Wait for initial load
        self.wait.until(
            EC.presence_of_element_located((By.ID, "hourly-temperature-chart-0"))
        )
        time.sleep(3)

        # Collect data for each day
        day_data = {}

        for day_index in range(5):
            # Click day selector
            day_selector = self.driver.find_element(By.ID, str(day_index))
            self.driver.execute_script("arguments[0].click();", day_selector)
            time.sleep(2)

            # Get chart data
            chart_data_script = f"""
                if (typeof charts !== 'undefined' && charts[{day_index}]) {{
                    const chart = charts[{day_index}];
                    const tempData = chart.data.datasets.find(ds => ds.label.includes('Temperature'));
                    return {{
                        hasData: tempData && tempData.data.length > 0,
                        dataPoints: tempData ? tempData.data.length : 0,
                        sampleData: tempData ? tempData.data.slice(0, 3) : []
                    }};
                }}
                return {{ hasData: false, dataPoints: 0 }};
            """

            data = self.driver.execute_script(chart_data_script)
            day_data[day_index] = data

            print(
                f"   Day {day_index}: {data['dataPoints']} data points, "
                f"Sample: {data.get('sampleData', [])}"
            )

        # Verify data persistence
        working_days = [day for day, data in day_data.items() if data["hasData"]]
        self.assertGreaterEqual(
            len(working_days),
            3,
            f"At least 3 days should have chart data, found: {working_days}",
        )

        # Test switching back and forth
        if len(working_days) >= 2:
            day1, day2 = working_days[0], working_days[1]

            # Switch to day1, then day2, then back to day1
            for switch_day in [day1, day2, day1]:
                day_selector = self.driver.find_element(By.ID, str(switch_day))
                self.driver.execute_script("arguments[0].click();", switch_day)
                time.sleep(1)

                # Verify chart still has data
                has_data = self.driver.execute_script(f"""
                    return typeof charts !== 'undefined' && charts[{switch_day}] &&
                           charts[{switch_day}].data.datasets[0].data.length > 0;
                """)

                self.assertTrue(
                    has_data, f"Day {switch_day} should maintain data after switching"
                )


def run_comprehensive_tests():
    """Run all comprehensive chart functionality tests."""
    print("🧪 Running Comprehensive Chart Functionality Tests")
    print("=" * 60)

    # Create test suite
    suite = unittest.TestSuite()

    # Add tests in order
    suite.addTest(
        ChartFunctionalityTest("test_01_temperature_and_precipitation_display_on_load")
    )
    suite.addTest(
        ChartFunctionalityTest("test_02_day_selection_no_scrolling_no_data_loss")
    )
    suite.addTest(
        ChartFunctionalityTest("test_03_temperature_alignment_with_day_icons")
    )
    suite.addTest(ChartFunctionalityTest("test_04_integration_all_issues_together"))
    suite.addTest(ChartFunctionalityTest("test_05_chart_data_persistence_across_days"))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("🎉 ALL TESTS PASSED! Chart functionality is working correctly.")
    else:
        print(
            f"💥 {len(result.failures)} test(s) failed, {len(result.errors)} error(s)"
        )
        for test, error in result.failures + result.errors:
            print(f"   ❌ {test}: {error.split(chr(10))[0]}")

    return result.wasSuccessful()


if __name__ == "__main__":
    try:
        success = run_comprehensive_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        sys.exit(1)
