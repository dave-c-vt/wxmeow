#!/usr/bin/env python3
"""
Unit tests for chart data processing in wxmeow weather application.

These tests verify that the data processing logic for charts works correctly
without requiring a browser or full Flask application.

Usage:
    python -m pytest tests/unit/test_chart_data_processing.py -v
    python tests/unit/test_chart_data_processing.py
"""

import sys
import os
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(project_root))

try:
    from wxmeow.wx2json_noaa import wxmeow
except ImportError as e:
    print(f"Error importing wxmeow: {e}")
    sys.exit(1)


class ChartDataProcessingTest(unittest.TestCase):
    """Unit tests for chart data processing logic."""

    def setUp(self):
        """Set up test data."""
        # Mock NOAA API response data
        self.mock_hourly_data = []

        # Generate 5 days of hourly data (24 hours each)
        from datetime import datetime, timedelta

        base_time = datetime.now()
        for day in range(5):
            for hour in range(24):
                time_offset = timedelta(days=day, hours=hour)
                item_time = base_time + time_offset

                self.mock_hourly_data.append(
                    {
                        "time": item_time.isoformat(),
                        "temperature": 65
                        + (day * 5)
                        + (hour % 12),  # Varying temperatures
                        "temp": 65 + (day * 5) + (hour % 12),
                        "condition": "Clear" if hour % 8 < 4 else "Cloudy",
                        "precip": 10 + (hour % 6) * 5
                        if day > 1
                        else 0,  # Precipitation for later days
                        "probabilityOfPrecipitation": 10 + (hour % 6) * 5
                        if day > 1
                        else 0,
                        "windSpeed": f"{5 + hour % 10} mph",
                        "windDirection": "NW",
                        "icon": "https://api.weather.gov/icons/land/day/clear",
                    }
                )

    def test_hourly_data_processing(self):
        """Test that hourly data is processed correctly."""
        # Mock the weather object
        mock_weather = Mock()
        mock_weather.jhourly = {"properties": {"periods": []}}

        # Create periods from our test data
        for item in self.mock_hourly_data:
            period = {
                "startTime": item["time"],
                "temperature": item["temperature"],
                "shortForecast": item["condition"],
                "windSpeed": item["windSpeed"],
                "windDirection": item["windDirection"],
                "icon": item["icon"],
                "probabilityOfPrecipitation": {"value": item["precip"]},
            }
            mock_weather.jhourly["properties"]["periods"].append(period)

        # Create wxmeow instance with mocked data
        with patch("wxmeow.wx2json_noaa.wxmeow.__init__", return_value=None):
            weather_obj = wxmeow.__new__(wxmeow)
            weather_obj.meow = mock_weather
            weather_obj.meowhourly = []

            # Call the processing method
            weather_obj._process_hourly_data()

            # Verify processed data
            self.assertIsInstance(weather_obj.meowhourly, list)
            self.assertEqual(len(weather_obj.meowhourly), len(self.mock_hourly_data))

            # Check first item structure
            if weather_obj.meowhourly:
                first_item = weather_obj.meowhourly[0]
                required_fields = ["time", "temperature", "temp", "condition", "precip"]
                for field in required_fields:
                    self.assertIn(field, first_item, f"Missing field: {field}")

    def test_temperature_alignment_data(self):
        """Test that temperature data aligns correctly with day structure."""
        # Mock a simple weather object
        with patch("wxmeow.wx2json_noaa.wxmeow.__init__", return_value=None):
            weather_obj = wxmeow.__new__(wxmeow)
            weather_obj.meowtp = [72, 75, 68, 71, 73]  # 5 days of temperatures
            weather_obj.meowhourly = self.mock_hourly_data

            # Test temperature row generation
            # This simulates the HTML generation logic
            temperature_values = []
            for i in range(5):
                temp_value = (
                    weather_obj.meowtp[i] if i < len(weather_obj.meowtp) else "??"
                )
                temperature_values.append(temp_value)

            # Verify we have 5 temperature values
            self.assertEqual(len(temperature_values), 5)

            # Verify all temperatures are numbers (not ??)
            for temp in temperature_values:
                self.assertNotEqual(temp, "??", "All temperatures should have values")
                self.assertIsInstance(
                    temp, (int, float), "Temperature should be numeric"
                )

    def test_precipitation_data_extraction(self):
        """Test that precipitation data is extracted correctly."""
        # Create test data with precipitation
        test_periods = []
        for i in range(24):
            period = {
                "startTime": f"2024-01-01T{i:02d}:00:00-05:00",
                "temperature": 70,
                "shortForecast": "Partly Cloudy",
                "probabilityOfPrecipitation": {
                    "value": 20 + (i % 5) * 10  # Varying precipitation
                },
            }
            test_periods.append(period)

        mock_weather = Mock()
        mock_weather.jhourly = {"properties": {"periods": test_periods}}

        with patch("wxmeow.wx2json_noaa.wxmeow.__init__", return_value=None):
            weather_obj = wxmeow.__new__(wxmeow)
            weather_obj.meow = mock_weather
            weather_obj.meowhourly = []

            weather_obj._process_hourly_data()

            # Verify precipitation data
            self.assertEqual(len(weather_obj.meowhourly), 24)

            for item in weather_obj.meowhourly:
                self.assertIn("precip", item)
                precip_value = item["precip"]
                self.assertIsInstance(precip_value, (int, float))
                self.assertGreaterEqual(precip_value, 0)
                self.assertLessEqual(precip_value, 100)

    def test_chart_data_filtering_by_date(self):
        """Test that chart data is correctly filtered by date."""
        from datetime import datetime, timedelta

        # Create test data spanning multiple days
        base_date = datetime(2024, 1, 1)
        test_data = []

        for day in range(3):
            for hour in range(24):
                item_time = base_date + timedelta(days=day, hours=hour)
                test_data.append(
                    {
                        "time": item_time.isoformat(),
                        "temperature": 60 + day * 10 + hour,
                        "precip": day * 10,
                    }
                )

        # Test filtering for day 1 (second day)
        target_date = base_date + timedelta(days=1)

        # Simulate the JavaScript filtering logic in Python
        filtered_data = []
        for item in test_data:
            if not item.get("time"):
                continue
            item_date = datetime.fromisoformat(item["time"].replace("Z", "+00:00"))
            if item_date.date() == target_date.date():
                filtered_data.append(item)

        # Should have 24 hours for day 1
        self.assertEqual(len(filtered_data), 24)

        # All items should be from the correct day
        for item in filtered_data:
            item_date = datetime.fromisoformat(item["time"].replace("Z", "+00:00"))
            self.assertEqual(item_date.date(), target_date.date())

    def test_chart_data_structure_validation(self):
        """Test that chart data has the correct structure for Chart.js."""
        # Mock processed hourly data
        sample_data = [
            {
                "time": "2024-01-01T00:00:00",
                "temperature": 65,
                "temp": 65,
                "precip": 0,
                "condition": "Clear",
            },
            {
                "time": "2024-01-01T01:00:00",
                "temperature": 63,
                "temp": 63,
                "precip": 5,
                "condition": "Partly Cloudy",
            },
        ]

        # Simulate chart data preparation (JavaScript logic in Python)
        labels = []
        temperatures = []
        precip_probs = []

        for item in sample_data:
            # Parse time and create label
            from datetime import datetime

            date = datetime.fromisoformat(item["time"])
            hour = date.hour

            if hour == 0:
                label = "12 AM"
            elif hour == 12:
                label = "12 PM"
            elif hour > 12:
                label = f"{hour - 12} PM"
            else:
                label = f"{hour} AM"

            labels.append(label)
            temperatures.append(item.get("temperature") or item.get("temp"))
            precip_probs.append(item.get("precip", 0))

        # Validate structure
        self.assertEqual(len(labels), len(sample_data))
        self.assertEqual(len(temperatures), len(sample_data))
        self.assertEqual(len(precip_probs), len(sample_data))

        # Validate data types
        for temp in temperatures:
            self.assertIsInstance(temp, (int, float))

        for precip in precip_probs:
            self.assertIsInstance(precip, (int, float))
            self.assertGreaterEqual(precip, 0)

    def test_empty_data_handling(self):
        """Test handling of empty or missing data."""
        # Test with empty hourly data
        mock_weather = Mock()
        mock_weather.jhourly = {"properties": {"periods": []}}

        with patch("wxmeow.wx2json_noaa.wxmeow.__init__", return_value=None):
            weather_obj = wxmeow.__new__(wxmeow)
            weather_obj.meow = mock_weather
            weather_obj.meowhourly = []

            weather_obj._process_hourly_data()

            # Should handle empty data gracefully
            self.assertIsInstance(weather_obj.meowhourly, list)
            self.assertEqual(len(weather_obj.meowhourly), 0)

        # Test with missing jhourly attribute
        mock_weather_no_hourly = Mock()
        del mock_weather_no_hourly.jhourly

        with patch("wxmeow.wx2json_noaa.wxmeow.__init__", return_value=None):
            weather_obj = wxmeow.__new__(wxmeow)
            weather_obj.meow = mock_weather_no_hourly
            weather_obj.meowhourly = []

            weather_obj._process_hourly_data()

            # Should handle missing data gracefully
            self.assertIsInstance(weather_obj.meowhourly, list)
            self.assertEqual(len(weather_obj.meowhourly), 0)

    def test_data_consistency_across_days(self):
        """Test that data remains consistent when accessing different days."""
        # Create consistent test data
        consistent_data = []
        for day in range(5):
            for hour in range(24):
                consistent_data.append(
                    {
                        "day": day,
                        "hour": hour,
                        "temperature": 70 + day * 2 + (hour - 12) * 0.5,
                        "precip": day * 5 + hour % 10,
                    }
                )

        # Test accessing data for each day
        for target_day in range(5):
            day_data = [item for item in consistent_data if item["day"] == target_day]

            self.assertEqual(
                len(day_data), 24, f"Day {target_day} should have 24 hours"
            )

            # Verify data consistency
            temps = [item["temperature"] for item in day_data]
            self.assertEqual(len(set(temps)), 24, "All temperatures should be unique")

            # Verify precipitation data exists
            precips = [item["precip"] for item in day_data]
            self.assertTrue(all(isinstance(p, (int, float)) for p in precips))


def run_unit_tests():
    """Run all unit tests for chart data processing."""
    print("🧪 Running Chart Data Processing Unit Tests")
    print("=" * 50)

    # Run tests
    unittest.main(verbosity=2, exit=False)


if __name__ == "__main__":
    run_unit_tests()
