"""
Background weather refresh for wxmeow.

Refreshes cached weather data for locations that have been viewed in the
last 3 days. Meant to run as a daemon thread inside the Flask app so that
fresh data is ready immediately when a user revisits a location.
"""

import glob
import logging
import os
import sys
import time
import traceback
from typing import List

try:
    from wxmeow import logger
except ImportError:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())


# Age thresholds
_THREE_DAYS_SECONDS = 3 * 24 * 60 * 60
_DEFAULT_REFRESH_SECONDS = 30 * 60  # 30 minutes


def refresh_meows(max_age_seconds: int = _DEFAULT_REFRESH_SECONDS) -> List[str]:
    """
    Refresh weather data for recently-viewed locations.

    A location is eligible for refresh when:
    - Its pickle file is older than max_age_seconds (stale), AND
    - It was viewed within the last 3 days (file mtime < 3 days ago)

    The wxmeow() constructor saves fresh data to cache automatically, so
    no explicit save step is needed here.

    Args:
        max_age_seconds: Minimum age in seconds before refreshing (default: 30 min)

    Returns:
        List of location strings that were refreshed.
    """
    # Import here to avoid circular imports at module load time
    try:
        from wxmeow import wx2json_noaa as wx
    except ImportError:
        import wx2json_noaa as wx  # type: ignore

    refreshed: List[str] = []
    now = time.time()
    cutoff_recent = now - _THREE_DAYS_SECONDS

    try:
        pkl_files = glob.glob("*.pkl")
        logger.info(f"refresh_meows: checking {len(pkl_files)} cached location(s)")

        for pkl_path in pkl_files:
            try:
                mtime = os.path.getmtime(pkl_path)

                # Skip files not viewed in the last 3 days
                if mtime < cutoff_recent:
                    continue

                age_seconds = now - mtime
                if age_seconds < max_age_seconds:
                    continue

                # Derive the location string from the filename
                loc = os.path.splitext(os.path.basename(pkl_path))[0]
                # Reverse the simple sanitization: underscores back to spaces
                # This is lossy but good enough for the refresh use case
                loc_display = loc.replace("_", " ").strip()

                logger.info(
                    f"Refreshing '{loc_display}' (age: {age_seconds/60:.1f} min)"
                )
                try:
                    wx.wxmeow(loc_display, include_hourly=True)
                    refreshed.append(loc_display)
                except Exception as e:
                    logger.warning(f"Could not refresh '{loc_display}': {e}")

            except OSError as e:
                logger.warning(f"Could not access {pkl_path}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error for {pkl_path}: {e}")
                logger.debug(traceback.format_exc())

    except Exception as e:
        logger.error(f"Error in refresh_meows: {e}")
        logger.debug(traceback.format_exc())

    if refreshed:
        logger.info(f"refresh_meows: refreshed {len(refreshed)} location(s): {refreshed}")
    return refreshed


if __name__ == "__main__":
    max_age = _DEFAULT_REFRESH_SECONDS
    if len(sys.argv) > 1:
        try:
            max_age = int(sys.argv[1])
        except ValueError:
            logger.error(f"Invalid max age: {sys.argv[1]}. Using default: {max_age}s")

    result = refresh_meows(max_age)
    logger.info(f"Refreshed {len(result)} location(s)")
