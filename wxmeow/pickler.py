#!/usr/bin/env python

from typing import Tuple, Any, Optional
import os
import pickle
import time
import logging

try:
    from wxmeow import logger
except ImportError:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())


# Define exception classes locally
class CacheReadError(Exception):
    def __init__(self, cache_key: str, message: Optional[str] = None):
        self.cache_key: str = cache_key
        self.message: Optional[str] = message
        msg = f"Could not read from cache: {cache_key}"
        if message:
            msg += f" - {message}"
        super().__init__(msg)


class CacheWriteError(Exception):
    def __init__(self, cache_key: str, message: Optional[str] = None):
        self.cache_key: str = cache_key
        self.message: Optional[str] = message
        msg = f"Could not write to cache: {cache_key}"
        if message:
            msg += f" - {message}"
        super().__init__(msg)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing/replacing problematic characters.

    Args:
        filename: The original filename

    Returns:
        A sanitized filename safe for filesystem use
    """
    # Handle None or empty strings
    if not filename or not filename.strip():
        return "unknown_location"

    # Replace problematic characters
    sanitized = str(filename)
    # Remove or replace commas, spaces, and other problematic characters
    sanitized = sanitized.replace(",", "_")
    sanitized = sanitized.replace(" ", "_")
    sanitized = sanitized.replace("\t", "_")
    sanitized = sanitized.replace("\n", "_")
    sanitized = sanitized.replace("\r", "_")
    # Replace path separators to avoid directory traversal
    sanitized = sanitized.replace("/", "_")
    sanitized = sanitized.replace("\\", "_")
    # Replace other potentially problematic characters
    sanitized = sanitized.replace(":", "_")
    sanitized = sanitized.replace("*", "_")
    sanitized = sanitized.replace("?", "_")
    sanitized = sanitized.replace('"', "_")
    sanitized = sanitized.replace("<", "_")
    sanitized = sanitized.replace(">", "_")
    sanitized = sanitized.replace("|", "_")

    # Remove multiple consecutive underscores
    while "__" in sanitized:
        sanitized = sanitized.replace("__", "_")

    # Remove leading/trailing underscores
    sanitized = sanitized.strip("_")

    # Ensure we don't end up with an empty string
    if not sanitized:
        sanitized = "unknown_location"

    return sanitized


def save_meow(meow: Any) -> bool:
    """
    Save a meow object to a pickle file.

    Args:
        meow: The weather object to save

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        sanitized_location = sanitize_filename(meow.location)
        pickle_name = sanitized_location + ".pkl"
        with open(pickle_name, "wb") as pkl:
            pickle.dump(meow, pkl)
        logger.debug(
            f"Successfully saved weather data for {meow.location} as {pickle_name}"
        )
        return True
    except Exception as e:
        location = getattr(meow, "location", "unknown")
        logger.error(f"Failed to save pickle for {location}: {str(e)}")
        raise CacheWriteError(location, str(e))
        return False


def load_meow(location: str) -> Tuple[Optional[Any], Optional[float]]:
    """
    Load a saved meow object.

    Args:
        location: Location string used as the base of the pickle filename

    Returns:
        Tuple containing:
        - The loaded meow object or None if loading failed
        - The age of the pickle file in minutes or None if loading failed
    """
    sanitized_location = sanitize_filename(location)
    pickle_name = sanitized_location + ".pkl"

    try:
        if not os.path.exists(pickle_name):
            logger.debug(f"Pickle file {pickle_name} does not exist")
            return None, None

        pickle_age = (time.time() - os.path.getmtime(pickle_name)) / 60
        with open(pickle_name, "rb") as pkl:
            meow = pickle.load(pkl)
        logger.debug(f"Loaded pickle for {location}, age: {pickle_age:.1f} minutes")
        return meow, pickle_age
    except (FileNotFoundError, PermissionError) as e:
        logger.error(f"File access error for {pickle_name}: {str(e)}")
        raise CacheReadError(location, f"File access error: {str(e)}")
        return None, None
    except pickle.UnpicklingError as e:
        logger.error(f"Unpickling error for {pickle_name}: {str(e)}")
        raise CacheReadError(location, f"Unpickling error: {str(e)}")
        return None, None
    except Exception as e:
        logger.error(f"Unexpected error loading {pickle_name}: {str(e)}")
        raise CacheReadError(location, f"Unexpected error: {str(e)}")
        return None, None


def test_filename_sanitization():
    """Test the filename sanitization function with various inputs."""
    test_cases = [
        ("New York, NY", "New_York_NY"),
        ("San Francisco, CA 94102", "San_Francisco_CA_94102"),
        ("Chicago, IL", "Chicago_IL"),
        ("lat:40.7128,lon:-74.0060", "lat_40.7128_lon_-74.0060"),
        ("Austin, TX\t78701", "Austin_TX_78701"),
        ("Boston\nMA", "Boston_MA"),
        ("Seattle/WA", "Seattle_WA"),
        ("Miami\\FL", "Miami_FL"),
        ("Denver:CO", "Denver_CO"),
        ("Portland*OR", "Portland_OR"),
        ("Phoenix?AZ", "Phoenix_AZ"),
        ('"Las Vegas, NV"', "_Las_Vegas_NV_"),
        ("Salt<Lake>City|UT", "Salt_Lake_City_UT"),
        ("  Spaces  Everywhere  ", "Spaces_Everywhere"),
        ("Multiple___Underscores", "Multiple_Underscores"),
        ("", "unknown_location"),
        ("   ", "unknown_location"),
        ("____", "unknown_location"),
        (None, "unknown_location"),
    ]

    print("Testing filename sanitization:")
    for original, expected in test_cases:
        try:
            result = sanitize_filename(original)
            status = "PASS" if result == expected else "FAIL"
            print(f"{status} '{original}' -> '{result}' (expected: '{expected}')")
        except Exception as e:
            print(f"FAIL '{original}' -> ERROR: {e}")

    return True


if __name__ == "__main__":
    test_filename_sanitization()
