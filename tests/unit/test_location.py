#!/usr/bin/env python3
"""
Test script for the wxmeow location service.

This script tests the location service's ability to geocode various types of locations
including cities, zip codes, and coordinates.
"""

import sys
import os
from pathlib import Path
import pytest

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent.parent.absolute()
sys.path.append(str(project_root))

from wxmeow.location_service import get_coordinates, get_location_name


@pytest.mark.unit
@pytest.mark.parametrize(
    "location_str",
    [
        # Cities
        "New York, NY",
        "Chicago",
        "San Francisco, CA",
        "Los Angeles",
        "Miami, FL",
        # Zip codes
        "10001",  # New York
        "60601",  # Chicago
        "90210",  # Beverly Hills
        # Coordinates
        "40.7128,-74.0060",  # New York
        "41.8781, -87.6298",  # Chicago with space
    ],
)
def test_valid_locations(location_str):
    """Test geocoding valid location strings."""
    coords = get_coordinates(location_str)
    assert coords is not None, f"Could not find coordinates for: {location_str}"

    lat, lon = coords
    assert isinstance(lat, float), "Latitude should be a float"
    assert isinstance(lon, float), "Longitude should be a float"
    assert -90 <= lat <= 90, "Latitude should be between -90 and 90"
    assert -180 <= lon <= 180, "Longitude should be between -180 and 180"

    # Try to get a human-readable name
    location_name = get_location_name(lat, lon)
    assert location_name is not None, "Should get a location name for valid coordinates"
    assert isinstance(location_name, str), "Location name should be a string"
    assert len(location_name) > 0, "Location name should not be empty"


@pytest.mark.unit
@pytest.mark.parametrize(
    "invalid_location",
    [
        "NonexistentCity12345",
        "ABC123",
        "1000.5,200.3",  # Invalid coordinates
        "",  # Empty string
    ],
)
def test_invalid_locations(invalid_location):
    """Test geocoding invalid location strings."""
    coords = get_coordinates(invalid_location)
    # Should either return None or raise an exception for invalid locations
    if coords is not None:
        lat, lon = coords
        # If coordinates are returned, they should at least be valid ranges
        assert -90 <= lat <= 90, "Latitude should be between -90 and 90"
        assert -180 <= lon <= 180, "Longitude should be between -180 and 180"


@pytest.mark.unit
def test_coordinate_parsing():
    """Test that coordinate strings are parsed correctly."""
    # Test various coordinate formats
    coords = get_coordinates("40.7128,-74.0060")
    assert coords is not None
    lat, lon = coords
    assert abs(lat - 40.7128) < 0.01, "Latitude should be approximately 40.7128"
    assert abs(lon - (-74.0060)) < 0.01, "Longitude should be approximately -74.0060"

    # Test with spaces
    coords = get_coordinates("41.8781, -87.6298")
    assert coords is not None
    lat, lon = coords
    assert abs(lat - 41.8781) < 0.01, "Latitude should be approximately 41.8781"
    assert abs(lon - (-87.6298)) < 0.01, "Longitude should be approximately -87.6298"


@pytest.mark.unit
def test_reverse_geocoding():
    """Test reverse geocoding (coordinates to location name)."""
    # Test known coordinates (New York)
    location_name = get_location_name(40.7128, -74.0060)
    assert location_name is not None, "Should get a location name"
    assert isinstance(location_name, str), "Location name should be a string"
    assert len(location_name) > 0, "Location name should not be empty"

    # Should contain some reference to New York area
    location_lower = location_name.lower()
    assert any(
        term in location_lower for term in ["new york", "ny", "manhattan", "brooklyn"]
    ), f"Location name '{location_name}' should reference New York area"
