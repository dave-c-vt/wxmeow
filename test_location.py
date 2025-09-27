#!/usr/bin/env python3
"""
Test script for the wxmeow location service.

This script tests the location service's ability to geocode various types of locations
including cities, zip codes, and coordinates.

Usage:
    python test_location.py
"""

import sys
import os
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).parent.absolute()
sys.path.append(str(project_root))

from wxmeow.location_service import get_coordinates, get_location_name


def test_location(location_str):
    """Test geocoding a location string."""
    print(f"\nTesting location: '{location_str}'")

    try:
        coords = get_coordinates(location_str)
        if coords:
            lat, lon = coords
            print(f"✅ Found coordinates: {lat}, {lon}")

            # Try to get a human-readable name
            location_name = get_location_name(lat, lon)
            print(f"📍 Location name: {location_name}")
            return True
        else:
            print(f"❌ Could not find coordinates for: {location_str}")
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def run_tests():
    """Run a series of location tests."""
    print("🔍 Testing wxmeow location service...\n")

    # Test cases
    test_cases = [
        # Cities
        "New York, NY",
        "Chicago",
        "San Francisco, CA",
        "Los Angeles",
        "Miami, FL",
        "Paris, France",
        "London, UK",
        "Tokyo, Japan",
        "Sydney, Australia",
        # Zip codes
        "10001",  # New York
        "60601",  # Chicago
        "90210",  # Beverly Hills
        # Coordinates
        "40.7128,-74.0060",  # New York
        "41.8781, -87.6298",  # Chicago with space
        # Invalid inputs
        "NonexistentCity12345",
        "ABC123",
        "1000.5,200.3",  # Invalid coordinates
    ]

    results = []
    for location in test_cases:
        success = test_location(location)
        results.append((location, success))

    # Print summary
    print("\n--- Summary ---")
    successful = sum(1 for _, success in results if success)
    print(f"Total tests: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(results) - successful}")

    # Print failures
    if len(results) - successful > 0:
        print("\nFailed locations:")
        for location, success in results:
            if not success:
                print(f"- {location}")


if __name__ == "__main__":
    run_tests()
