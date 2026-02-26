#!/usr/bin/env python3
"""
Tests for Canadian weather sources
"""

import unittest
from unittest.mock import patch, Mock
from wxmeow.weather_query import is_canadian_location, environment_canada, LocationError, ApiError


class CanadianWeatherTest(unittest.TestCase):
    """Test Canadian weather functionality"""

    def test_canadian_location_detection(self):
        """Test that Canadian locations are correctly identified"""
        # Test positive cases
        canadian_locations = [
            "Toronto, ON",
            "Montreal, QC", 
            "Vancouver, BC",
            "Calgary, AB",
            "Ottawa, Ontario",
            "Quebec City, Quebec",
            "Halifax, NS",
            "Winnipeg, Manitoba"
        ]
        
        for location in canadian_locations:
            with self.subTest(location=location):
                self.assertTrue(is_canadian_location(location), f"{location} should be detected as Canadian")

    def test_non_canadian_location_detection(self):
        """Test that non-Canadian locations are not identified as Canadian"""
        non_canadian_locations = [
            "New York, NY",
            "Chicago, IL", 
            "Berlin, Germany",
            "Paris, France",
            "Tokyo, Japan",
            "Sydney, Australia"
        ]
        
        for location in non_canadian_locations:
            with self.subTest(location=location):
                self.assertFalse(is_canadian_location(location), f"{location} should not be detected as Canadian")

    @patch('wxmeow.weather_query.get_coordinates')
    def test_environment_canada_basic_functionality(self, mock_coords):
        """Test basic Environment Canada functionality with mocked responses"""
        # Mock coordinates
        mock_coords.return_value = (43.6532, -79.3832)  # Toronto coordinates
        
        # Test Environment Canada initialization
        weather = environment_canada("Toronto, ON")
        
        # Verify basic properties
        self.assertEqual(weather.city, "Toronto")
        self.assertEqual(weather.lat, "43.6532")
        self.assertEqual(weather.lon, "-79.3832")
        self.assertIsNotNone(weather.jforecast)

    @patch('wxmeow.weather_query.get_coordinates')
    def test_environment_canada_location_error(self, mock_coords):
        """Test Environment Canada handles location errors properly with fallback data"""
        # Mock coordinates failure
        mock_coords.return_value = None
        
        # Should now provide fallback data instead of raising error
        weather = environment_canada("InvalidLocation")
        
        # Verify we got fallback data
        self.assertIsNotNone(weather.jforecast)
        self.assertEqual(weather.city, "InvalidLocation")
        self.assertEqual(weather.state, "Canada")


if __name__ == "__main__":
    unittest.main()