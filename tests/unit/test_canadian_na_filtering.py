#!/usr/bin/env python3

import unittest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from wxmeow.wx2json_noaa import wxmeow

class TestCanadianForecastNAFiltering(unittest.TestCase):
    """Test enhanced N/A filtering for Canadian weather forecasts"""
    
    def setUp(self):
        """Set up a weather instance for testing"""
        self.weather = wxmeow("Toronto,ON")
    
    def test_temperature_safe_formatting(self):
        """Test that _format_temperature_safe properly filters N/A values"""
        test_cases = [
            # (input, expected_output)
            (None, "—"),
            ("", "—"),
            ("N/A", "—"),
            ("n/a", "—"),
            ("NA", "—"),
            ("na", "—"),
            ("??", "—"),
            ("None", "—"),
            ("NONE", "—"),
            ("null", "—"),
            ("NULL", "—"),
            ("undefined", "—"),
            # New edge cases
            ("no_data", "—"),
            ("ERROR", "—"),
            ("timeout", "—"),
            ("#N/A", "—"),
            ("---°F", "—"),
            ("n/a°F", "—"),
            ("25", "25°F"),
            ("25.5", "25°F"),
            (" 30 ", "30°F"),
            ("invalid", "—"),
            (42, "42°F"),
            (32.0, "32°F"),
        ]
        
        for input_val, expected in test_cases:
            with self.subTest(input=input_val):
                result = self.weather._format_temperature_safe(input_val)
                self.assertEqual(result, expected, 
                               f"Input {input_val!r} should produce {expected!r}, got {result!r}")
    
    def test_safe_temp_string_filtering(self):
        """Test that _safe_temp_string properly filters N/A values for data processing"""
        test_cases = [
            # (input, expected_output)
            (None, ""),
            ("", ""),
            ("N/A", ""),
            ("n/a", ""),
            ("NA", ""),
            ("na", ""),
            ("??", ""),
            ("None", ""),
            ("NONE", ""),
            ("null", ""),
            ("NULL", ""),
            ("undefined", ""),
            # New edge cases
            ("no_data", ""),
            ("ERROR", ""),
            ("timeout", ""),
            ("#N/A", ""),
            ("25", "25"),
            ("25.5", "25"),
            (" 30 ", "30"),
            ("invalid", ""),
            (42, "42"),
            (32.0, "32"),
        ]
        
        for input_val, expected in test_cases:
            with self.subTest(input=input_val):
                result = self.weather._safe_temp_string(input_val)
                self.assertEqual(result, expected, 
                               f"Input {input_val!r} should produce {expected!r}, got {result!r}")
    
    def test_canadian_forecast_no_na_values(self):
        """Test that Canadian forecasts don't contain N/A values"""
        canadian_locations = ["Toronto,ON", "Montreal,QC", "Vancouver,BC", "Calgary,AB"]
        
        for location in canadian_locations:
            with self.subTest(location=location):
                weather = wxmeow(location)
                
                # Check temperatures
                if hasattr(weather, 'meowtp'):
                    for i, temp in enumerate(weather.meowtp):
                        self.assertNotIn('N/A', str(temp), 
                                       f"Found N/A in temperature {i} for {location}: {temp}")
                        self.assertNotIn('n/a', str(temp), 
                                       f"Found n/a in temperature {i} for {location}: {temp}")
                
                # Check HTML output
                if hasattr(weather, 'futuremeow') and weather.futuremeow:
                    self.assertNotIn('N/A', weather.futuremeow,
                                   f"Found N/A in HTML output for {location}")
                    self.assertNotIn('n/a', weather.futuremeow,
                                   f"Found n/a in HTML output for {location}")

if __name__ == '__main__':
    unittest.main()