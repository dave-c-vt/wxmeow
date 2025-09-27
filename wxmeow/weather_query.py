from typing import Any, Optional, cast
import csv
import json
import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import traceback
from pathlib import Path

try:
    from wxmeow import logger
except ImportError:
    import logging

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())

from wxmeow.location_service import get_coordinates


# Define exception classes for weather queries
class ApiError(Exception):
    def __init__(
        self, message: str, status_code: Optional[int] = None, url: Optional[str] = None
    ):
        self.status_code: Optional[int] = status_code
        self.url: Optional[str] = url
        super().__init__(message)


class LocationError(Exception):
    def __init__(self, location: str, message: Optional[str] = None):
        self.location: str = location
        self.message: Optional[str] = message
        super().__init__(
            f"Invalid location: {location} - {message}"
            if message
            else f"Invalid location: {location}"
        )


class DataParsingError(Exception):
    def __init__(self, data_type: str, message: Optional[str] = None):
        self.data_type: str = data_type
        self.message: Optional[str] = message
        super().__init__(
            f"Error parsing {data_type} data: {message}"
            if message
            else f"Error parsing {data_type} data"
        )


class WeatherDataError(Exception):
    """Generic error for weather data processing issues."""

    def __init__(self, message: str = "Weather data error"):
        self.message: str = message
        super().__init__(message)


# functions for validating user input --------------
def hasperiod(string: str) -> bool:
    """Check if a string contains a period."""
    return "." in string


def hasnumbers(string: str) -> bool:
    """Check if a string contains any digits."""
    return any(char.isdigit() for char in string)


def iszipcode(string: str) -> bool:
    """Check if a string is a valid zip code (5 digits for US, 6 for Canada)."""
    string = string.replace(" ", "")
    if len(string) == 5 or len(string) == 6:
        return string.isdigit()
    return False


def islatlong(string: str) -> list[str] | bool:
    """
    Check if a string contains valid latitude/longitude coordinates.

    Args:
        string: A string that might contain lat/long coordinates

    Returns:
        List of two strings representing latitude and longitude if valid,
        False otherwise
    """
    arglist = string.replace(",", " ").replace(";", " ").split(" ")
    latlon = [inc for inc in arglist if inc]

    if len(latlon) < 2:
        return False

    try:
        # Check if the first two values are valid floating point numbers
        lat = float(latlon[0])
        lon = float(latlon[1])

        # Basic validation of coordinates
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return [latlon[0], latlon[1]]
        else:
            return False
    except (ValueError, IndexError):
        return False


class geo:
    """Geocoding service using OpenStreetMap Nominatim."""

    def __init__(self, location: str):
        """
        Initialize a geocoding request.

        Args:
            location: Address, zip code, or coordinates to geocode
        """
        self.location: str = location
        coords = get_coordinates(location)
        if coords:
            self.lat = str(coords[0])
            self.lon = str(coords[1])
        else:
            raise LocationError(
                location=location, message=f"Could not geocode location: {location}"
            )


class noaa:
    """
    NOAA Weather API client

    Fetches weather data from the National Weather Service API including:
    - Current conditions from nearby weather stations
    - Forecast data for the specified location
    - Location metadata

    API endpoints:
    - Points: https://api.weather.gov/points/{lat},{lon}
    - Stations: https://api.weather.gov/points/{lat},{lon}/stations
    - Observations: https://api.weather.gov/stations/{stationid}/observations
    - Forecast: https://api.weather.gov/points/{lat},{lon}/forecast
    - Hourly forecast: https://api.weather.gov/points/{lat},{lon}/forecast/hourly
    """

    def __init__(self, location: str):
        """
        Initialize the NOAA API client with a location.

        Args:
            location: Zipcode or lat,lon coordinates
        """
        self.location: str = str(location)
        self.lat: str | None = None
        self.lon: str | None = None
        self.city: str = "wherever"
        self.state: str = "who cares"
        self.station: str | None = None
        self.station_name: str | None = None
        self.station_reserve: str | None = None
        self.station_reserve2: str | None = None
        self.jconditions: dict[str, Any] | None = None
        self.jforecast: dict[str, Any] | None = None
        self.jhourly: dict[str, Any] | None = None

        # Configure requests with retry functionality
        self.session: requests.Session = self._create_request_session()

        # Base URLs for API endpoints
        self.baseurl: str = "https://api.weather.gov/points/"
        self.stationurl: str = "https://api.weather.gov/stations/"
        # Handle zipfile path without Flask dependency
        self.zipfile: str = os.path.join(
            os.path.dirname(__file__), "static", "zips.txt"
        )
        if not os.path.exists(os.path.dirname(self.zipfile)):
            os.makedirs(os.path.dirname(self.zipfile))

        # Get lat/lon from input
        self._get_coordinates()

        # Exit early if we couldn't determine coordinates
        if not self.lat or not self.lon:
            logger.error(f"Could not determine coordinates for location: {location}")
            return

        # Get weather data
        self._fetch_weather_data()

    def _create_request_session(self) -> requests.Session:
        """
        Create a requests session with retry functionality.

        Returns:
            Configured requests Session object
        """
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _get_coordinates(self) -> None:
        """Get latitude and longitude from zip code, coordinates, or city name."""
        # Check if input is already lat,lon
        latlon = islatlong(self.location)
        if isinstance(latlon, list) and len(latlon) >= 2:
            self.lat = latlon[0]
            self.lon = latlon[1]
            return

        # If it's a zipcode, try the zipcode database first
        if iszipcode(self.location):
            self._ensure_zipfile_exists()
            try:
                with open(self.zipfile, "rt") as file:
                    csv_file = csv.reader(file, delimiter=",")
                    for row in csv_file:
                        # Skip empty rows
                        if not row:
                            continue

                        try:
                            # Make sure the row has enough columns
                            if len(row) >= 3 and self.location == row[0]:
                                self.lat = row[1].strip()
                                self.lon = row[2].strip()
                                return
                        except IndexError:
                            continue
            except Exception as e:
                logger.warning(f"Error searching zipcode database: {str(e)}")
                # Continue to try online service

        # If not found in zipcode database, try online geocoding service
        try:
            logger.info(f"Using location service for: {self.location}")
            coords = get_coordinates(self.location)
            if coords:
                self.lat = str(coords[0])
                self.lon = str(coords[1])
                logger.info(
                    f"Found coordinates for {self.location}: {self.lat}, {self.lon}"
                )
                return
            else:
                logger.warning(
                    f"Location service couldn't find coordinates for: {self.location}"
                )
        except Exception as e:
            logger.error(f"Error from location service for {self.location}: {str(e)}")

        # If we get here, we couldn't find coordinates
        if not hasattr(self, "lat") or not self.lat:
            logger.error(f"Unable to find coordinates for {self.location}")
            raise LocationError(
                location=self.location,
                message=f"Could not find coordinates for {self.location}. Try a zip code, latitude/longitude, or a more specific location.",
            )

    def _ensure_zipfile_exists(self) -> None:
        """Download the zip code database if it doesn't exist."""
        if not os.path.exists(self.zipfile):
            z_url = "https://gist.githubusercontent.com/erichurst/7882666/raw/5bdc46db47d9515269ab12ed6fb2850377fd869e/US%2520Zip%2520Codes%2520from%25202013%2520Government%2520Data"
            try:
                response = self.session.get(z_url)
                response.raise_for_status()
                with open(self.zipfile, "wb") as _zipfile:
                    _zipfile.write(response.content)
                logger.info(f"Downloaded zip code database to {self.zipfile}")
            except Exception as e:
                logger.error(f"Failed to download zip code database: {str(e)}")
                raise ApiError(
                    message=f"Failed to download zip code database", url=z_url
                )

    def _fetch_weather_data(self) -> None:
        """Fetch all weather data from the NOAA API."""
        if not self.lat or not self.lon:
            return

        try:
            # First get points data, which contains URLs for other endpoints
            points_url = f"{self.baseurl}{self.lat},{self.lon}"
            points_data = self._make_api_request(points_url)
            if not points_data:
                return

            # Get location data
            self._get_location_data(points_data)

            # Get forecast URL and data
            self._get_forecast_data(points_data)

            # Get stations and observations
            self._get_station_data()

        except Exception as e:
            logger.error(f"Error fetching weather data: {str(e)}")
            logger.debug(traceback.format_exc())
            raise DataParsingError(data_type="weather", message=str(e))

    def _make_api_request(
        self, url: str, required: bool = True
    ) -> dict[str, Any] | None:
        """
        Make a request to the NOAA API with error handling.

        Args:
            url: API endpoint URL
            required: If True, raises ApiError on failure; if False, returns None

        Returns:
            JSON response as dictionary or None if request failed
        """
        response = None
        try:
            response = self.session.get(url, headers={"Accept": "application/json"})
            response.raise_for_status()
            return response.json()
        except Exception as e:
            status_code = getattr(response, "status_code", None) if response else None
            error_msg = f"API request failed for {url}: {str(e)}"

            if required:
                logger.error(error_msg)
                raise ApiError(
                    message=f"API request failed", status_code=status_code, url=url
                )
            else:
                logger.warning(error_msg)
                return None

    def _get_location_data(self, points_data: dict[str, Any]) -> None:
        """
        Extract location data from the points response.

        Args:
            points_data: JSON response from the points API
        """
        try:
            if (
                points_data
                and "properties" in points_data
                and "relativeLocation" in points_data["properties"]
            ):
                rel_location = cast(
                    dict[str, Any],
                    points_data["properties"]["relativeLocation"]["properties"],
                )
                self.city = str(rel_location.get("city", "wherever"))
                self.state = str(rel_location.get("state", "who cares"))
            else:
                logger.warning("Location data not found in API response")
        except Exception as e:
            logger.error(f"Error extracting location data: {str(e)}")
            self.city = "wherever"
            self.state = "who cares"
            raise DataParsingError(data_type="location", message=str(e))

    def _get_forecast_data(self, points_data: dict[str, Any]) -> None:
        """
        Fetch forecast data from the forecast URL in points response.

        Args:
            points_data: JSON response from the points API
        """
        try:
            if "properties" in points_data and "forecast" in points_data["properties"]:
                forecast_url = str(points_data["properties"]["forecast"])
                self.jforecast = self._make_api_request(forecast_url)

                # Also get hourly forecast (but make it optional)
                try:
                    if "forecastHourly" in points_data["properties"]:
                        hourly_url = str(points_data["properties"]["forecastHourly"])
                        self.jhourly = self._make_api_request(
                            hourly_url, required=False
                        )
                    else:
                        logger.warning(
                            "Hourly forecast URL not found in points response"
                        )
                        self.jhourly = None
                except Exception as e:
                    logger.warning(f"Hourly forecast unavailable: {str(e)}")
                    self.jhourly = None  # Continue without hourly forecast
            else:
                logger.warning("Forecast URL not found in API response")
        except Exception as e:
            logger.error(f"Error getting forecast data: {str(e)}")
            raise DataParsingError(data_type="forecast", message=str(e))

    def _get_station_data(self) -> None:
        """Fetch station data and observations."""
        try:
            # Get nearby stations
            stations_url = f"{self.baseurl}{self.lat},{self.lon}/stations"
            stations_data = self._make_api_request(stations_url)

            if (
                not stations_data
                or "features" not in stations_data
                or len(stations_data["features"]) < 3
            ):
                logger.warning("Station data incomplete or missing")
                return

            # Get station IDs for the three closest stations
            stations: list[str] = []
            for i in range(min(3, len(stations_data["features"]))):
                if "id" in stations_data["features"][i]:
                    stations.append(str(stations_data["features"][i]["id"]))

            if len(stations) < 3:
                logger.warning(f"Found only {len(stations)} stations, need 3")
                return

            self.station = stations[0]
            self.station_reserve = stations[1]
            self.station_reserve2 = stations[2]

            if self.station:
                self.station_name = self.station.split("/")[-1]

            # Try to get observations from each station until we find valid data
            self._get_observations_data(stations)

        except Exception as e:
            logger.error(f"Error getting station data: {str(e)}")
            raise DataParsingError(data_type="station", message=str(e))

    def _get_observations_data(self, stations: list[str]) -> None:
        """
        Fetch and validate observations from multiple stations.

        Args:
            stations: List of station URLs to try
        """
        for station in stations:
            try:
                observations_url = f"{station}/observations"
                observations_data = self._make_api_request(observations_url)

                if (
                    observations_data
                    and "features" in observations_data
                    and observations_data["features"]
                ):
                    # Verify we have temperature data
                    try:
                        temp_value = observations_data["features"][0]["properties"][
                            "temperature"
                        ]["value"]
                        if temp_value is not None:
                            self.jconditions = observations_data
                            return
                    except (KeyError, TypeError, IndexError):
                        logger.debug(f"No valid temperature data in station: {station}")
            except Exception as e:
                logger.debug(f"Error getting observations from {station}: {str(e)}")

        logger.warning("Could not find valid observations from any station")

    def format_for_meow(self) -> None:
        """
        Format NOAA response for wxmeow presentation.
        """
        # Implementation to be added when needed
        pass

    # This is a duplicate method, removing it


class openweathermap:
    """
    OpenWeatherMap API client

    API documentation:
    - Forecast: http://openweathermap.org/forecast5
    - Current conditions: http://openweathermap.org/current
    - Icons: https://openweathermap.org/weather-conditions
    """

    baseurl: str = "https://api.openweathermap.org/data/2.5/"
    key: str = ""

    def __init__(self, location: str):
        """
        Initialize the OpenWeatherMap API client.

        Args:
            location: Zipcode, lat,lon coordinates, or city name
        """
        self.location: str = location
        # This class appears to be a placeholder for future implementation

    def locationtype(self) -> str:
        """
        Determine the type of location provided.

        Returns:
            String indicating the type of location: 'zip', 'latlon', or 'city'
        """
        if iszipcode(self.location):
            return "zip"
        elif islatlong(self.location):
            return "latlon"
        else:
            return "city"
