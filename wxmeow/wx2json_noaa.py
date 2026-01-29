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
import json
from typing import Dict, List, Any, Optional
# Removed custom weather icons - using NOAA icons directly

from wxmeow.weather_query import (
    noaa,
    environment_canada,
    is_canadian_location,
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

    def __init__(self, location: str, include_hourly: bool = True):
        """
        Initialize a weather information object for the given location.

        Args:
            location: Zipcode or lat,lon coordinates
            include_hourly: Whether to fetch hourly forecast data for charts
        """
        self.location = location
        self.include_hourly = include_hourly
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
            # Try to load from cache first with more aggressive caching for Canadian locations
            try:
                self.meow, self.age = load_meow(self.location)
                # For Canadian locations, use cache longer since we have limited data anyway
                cache_timeout = 45 if is_canadian_location(self.location) else 15  # Reduced cache timeout for faster updates
                
                if self.age is None or self.meow is None or self.age > cache_timeout:
                    logger.info(
                        f"Cache miss or expired for {location} (age: {self.age}, timeout: {cache_timeout}), fetching new data"
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
                        self.meowtp.append(str(period.get("temperature", "N/A")))
                        self.meowlt.append(str(period.get("temperature", "N/A")))
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
                        self.meowtp.append("N/A")
                        self.meowlt.append("N/A")
                        self.detail.append(f"<h3>day {i}</h3>No forecast available")

                # Fill with placeholders if we don't have 5 periods
                while len(self.dayname) < 5:
                    i = len(self.dayname)
                    self.dayname.append(f"day {i}")
                    self.meowfc.append("")  # Empty string for no icon
                    self.meowtp.append("N/A")
                    self.meowlt.append("N/A")
                    self.detail.append(f"<h3>day {i}</h3>No forecast available")
            else:
                logger.warning("No forecast data available")
                # Check if location failed completely vs partial data
                has_any_data = (self.meowtemp != "??" or self.meowobs != "unknown")
                
                if not has_any_data:
                    # Complete failure - show a nice message instead of placeholders
                    for i in range(5):
                        self.dayname.append(f"day {i}")
                        self.meowfc.append("")
                        self.meowtp.append("")  # Empty instead of ??
                        self.meowlt.append("")   # Empty instead of ??
                        self.detail.append(f"<h3>day {i}</h3>Forecast data unavailable")
                else:
                    # Partial data - we have current conditions but no forecast
                    for i in range(5):
                        self.dayname.append(f"day {i}")
                        self.meowfc.append("")
                        self.meowtp.append("N/A")
                        self.meowlt.append("N/A")
                        self.detail.append(f"<h3>day {i}</h3>Forecast not available")
        except Exception as e:
            logger.error(f"Error processing forecast: {str(e)}")
            logger.debug(traceback.format_exc())

        table = "<table>", "</table>"
        tr = "<tr>", "</tr>"
        td = "<td>", "</td>"
        tdc = "<td class='one'>"

        try:
            # Check if we have adequate weather data
            has_temp = self.meowtemp != "??"
            has_conditions = self.meowobs != "unknown"
            has_pressure = self.meowbp != "??"
            has_dewpoint = self.meowdp != "??"
            
            # If this looks like a failed lookup, provide a better message
            if not has_temp and not has_conditions:
                if is_canadian_location(self.location):
                    self.wxmeow = f"<h1>{self.meowplace}</h1><h2>Canadian Location Notice</h2><p>Weather data for Canadian locations is currently limited. We're working to add Environment and Climate Change Canada as a data source.</p><p>For now, please try using specific coordinates or a nearby US location for more detailed weather information.</p>"
                else:
                    self.wxmeow = f"<h1>{self.meowplace}</h1><h2>Weather Data Unavailable</h2><p>We couldn't retrieve current weather data for this location.</p><p>Try being more specific (e.g., 'Chicago, IL' instead of 'Chicago') or use a zip code.</p>"
            elif not has_temp:
                # We have conditions but no temperature
                self.wxmeow = f"<h1>{self.meowplace}<br> <small>is</small> {self.meowobs} <small>but temperature data unavailable</small></h1>"
            else:
                # We have some data, build the normal display
                temp_text = f"{self.meowtemp} F" if has_temp else "temperature unavailable"
                condition_text = self.meowobs if has_conditions else "conditions unknown"
                
                wxmeow = f"<h1>{self.meowplace}<br> <small>is</small> {condition_text} <small>and</small> {temp_text}"
                
                if has_dewpoint:
                    wxmeow += f"</br></br>dew point <small>is</small> {self.meowdp} F"
                
                if has_pressure:
                    wxmeow += f"</br>pressure <small>is</small> {self.meowbptrend} <small>at</small> {self.meowbp} inches"
                
                wxmeow += "</h1>"
                self.wxmeow = wxmeow.lower()
                
        except Exception as e:
            logger.error(f"Error creating weather HTML: {str(e)}")
            # Create a simpler version with whatever data we have
            self.wxmeow = f"<h1>{self.meowplace}<br> <small>weather data partially available</small></h1>"

        # Process hourly data for charts
        try:
            self._process_hourly_data()
            logger.info(f"Processed hourly data: {len(self.meowhourly)} items")
        except Exception as e:
            logger.error(f"Error in _process_hourly_data: {str(e)}")
            logger.debug(traceback.format_exc())
            self.meowhourly = []

        # If we don't have hourly data, log and continue without dummy data  
        if not self.meowhourly or len(self.meowhourly) == 0:
            logger.info("No hourly data available - will not generate dummy data")
            self.meowhourly = []

        # Build single combined forecast table with weather icons and temperatures
        forecast_table = '<div class="forecast-container" style="width: 100%; overflow-x: auto; margin: 10px 0;">\n'
        forecast_table += '<table class="weather-forecast-table" style="min-width: 400px; width: max-content; border-collapse: separate; border-spacing: 4px;">\n'
        forecast_table += '<tr class="day-headers">\n'

        # Add 12-hour period headers
        for i in range(5):
            period_label = (
                f"{self.dayname[i]}<br><small></small>"
                if i < len(self.dayname)
                else f"Period {i + 1}<br><small></small>"
            )
            forecast_table += f'<td style="text-align: center; padding: 4px; white-space: nowrap; font-weight: bold; font-size: 0.9em;"><span id="date-{i}" class="date-header">{period_label}</span></td>\n'

        forecast_table += '</tr>\n<tr class="weather-icons">\n'

        # Add weather icons using NOAA API icons directly
        for i in range(5):
            try:
                # Use NOAA icon URL directly
                icon_url = ""
                if i < len(self.meowfc) and self.meowfc[i]:
                    icon_url = self.meowfc[i]
                    logger.debug(f"Day {i} NOAA icon URL: '{icon_url}'")

                onclick_handler = f"selectDay({i}, event); return false;"

                forecast_table += f'<td style="text-align: center; padding: 2px; cursor: pointer; min-width: 80px;" id="{i}" class="day-selector weather-icon-cell" onclick="{onclick_handler}" role="button" aria-label="Select period {i + 1} forecast" tabindex="0">\n'

                if icon_url:
                    # Use NOAA icon directly
                    forecast_table += f'<img src="{icon_url}" alt="Weather forecast" width="64" height="64" style="display: block; margin: 0 auto;" />\n'
                else:
                    # Show a placeholder for missing forecast data
                    forecast_table += f'<div style="width: 64px; height: 64px; background: #f0f0f0; border: 1px solid #ccc; display: flex; align-items: center; justify-content: center; margin: 0 auto; font-size: 12px;">N/A</div>\n'

                forecast_table += "</td>\n"
            except Exception as e:
                logger.warning(f"Error generating weather icon for day {i}: {str(e)}")
                logger.debug(
                    f"Weather condition was: '{weather_condition if 'weather_condition' in locals() else 'unknown'}'"
                )
                onclick_handler = f"selectDay({i}, event); return false;"
                forecast_table += f'<td style="text-align: center; padding: 2px; cursor: pointer; min-width: 80px;" id="{i}" class="day-selector weather-icon-cell" onclick="{onclick_handler}">\n'
                forecast_table += '<img src="/static/weather-icons/unknown.svg" alt="Unknown weather" width="48" height="48" style="display: block; margin: 0 auto;" />'
                forecast_table += "</td>\n"

        forecast_table += '</tr>\n<tr class="temperatures">\n'

        # Add temperatures
        for i in range(5):
            temp_value = self.meowtp[i] if i < len(self.meowtp) else ""
            # Handle None values and other invalid temperatures
            if temp_value is None or temp_value == "??" or temp_value == "":
                temp_display = "—"  # em dash for unavailable
            elif temp_value == "N/A":
                temp_display = "N/A"
            elif str(temp_value) == "None":  # Handle string "None" values
                temp_display = "—"
            else:
                temp_display = f"{temp_value}°F"
            forecast_table += f'<td style="text-align: center; padding: 2px; font-weight: bold; font-size: 1.1em;">{temp_display}</td>\n'

        forecast_table += "</tr>\n</table>\n</div>\n"
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

        futuremeow = self.js + forecast_table + day_descriptions + futuretext
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
        Get a fresh read from NOAA API, with optimized fallback to Environment Canada for Canadian locations.
        """
        max_retries = 2  # Try up to 2 times (initial + 1 retry)
        retry_count = 0
        
        # Check if this is a Canadian location
        is_canadian = is_canadian_location(self.location)
        
        while retry_count <= max_retries:
            try:
                if is_canadian:
                    # For clearly Canadian locations, try Environment Canada first to save time
                    try:
                        logger.info(f"Trying Canadian weather service for '{self.location}'")
                        self.meow = environment_canada(self.location, include_hourly=self.include_hourly)
                        logger.info(f"Successfully used Canadian weather service for '{self.location}'")
                    except (LocationError, ApiError) as canada_error:
                        logger.info(f"Canadian weather service failed for '{self.location}': {canada_error}")
                        # Only try NOAA as fallback for border cities
                        coords = get_coordinates(self.location) 
                        if coords and 42.0 <= coords[0] <= 50.0:  # Near US border
                            logger.info(f"Trying NOAA as fallback for Canadian border location '{self.location}'")
                            self.meow = noaa(self.location, include_hourly=self.include_hourly)
                            logger.info(f"Successfully fetched Canadian location '{self.location}' from NOAA")
                        else:
                            # Re-raise for non-border cities
                            raise canada_error
                else:
                    self.meow = noaa(self.location, include_hourly=self.include_hourly)
                
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

        javascript = (
            """
<style>
/* Day selector cells in forecast table */
.weather-icon-cell {
    cursor: pointer;
    transition: background-color 0.2s ease;
    background: transparent;
    text-decoration: none !important;
    position: relative;
}

.weather-icon-cell:hover {
    background-color: var(--background-color, #fff);
    filter: invert(10%);
    text-decoration: none !important;
}

.weather-icon-cell.selected {
    background-color: var(--text-color, #333) !important;
    color: var(--background-color, #fff) !important;
}

.weather-icon-cell.selected pre {
    color: var(--background-color, #fff) !important;
}

a {
    text-decoration: none !important;
}
a:hover {
    text-decoration: none !important;
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

/* Weather icon images styling in table */
.weather-icon-cell img {
    margin: 0 auto;
    padding: 2px;
    display: block;
    max-width: 48px;
    max-height: 48px;
    width: auto;
    height: auto;
    transition: opacity 0.2s ease;
}
.hourly-chart {
    margin: 15px auto;
    padding: 10px;
    border-radius: 8px;
    border: 1px solid var(--border-color, #eee);
    width: 95%;
    background-color: var(--card-bg-color, #fff);
    min-height: 300px;
    display: none;
}
[id^='hourly-temperature-chart-'] {
    display: none;
    min-height: 300px;
    width: 100%;
    max-width: 800px;
    margin: 20px auto;
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
           // Set up hourly data for charts BEFORE loading temperature-chart.js
           window.hourlyData = """
            + json.dumps(self.meowhourly)
            + """;
           console.log("Hourly data loaded:", window.hourlyData ? window.hourlyData.length : 0, "data points");

</script>
<script>
          // Global variables
          var lastSelectedDay = 0;
          let charts = {};

          function isDarkMode() {
              return document.documentElement.getAttribute("data-theme") === "dark";
          }

          function createTemperatureChart(dayIndex) {
              console.log("Creating chart for day " + dayIndex);

              // Debug timing and DOM state
              console.log("DOM ready state:", document.readyState);
              console.log("Window hourly data available:", !!window.hourlyData);

              if (!window.hourlyData || window.hourlyData.length === 0) {
                  console.error("No hourly data available");
                  return;
              }

              const chartContainer = document.getElementById("hourly-temperature-chart-" + dayIndex);
              if (!chartContainer) {
                  console.error("Chart container not found for day " + dayIndex);
                  // List all available chart containers for debugging
                  const allContainers = document.querySelectorAll('[id^="hourly-temperature-chart-"]');
                  console.log("Available chart containers:", Array.from(allContainers).map(c => c.id));
                  return;
              }

              console.log("Chart container found:", chartContainer.id, "display:", chartContainer.style.display);

              // Destroy existing chart
              if (charts[dayIndex]) {
                  charts[dayIndex].destroy();
                  charts[dayIndex] = null;
              }

              // Filter data for selected day - use a simpler approach
              // Each day gets 24 hours starting from dayIndex * 24
              const startIndex = dayIndex * 24;
              const endIndex = Math.min(startIndex + 24, window.hourlyData.length);
              const filteredData = window.hourlyData.slice(startIndex, endIndex);

              console.log("Day " + dayIndex + ": startIndex=" + startIndex + ", endIndex=" + endIndex + ", filteredData.length=" + filteredData.length);

              if (filteredData.length === 0) {
                  console.error("No data for day " + dayIndex);
                  chartContainer.innerHTML = "<p>No data available for this day</p>";
                  return;
              }

              // Prepare chart data
              const labels = [];
              const temperatures = [];
              const precipProbs = [];

              filteredData.forEach(function(item) {
                  const date = new Date(item.time);
                  const hour = date.getHours();
                  labels.push(hour === 0 ? '12 AM' : hour === 12 ? '12 PM' : hour > 12 ? (hour-12) + ' PM' : hour + ' AM');
                  temperatures.push(item.temperature || item.temp);
                  precipProbs.push(item.precip || 0);
              });

              // Create canvas
              chartContainer.innerHTML = '<canvas id="chart-canvas-' + dayIndex + '" style="width: 100%; height: 300px;"></canvas>';
              const canvas = document.getElementById("chart-canvas-" + dayIndex);
              canvas.style.display = 'block';
              const ctx = canvas.getContext('2d');

              // Create gradient
              const gradient = ctx.createLinearGradient(0, 0, 0, 200);
              gradient.addColorStop(0, "rgba(204, 85, 0, 0.7)");
              gradient.addColorStop(1, "rgba(204, 85, 0, 0.05)");

              // Create chart
              charts[dayIndex] = new Chart(ctx, {
                  type: 'line',
                  data: {
                      labels: labels,
                      datasets: [{
                          label: 'Temperature (°F)',
                          data: temperatures,
                          backgroundColor: gradient,
                          borderColor: "rgba(204, 85, 0, 1)", // Warm orange for temperature
                          borderWidth: 2,
                          pointRadius: 3,
                          fill: true,
                          tension: 0.4,
                          yAxisID: 'temp'
                      }, {
                          label: 'Precipitation %',
                          data: precipProbs,
                          borderColor: "rgba(0, 120, 140, 1)", // Cool teal for precipitation - contrasts with orange
                          backgroundColor: "rgba(0, 120, 140, 0.2)",
                          borderWidth: 2,
                          pointRadius: 3,
                          fill: false,
                          tension: 0.4,
                          yAxisID: 'precip'
                      }]
                  },
                  options: {
                      responsive: true,
                      maintainAspectRatio: false,
                      animation: {
                          duration: 800,
                          onComplete: function() {
                              console.log("Chart animation completed for day " + dayIndex);
                          }
                      },
                      plugins: {
                          legend: {
                              display: true,
                              position: 'top'
                          },
                          tooltip: {
                              mode: 'index',
                              intersect: false,
                              callbacks: {
                                  label: function(context) {
                                      if (context.datasetIndex === 0) {
                                          return 'Temperature: ' + context.parsed.y + '°F';
                                      } else {
                                          return 'Precipitation: ' + context.parsed.y + '%';
                                      }
                                  }
                              }
                          }
                      },
                      scales: {
                          temp: {
                              type: 'linear',
                              position: 'left',
                              beginAtZero: false,
                              title: { display: true, text: 'Temperature (°F)' },
                              grid: { display: true }
                          },
                          precip: {
                              type: 'linear',
                              position: 'right',
                              min: 0,
                              max: 100,
                              title: { display: true, text: 'Precipitation (%)' },
                              grid: { display: false }
                          },
                          x: {
                              title: { display: true, text: 'Hour of Day' }
                          }
                      },
                      interaction: {
                          intersect: false,
                          mode: 'index'
                      }
                  }
              });

              console.log("Chart created successfully for day " + dayIndex);
          }

          // Global function for day selection
          function selectDay(dayIndex, event) {
              console.log("Selecting day:", dayIndex);

              // Prevent any default browser behavior
              if (event) {
                  event.preventDefault();
                  event.stopPropagation();
              }

              // Preserve scroll position to prevent page jumping
              const currentScrollY = window.scrollY;
              const currentScrollX = window.scrollX;

              // Hide all chart containers first
              $("[id^='hourly-temperature-chart-']").hide();

              // Hide all day descriptions
              $(".day-description").hide();
              $(".weather-icon-cell").removeClass("selected");

              // Show selected day's content
              $("#day-description-" + dayIndex).show();
              $("#" + dayIndex).addClass("selected");

              // Show ONLY the selected chart
              $("#hourly-temperature-chart-" + dayIndex).show();

              // Update global state
              lastSelectedDay = parseInt(dayIndex);

              // Create chart for selected day
              createTemperatureChart(dayIndex);

              // Restore scroll position after a brief delay to prevent jumping
              setTimeout(function() {
                  window.scrollTo(currentScrollX, currentScrollY);
              }, 10);
          }

          $(document).ready(function(){
               console.log("Weather forecast day selector initialization");
               console.log("Document ready, DOM state:", document.readyState);

               // Wait a moment for DOM to fully settle, then initialize
               setTimeout(function() {
                   console.log("Initializing after timeout...");
                   // Initially select day 0 (this will create the chart)
                   selectDay(0);
               }, 100);
           });
</script>
        """
        )
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
