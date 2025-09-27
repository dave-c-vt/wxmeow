#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WXMEOW - Weather Information Formatter
for wxmeow at https://wxmeow.com/

Weather data from the National Weather Service API
"""

import sys
import time
import logging
import traceback
from typing import Dict, List, Any, Optional

from wxmeow.weather_query import (
    noaa,
    LocationError,
    ApiError,
    DataParsingError,
    WeatherDataError,
)
from wxmeow.pickler import save_meow, load_meow, CacheReadError

# Configure logger
logger = logging.getLogger(__name__)


class wxmeow:
    """
    Weather data formatter for wxmeow.

    Formats weather data from NOAA API into HTML.
    """

    def __init__(self, location: str):
        """
        Initialize a weather information object for the given location.

        Args:
            location: Zipcode or lat,lon coordinates
        """
        self.location = location
        self.meow = None
        self.age = None
        self.wxmeow = ""
        self.futuremeow = ""
        self.meowhourly = []
        self.js: str = ""

        # Default values in case we can't get weather data
        self.meowplace = location
        self.meowobs = "unknown"
        self.meowtemp = "??"
        self.meowdp = "??"
        self.meowbp = "??"
        self.meowbptrend = "whatever"
        self.dayname = []
        self.meowfc = []
        self.meowtp = []
        self.meowlt = []
        self.detail = []

        try:
            # Try to load from cache first
            try:
                self.meow, self.age = load_meow(self.location)
                if self.age is None or self.meow is None or self.age > 10:
                    logger.info(
                        f"Cache miss or expired for {location}, fetching new data"
                    )
                    self.reload()
                else:
                    logger.info(
                        f"Using cached data for {location} (age: {self.age:.1f} minutes)"
                    )
            except CacheReadError as e:
                logger.warning(f"Error loading cached data: {str(e)}")
                self.reload()
        except (LocationError, ApiError, DataParsingError, WeatherDataError) as e:
            logger.error(f"No valid weather data available for {location}: {str(e)}")
            # Set a default error message
            self.wxmeow = f"<h1>Unable to get weather for {location}</h1>"
            self.futuremeow = ""
            return

        # We have some data, but we might be missing conditions
        if not getattr(self.meow, "jconditions", None):
            logger.warning(f"No conditions data available for {location}")

        try:
            try:
                if hasattr(self.meow, "city") and hasattr(self.meow, "state"):
                    if hasattr(self.meow, "city_full") and self.meow.city_full:
                        self.meowplace = self.meow.city_full
                    else:
                        self.meowplace = ", ".join([self.meow.city, self.meow.state])
            except Exception as loc_err:
                logger.error(f"Error getting location name: {str(loc_err)}")
                self.meowplace = ", ".join([self.meow.city, self.meow.state])

            if (
                self.meow.jconditions
                and "features" in self.meow.jconditions
                and self.meow.jconditions["features"]
            ):
                feature = self.meow.jconditions["features"][0]["properties"]

                self.meowobs = feature.get("textDescription", "unknown")

                if "temperature" in feature:
                    self.meowtemp = str(
                        int(round(self.cel2fahr(feature["temperature"])))
                    )

                if "dewpoint" in feature:
                    self.meowdp = str(int(round(self.cel2fahr(feature["dewpoint"]))))

                if "seaLevelPressure" in feature:
                    self.meowbp = str(int(self.pa2inches(feature["seaLevelPressure"])))

                if "features" in self.meow.jconditions:
                    self.meowbptrend = self.check_pressure_trend(
                        self.meow.jconditions["features"]
                    )
        except Exception as e:
            logger.error(f"Error processing conditions: {str(e)}")
            logger.debug(traceback.format_exc())

        logger.info(f"place: {self.meowplace}")

        # Reset lists for forecast data
        self.meowfc = []  # forecast icon (sunny, cloudy, etc.)
        self.meowtp = []  # forecast high temp
        self.meowlt = []  # forecast low temp
        self.dayname = []  # forecast element label
        self.detail = []  # detailed forecast

        # Process forecast data if available
        try:
            if (
                hasattr(self.meow, "jforecast")
                and self.meow.jforecast
                and "properties" in self.meow.jforecast
                and "periods" in self.meow.jforecast["properties"]
            ):
                periods = self.meow.jforecast["properties"]["periods"]

                # Get up to 5 forecast periods
                for i in range(min(5, len(periods))):
                    try:
                        period = periods[i]
                        self.dayname.append(period.get("name", f"Day {i}").lower())
                        self.meowfc.append(period.get("icon", ""))
                        self.meowtp.append(str(period.get("temperature", "??")))
                        self.meowlt.append(str(period.get("temperature", "??")))
                        self.detail.append(
                            "<h3>{0}</h3>{1}".format(
                                period.get("name", f"Day {i}").lower(),
                                period.get("detailedForecast", "No forecast available"),
                            )
                        )
                    except Exception as e:
                        logger.warning(
                            f"Error processing forecast period {i}: {str(e)}"
                        )
                        # Add placeholder data for this period
                        self.dayname.append(f"day {i}")
                        self.meowfc.append("")
                        self.meowtp.append("??")
                        self.meowlt.append("??")
                        self.detail.append(f"<h3>day {i}</h3>No forecast available")

                # Fill with placeholders if we don't have 5 periods
                while len(self.dayname) < 5:
                    i = len(self.dayname)
                    self.dayname.append(f"day {i}")
                    self.meowfc.append("")  # Empty string for no icon
                    self.meowtp.append("??")
                    self.meowlt.append("??")
                    self.detail.append(f"<h3>day {i}</h3>No forecast available")
            else:
                logger.warning("No forecast data available")
                # Add placeholder data
                for i in range(5):
                    self.dayname.append(f"day {i}")
                    self.meowfc.append("")
                    self.meowtp.append("??")
                    self.meowlt.append("??")
                    self.detail.append(f"<h3>day {i}</h3>No forecast available")
        except Exception as e:
            logger.error(f"Error processing forecast: {str(e)}")
            logger.debug(traceback.format_exc())

        table = "<table>", "</table>"
        tr = "<tr>", "</tr>"
        td = "<td>", "</td>"
        tdc = "<td class='one'>"

        try:
            wxmeow = (
                "<h1>"
                + self.meowplace
                + "<br> <small>is</small> "
                + self.meowobs
                + " <small>and</small> "
                + self.meowtemp
                + " F </br></br>Dew point <small>is</small> "
                + str(self.meowdp)
                + " F </br>Pressure <small>is</small> "
                + self.meowbptrend
                + " <small>at</small> "
                + self.meowbp
                + " inches</h1>"
            )
            self.wxmeow = wxmeow.lower()
        except Exception as e:
            logger.error(f"Error creating weather HTML: {str(e)}")
            # Create a simpler version with whatever data we have
            self.wxmeow = f"<h1>{self.meowplace}<br> <small>Weather data partially available</small></h1>"

        # Process hourly data for charts
        try:
            self._process_hourly_data()
            logger.info(f"Processed hourly data: {len(self.meowhourly)} items")
        except Exception as e:
            logger.error(f"Error in _process_hourly_data: {str(e)}")
            logger.debug(traceback.format_exc())
            self.meowhourly = []

        # If we don't have hourly data, create placeholder data
        if not self.meowhourly or len(self.meowhourly) == 0:
            self._make_hourly_data()

        futureth = (
            tr[0]
            + td[0]
            + f'<span id="date-0" class="date-header">{self.dayname[0]}</span>'
            + td[1]
            + td[0]
            + f'<span id="date-1" class="date-header">{self.dayname[1]}</span>'
            + td[1]
            + td[0]
            + f'<span id="date-2" class="date-header">{self.dayname[2]}</span>'
            + td[1]
            + td[0]
            + f'<span id="date-3" class="date-header">{self.dayname[3]}</span>'
            + td[1]
            + td[0]
            + f'<span id="date-4" class="date-header">{self.dayname[4]}</span>'
            + td[1]
            + tr[1]
        )
        futurepics = '<table class="weather-forecast-table">' + tr[0]
        # Safely process each forecast icon, handling empty strings
        for i in range(5):
            try:
                td_style = tdc if i >= 3 else td[0]
                img_src = ""
                if i < len(self.meowfc):
                    if self.meowfc[i] and " " in self.meowfc[i]:
                        img_src = self.meowfc[i].split(" ")[0]
                    elif self.meowfc[i]:
                        img_src = self.meowfc[i]

                # Create weather icon for each day
                if img_src:
                    weather_emoji = self._get_weather_emoji(img_src)
                else:
                    # Use placeholder for empty images
                    weather_emoji = "⚡"

                # Simplified click handler
                onclick_handler = f"selectDay({i}); return false;"

                futurepics += (
                    td_style
                    + f"<span id='{i}' class='day-selector weather-icon' "
                    + "style='cursor:pointer; display:block; padding: 15px; text-align:center; font-size:48px; border-radius:4px;' "
                    + f'onclick="{onclick_handler}" '
                    + f'role="button" '
                    + f'aria-label="Select day {i + 1} forecast" '
                    + 'tabindex="0">'
                    + weather_emoji
                    + "</span>"
                    + td[1]
                )
            except Exception as e:
                logger.warning(
                    f"Error generating forecast icon HTML for day {i}: {str(e)}"
                )
                onclick_handler = (
                    "$('.day-selector').removeClass('selected-day');"
                    + "$(this).addClass('selected-day');"
                    + "$('.tr"
                    + str(i)
                    + "').show();"
                    + "$('.tr0,.tr1,.tr2,.tr3,.tr4').not('.tr"
                    + str(i)
                    + "').hide();"
                    + "$('.day-description').hide();"
                    + "$('#day-description-"
                    + str(i)
                    + "').show();"
                    + "lastSelectedDay="
                    + str(i)
                    + ";"
                    + "$(document).trigger('daySelected', ["
                    + str(i)
                    + "]);"
                )
                td_style = tdc if i >= 3 else td[0]
                futurepics += (
                    td_style
                    + "<span id='"
                    + str(i)
                    + "' class='day-selector weather-icon' "
                    + "style='cursor:pointer; display:block; padding: 15px; text-align:center; font-size:48px; border-radius:4px;' "
                    + 'onclick="'
                    + onclick_handler
                    + '">⚡</span>'
                    + td[1]
                )
        futurepics += tr[1] + "</table>"

        # Build temperature row with proper alignment to weather icons
        futuretemp = tr[0]
        for i in range(5):
            td_style = tdc if i >= 3 else td[0]
            temp_value = self.meowtp[i] if i < len(self.meowtp) else "??"
            futuretemp += td_style + str(temp_value) + " F" + td[1]
        futuretemp += tr[1]
        # Add day descriptions immediately after the weather table
        day_descriptions = (
            '<div style="margin: 20px auto; max-width: 800px; text-align: center;">'
        )
        for i in range(5):
            if i < len(self.detail):
                display_style = "block" if i == 0 else "none"
                day_descriptions += f'<div id="day-description-{i}" class="day-description" style="display:{display_style}; font-size:18px; line-height:1.6; margin:20px auto; padding:15px; text-align:left; color:var(--text-color,#333); background-color:var(--card-bg-color,#f8f8f8); border-radius:8px; max-width:600px;">{self.detail[i]}</div>'
        day_descriptions += "</div>"

        # Build the chart containers
        futuretext = '<div style="margin: 20px auto; max-width: 800px;">'
        for i in range(5):
            chart_display = "block" if i == 0 else "none"
            futuretext += f'<div id="hourly-temperature-chart-{i}" class="hourly-chart" style="display:{chart_display}; width:100%; max-width:800px; margin:20px auto; min-height:300px;"></div>'
        futuretext += "</div>"

        self.javascript()

        futuremeow = (
            self.js
            + table[0]
            + futureth
            + futurepics
            + futuretemp
            + table[1]
            + day_descriptions
            + futuretext
        )
        self.futuremeow = futuremeow

        # logger.debug(wxmeow)
        # logger.debug(futuremeow)
        # logger.debug("<br><br>")

        try:
            save_meow(self.meow)
            logger.debug(f"Successfully cached weather data for {self.location}")
        except Exception as e:
            logger.warning(
                f"Failed to cache weather data for {self.location}: {str(e)}"
            )
            # Continue execution even if caching fails

    def reload(self) -> None:
        """
        Get a fresh read from NOAA API.
        """
        max_retries = 2  # Try up to 2 times (initial + 1 retry)
        retry_count = 0

        while retry_count <= max_retries:
            try:
                self.meow = noaa(self.location)
                # If we get here, we succeeded - process the data
                self._process_hourly_data()
                # Save the fresh data to cache
                try:
                    save_meow(self.meow)
                    logger.debug(f"Cached fresh weather data for {self.location}")
                except Exception as cache_e:
                    logger.warning(f"Failed to cache fresh data: {str(cache_e)}")
                return
            except LocationError as e:
                logger.error(
                    f"Failed to reload weather data - location error: {str(e)}"
                )
                logger.debug(traceback.format_exc())
                # Don't retry for location errors (invalid input)
                break
            except ApiError as e:
                logger.error(f"Failed to reload weather data - API error: {str(e)}")
                logger.debug(traceback.format_exc())
                retry_count += 1
                if retry_count <= max_retries:
                    logger.info(
                        f"Retrying API request (attempt {retry_count}/{max_retries})..."
                    )
                    time.sleep(1)  # Wait a second before retrying
                continue
            except DataParsingError as e:
                logger.error(
                    f"Failed to reload weather data - data parsing error: {str(e)}"
                )
                logger.debug(traceback.format_exc())
                break
            except WeatherDataError as e:
                logger.error(
                    f"Failed to reload weather data - weather data error: {str(e)}"
                )
                logger.debug(traceback.format_exc())
                break
            except Exception as e:
                logger.error(
                    f"Failed to reload weather data - unexpected error: {str(e)}"
                )
                logger.debug(traceback.format_exc())
                break

    def _make_hourly_data(self) -> None:
        """
        Create hourly data for charts if not available.

        Generates placeholder hourly data when actual data is not available.
        """
        import math
        from datetime import datetime, timedelta

        # Generate some sample data if we don't have hourly data
        if not self.meowhourly or len(self.meowhourly) == 0:
            logger.info("Creating placeholder hourly data")
            self.meowhourly = []

            now = datetime.now()
            # Create 24 hours of placeholder data
            for i in range(24):
                hour_time = now + timedelta(hours=i)
                # Simple sine wave temperature pattern
                temp = 65 + 10 * math.sin(i / 4)

                self.meowhourly.append(
                    {
                        "time": hour_time.isoformat(),
                        "temp": round(temp, 1),
                        "condition": "Forecast unavailable",
                        "windSpeed": "5 mph",
                        "windDir": "N",
                        "icon": "",
                        "precip": 0,
                    }
                )

    def _process_hourly_data(self) -> None:
        """
        Process the hourly forecast data from the NOAA API response.

        Extracts hourly temperature and condition data for use in the temperature chart.
        """
        self.meowhourly = []  # Initialize to empty list by default

        try:
            if not hasattr(self.meow, "jhourly"):
                logger.warning(
                    "No hourly forecast data available - jhourly attribute missing"
                )
                self.meowhourly = []
                return

            if not self.meow.jhourly:
                logger.warning("No hourly forecast data available - jhourly is empty")
                self.meowhourly = []
                return

            logger.info("Processing hourly data from NOAA API response")

            jhourly_data = self.meow.jhourly
            if (
                isinstance(jhourly_data, dict)
                and "properties" in jhourly_data
                and "periods" in jhourly_data["properties"]
            ):
                periods = jhourly_data["properties"]["periods"]
                hourly_data = []

                # Process hourly periods
                for period in periods:
                    try:
                        # Convert time to a standard format
                        start_time = period.get("startTime", "")
                        temp = period.get("temperature")

                        # Extract temperature and other data
                        hourly_item = {
                            "time": start_time,
                            "temp": temp,
                            "temperature": temp,  # Include both for compatibility
                            "condition": period.get("shortForecast", ""),
                            "windSpeed": period.get("windSpeed", ""),
                            "windDir": period.get("windDirection", ""),
                            "icon": period.get("icon", ""),
                            "precip": period.get("probabilityOfPrecipitation", {}).get(
                                "value"
                            ),
                        }
                        hourly_data.append(hourly_item)
                    except Exception as e:
                        logger.warning(f"Error processing hourly period: {str(e)}")
                        continue

                self.meowhourly = hourly_data
                logger.info(f"Processed {len(hourly_data)} hourly forecast periods")
            else:
                logger.warning("Hourly forecast data structure is not as expected")
                self.meowhourly = []
        except Exception as e:
            logger.error(f"Error processing hourly data: {str(e)}")
            logger.debug(traceback.format_exc())
            self.meowhourly = []
            logger.error(f"Error processing hourly forecast data: {str(e)}")
            logger.debug(traceback.format_exc())
            self.meowhourly = []

    def _get_weather_emoji(self, icon_url: str) -> str:
        """
        Convert a weather icon URL to an appropriate emoji.

        Args:
            icon_url: The URL of the weather icon

        Returns:
            A weather emoji representing the condition
        """
        # Extract condition from icon URL
        condition = "unknown"
        try:
            if not icon_url:
                return "🌈"

            url_lower = str(icon_url).lower()

            # Debug output
            logger.debug(f"Processing weather icon URL: {url_lower}")

            # Night vs Day detection
            is_night = "night" in url_lower or "n/" in url_lower

            # Create sets for faster matching
            clear_set = {"skc", "few", "clear"}
            cloud_set = {"bkn", "ovc", "cloud", "cloudy"}
            rain_set = {"rain", "shra"}
            snow_set = {"snow", "blizzard"}
            sleet_set = {"sleet", "fzra"}
            storm_set = {"thunder", "tsra"}
            fog_set = {"fog", "mist"}

            # Check for specific condition patterns in the URL
            if any(code in url_lower for code in clear_set):
                condition = "clear_night" if is_night else "clear"
            elif "sct" in url_lower:
                condition = "partly_cloudy_night" if is_night else "partly_cloudy"
            elif any(code in url_lower for code in cloud_set):
                condition = "cloudy"
                logger.debug(f"matched {cloud_set}")
            elif any(code in url_lower for code in rain_set):
                condition = "rain"
            elif any(code in url_lower for code in snow_set):
                condition = "snow"
            elif any(code in url_lower for code in sleet_set):
                condition = "sleet"
            elif any(code in url_lower for code in storm_set):
                condition = "storm"
            elif any(code in url_lower for code in fog_set):
                condition = "fog"
            elif "wind" in url_lower:
                condition = "windy"
            elif "hot" in url_lower:
                condition = "hot"
            else:
                logger.debug("could not match")

        except Exception as e:
            logger.warning(f"Error processing weather icon: {str(e)}")
            return "🌈"

        # Map conditions to emojis - more diverse set of weather emojis
        emoji_map = {
            "clear": "☀️",
            "clear_night": "🌙",
            "partly_cloudy": "⛅",
            "partly_cloudy_night": "🌤️",
            "cloudy": "☁️",
            "rain": "🌧️",
            "shower": "🌦️",
            "snow": "❄️",
            "sleet": "🌨️",
            "storm": "⛈️",
            "lightning": "⚡",
            "fog": "🌫️",
            "windy": "💨",
            "tornado": "🌪️",
            "hot": "🔥",
            "hurricane": "🌀",
            "unknown": "🌈",
        }

        return emoji_map.get(condition, "🌈")

    def _get_weather_condition_text(self, icon_url: str) -> str:
        """
        Convert a weather icon URL to descriptive text for screen readers.

        Args:
            icon_url: The URL of the weather icon

        Returns:
            A text description of the weather condition
        """
        try:
            if not icon_url:
                return "weather condition unknown"

            url_lower = str(icon_url).lower()

            # Night vs Day detection
            is_night = "night" in url_lower or "n/" in url_lower
            time_prefix = "nighttime" if is_night else "daytime"

            # Check for specific condition patterns
            if any(code in url_lower for code in ["skc", "few", "clear"]):
                return f"{time_prefix} clear skies"
            elif "sct" in url_lower:
                return f"{time_prefix} partly cloudy"
            elif any(code in url_lower for code in ["bkn", "ovc", "cloud"]):
                return "cloudy conditions"
            elif any(code in url_lower for code in ["rain", "shra"]):
                return "rain expected"
            elif any(code in url_lower for code in ["snow", "blizzard"]):
                return "snow conditions"
            elif any(code in url_lower for code in ["sleet", "fzra"]):
                return "sleet or freezing rain"
            elif any(code in url_lower for code in ["thunder", "tsra"]):
                return "thunderstorms possible"
            elif any(code in url_lower for code in ["fog", "mist"]):
                return "foggy conditions"
            elif "wind" in url_lower:
                return "windy conditions"
            elif "hot" in url_lower:
                return "hot weather"
            else:
                return "mixed weather conditions"

        except Exception as e:
            logger.warning(f"Error processing weather condition text: {str(e)}")
            return "weather condition unknown"

    def cel2fahr(self, val: Dict[str, Any]) -> float:
        """
        Convert Celsius to Fahrenheit if needed.

        Args:
            val: Temperature value dictionary with unitCode and value

        Returns:
            Temperature value in Fahrenheit
        """
        c_desc = ["degc", "c", "celsius", "centegrade", "cel", "centigrade"]
        try:
            if "unitCode" in val and "value" in val and val["value"] is not None:
                if any(c in val["unitCode"].lower() for c in c_desc):
                    return float(val["value"]) * 9.0 / 5.0 + 32.0
                return float(val["value"])
        except Exception as e:
            logger.error(f"Error converting Celsius to Fahrenheit: {str(e)}")
            return 0.0
        return 0.0

    def pa2inches(self, val: Dict[str, Any]) -> float:
        """
        Convert Pascal to inches of mercury.

        Args:
            val: Pressure value dictionary with unitCode and value

        Returns:
            Pressure value in inches of mercury
        """
        pa_desc = ["pa", "pascal"]
        try:
            if "unitCode" in val and "value" in val and val["value"] is not None:
                if any(p in val["unitCode"].lower() for p in pa_desc):
                    return float(val["value"]) * 0.0002953
                return float(val["value"])
        except Exception as e:
            logger.error(f"Error converting Pascal to inches: {str(e)}")
            return 0.0
        return 0.0

    def check_pressure_trend(self, features):
        """
        Check the pressure trend from the features list.

        Args:
            features: List of weather features

        Returns:
            Pressure trend description (rising, falling, stable, or whatever)
        """
        try:
            if (
                len(features) > 1
                and "properties" in features[0]
                and "seaLevelPressure" in features[0]["properties"]
                and "properties" in features[1]
                and "seaLevelPressure" in features[1]["properties"]
                and "value" in features[1]["properties"]["seaLevelPressure"]
                and "value" in features[0]["properties"]["seaLevelPressure"]
            ):
                p1 = features[1]["properties"]["seaLevelPressure"]["value"]
                p2 = features[0]["properties"]["seaLevelPressure"]["value"]

                if p1 is not None and p2 is not None:
                    if p1 > p2:
                        return "falling"
                    elif p1 < p2:
                        return "rising"
                    else:
                        return "stable"
        except Exception as e:
            logger.debug(f"Error checking pressure trend: {str(e)}")

        return "whatever"

    def persist():
        # check if zip code file exists < 30 min old
        ## if it does, use it, return the json contents
        ## else, perform a weather query
        """Probably makes sense to
            1. Check DB for up to date data (last 30 min?)
            2. If up to date, lock and load for page display
            3. If not,
                a. do a set of queries to refresh datas
                b. store them in DB
                c. go back to step 1

        This means, need to develop
            1. a Db schema for wxmeow
            2. functions to write/read from schema
            3. probably some auto refresh for known locations, to keep the responses faster for all the mega fans of wxmeow


        """

        pass

    def javascript(self):
        """Generate JavaScript for weather app functionality."""
        """
        text output of javascript functions.
        there must be a better way, but who cares...
        """

        javascript = """
<style>
.day-selector {
    cursor: pointer;
    transition: all 0.2s ease;
    padding: 8px;
    border-radius: 8px;
    display: block;
    margin: auto;
    width: 90px;
    height: 90px;
}
.day-description {
    margin-top: 5px;
    margin-bottom: 10px;
    min-height: 40px;
    font-size: 14px;
    text-align: center;
    max-width: 100%;
    box-sizing: border-box;
    object-fit: contain;
    text-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.weather-icon {
    font-size: 48px !important;
    line-height: 1.2;
    display: flex !important;
    align-items: center;
    justify-content: center;
    text-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.day-selector:hover, .day-selector.selected-day {
    background-color: var(--button-hover-bg, rgba(100, 100, 100, 0.2));
    transform: scale(1.08);
    box-shadow: 0 3px 10px var(--border-color, rgba(0, 0, 0, 0.2));
    border: 2px solid var(--border-color, #ccc);
}
.hourly-chart {
    margin: 15px auto;
    padding: 10px;
    border-radius: 8px;
    border: 1px solid var(--border-color, #eee);
    width: 95%;
    background-color: var(--card-bg-color, #fff);
    min-height: 300px;
}
.chart-row {
    display: block;
    width: 100%;
}
.chart-row td {
    padding: 10px 0;
    width: 100%;
}
td {
    vertical-align: middle;
    text-align: center;
}
tr {
    display: table-row;
}
table {
    border-collapse: collapse;
}
</style>
<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.3.1/jquery.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<script>
           // Global variable to track the selected day
           var lastSelectedDay = 0;

           // Global function for day selection
           function selectDay(dayIndex) {
               console.log("Selecting day:", dayIndex);

               // Hide all chart containers first
               $("[id^='hourly-temperature-chart-']").hide().css("display", "none");

               // Hide all day details and charts
               $(".day-detail, .chart-row").hide();
               $(".day-selector").removeClass("selected-day");

               // Show selected day's content
               $(".tr" + dayIndex).show();
               $("#" + dayIndex).addClass("selected-day");

               // Show ONLY the selected chart and hide all others
               for (let i = 0; i < 5; i++) {
                   const chartElement = $("#hourly-temperature-chart-" + i);
                   if (i === parseInt(dayIndex)) {
                       chartElement.css({
                           "display": "block",
                           "width": "100%",
                           "max-width": "800px",
                           "margin": "20px auto",
                           "min-height": "300px"
                       }).show();
                   } else {
                       chartElement.hide().css("display", "none");
                   }
               }

               // Update global state
               lastSelectedDay = parseInt(dayIndex);

               // Trigger chart update event
               $(document).trigger('daySelected', [dayIndex]);
           }

           $(document).ready(function(){
                console.log("Weather forecast day selector initialization");

                // Initially select day 0
                selectDay(0);

                // Initialize charts after a delay to ensure DOM is ready
                setTimeout(function() {
                    console.log("Initializing temperature charts...");
                    $(document).trigger('daySelected', [0]);
                }, 500);
            });
</script>
        """
        self.js = javascript


if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            result = wxmeow(sys.argv[1])
            logger.info(f"Successfully processed weather for {sys.argv[1]}")
        except LocationError as e:
            logger.error(f"Failed to process weather - invalid location: {str(e)}")
            logger.debug(traceback.format_exc())
            sys.exit(1)
        except ApiError as e:
            logger.error(f"Failed to process weather - API error: {str(e)}")
            logger.debug(traceback.format_exc())
            sys.exit(2)
        except WeatherDataError as e:
            logger.error(f"Failed to process weather - data error: {str(e)}")
            logger.debug(traceback.format_exc())
            sys.exit(3)
        except Exception as e:
            logger.error(f"Failed to process weather - unexpected error: {str(e)}")
            logger.debug(traceback.format_exc())
            sys.exit(4)
