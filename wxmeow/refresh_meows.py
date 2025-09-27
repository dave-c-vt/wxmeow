from typing import List, Optional
import glob
import os
import shutil
import sys
import time
import traceback

try:
    from wxmeow import logger
    from . import wx2json_noaa as wx
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())
    import wx2json_noaa as wx

# Import exception classes or define locally if needed
try:
    from .wx2json_noaa import WeatherDataError
except ImportError:
    class WeatherDataError(Exception):
        pass

try:
    from .pickler import CacheReadError, CacheWriteError
except ImportError:
    class CacheReadError(Exception):
        def __init__(self, cache_key, message=None):
            self.cache_key = cache_key
            self.message = message
            super().__init__(f"Cache read error: {cache_key} - {message}" if message else f"Cache read error: {cache_key}")

    class CacheWriteError(Exception):
        def __init__(self, cache_key, message=None):
            self.cache_key = cache_key
            self.message = message
            super().__init__(f"Cache write error: {cache_key} - {message}" if message else f"Cache write error: {cache_key}")

def refresh_meows(max_age_seconds: int = 600) -> List[str]:
    """
    Refresh weather data for locations with stale pickle files.

    Args:
        max_age_seconds: Maximum age in seconds before refreshing a pickle file

    Returns:
        List of locations that were refreshed
    """
    ext = ".pkl"
    refreshed_locations: List[str] = []

    try:
        files = sorted(glob.glob("../*" + ext))
        now = time.time()

        for f in files:
            try:
                # Extract location from filename
                loc = f.split("/")[1].split(".")[0]

                # Check if file is older than max_age_seconds
                try:
                    file_age = now - os.path.getmtime(f)
                    if file_age > max_age_seconds:
                        logger.info(f"Refreshing {loc} (age: {file_age/60:.1f} min)")

                        try:
                            # Create new weather data
                            meow = wx.wxmeow(loc)

                            # Move file (with backup)
                            try:
                                shutil.move(f.split("/")[1], f)
                                refreshed_locations.append(loc)
                            except (shutil.Error, IOError) as e:
                                logger.error(f"Error moving file for {loc}: {str(e)}")
                                raise CacheWriteError(loc, f"File move error: {str(e)}")
                        except WeatherDataError as e:
                            logger.error(f"Weather data error for {loc}: {str(e)}")
                        except (CacheReadError, CacheWriteError) as e:
                            logger.error(f"Cache error for {loc}: {str(e)}")
                        except Exception as e:
                            logger.error(f"Unexpected error for {loc}: {str(e)}")
                except OSError as e:
                    logger.error(f"Error accessing file {f}: {str(e)}")
            except Exception as e:
                logger.error(f"Error processing {f}: {str(e)}")
                logger.debug(traceback.format_exc())
    except Exception as e:
        logger.error(f"Error in refresh_meows: {str(e)}")
        logger.debug(traceback.format_exc())

    return refreshed_locations

if __name__ == "__main__":
    # Allow custom max age from command line
    max_age = 600  # Default: 10 minutes
    if len(sys.argv) > 1:
        try:
            max_age = int(sys.argv[1])
        except ValueError:
            logger.error(f"Invalid max age: {sys.argv[1]}. Using default: 600 seconds")

    refreshed = refresh_meows(max_age)
    logger.info(f"Refreshed {len(refreshed)} locations")
