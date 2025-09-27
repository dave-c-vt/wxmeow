"""
Custom exceptions for wxmeow application.

This module defines exception classes that are specific to the wxmeow application,
providing more descriptive error handling and more precise exception catching.
"""
from typing import Optional


class WxMeowException(Exception):
    """Base exception for all wxmeow-specific exceptions."""
    pass


class WeatherDataError(WxMeowException):
    """Raised when there's an issue with weather data retrieval or processing."""
    pass


class ApiError(WeatherDataError):
    """Raised when there's an issue with API communication."""
    def __init__(self, message: str, status_code: Optional[int] = None, url: Optional[str] = None):
        self.status_code = status_code
        self.url = url
        super().__init__(f"{message} (Status: {status_code}, URL: {url})")


class LocationError(WeatherDataError):
    """Raised when a location cannot be found or geocoded."""
    def __init__(self, location: str, message: Optional[str] = None):
        self.location = location
        msg = f"Invalid location: {location}"
        if message:
            msg += f" - {message}"
        super().__init__(msg)


class DataParsingError(WeatherDataError):
    """Raised when weather data cannot be parsed correctly."""
    def __init__(self, data_type: str, message: Optional[str] = None):
        self.data_type = data_type
        msg = f"Error parsing {data_type} data"
        if message:
            msg += f": {message}"
        super().__init__(msg)


class CacheError(WxMeowException):
    """Raised when there's an issue with the cache."""
    pass


class CacheReadError(CacheError):
    """Raised when a cached item cannot be read."""
    def __init__(self, cache_key: str, message: Optional[str] = None):
        self.cache_key = cache_key
        msg = f"Could not read from cache: {cache_key}"
        if message:
            msg += f" - {message}"
        super().__init__(msg)


class CacheWriteError(CacheError):
    """Raised when a cached item cannot be written."""
    def __init__(self, cache_key: str, message: Optional[str] = None):
        self.cache_key = cache_key
        msg = f"Could not write to cache: {cache_key}"
        if message:
            msg += f" - {message}"
        super().__init__(msg)
