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


def save_meow(meow: Any) -> bool:
    """
    Save a meow object to a pickle file.

    Args:
        meow: The weather object to save

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        pickle_name = meow.location + ".pkl"
        with open(pickle_name, 'wb') as pkl:
            pickle.dump(meow, pkl)
        logger.debug(f"Successfully saved weather data for {meow.location}")
        return True
    except Exception as e:
        location = getattr(meow, 'location', 'unknown')
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
    pickle_name = location + ".pkl"

    try:
        if not os.path.exists(pickle_name):
            logger.debug(f"Pickle file {pickle_name} does not exist")
            return None, None

        pickle_age = (time.time() - os.path.getmtime(pickle_name)) / 60
        with open(pickle_name, 'rb') as pkl:
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
