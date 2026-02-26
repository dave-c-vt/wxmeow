#!/usr/bin/env python3
"""
Tests for European weather sources
"""

import unittest
from unittest.mock import patch, Mock
from wxmeow.weather_query import is_european_location, metno, LocationError, ApiError


class EuropeanWeatherTest(unittest.TestCase):
    """Test European weather functionality"""

    def test_european_location_detection(self):
        """Test that European locations are correctly identified"""
        # Test positive cases
        european_locations = [
            "Berlin, Germany",
            "Paris, France", 
            "London, UK",
            "Oslo, Norway",
            "Amsterdam, Netherlands",
            "Rome, Italy",
            "Madrid, Spain"
        ]
        
        for location in european_locations:
            with self.subTest(location=location):
                self.assertTrue(is_european_location(location), f"{location} should be detected as European")

    def test_non_european_location_detection(self):
        """Test that non-European locations are not identified as European"""
        non_european_locations = [
            "New York, NY",
            "Chicago, IL", 
            "Toronto, ON",
            "Tokyo, Japan",
            "Sydney, Australia"
        ]
        
        for location in non_european_locations:
            with self.subTest(location=location):
                self.assertFalse(is_european_location(location), f"{location} should not be detected as European")

    @patch('wxmeow.weather_query.get_coordinates')
    @patch('wxmeow.weather_query.requests.Session.get')
    def test_metno_basic_functionality(self, mock_get, mock_coords):
        """Test basic Met.no API functionality with mocked responses"""
        # Mock coordinates
        mock_coords.return_value = (59.9133, 10.7389)  # Oslo coordinates
        
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'properties': {
                'timeseries': [
                    {
                        'time': '2024-01-01T12:00:00Z',
                        'data': {
                            'instant': {
                                'details': {
                                    'air_temperature': -5.0,
                                    'relative_humidity': 80,
                                    'air_pressure_at_sea_level': 1013.25,
                                    'wind_speed': 5.0,
                                    'wind_from_direction': 270
                                }
                            },
                            'next_1_hours': {
                                'summary': {
                                    'symbol_code': 'cloudy_day'
                                }
                            }
                        }
                    }
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test Met.no initialization
        weather = metno("Oslo, Norway")
        
        # Verify basic properties
        self.assertEqual(weather.city, "Oslo")
        self.assertEqual(weather.lat, 59.9133)
        self.assertEqual(weather.lon, 10.7389)
        self.assertIsNotNone(weather.jconditions)
        
        # Verify conditions data
        conditions = weather.jconditions
        self.assertEqual(conditions['temperature'], -5.0)
        self.assertEqual(conditions['condition'], 'cloudy')

    @patch('wxmeow.weather_query.get_coordinates')
    def test_metno_location_error(self, mock_coords):
        """Test Met.no handles location errors properly"""
        # Mock coordinates failure
        mock_coords.return_value = None
        
        with self.assertRaises(LocationError):
            metno("InvalidLocation")

    @patch('wxmeow.weather_query.get_coordinates')
    @patch('wxmeow.weather_query.requests.Session.get')
    def test_metno_api_error(self, mock_get, mock_coords):
        """Test Met.no handles API errors properly with fallback"""
        # Mock coordinates
        mock_coords.return_value = (59.9133, 10.7389)
        
        # Mock API error - use requests exception
        import requests
        mock_get.side_effect = requests.exceptions.RequestException("API Error")
        
        # With fallback mechanisms, this should not raise an error but fall back gracefully
        try:
            weather = metno("Oslo, Norway")
            # Should have fallback data
            self.assertIsNotNone(weather.jforecast)
            self.assertIsNotNone(weather.jconditions)
        except Exception as e:
            self.fail(f"Met.no should handle API errors gracefully with fallback, but raised: {e}")


if __name__ == "__main__":
    unittest.main()