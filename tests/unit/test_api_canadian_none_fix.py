#!/usr/bin/env python3
"""
Test that the API properly handles None values in Canadian forecasts
"""

import unittest
import json
from wxmeow import create_app


class TestAPICanadianNoneFix(unittest.TestCase):
    """Test API response for Canadian locations doesn't contain None values"""

    def setUp(self):
        """Set up test client"""
        self.app = create_app()
        self.client = self.app.test_client()

    def test_canadian_weather_api_no_none_values(self):
        """Test that Canadian weather API responses don't contain None temperature values"""
        canadian_locations = ["Toronto,ON", "Montreal,QC", "Vancouver,BC", "Calgary,AB"]
        
        for location in canadian_locations:
            with self.subTest(location=location):
                response = self.client.get(f'/api/weather/{location}')
                self.assertEqual(response.status_code, 200)
                
                data = json.loads(response.data)
                
                # Check that forecast data exists
                self.assertIn('forecast', data)
                
                # Check each forecast item for None values
                for item in data.get('forecast', []):
                    temp = item.get('temperature', {})
                    high = temp.get('high')
                    low = temp.get('low')
                    
                    # None values should be converted to em dash or reasonable value
                    self.assertNotEqual(high, None, f"Found None high temperature in {location} forecast")
                    self.assertNotEqual(low, None, f"Found None low temperature in {location} forecast")
                    
                    # Should not contain string "None" either
                    self.assertNotEqual(str(high).lower(), 'none', f"Found 'None' string in high temp for {location}")
                    self.assertNotEqual(str(low).lower(), 'none', f"Found 'None' string in low temp for {location}")

    def test_canadian_forecast_api_no_none_values(self):
        """Test that Canadian forecast API endpoint doesn't contain None temperature values"""
        canadian_locations = ["Toronto,ON", "Montreal,QC", "Vancouver,BC", "Calgary,AB"]
        
        for location in canadian_locations:
            with self.subTest(location=location):
                response = self.client.get(f'/api/forecast/{location}')
                self.assertEqual(response.status_code, 200)
                
                data = json.loads(response.data)
                
                # Check that daily forecast data exists
                self.assertIn('daily_forecast', data)
                
                # Check each forecast item for None values
                for item in data.get('daily_forecast', []):
                    temp = item.get('temperature', {})
                    high = temp.get('high')
                    low = temp.get('low')
                    
                    # None values should be converted to em dash or reasonable value
                    self.assertNotEqual(high, None, f"Found None high temperature in {location} forecast")
                    self.assertNotEqual(low, None, f"Found None low temperature in {location} forecast")


if __name__ == "__main__":
    unittest.main()