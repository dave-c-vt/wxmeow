#!/usr/bin/env python3

import unittest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from wxmeow.wx2json_noaa import wxmeow

class TestEnhancedNAProtection(unittest.TestCase):
    """Test the enhanced N/A protection system"""
    
    def setUp(self):
        """Set up a weather instance for testing"""
        self.weather = wxmeow("Toronto,ON")
    
    def test_validate_forecast_json_with_na_values(self):
        """Test that _validate_forecast_json properly filters N/A values"""
        # Create test forecast data with various N/A patterns
        test_forecast = [
            {
                'date': '2026-01-29',
                'condition': 'Sunny',
                'high': 25,
                'low': 15,
                'precip': 0
            },
            {
                'date': '2026-01-30', 
                'condition': 'N/A',  # Should be filtered
                'high': 'n/a',       # Should be filtered
                'low': 'N/A',        # Should be filtered  
                'precip': 'null'     # Should be filtered
            },
            {
                'date': '2026-01-31',
                'condition': 'error: timeout',  # Should be filtered
                'high': 'invalid',              # Should be filtered
                'low': '??',                    # Should be filtered
                'precip': 'unavailable'         # Should be filtered
            },
            {
                'date': '2026-02-01',
                'condition': 'Cloudy',
                'high': '30',          # Should be converted to int
                'low': 20.5,          # Should be converted to int  
                'precip': '5'         # Should work
            }
        ]
        
        # Run validation
        validated = self.weather._validate_forecast_json(test_forecast)
        
        # Check that we got the right number of items
        self.assertEqual(len(validated), 4)
        
        # Item 0 - should be unchanged (valid data)
        self.assertEqual(validated[0]['condition'], 'Sunny')
        self.assertEqual(validated[0]['high'], 25)
        self.assertEqual(validated[0]['low'], 15)
        self.assertEqual(validated[0]['precip'], 0)
        
        # Item 1 - N/A values should be filtered
        self.assertEqual(validated[1]['condition'], 'Unknown')  # N/A -> Unknown
        self.assertIsNone(validated[1]['high'])               # n/a -> None
        self.assertIsNone(validated[1]['low'])                # N/A -> None
        self.assertEqual(validated[1]['precip'], 0)           # null -> 0
        
        # Item 2 - error/invalid patterns should be filtered
        self.assertEqual(validated[2]['condition'], 'Unknown')  # error -> Unknown  
        self.assertIsNone(validated[2]['high'])               # invalid -> None
        self.assertIsNone(validated[2]['low'])                # ?? -> None
        self.assertEqual(validated[2]['precip'], 0)           # unavailable -> 0
        
        # Item 3 - valid string numbers should be converted
        self.assertEqual(validated[3]['condition'], 'Cloudy')
        self.assertEqual(validated[3]['high'], 30)            # '30' -> 30
        self.assertEqual(validated[3]['low'], 20)             # 20.5 -> 20  
        
    def test_comprehensive_na_patterns(self):
        """Test various N/A patterns that might appear in real data"""
        na_patterns = [
            'N/A', 'n/a', 'NA', 'na', 'null', 'NULL', 'undefined', 'UNDEFINED',
            'NaN', 'nan', 'None', 'NONE', '??', '???', 'error', 'ERROR',
            'fail', 'FAIL', 'invalid', 'INVALID', 'unavailable', 'UNAVAILABLE',
            'timeout', 'TIMEOUT', '--', '---', 'n.a.', 'N.A.',
            'no data', 'NO DATA', 'not available', 'NOT AVAILABLE'
        ]
        
        for pattern in na_patterns:
            with self.subTest(pattern=pattern):
                test_forecast = [{
                    'date': '2026-01-29',
                    'condition': pattern,
                    'high': pattern,
                    'low': pattern,
                    'precip': pattern
                }]
                
                validated = self.weather._validate_forecast_json(test_forecast)
                
                # All N/A patterns should be cleaned
                self.assertEqual(validated[0]['condition'], 'Unknown')
                self.assertIsNone(validated[0]['high'])
                self.assertIsNone(validated[0]['low']) 
                self.assertEqual(validated[0]['precip'], 0)
    
    def test_temperature_range_validation(self):
        """Test that extreme temperatures are filtered out"""
        extreme_temps = [-300, 300, -999, 999, 1000]
        
        for temp in extreme_temps:
            with self.subTest(temp=temp):
                test_forecast = [{
                    'date': '2026-01-29',
                    'condition': 'Test',
                    'high': temp,
                    'low': temp,
                    'precip': 0
                }]
                
                validated = self.weather._validate_forecast_json(test_forecast)
                
                # Extreme temperatures should be filtered to None
                self.assertIsNone(validated[0]['high'])
                self.assertIsNone(validated[0]['low'])
    
    def test_canadian_locations_no_na_in_output(self):
        """Test that Canadian locations never produce N/A in their output"""
        canadian_locations = ["Toronto,ON", "Montreal,QC", "Vancouver,BC", "Calgary,AB", "Winnipeg,MB"]
        
        for location in canadian_locations:
            with self.subTest(location=location):
                weather = wxmeow(location)
                
                # Check that meowforecast (JSON) doesn't contain N/A patterns
                if hasattr(weather, 'meowforecast') and weather.meowforecast:
                    import json
                    forecast_json = json.dumps(weather.meowforecast)
                    
                    # Check for N/A patterns in string values (not null)
                    na_patterns = ['\"N/A\"', '\"n/a\"', '\"NA\"', '\"na\"', '\"error\"', '\"fail\"', '\"invalid\"', '\"??\"']
                    
                    for pattern in na_patterns:
                        self.assertNotIn(pattern, forecast_json, 
                                       f"Found {pattern} in forecast JSON for {location}")

if __name__ == '__main__':
    unittest.main()