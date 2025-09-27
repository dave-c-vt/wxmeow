"""
Location Service for wxmeow.
Uses Nominatim from OpenStreetMap to geocode locations.
"""

import logging
import time
import urllib.parse
import urllib.request
import json
from typing import Dict, Tuple, Optional, List, Any, Union
import re
from urllib.error import URLError

# Configure logger
logger = logging.getLogger("wxmeow")


class LocationServiceError(Exception):
    """Base exception for location service errors"""

    pass


class GeocodeError(LocationServiceError):
    """Exception raised when geocoding fails"""

    pass


class LocationService:
    """Service for geocoding locations using Nominatim from OpenStreetMap"""

    BASE_URL = "https://nominatim.openstreetmap.org/search"
    USER_AGENT = "wxmeow/1.0"

    def __init__(self):
        # Add rate limiting to respect Nominatim's usage policy
        self.last_request_time = 0
        self.min_delay = 1.0  # minimum 1 second between requests

    def _make_request(self, params: Dict[str, str]) -> List[Dict[str, Any]]:
        """Make a request to the Nominatim API with rate limiting"""
        # Respect rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_delay:
            time.sleep(self.min_delay - time_since_last)

        # Build the URL
        query_string = urllib.parse.urlencode(params)
        url = f"{self.BASE_URL}?{query_string}"

        # Make the request
        logger.debug(f"Making request to: {url}")
        try:
            headers = {"User-Agent": self.USER_AGENT}
            request = urllib.request.Request(url, headers=headers)

            with urllib.request.urlopen(request) as response:
                self.last_request_time = time.time()
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    return data
                else:
                    logger.error(f"Error from Nominatim API: {response.status}")
                    raise GeocodeError(
                        f"Geocoding API returned status {response.status}"
                    )

        except urllib.error.URLError as e:
            logger.error(f"Error connecting to Nominatim: {e}")
            raise GeocodeError(f"Error connecting to geocoding service: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            raise GeocodeError(f"Error parsing geocoding service response: {str(e)}")

    def geocode(self, location: str) -> Optional[Tuple[float, float]]:
        """
        Geocode a location string to latitude and longitude.

        Args:
            location: Location string (e.g., "New York, NY" or "Paris, France")

        Returns:
            Tuple of (latitude, longitude) if successful, None otherwise
        """
        # Check if the input is already lat/lon coordinates
        lat_lon = self._parse_latlon(location)
        if lat_lon:
            return lat_lon

        # Check if the input is a zip code
        if self._is_zip_code(location):
            params = {
                "postalcode": location.strip(),
                "format": "json",
                "limit": "1",
                "countrycodes": "us",  # Assuming US zip codes
            }
        else:
            # Otherwise treat as a free-form location search
            params = {
                "q": location.strip(),
                "format": "json",
                "limit": "1",
            }

        results = self._make_request(params)

        if not results:
            logger.info(f"No results found for location: {location}")
            return None

        try:
            latitude = float(results[0]["lat"])
            longitude = float(results[0]["lon"])
            display_name = results[0].get("display_name", "Unknown location")
            logger.info(
                f"Found coordinates for '{location}': {latitude}, {longitude} ({display_name})"
            )
            return (latitude, longitude)
        except (KeyError, ValueError) as e:
            logger.error(f"Error extracting coordinates from response: {e}")
            return None

    def _parse_latlon(self, location: str) -> Optional[Tuple[float, float]]:
        """
        Check if the input string is already in latitude,longitude format.

        Args:
            location: String to check

        Returns:
            Tuple of (latitude, longitude) if it's a valid format, None otherwise
        """
        # Try to match patterns like "40.7128, -74.0060" or "40.7128,-74.0060"
        pattern = r"^\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*$"
        match = re.match(pattern, location)

        if match:
            try:
                lat = float(match.group(1))
                lon = float(match.group(2))

                # Basic validation of latitude and longitude values
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return (lat, lon)
            except ValueError:
                pass

        return None

    def _is_zip_code(self, location: str) -> bool:
        """
        Check if the input string looks like a US zip code.

        Args:
            location: String to check

        Returns:
            True if it looks like a US zip code, False otherwise
        """
        # Simple pattern for US zip codes (5 digits or ZIP+4)
        pattern = r"^\d{5}(-\d{4})?$"
        return bool(re.match(pattern, location.strip()))

    def get_suggestions(self, query: str, limit: int = 5) -> List[Dict[str, str]]:
        """
        Get location suggestions based on a partial query string.

        Uses Nominatim's search with autocomplete.

        Args:
            query: The partial location name
            limit: Maximum number of results to return

        Returns:
            List of dictionaries with location suggestions
        """
        if len(query) < 3:
            return []

        params = {
            "q": query.strip(),
            "format": "json",
            "addressdetails": "1",
            "limit": str(limit * 2),  # Request more results to allow for better sorting
            "namedetails": "1",
        }

        try:
            results = self._make_request(params)
            suggestions = []

            for result in results:
                # Extract the display name and coordinates
                name = result.get("display_name", "")
                lat = result.get("lat")
                lon = result.get("lon")

                # Format a shorter, more user-friendly label
                label = name
                address = result.get("address", {})

                # Try to create a more concise label
                if address:
                    city = address.get(
                        "city", address.get("town", address.get("village", ""))
                    )
                    state = address.get("state", "")
                    country = address.get("country", "")

                    if city and state and country:
                        label = f"{city}, {state}, {country}"
                    elif city and country:
                        label = f"{city}, {country}"

                # Store city for sorting
                primary_name = (
                    city if city else (label.split(",")[0] if "," in label else label)
                )

                suggestions.append(
                    {
                        "label": label,
                        "value": name,
                        "lat": lat,
                        "lon": lon,
                        "primary_name": primary_name,
                    }
                )

            # Sort suggestions to prioritize prefix matches
            query_lower = query.lower()

            # Custom sort function to prioritize:
            # 1. Exact prefix matches with city/town name
            # 2. Contains matches
            # 3. Nominatim's original ranking
            def sort_key(item):
                primary = item.get("primary_name", "")
                if not primary:
                    return (2, 0)

                primary_lower = primary.lower()

                # Exact prefix match
                if primary_lower.startswith(query_lower):
                    # Calculate how much of the string matches (100% is best)
                    match_ratio = len(query_lower) / len(primary_lower)
                    return (0, -match_ratio)

                # Contains match
                if query_lower in primary_lower:
                    return (1, 0)

                # Fall back to original order
                return (2, 0)

            # Sort suggestions and limit results
            sorted_suggestions = sorted(suggestions, key=sort_key)[:limit]

            # Remove the sorting fields before returning
            for suggestion in sorted_suggestions:
                if "primary_name" in suggestion:
                    del suggestion["primary_name"]

            return sorted_suggestions

        except URLError as e:
            logger.error(f"Network error getting suggestions: {e}")
            return []
        except Exception as e:
            logger.error(f"Error getting suggestions: {e}")
            return []

    def reverse_geocode(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Convert latitude and longitude to a human-readable address.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Dictionary with address components if successful, None otherwise
        """
        # Use the reverse geocoding endpoint
        base_url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "lat": str(lat),
            "lon": str(lon),
            "format": "json",
            "addressdetails": "1",
        }

        # Build the URL
        query_string = urllib.parse.urlencode(params)
        url = f"{base_url}?{query_string}"

        # Make the request
        logger.debug(f"Making reverse geocoding request to: {url}")
        try:
            # Respect rate limiting
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.min_delay:
                time.sleep(self.min_delay - time_since_last)

            headers = {"User-Agent": self.USER_AGENT}
            request = urllib.request.Request(url, headers=headers)

            with urllib.request.urlopen(request) as response:
                self.last_request_time = time.time()
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    return data
                else:
                    logger.error(f"Error from Nominatim reverse API: {response.status}")
                    return None

        except urllib.error.URLError as e:
            logger.error(f"Error connecting to Nominatim reverse: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing reverse geocoding JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Error in reverse geocoding: {e}")
            return None


# Create a singleton instance for use throughout the application
location_service = LocationService()


def get_coordinates(location_str: str) -> Optional[Tuple[float, float]]:
    """
    Convenience function to get coordinates from a location string.

    Args:
        location_str: Location string (city, address, zip, etc.)

    Returns:
        Tuple of (latitude, longitude) if successful, None otherwise
    """
    return location_service.geocode(location_str)


def get_location_name(lat: float, lon: float) -> str:
    """
    Get a user-friendly location name from coordinates.

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        A formatted location name (city, state, country) or the coordinates as string if not found
    """
    location_data = location_service.reverse_geocode(lat, lon)

    if not location_data:
        return f"{lat}, {lon}"

    # Try to format a nice location name from the response
    try:
        # Get the address details
        address = location_data.get("address", {})

        # For US locations, prefer "City, State" format
        if address.get("country_code") == "us" and address.get("state"):
            city = address.get("city", address.get("town", address.get("village", "")))
            if city:
                return f"{city}, {address['state']}"

        # For international locations with city and country
        city = address.get(
            "city",
            address.get("town", address.get("village", address.get("suburb", ""))),
        )
        country = address.get("country", "")

        if city and country:
            return f"{city}, {country}"

        # If we can't extract structured components, fall back to display_name
        # but try to shorten it
        if "display_name" in location_data:
            display_name = location_data["display_name"]
            # If it's too long, try to shorten it
            if len(display_name) > 50:
                parts = display_name.split(", ")
                if len(parts) > 3:
                    return ", ".join([parts[0], parts[-2], parts[-1]])
            return display_name

        # Last resort
        return f"{lat}, {lon}"
    except Exception as e:
        logger.error(f"Error formatting location name: {e}")
        return f"{lat}, {lon}"
