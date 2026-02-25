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
from datetime import datetime, date as _date
from typing import Dict, List, Any, Optional
# Removed custom weather icons - using NOAA icons directly

from wxmeow.weather_query import (
    noaa,
    environment_canada,
    is_canadian_location,
    is_european_location,
    metno,
    LocationError,
    ApiError,
    DataParsingError,
    WeatherDataError,
)
from wxmeow.pickler import save_meow, load_meow, CacheReadError
from wxmeow.location_service import get_coordinates

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
        self.meowdates = []
        self.meowfc = []
        self.meowtp = []
        self.meowlt = []
        self.detail = []
        self.alerts = []
        self.meow_alerts = ""

        try:
            # Try to load from cache first with more aggressive caching for Canadian locations
            try:
                self.meow, self.age = load_meow(self.location)
                # For Canadian and European locations, use cache longer since we have limited data anyway
                is_canadian = is_canadian_location(self.location)
                is_european = is_european_location(self.location)
                cache_timeout = 45 if (is_canadian or is_european) else 15  # Reduced cache timeout for faster updates
                
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

            # Extract current conditions - handle different API formats
            if hasattr(self.meow, 'jconditions') and self.meow.jconditions:
                self._extract_conditions_data()
            
            # Always try to process forecast data, even if conditions are missing
            self._process_forecast_data()
            
            # Continue with HTML building
            self._build_html()
                
        except Exception as e:
            logger.error(f"Error processing weather data: {str(e)}")
            logger.debug(traceback.format_exc())
            
    def _build_html(self):
        """Build the HTML representation of weather data"""
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
            
            # If this looks like a failed lookup, provide a better message but still show forecast
            if not has_temp and not has_conditions:
                if is_canadian_location(self.location):
                    self.wxmeow = f"<h1>{self.meowplace}</h1><h2>Canadian Location</h2><p>Current conditions not available. Forecast data shown below.</p>"
                elif is_european_location(self.location):
                    self.wxmeow = f"<h1>{self.meowplace}</h1><h2>European Location</h2><p>Current conditions not available. Forecast data shown below.</p>"
                else:
                    self.wxmeow = f"<h1>{self.meowplace}</h1><h2>Weather Data Limited</h2><p>Current conditions not available. Forecast data shown below.</p>"
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

        # Process alerts before building forecast HTML
        self._process_alerts()

        num_days = len(self.dayname)

        # Build single combined forecast table with weather icons and temperatures
        forecast_table = '<div class="forecast-container" id="forecast-container" style="overflow-x: auto; -webkit-overflow-scrolling: touch; margin: 0;">\n'
        forecast_table += '<table class="weather-forecast-table" style="width: max-content; border-collapse: separate; border-spacing: 6px;">\n'
        forecast_table += '<tr class="day-headers">\n'

        for i in range(num_days):
            period_label = f"{self.dayname[i]}<br><small></small>"
            forecast_table += f'<td style="text-align: center; padding: 4px; white-space: nowrap; font-weight: bold; font-size: 1em;"><span id="date-{i}" class="date-header">{period_label}</span></td>\n'

        forecast_table += '</tr>\n<tr class="weather-icons">\n'

        for i in range(num_days):
            try:
                icon_url = self.meowfc[i] if i < len(self.meowfc) and self.meowfc[i] else ""
                day_date = self.meowdates[i] if i < len(self.meowdates) else ""
                onclick_handler = f"selectDay({i}, event); return false;"

                forecast_table += f'<td style="text-align: center; padding: 4px; cursor: pointer; min-width: 100px;" id="{i}" class="day-selector weather-icon-cell" onclick="{onclick_handler}" data-date="{day_date}" role="button" aria-label="Select period {i + 1} forecast" tabindex="0">\n'

                if icon_url:
                    large_icon_url = icon_url.replace('size=small', 'size=large').replace('size=medium', 'size=large')
                    forecast_table += f'<img src="{large_icon_url}" alt="Weather forecast" style="display: block; margin: 0 auto; width: 160px; height: 160px;" />\n'
                else:
                    day_num = i + 1 if i > 0 else "today"
                    forecast_table += f'<div style="width: 160px; height: 160px; background: #f0f0f0; border: 1px solid #ccc; display: flex; align-items: center; justify-content: center; margin: 0 auto; font-size: 11px; flex-direction: column;"><div>day</div><div>{day_num}</div></div>\n'

                forecast_table += "</td>\n"
            except Exception as e:
                logger.warning(f"Error generating weather icon for day {i}: {str(e)}")
                onclick_handler = f"selectDay({i}, event); return false;"
                forecast_table += f'<td style="text-align: center; padding: 2px; cursor: pointer; min-width: 80px;" id="{i}" class="day-selector weather-icon-cell" onclick="{onclick_handler}" data-date="">\n'
                forecast_table += "</td>\n"

        forecast_table += '</tr>\n<tr class="temperatures">\n'

        for i in range(num_days):
            temp_value = self.meowtp[i] if i < len(self.meowtp) else ""
            temp_display = self._format_temperature_safe(temp_value)

            if any(na_pattern in str(temp_display).lower() for na_pattern in ['n/a', 'na', 'n.a', 'null', 'undefined', 'error']):
                temp_display = "—"

            forecast_table += f'<td style="text-align: center; padding: 2px; font-weight: bold; font-size: 1.1em;">{temp_display}</td>\n'

        forecast_table += "</tr>\n</table>\n</div>\n"

        # Add day descriptions immediately after the weather table
        day_descriptions = '<div style="margin: 20px auto; max-width: 800px; text-align: center;">'
        for i in range(num_days):
            if i < len(self.detail):
                display_style = "block" if i == 0 else "none"
                day_descriptions += f'<div id="day-description-{i}" class="day-description" style="display:{display_style}; font-size:18px; line-height:1.6; margin:20px auto; padding:15px; text-align:left; color:var(--text-color,#333); background-color:var(--card-bg-color,#f8f8f8); border-radius:8px; max-width:600px;">{self.detail[i]}</div>'
        day_descriptions += "</div>"

        # Build the chart containers
        futuretext = '<div style="margin: 20px auto; max-width: 800px;">'
        for i in range(num_days):
            chart_display = "block" if i == 0 else "none"
            futuretext += f'<div id="hourly-temperature-chart-{i}" class="hourly-chart" style="display:{chart_display}; width:100%; max-width:800px; margin:16px auto; min-height:200px;"></div>'
        futuretext += '</div>'

        # Combine forecast table, descriptions, and chart area
        self.futuremeow = forecast_table + day_descriptions + futuretext
        
        # Generate the JavaScript for the charts at the end
        self.javascript()

    def _process_forecast_data(self):
        """Process forecast data from weather source"""
        logger.info(f"place: {self.meowplace}")
        logger.debug("Starting forecast data processing")

        # Reset lists for forecast data
        self.meowfc = []  # forecast icon (sunny, cloudy, etc.)
        self.meowtp = []  # forecast high temp
        self.meowlt = []  # forecast low temp
        self.meowdates = []  # actual calendar dates for each forecast day (YYYY-MM-DD)
        self.dayname = []  # forecast element label
        self.detail = []  # detailed forecast

        # Process forecast data if available
        try:
            logger.debug(f"Checking for jforecast: hasattr={hasattr(self.meow, 'jforecast')}")
            if hasattr(self.meow, 'jforecast'):
                logger.debug(f"jforecast exists: {self.meow.jforecast is not None}")
                if self.meow.jforecast and "properties" in self.meow.jforecast:
                    logger.debug(f"Has properties: {'periods' in self.meow.jforecast['properties']}")

            if (
                hasattr(self.meow, "jforecast")
                and self.meow.jforecast
                and "properties" in self.meow.jforecast
                and "periods" in self.meow.jforecast["properties"]
            ):
                logger.info("Processing forecast data from jforecast")
                periods = self.meow.jforecast["properties"]["periods"]

                # Process forecast periods, grouping day/night pairs for proper high/low temperatures
                i = 0
                while i < len(periods):
                    try:
                        period = periods[i]
                        is_daytime = period.get("isDaytime", True)
                        
                        if is_daytime:
                            # This is a daytime period
                            day_period = period
                            night_period = periods[i + 1] if i + 1 < len(periods) else None
                            
                            # Use the day name directly from NOAA ("today", "monday", "tuesday", etc.)
                            base_name = period.get("name", f"day {len(self.dayname) + 1}").lower()
                            
                            self.dayname.append(base_name)
                            self.meowfc.append(period.get("icon", ""))
                            # Store the actual calendar date (YYYY-MM-DD) for chart alignment
                            start_time = period.get("startTime", "")
                            self.meowdates.append(start_time[:10] if start_time else "")

                            # Get temperatures from both periods and determine which is high/low
                            day_temp = day_period.get("temperature", "")
                            night_temp = night_period.get("temperature", day_temp) if night_period else day_temp
                            
                            # Determine high and low temperatures correctly
                            try:
                                day_temp_val = float(day_temp) if day_temp and day_temp != "" else None
                                night_temp_val = float(night_temp) if night_temp and night_temp != "" else None
                                
                                if day_temp_val is not None and night_temp_val is not None:
                                    high_temp = max(day_temp_val, night_temp_val)
                                    low_temp = min(day_temp_val, night_temp_val)
                                elif day_temp_val is not None:
                                    high_temp = low_temp = day_temp_val
                                elif night_temp_val is not None:
                                    high_temp = low_temp = night_temp_val
                                else:
                                    high_temp = low_temp = ""
                                    
                                # Filter out N/A values before appending using safe function
                                high_str = self._safe_temp_string(high_temp)
                                low_str = self._safe_temp_string(low_temp)
                                self.meowtp.append(high_str)
                                self.meowlt.append(low_str)
                            except (ValueError, TypeError):
                                # Fallback to original logic if conversion fails, but filter out N/A values
                                day_str = self._safe_temp_string(day_temp)
                                night_str = self._safe_temp_string(night_temp)
                                self.meowtp.append(day_str)
                                self.meowlt.append(night_str)
                            
                            # Create detail with day description
                            day_forecast = day_period.get("detailedForecast", day_period.get("shortForecast", "no forecast available")).lower()
                            self.detail.append(f"<h3>{base_name}</h3>{day_forecast}")
                            
                            logger.debug(f"Processed forecast day {len(self.dayname)-1}: {base_name} ({day_temp}°F/{night_temp}°F)")
                            # Only skip the night period if it exists, otherwise just advance by 1
                            if night_period:
                                i += 2  # Skip the night period since we processed it
                            else:
                                i += 1  # No night period to skip
                        else:
                            # This is a nighttime period without a preceding day period
                            night_period = period
                            raw_name = period.get("name", "")
                            base_name = (raw_name.replace(" Night", "").strip() or f"day {len(self.dayname) + 1}").lower()
                            
                            self.dayname.append(base_name)
                            self.meowfc.append(period.get("icon", ""))
                            start_time = period.get("startTime", "")
                            self.meowdates.append(start_time[:10] if start_time else "")

                            # For night-only periods, use the same temp for high/low
                            night_temp = night_period.get("temperature", "")
                            self.meowtp.append(str(night_temp))
                            self.meowlt.append(str(night_temp))
                            
                            night_forecast = night_period.get("detailedForecast", night_period.get("shortForecast", "no forecast available")).lower()
                            self.detail.append(f"<h3>{base_name}</h3>{night_forecast}")
                            
                            logger.debug(f"Processed forecast night {len(self.dayname)-1}: {base_name} ({night_temp}°F)")
                            i += 1
                            
                    except Exception as e:
                        logger.warning(f"Error processing forecast period {i}: {str(e)}")
                        # Add placeholder data for this period
                        self.dayname.append(f"day {len(self.dayname)}")
                        self.meowfc.append("")
                        self.meowdates.append("")
                        self.meowtp.append("")
                        self.meowlt.append(str(self._get_current_temp_or_default() - 15))
                        self.detail.append(f"<h3>day {len(self.dayname)-1}</h3>No forecast available")
                        i += 1
                
                logger.info(f"Processed {len(self.dayname)} forecast periods")
            elif (
                hasattr(self.meow, "jforecast")
                and self.meow.jforecast
                and isinstance(self.meow.jforecast, list)
            ):
                # Handle Canadian/European list format: [{'date': '2024-01-01', 'high': 20, 'low': 10, 'condition': '...'}, ...]
                logger.info("Processing forecast data from jforecast (list format)")
                forecast_items = self.meow.jforecast  # All available days

                for i, item in enumerate(forecast_items):
                    try:
                        d = datetime.strptime(item.get("date", ""), "%Y-%m-%d").date()
                        day_name = "today" if d == _date.today() else d.strftime("%A").lower()
                    except (ValueError, TypeError):
                        day_name = "today" if i == 0 else f"day {i + 1}"
                    self.dayname.append(day_name)
                    self.meowfc.append("")
                    self.meowdates.append(item.get("date", ""))
                    
                    # Extract temperatures
                    high_temp = item.get('high', '')
                    low_temp = item.get('low', '')
                    
                    # Convert to Fahrenheit if needed (Canadian data might be in Celsius)
                    try:
                        if isinstance(high_temp, (int, float)):
                            # Convert from Celsius to Fahrenheit for display consistency
                            high_temp_f = int(high_temp * 9/5 + 32)
                            self.meowtp.append(str(high_temp_f))
                        else:
                            # Ensure we don't pass through N/A values
                            temp_str = self._safe_temp_string(high_temp)
                            self.meowtp.append(temp_str)
                            
                        if isinstance(low_temp, (int, float)):
                            # Convert from Celsius to Fahrenheit for display consistency  
                            low_temp_f = int(low_temp * 9/5 + 32)
                            self.meowlt.append(str(low_temp_f))
                        else:
                            # Ensure we don't pass through N/A values  
                            temp_str = self._safe_temp_string(low_temp)
                            self.meowlt.append(temp_str)
                    except (ValueError, TypeError):
                        # Ensure we don't pass through N/A values in error cases
                        high_str = self._safe_temp_string(high_temp)
                        low_str = self._safe_temp_string(low_temp)
                        self.meowtp.append(high_str)
                        self.meowlt.append(low_str)
                    
                    # Add condition description
                    condition = item.get('condition', 'no forecast available').lower()
                    self.detail.append(f"<h3>{day_name}</h3>{condition}")
                
                logger.info(f"Processed {len(forecast_items)} forecast items from list format")
            else:
                logger.warning("No forecast data available")
                # Check if location failed completely vs partial data
                has_any_data = (self.meowtemp != "??" or self.meowobs != "unknown")
                
                if not has_any_data:
                    self.dayname.append("today")
                    self.meowfc.append("")
                    self.meowdates.append("")
                    self.meowtp.append("")
                    self.meowlt.append("")
                    self.detail.append("<h3>today</h3>Forecast data unavailable")
                else:
                    self.dayname.append("today")
                    self.meowfc.append("")
                    self.meowdates.append("")
                    self.meowtp.append("")
                    self.meowlt.append("")
                    self.detail.append("<h3>today</h3>Forecast not available")
        except Exception as e:
            logger.error(f"Error processing forecast: {str(e)}")
            logger.debug(traceback.format_exc())
            
        # Create meowforecast attribute for API consumption
        self._create_forecast_json()
        
    def _get_seasonal_fallback_temp(self):
        """Get reasonable fallback temperature based on current date"""
        import datetime
        import random
        month = datetime.datetime.now().month
        
        # Seasonal temperatures in Fahrenheit for fallback
        if month in [12, 1, 2]:  # Winter
            return random.randint(25, 45)
        elif month in [3, 4, 5]:  # Spring  
            return random.randint(50, 70)
        elif month in [6, 7, 8]:  # Summer
            return random.randint(70, 85)
        else:  # Fall (9, 10, 11)
            return random.randint(45, 65)
            
    def _get_current_temp_or_default(self):
        """Get current temperature or reasonable default"""
        try:
            if self.meowtemp and self.meowtemp != "??":
                # Try to extract numeric value from current temp
                import re
                temp_match = re.search(r'-?\d+', str(self.meowtemp))
                if temp_match:
                    return int(temp_match.group())
        except (ValueError, TypeError, AttributeError):
            pass
        
        # Fallback to seasonal temp
        return self._get_seasonal_fallback_temp()

    def _add_placeholder_forecast_day(self, day_index, show_unavailable=False):
        """Add placeholder data for a single forecast day"""
        self.dayname.append(f"day {day_index}")
        self.meowfc.append("")
        
        if show_unavailable:
            self.meowtp.append("")  # Empty string will be handled as "—" in display
            self.meowlt.append(str(self._get_current_temp_or_default() - 15))  # Use reasonable temp instead of empty
            self.detail.append(f"<h3>day {day_index}</h3>Forecast not available")
        else:
            # Provide reasonable placeholder temperatures instead of empty strings
            base_temp = 50  # Default reasonable temperature
            if len(self.meowtp) > 0:
                try:
                    base_temp = int(self.meowtp[-1]) if self.meowtp[-1] else 50
                except (ValueError, TypeError):
                    base_temp = 50
            self.meowtp.append(str(base_temp))
            self.meowlt.append(str(base_temp - 10))
            self.detail.append(f"<h3>day {day_index}</h3>Extended forecast unavailable")

    def _extract_conditions_data(self):
        """Extract current conditions from different weather API formats"""
        try:
            conditions = self.meow.jconditions
            
            # NOAA format (GeoJSON features)
            if isinstance(conditions, dict) and "features" in conditions and conditions["features"]:
                feature = conditions["features"][0]["properties"]
                
                self.meowobs = feature.get("textDescription", "unknown")

                if "temperature" in feature:
                    self.meowtemp = str(int(round(self.cel2fahr(feature["temperature"]))))

                if "dewpoint" in feature:
                    self.meowdp = str(int(round(self.cel2fahr(feature["dewpoint"]))))

                if "seaLevelPressure" in feature:
                    self.meowbp = str(int(self.pa2inches(feature["seaLevelPressure"])))

                if "features" in conditions:
                    self.meowbptrend = self.check_pressure_trend(conditions["features"])
            
            # Environment Canada format (nested properties structure)
            elif (isinstance(conditions, dict) and "type" in conditions and conditions["type"] == "Feature" 
                  and "properties" in conditions):
                properties = conditions["properties"]
                
                self.meowobs = properties.get("textDescription", "unknown")

                # Handle nested temperature structure
                if "temperature" in properties and isinstance(properties["temperature"], dict):
                    temp_celsius = properties["temperature"].get("value")
                    if temp_celsius is not None:
                        self.meowtemp = str(int(round(self.cel2fahr(temp_celsius))))

                # Handle barometric pressure
                if "barometricPressure" in properties and isinstance(properties["barometricPressure"], dict):
                    pressure_pa = properties["barometricPressure"].get("value")
                    if pressure_pa is not None:
                        self.meowbp = str(round(self.pa2inches(pressure_pa), 2))
                        
                # Set a default pressure trend for Environment Canada
                self.meowbptrend = "steady"
                    
            # Met.no format (direct properties)
            elif isinstance(conditions, dict) and "temperature" in conditions:
                self.meowobs = conditions.get("condition", "unknown")
                
                if "temperature" in conditions:
                    temp_c = conditions["temperature"]
                    self.meowtemp = str(int(round(self.cel2fahr(temp_c))))
                    
                if "dewpoint" in conditions:
                    dewpoint_c = conditions["dewpoint"] 
                    self.meowdp = str(int(round(self.cel2fahr(dewpoint_c))))
                    
                if "pressure" in conditions:
                    pressure_hpa = conditions["pressure"]
                    # Convert hPa to inches of mercury (1 hPa = 0.02953 inHg)
                    self.meowbp = f"{pressure_hpa * 0.02953:.2f}"
                    
                # Set a default pressure trend for non-NOAA sources
                self.meowbptrend = "steady"
            
        except Exception as e:
            logger.error(f"Error extracting conditions data: {str(e)}")
            logger.debug(traceback.format_exc())

        logger.info(f"place: {self.meowplace}")

        # Reset lists for forecast data
        self.meowfc = []  # forecast icon (sunny, cloudy, etc.)
        self.meowtp = []  # forecast high temp
        self.meowlt = []  # forecast low temp
        self.dayname = []  # forecast element label
        self.detail = []  # detailed forecast

        try:
            if (
                hasattr(self.meow, "jforecast")
                and self.meow.jforecast
                and "properties" in self.meow.jforecast
                and "periods" in self.meow.jforecast["properties"]
            ):
                periods = self.meow.jforecast["properties"]["periods"]
                
                # Check if this looks like NOAA-style alternating day/night periods
                has_is_daytime = any(period.get("isDaytime") is not None for period in periods[:3])
                
                if has_is_daytime:
                    # Process NOAA-style alternating day/night periods into daily forecasts
                    logger.debug("Processing NOAA-style day/night periods")
                    daily_forecasts = []
                    
                    i = 0
                    while i < len(periods) and len(daily_forecasts) < 5:
                        day_period = None
                        night_period = None
                        
                        # Look for day period first
                        if i < len(periods) and periods[i].get("isDaytime"):
                            day_period = periods[i]
                            i += 1
                            # Look for matching night period
                            if i < len(periods) and not periods[i].get("isDaytime"):
                                night_period = periods[i]
                                i += 1
                        elif i < len(periods) and not periods[i].get("isDaytime"):
                            # Start with night period
                            night_period = periods[i]
                            i += 1
                            # Look for next day period  
                            if i < len(periods) and periods[i].get("isDaytime"):
                                day_period = periods[i]
                                i += 1
                        else:
                            i += 1
                            continue
                        
                        # Create daily forecast from day/night pair
                        if day_period or night_period:
                            primary_period = day_period or night_period
                            day_name = primary_period.get("name", f"day {len(daily_forecasts) + 1}").lower()

                            # Clean up day names for consistency
                            if "tonight" in day_name:
                                day_name = "today"
                            elif "tomorrow" in day_name and "night" in day_name:
                                day_name = "tomorrow"
                            
                            high_temp = day_period.get("temperature", "") if day_period else ""
                            low_temp = night_period.get("temperature", "") if night_period else ""
                            
                            # Fix missing temperatures - ensure we always have valid values
                            if not high_temp and low_temp:
                                # Use night temp + 10 as a reasonable high temp estimate
                                try:
                                    high_temp = int(low_temp) + 10
                                except (ValueError, TypeError):
                                    high_temp = 60  # Default
                            elif not low_temp and high_temp:
                                # Use day temp - 10 as a reasonable low temp estimate
                                try:
                                    low_temp = int(high_temp) - 10
                                except (ValueError, TypeError):
                                    low_temp = 40  # Default
                            elif not high_temp and not low_temp:
                                # No temperatures available - use reasonable defaults
                                high_temp = 60
                                low_temp = 40
                            
                            # Use day period for icon and description if available
                            icon = day_period.get("icon", "") if day_period else night_period.get("icon", "")
                            description = day_period.get("detailedForecast", "") if day_period else night_period.get("detailedForecast", "")
                            
                            daily_forecasts.append({
                                'name': day_name.lower(),
                                'icon': icon,
                                'high': str(high_temp),
                                'low': str(low_temp),
                                'description': description
                            })
                    
                    # Add daily forecasts to arrays
                    for daily in daily_forecasts:
                        self.dayname.append(daily['name'])
                        self.meowfc.append(daily['icon'])
                        self.meowtp.append(daily['high'])
                        self.meowlt.append(daily['low'])
                        self.detail.append(f"<h3>{daily['name']}</h3>{daily['description'].lower()}")
                        
                else:
                    # Process as simple period list (original logic for non-NOAA format)
                    logger.debug("Processing simple period list")
                    for i in range(min(5, len(periods))):
                        try:
                            period = periods[i]
                            self.dayname.append(period.get("name", f"Day {i}").lower())
                            self.meowfc.append(period.get("icon", ""))
                            temp_value = period.get("temperature", "")
                            self.meowtp.append(self._safe_temp_string(temp_value))
                            temp_value = period.get("temperature", "")
                            self.meowlt.append(self._safe_temp_string(temp_value))
                            self.detail.append(
                                "<h3>{0}</h3>{1}".format(
                                    period.get("name", f"day {i}").lower(),
                                    period.get("detailedForecast", "no forecast available").lower(),
                                )
                            )
                        except Exception as e:
                            logger.warning(f"Error processing forecast period {i}: {str(e)}")
                            self._add_placeholder_forecast_day(i)

                # Fill with placeholders if we don't have 5 periods
                while len(self.dayname) < 5:
                    i = len(self.dayname)
                    self._add_placeholder_forecast_day(i)
            else:
                logger.warning("No forecast data available")
                # Check if location failed completely vs partial data
                has_any_data = (self.meowtemp != "??" or self.meowobs != "unknown")
                
                if not has_any_data:
                    self.dayname.append("today")
                    self.meowfc.append("")
                    self.meowdates.append("")
                    self.meowtp.append("")
                    self.meowlt.append("")
                    self.detail.append("<h3>today</h3>Forecast data unavailable")
                else:
                    self.dayname.append("today")
                    self.meowfc.append("")
                    self.meowdates.append("")
                    self.meowtp.append("")
                    self.meowlt.append("")
                    self.detail.append("<h3>today</h3>Forecast not available")
        except Exception as e:
            logger.error(f"Error processing forecast: {str(e)}")
            logger.debug(traceback.format_exc())
            
        # Create meowforecast attribute for API consumption
        self._create_forecast_json()

    def _create_conditions_html(self):
        tr = "<tr>", "</tr>"
        td = "<td>", "</td>"
        tdc = "<td class='one'>"

        try:
            # Check if we have adequate weather data
            has_temp = self.meowtemp != "??"
            has_conditions = self.meowobs != "unknown"
            has_pressure = self.meowbp != "??"
            has_dewpoint = self.meowdp != "??"
            
            # If this looks like a failed lookup, provide a better message but still show forecast
            if not has_temp and not has_conditions:
                if is_canadian_location(self.location):
                    self.wxmeow = f"<h1>{self.meowplace}</h1><h2>Canadian Location</h2><p>Current conditions not available. Forecast data shown below.</p>"
                elif is_european_location(self.location):
                    self.wxmeow = f"<h1>{self.meowplace}</h1><h2>European Location</h2><p>Current conditions not available. Forecast data shown below.</p>"
                else:
                    self.wxmeow = f"<h1>{self.meowplace}</h1><h2>Weather Data Limited</h2><p>Current conditions not available. Forecast data shown below.</p>"
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
        forecast_table = '<div class="forecast-container" id="forecast-container" style="overflow-x: auto; -webkit-overflow-scrolling: touch; margin: 0;">\n'
        forecast_table += '<table class="weather-forecast-table" style="width: max-content; border-collapse: separate; border-spacing: 6px;">\n'
        forecast_table += '<tr class="day-headers">\n'

        # Add 12-hour period headers
        for i in range(5):
            period_label = (
                f"{self.dayname[i]}<br><small></small>"
                if i < len(self.dayname)
                else f"Period {i + 1}<br><small></small>"
            )
            forecast_table += f'<td style="text-align: center; padding: 4px; white-space: nowrap; font-weight: bold; font-size: 1em;"><span id="date-{i}" class="date-header">{period_label}</span></td>\n'

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

                forecast_table += f'<td style="text-align: center; padding: 4px; cursor: pointer; min-width: 140px;" id="{i}" class="day-selector weather-icon-cell" onclick="{onclick_handler}" role="button" aria-label="Select period {i + 1} forecast" tabindex="0">\n'

                if icon_url:
                    large_icon_url = icon_url.replace('size=small', 'size=large').replace('size=medium', 'size=large')
                    forecast_table += f'<img src="{large_icon_url}" alt="Weather forecast" style="display: block; margin: 0 auto; width: 160px; height: 160px;" />\n'
                else:
                    day_num = i + 1 if i > 0 else "today"
                    forecast_table += f'<div style="width: 160px; height: 160px; background: #f0f0f0; border: 1px solid #ccc; display: flex; align-items: center; justify-content: center; margin: 0 auto; font-size: 11px; flex-direction: column;"><div>day</div><div>{day_num}</div></div>\n'

                forecast_table += "</td>\n"
            except Exception as e:
                logger.warning(f"Error generating weather icon for day {i}: {str(e)}")
                logger.debug(
                    f"Weather condition was: '{weather_condition if 'weather_condition' in locals() else 'unknown'}'"
                )
                onclick_handler = f"selectDay({i}, event); return false;"
                forecast_table += f'<td style="text-align: center; padding: 4px; cursor: pointer; min-width: 140px;" id="{i}" class="day-selector weather-icon-cell" onclick="{onclick_handler}">\n'
                forecast_table += '<div style="width: 160px; height: 160px; background: #f0f0f0; border: 1px solid #ccc; display: flex; align-items: center; justify-content: center; margin: 0 auto; font-size: 11px;">?</div>'
                forecast_table += "</td>\n"

        forecast_table += '</tr>\n<tr class="temperatures">\n'

        # Add temperatures with additional N/A protection for Canadian forecasts
        for i in range(5):
            temp_value = self.meowtp[i] if i < len(self.meowtp) else ""
            temp_display = self._format_temperature_safe(temp_value)
            
            # Extra safety check to ensure no N/A values slip through
            if any(na_pattern in str(temp_display).lower() for na_pattern in ['n/a', 'na', 'n.a', 'null', 'undefined', 'error']):
                temp_display = "—"  # Replace any N/A that somehow got through
                logger.warning(f"Caught N/A value in temperature display for day {i}: {temp_value} -> replaced with —")
            
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
            futuretext += f'<div id="hourly-temperature-chart-{i}" class="hourly-chart" style="display:{chart_display}; width:100%; max-width:800px; margin:16px auto; min-height:200px;"></div>'
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

    def _format_temperature_safe(self, temp_value):
        """
        Safely format temperature value, filtering out N/A and invalid values.
        Returns either a formatted temperature string or em dash for invalid values.
        Enhanced protection against Canadian forecast N/A values.
        """
        # Comprehensive list of values to treat as unavailable/invalid
        invalid_values = {
            None, "", "N/A", "n/a", "NA", "na", "??", "None", "NONE", 
            "null", "NULL", "undefined", "UNDEFINED", "NaN", "nan",
            "-", "--", "---", "...", "TBD", "tbd", "Unknown", "unknown",
            "UNKNOWN", "nil", "NIL", "void", "VOID", "missing", "MISSING",
            "unavailable", "UNAVAILABLE", " ", "  ", "\t", "\n",
            # Additional edge cases that could appear in weather data
            "no_data", "NO_DATA", "error", "ERROR", "fail", "FAIL",
            "timeout", "TIMEOUT", "invalid", "INVALID", "#N/A", "#n/a",
            "---°F", "n/a°F", "N/A°F", "??°F", "—°F", "--°F",
            # Additional Canadian-specific edge cases
            "n.a.", "N.A.", "not available", "NOT AVAILABLE", "no data",
            "NO DATA", "data unavailable", "DATA UNAVAILABLE"
        }
        
        # Check if value is in invalid set or string representation is invalid
        if temp_value in invalid_values:
            logger.debug(f"Filtered invalid temperature value (direct match): {temp_value!r}")
            return "—"  # em dash for unavailable
        
        # Check string representation for invalid values with enhanced pattern matching
        temp_str = str(temp_value).strip()
        temp_str_lower = temp_str.lower()
        
        # Enhanced pattern matching for N/A variations with stricter checking
        if (not temp_str or 
            temp_str_lower in {v.lower() if isinstance(v, str) else v for v in invalid_values} or
            'n/a' in temp_str_lower or 
            'n.a' in temp_str_lower or
            temp_str_lower.startswith('na') or
            'unavailable' in temp_str_lower or
            'error' in temp_str_lower or
            'fail' in temp_str_lower or
            temp_str_lower in ['?', '??', '???'] or
            # Additional patterns that might appear in weather APIs
            'invalid' in temp_str_lower or
            'timeout' in temp_str_lower or
            temp_str_lower.startswith('err') or
            temp_str_lower.startswith('no') or
            len(temp_str.strip()) == 0):
            
            logger.debug(f"Filtered invalid temperature value (enhanced pattern match): {temp_value!r} -> '{temp_str}'")
            return "—"
        
        # Try to convert to numeric value
        try:
            # Handle both string and numeric inputs
            if isinstance(temp_value, (int, float)):
                # Check for special float values
                if not (-200 <= temp_value <= 200):  # Reasonable temperature range
                    logger.debug(f"Temperature out of reasonable range: {temp_value}")
                    return "—"
                temp_num = int(temp_value)
            else:
                # Strip whitespace and convert
                if not temp_str:  # Empty after stripping
                    return "—"
                    
                # Remove any trailing units (°F, °C, F, C) before conversion
                clean_str = temp_str.rstrip('°FfCc ')
                if not clean_str:
                    return "—"
                    
                temp_num = int(float(clean_str))  # Handle decimal inputs
                
                # Validate reasonable temperature range
                if not (-200 <= temp_num <= 200):
                    logger.debug(f"Converted temperature out of reasonable range: {temp_num}")
                    return "—"
            
            # Final validation - ensure we have a valid integer
            if not isinstance(temp_num, int):
                logger.debug(f"Temperature not an integer after conversion: {temp_num}")
                return "—"
            
            return f"{temp_num}°F"
        except (ValueError, TypeError, AttributeError, OverflowError) as e:
            logger.debug(f"Error converting temperature value '{temp_value}': {e}")
            return "—"

    def _safe_temp_string(self, temp_value):
        """
        Safely convert temperature value to string, filtering out N/A values.
        Returns empty string for invalid values to prevent N/A from getting into data.
        Enhanced for Canadian weather data edge cases.
        """
        invalid_values = {
            None, "", "N/A", "n/a", "NA", "na", "??", "None", "NONE", 
            "null", "NULL", "undefined", "UNDEFINED", "NaN", "nan",
            "-", "--", "---", "...", "TBD", "tbd", "Unknown", "unknown",
            "UNKNOWN", "nil", "NIL", "void", "VOID", "missing", "MISSING",
            "unavailable", "UNAVAILABLE", " ", "  ", "\t", "\n",
            # Additional edge cases that could appear in weather data
            "no_data", "NO_DATA", "error", "ERROR", "fail", "FAIL",
            "timeout", "TIMEOUT", "invalid", "INVALID", "#N/A", "#n/a",
            # Additional Canadian-specific patterns
            "n.a.", "N.A.", "not available", "NOT AVAILABLE", "no data",
            "NO DATA", "data unavailable", "DATA UNAVAILABLE"
        }
        
        # Check if value is in invalid set
        if temp_value in invalid_values:
            logger.debug(f"_safe_temp_string filtered invalid value (direct match): {temp_value!r}")
            return ""
        
        # Enhanced string representation checking for invalid values
        temp_str = str(temp_value).strip()
        temp_str_lower = temp_str.lower()
        
        # Enhanced pattern matching for N/A variations and error conditions with stricter checking
        if (not temp_str or 
            temp_str_lower in {v.lower() if isinstance(v, str) else v for v in invalid_values} or
            'n/a' in temp_str_lower or 
            'n.a' in temp_str_lower or
            temp_str_lower.startswith('na') or
            'unavailable' in temp_str_lower or
            'error' in temp_str_lower or
            'fail' in temp_str_lower or
            temp_str_lower in ['?', '??', '???'] or
            # Additional patterns that might slip through
            'invalid' in temp_str_lower or
            'timeout' in temp_str_lower or
            temp_str_lower.startswith('err') or
            temp_str_lower.startswith('no') or
            len(temp_str.strip()) == 0):
            
            logger.debug(f"_safe_temp_string filtered invalid value (enhanced pattern match): {temp_value!r} -> '{temp_str}'")
            return ""
        
        try:
            if isinstance(temp_value, (int, float)):
                # Check for special float values and reasonable temperature range
                if not (-200 <= temp_value <= 200):
                    logger.debug(f"Temperature out of reasonable range: {temp_value}")
                    return ""
                return str(int(temp_value))
            else:
                # Handle string inputs
                clean_str = temp_str.rstrip('°FfCc ')
                if not clean_str:
                    return ""
                    
                temp_num = float(clean_str)
                
                # Validate range
                if not (-200 <= temp_num <= 200):
                    logger.debug(f"String temperature out of reasonable range: {temp_num}")
                    return ""
                    
                # Ensure we return a valid integer string
                result = str(int(temp_num))
                
                # Final validation - make sure result doesn't contain invalid patterns
                if any(invalid in result.lower() for invalid in ['n/a', 'na', 'null', 'undefined', 'error']):
                    logger.debug(f"Invalid pattern found in final result: {result}")
                    return ""
                    
                return result
        except (ValueError, TypeError, AttributeError, OverflowError) as e:
            logger.debug(f"Error processing temperature value '{temp_value}': {e}")
            return ""

    def reload(self) -> None:
        """
        Get a fresh read from NOAA API, with optimized fallback to Environment Canada for Canadian locations.
        """
        max_retries = 2  # Try up to 2 times (initial + 1 retry)
        retry_count = 0
        
        # Check location type for appropriate weather source
        is_canadian = is_canadian_location(self.location)
        is_european = is_european_location(self.location)
        
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
                elif is_european:
                    # For European locations, try Met.no first
                    try:
                        logger.info(f"Trying Met.no weather service for European location '{self.location}'")
                        self.meow = metno(self.location, include_hourly=self.include_hourly)
                        logger.info(f"Successfully used Met.no weather service for '{self.location}'")
                    except (LocationError, ApiError) as europe_error:
                        logger.info(f"Met.no weather service failed for '{self.location}': {europe_error}")
                        # Try coordinate-based fallback for European locations near US bases or international areas
                        coords = get_coordinates(self.location)
                        if coords:
                            logger.info(f"Trying coordinate-based fallback for European location '{self.location}'")
                            try:
                                # For some European locations, NOAA might have data from US military bases or international areas
                                self.meow = noaa(f"{coords[0]},{coords[1]}", include_hourly=self.include_hourly)
                                logger.info(f"Successfully fetched European location '{self.location}' using coordinate fallback")
                            except (LocationError, ApiError):
                                logger.info(f"Coordinate fallback also failed for '{self.location}'")
                                # Create enhanced fallback data with better information
                                self.meow = self._create_enhanced_european_fallback(self.location, coords)
                                logger.info(f"Created enhanced fallback data for European location '{self.location}'")
                        else:
                            raise europe_error
                else:
                    # For US and other locations, use NOAA
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
                        
                        # Validate and clean temperature value with enhanced filtering
                        validated_temp = self._safe_temp_string(temp)
                        if validated_temp and validated_temp.strip():
                            # Additional validation - ensure the result is numeric
                            try:
                                temp_int = int(validated_temp)
                                # Range check
                                if -200 <= temp_int <= 200:
                                    temp = temp_int
                                else:
                                    logger.debug(f"Hourly temperature out of range: {temp_int}")
                                    temp = None
                            except (ValueError, TypeError):
                                logger.debug(f"Could not convert validated temp to int: '{validated_temp}'")
                                temp = None
                        else:
                            temp = None  # Use None for invalid temperatures

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
                                "value", 0
                            ),
                        }
                        hourly_data.append(hourly_item)
                    except Exception as e:
                        logger.warning(f"Error processing hourly period: {str(e)}")
                        continue

                self.meowhourly = hourly_data
                
                # Additional safety filter to ensure no N/A values in JSON serialization
                self._clean_hourly_data()
                
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

    def _validate_forecast_json(self, forecast_items):
        """
        Final validation pass to ensure no N/A values make it into the forecast JSON.
        This provides absolute protection against any edge cases.
        """
        invalid_patterns = {
            'N/A', 'n/a', 'NA', 'na', 'null', 'NULL', 'undefined', 'UNDEFINED',
            'NaN', 'nan', 'None', 'NONE', '??', '???', 'error', 'ERROR',
            'fail', 'FAIL', 'invalid', 'INVALID', 'unavailable', 'UNAVAILABLE',
            'timeout', 'TIMEOUT', '--', '---', 'n.a.', 'N.A.',
            'no data', 'NO DATA', 'not available', 'NOT AVAILABLE'
        }
        
        validated_items = []
        
        for item in forecast_items:
            validated_item = item.copy()
            
            # Validate temperature values
            for temp_key in ['high', 'low']:
                temp_value = validated_item.get(temp_key)
                
                if temp_value is None:
                    continue  # None is acceptable
                
                # Check for invalid string patterns
                if isinstance(temp_value, str):
                    temp_str = str(temp_value).strip()
                    if (temp_str in invalid_patterns or
                        not temp_str or
                        any(pattern.lower() in temp_str.lower() for pattern in invalid_patterns) or
                        temp_str.lower().startswith(('n/a', 'na', 'error', 'fail', 'invalid'))):
                        logger.warning(f"Removing invalid temperature value in forecast JSON: '{temp_value}'")
                        validated_item[temp_key] = None
                        continue
                    
                    # Try to convert to integer
                    try:
                        temp_num = int(float(temp_str))
                        if -200 <= temp_num <= 200:
                            validated_item[temp_key] = temp_num
                        else:
                            logger.warning(f"Temperature out of range in forecast JSON: {temp_num}")
                            validated_item[temp_key] = None
                    except (ValueError, TypeError):
                        logger.warning(f"Could not convert temperature in forecast JSON: '{temp_str}'")
                        validated_item[temp_key] = None
                
                # Validate numeric values
                elif isinstance(temp_value, (int, float)):
                    if not (-200 <= temp_value <= 200):
                        logger.warning(f"Numeric temperature out of range in forecast JSON: {temp_value}")
                        validated_item[temp_key] = None
                    else:
                        validated_item[temp_key] = int(temp_value)
                else:
                    # Unknown type, set to None
                    logger.warning(f"Unknown temperature type in forecast JSON: {type(temp_value)}")
                    validated_item[temp_key] = None
            
            # Validate condition string
            condition = validated_item.get('condition', '')
            if isinstance(condition, str):
                condition_str = condition.strip()
                if condition_str in invalid_patterns or any(pattern.lower() in condition_str.lower() for pattern in ['n/a', 'error', 'fail', 'invalid']):
                    logger.warning(f"Cleaning invalid condition in forecast JSON: '{condition}'")
                    validated_item['condition'] = "Unknown"
                else:
                    validated_item['condition'] = condition_str
            else:
                validated_item['condition'] = "Unknown"
            
            # Ensure precipitation is valid
            precip = validated_item.get('precip')
            if precip is None or (isinstance(precip, str) and precip.strip() in invalid_patterns):
                validated_item['precip'] = 0
            elif isinstance(precip, (int, float)) and 0 <= precip <= 100:
                validated_item['precip'] = precip
            else:
                validated_item['precip'] = 0
            
            validated_items.append(validated_item)
        
        logger.debug(f"Validated {len(validated_items)} forecast items for N/A protection")
        return validated_items

    def _process_alerts(self) -> None:
        """Build alert HTML from NOAA active alerts data."""
        self.alerts = []
        self.meow_alerts = ""

        try:
            if not hasattr(self.meow, "jalerts") or not self.meow.jalerts:
                return

            features = self.meow.jalerts.get("features", [])
            if not features:
                return

            severity_class = {
                "Extreme": "wx-alert-extreme",
                "Severe": "wx-alert-severe",
                "Moderate": "wx-alert-moderate",
                "Minor": "wx-alert-minor",
            }

            html = '<div class="wx-alerts">\n'
            for feature in features:
                props = feature.get("properties", {})
                event = props.get("event", "weather alert").lower()
                severity = props.get("severity", "Unknown")
                area = props.get("areaDesc", "").lower()
                expires = props.get("expires", "")
                headline = props.get("headline", "").lower()
                web = props.get("web", "")

                # Format expires time as readable string
                expires_str = ""
                if expires:
                    try:
                        from datetime import datetime
                        import re
                        # Strip timezone offset for parsing
                        dt_str = re.sub(r'[+-]\d{2}:\d{2}$', '', expires)
                        dt = datetime.fromisoformat(dt_str)
                        expires_str = f"until {dt.strftime('%-I:%M %p').lower()} on {dt.strftime('%a %-m/%-d')}"
                    except Exception:
                        expires_str = ""

                css_class = severity_class.get(severity, "")
                link = f' | <a href="{web}">details</a>' if web else ""

                html += f'<div class="wx-alert {css_class}">\n'
                html += f'  <strong>{event}</strong>\n'
                if area:
                    html += f'  <span class="wx-alert-area">{area}</span>\n'
                if expires_str or link:
                    html += f'  <p class="wx-alert-expires">{expires_str}{link}</p>\n'
                html += '</div>\n'

                self.alerts.append({"event": event, "severity": severity, "area": area})

            html += '</div>\n'
            self.meow_alerts = html
            logger.info(f"Processed {len(features)} weather alerts")

        except Exception as e:
            logger.warning(f"Error processing alerts: {e}")
            self.meow_alerts = ""

    def _create_forecast_json(self):
        """
        Create forecast JSON data for API consumption from processed forecast arrays.
        """
        try:
            from datetime import datetime, timedelta
            forecast_items = []
            
            # Use the shorter of the available lists to avoid index errors
            forecast_count = min(len(self.dayname), len(self.meowfc), len(self.meowtp), len(self.meowlt))
            
            for i in range(forecast_count):
                # Convert generic day names to actual dates
                raw_date = self.dayname[i] if i < len(self.dayname) else f"day {i}"
                
                if raw_date.lower() == "today":
                    date = datetime.now().strftime("%Y-%m-%d")
                elif raw_date.lower() == "tomorrow":
                    date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                elif raw_date.startswith("day "):
                    try:
                        day_offset = int(raw_date.split()[1])
                        date = (datetime.now() + timedelta(days=day_offset)).strftime("%Y-%m-%d")
                    except (ValueError, IndexError):
                        date = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
                else:
                    # Use as-is for proper date strings, or generate date for index
                    date = raw_date if '-' in raw_date else (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
                
                # Get the condition from forecast data first, fall back to detail HTML
                condition = ""
                
                # Try to get condition from original forecast periods if available
                if hasattr(self.meow, 'jforecast') and self.meow.jforecast:
                    try:
                        if isinstance(self.meow.jforecast, dict) and 'properties' in self.meow.jforecast:
                            periods = self.meow.jforecast['properties'].get('periods', [])
                            if i < len(periods):
                                period = periods[i]
                                # Use shortForecast if available, otherwise detailedForecast
                                condition = period.get('shortForecast') or period.get('detailedForecast', '')
                                if condition and condition != '':
                                    # Clean up the condition text
                                    if 'Simulated weather data for' in condition:
                                        # Extract just the weather description from simulated data
                                        parts = condition.split('. ')
                                        condition = parts[-1] if len(parts) > 1 else condition
                    except (KeyError, TypeError, IndexError):
                        pass  # Fall back to detail extraction
                
                # If we didn't get a good condition from forecast periods, try detail HTML
                if condition == "" and i < len(self.detail) and self.detail[i]:
                    # Extract condition description from detail HTML
                    detail_text = self.detail[i]
                    if "No forecast" in detail_text or "not available" in detail_text or "unavailable" in detail_text:
                        condition = ""
                    else:
                        # Extract text content from HTML, remove <h3> tags
                        import re
                        # Remove the <h3>day name</h3> part and get the remaining text
                        text_content = re.sub(r'<h3>[^<]+</h3>', '', detail_text).strip()
                        if text_content:
                            condition = text_content
                        else:
                            condition = "Unknown"
                
                # Get temperatures - handle both string and numeric values
                high_temp = None
                low_temp = None
                
                if i < len(self.meowtp) and self.meowtp[i]:
                    try:
                        # Use safe string validation - no need to check again since data is already filtered
                        if self.meowtp[i]:  # Just check if non-empty since _safe_temp_string already filtered
                            high_temp = int(self.meowtp[i])
                    except (ValueError, TypeError):
                        high_temp = None
                        
                if i < len(self.meowlt) and self.meowlt[i]:
                    try:
                        # Use safe string validation - no need to check again since data is already filtered
                        if self.meowlt[i]:  # Just check if non-empty since _safe_temp_string already filtered
                            low_temp = int(self.meowlt[i])
                    except (ValueError, TypeError):
                        low_temp = None
                
                # Fix temperature inversion issue - ensure high >= low
                if high_temp is not None and low_temp is not None:
                    if high_temp < low_temp:
                        # Swap them
                        high_temp, low_temp = low_temp, high_temp
                        logger.debug(f"Fixed temperature inversion for day {i}: swapped high/low temperatures")
                
                forecast_item = {
                    "date": date,
                    "condition": condition,
                    "high": high_temp,
                    "low": low_temp,
                    "precip": 0  # No precipitation data available - use 0 instead of None
                }
                
                forecast_items.append(forecast_item)
            
            # Final validation pass to ensure absolutely no N/A values in forecast JSON
            self.meowforecast = self._validate_forecast_json(forecast_items)
            logger.info(f"Created forecast JSON with {len(self.meowforecast)} items")
            
        except Exception as e:
            logger.error(f"Error creating forecast JSON: {str(e)}")
            logger.debug(traceback.format_exc())
            # Create empty forecast on error
            self.meowforecast = []


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

    def cel2fahr(self, val) -> float:
        """
        Convert Celsius to Fahrenheit if needed.

        Args:
            val: Temperature value - can be a dictionary with unitCode and value (NOAA format)
                 or a simple numeric value (Environment Canada format)

        Returns:
            Temperature value in Fahrenheit
        """
        c_desc = ["degc", "c", "celsius", "centegrade", "cel", "centigrade"]
        try:
            # Handle NOAA-style dictionary format
            if isinstance(val, dict):
                if "unitCode" in val and "value" in val and val["value"] is not None:
                    if any(c in val["unitCode"].lower() for c in c_desc):
                        return float(val["value"]) * 9.0 / 5.0 + 32.0
                    return float(val["value"])
            # Handle simple numeric value (assume Celsius for Environment Canada)
            elif isinstance(val, (int, float)):
                return float(val) * 9.0 / 5.0 + 32.0
            # Handle string numeric value
            elif isinstance(val, str) and val.replace('.', '').replace('-', '').isdigit():
                return float(val) * 9.0 / 5.0 + 32.0
        except Exception as e:
            logger.error(f"Error converting Celsius to Fahrenheit: {str(e)}")
            return 0.0
        return 0.0

    def pa2inches(self, val) -> float:
        """
        Convert Pascal to inches of mercury.

        Args:
            val: Pressure value - can be a dictionary with unitCode and value (NOAA format)
                 or a simple numeric value (Environment Canada format)

        Returns:
            Pressure value in inches of mercury
        """
        pa_desc = ["pa", "pascal"]
        try:
            # Handle NOAA-style dictionary format
            if isinstance(val, dict):
                if "unitCode" in val and "value" in val and val["value"] is not None:
                    if any(p in val["unitCode"].lower() for p in pa_desc):
                        return float(val["value"]) * 0.0002953
                    return float(val["value"])
            # Handle simple numeric value (assume Pascals for Environment Canada)
            elif isinstance(val, (int, float)):
                return float(val) * 0.0002953
            # Handle string numeric value
            elif isinstance(val, str) and val.replace('.', '').replace('-', '').isdigit():
                return float(val) * 0.0002953
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
    width: 160px;
    height: 160px;
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
                  return;
              }

              // Destroy existing chart
              if (charts[dayIndex]) {
                  charts[dayIndex].destroy();
                  charts[dayIndex] = null;
              }

              // Filter hourly data by the actual date stored in the day cell's data-date attribute
              const selectedCell = document.getElementById(String(dayIndex));
              const targetDate = selectedCell ? selectedCell.getAttribute('data-date') : null;
              let filteredData;
              if (targetDate && targetDate.length === 10) {
                  filteredData = window.hourlyData.filter(function(item) {
                      return item.time && item.time.substring(0, 10) === targetDate;
                  });
                  if (filteredData.length === 0) {
                      // Fallback to index-based if no date match (e.g. cached data without dates)
                      const si = dayIndex * 24;
                      filteredData = window.hourlyData.slice(si, Math.min(si + 24, window.hourlyData.length));
                  }
              } else {
                  const si = dayIndex * 24;
                  filteredData = window.hourlyData.slice(si, Math.min(si + 24, window.hourlyData.length));
              }

              console.log("Day " + dayIndex + " (date=" + targetDate + "): filteredData.length=" + filteredData.length);

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
                  
                  // Safely extract temperature with validation
                  const tempValue = item.temperature || item.temp;
                  let validTemp = null;
                  
                  if (typeof tempValue === 'number' && tempValue >= -200 && tempValue <= 200) {
                      validTemp = tempValue;
                  } else if (typeof tempValue === 'string' && tempValue.trim() !== '') {
                      const parsed = parseFloat(tempValue.trim());
                      if (!isNaN(parsed) && parsed >= -200 && parsed <= 200) {
                          validTemp = parsed;
                      }
                  }
                  
                  temperatures.push(validTemp);
                  precipProbs.push(item.precip || 0);
              });
              
              // Filter out null temperatures and corresponding labels
              const validDataPoints = [];
              for (let i = 0; i < temperatures.length; i++) {
                  if (temperatures[i] !== null) {
                      validDataPoints.push({
                          label: labels[i],
                          temp: temperatures[i],
                          precip: precipProbs[i]
                      });
                  }
              }
              
              // If no valid temperatures, show error message
              if (validDataPoints.length === 0) {
                  chartContainer.innerHTML = "<p style='text-align: center; color: #666; font-style: italic;'>Temperature data not available for this day</p>";
                  return;
              }
              
              // Extract clean arrays
              const cleanLabels = validDataPoints.map(dp => dp.label);
              const cleanTemperatures = validDataPoints.map(dp => dp.temp);
              const cleanPrecipProbs = validDataPoints.map(dp => dp.precip);

              // Create canvas
              chartContainer.innerHTML = '<canvas id="chart-canvas-' + dayIndex + '" style="width: 100%; height: 200px;"></canvas>';
              const canvas = document.getElementById("chart-canvas-" + dayIndex);
              canvas.style.display = 'block';
              const ctx = canvas.getContext('2d');

              // Create chart (lo-fi: monochrome, no fill, straight lines)
              charts[dayIndex] = new Chart(ctx, {
                  type: 'line',
                  data: {
                      labels: cleanLabels,
                      datasets: [{
                          data: cleanTemperatures,
                          borderColor: "#333",
                          borderWidth: 1,
                          pointRadius: 2,
                          pointBackgroundColor: "#333",
                          fill: false,
                          tension: 0,
                          yAxisID: 'y'
                      }, {
                          data: cleanPrecipProbs,
                          borderColor: "#aaa",
                          borderWidth: 1,
                          borderDash: [3, 3],
                          pointRadius: 1,
                          pointBackgroundColor: "#aaa",
                          fill: false,
                          tension: 0,
                          yAxisID: 'precip'
                      }]
                  },
                  options: {
                      responsive: true,
                      maintainAspectRatio: false,
                      animation: { duration: 0 },
                      plugins: {
                          legend: { display: false },
                          tooltip: {
                              mode: 'index',
                              intersect: false,
                              callbacks: {
                                  label: function(context) {
                                      if (context.datasetIndex === 0) return context.parsed.y + '°f';
                                      return context.parsed.y + '% precip';
                                  }
                              }
                          }
                      },
                      scales: {
                          y: {
                              position: 'left',
                              beginAtZero: false,
                              grid: { color: 'rgba(0,0,0,0.06)' },
                              ticks: {
                                  font: { family: 'monospace', size: 10 },
                                  color: '#333',
                                  callback: function(val) { return val + '°'; }
                              },
                              border: { display: false }
                          },
                          precip: {
                              type: 'linear',
                              position: 'right',
                              min: 0,
                              max: 100,
                              grid: { drawOnChartArea: false },
                              ticks: {
                                  font: { family: 'monospace', size: 10 },
                                  color: '#aaa',
                                  stepSize: 50,
                                  callback: function(val) { return val + '%'; }
                              },
                              border: { display: false }
                          },
                          x: {
                              grid: { display: false },
                              ticks: {
                                  font: { family: 'monospace', size: 10 },
                                  color: '#333',
                                  maxRotation: 0
                              },
                              border: { display: false }
                          }
                      }
                  }
              });
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
               // Initially select day 0 (this will create the chart)
               setTimeout(function() { selectDay(0); }, 100);
           });
</script>
        """
        )
        self.js = javascript

    def _create_enhanced_european_fallback(self, location: str, coords: tuple) -> object:
        """
        Create enhanced fallback weather data for European locations.
        
        Args:
            location: The European location string
            coords: Tuple of (lat, lon) coordinates
            
        Returns:
            A mock weather object with basic location info and fallback data
        """
        class EuropeanFallback:
            def __init__(self, location, coords):
                self.city = location.split(',')[0].strip().title() if ',' in location else location.title()
                self.state = "Europe"
                self.lat = str(coords[0])
                self.lon = str(coords[1])
                self.jconditions = None
                self.jforecast = self._create_basic_forecast()
                self.jhourly = None
                
            def _create_basic_forecast(self):
                """Create a basic forecast structure"""
                return {
                    "properties": {
                        "periods": [
                            {
                                "name": f"day {i}",
                                "temperature": "",
                                "icon": "",
                                "detailedForecast": f"European weather data not available for this location. Try using more specific coordinates or a nearby major city."
                            } for i in range(5)
                        ]
                    }
                }
        
        return EuropeanFallback(location, coords)

    def _clean_hourly_data(self):
        """
        Final cleanup pass on hourly data to ensure no N/A values make it into JSON serialization.
        Enhanced to catch any edge cases that might slip through other filters.
        """
        if not self.meowhourly:
            return
            
        cleaned_data = []
        invalid_patterns = {
            'N/A', 'n/a', 'NA', 'na', 'null', 'NULL', 'undefined', 'UNDEFINED', 
            'NaN', 'nan', 'None', 'NONE', '??', '???', 'error', 'ERROR',
            'fail', 'FAIL', 'invalid', 'INVALID', 'unavailable', 'UNAVAILABLE',
            'timeout', 'TIMEOUT', '--', '---', 'n.a.', 'N.A.'
        }
        
        for item in self.meowhourly:
            cleaned_item = item.copy()
            
            # Check and clean temperature fields
            for temp_field in ['temp', 'temperature']:
                if temp_field in cleaned_item:
                    temp_value = cleaned_item[temp_field]
                    
                    # Handle None values
                    if temp_value is None:
                        continue  # None is acceptable
                    
                    # Check string values for invalid patterns with more comprehensive checking
                    if isinstance(temp_value, str):
                        temp_str = temp_value.strip()
                        # More comprehensive invalid pattern detection
                        if (temp_str in invalid_patterns or 
                            not temp_str or
                            temp_str.lower().startswith('n') and ('a' in temp_str.lower() or '/' in temp_str) or
                            any(invalid.lower() in temp_str.lower() for invalid in invalid_patterns if isinstance(invalid, str)) or
                            temp_str.lower() in ['error', 'fail', 'invalid', 'timeout', 'null', 'undefined']):
                            logger.debug(f"Cleaning invalid temperature value: '{temp_value}'")
                            cleaned_item[temp_field] = None
                            continue
                        
                        # Try to convert to number and validate range
                        try:
                            temp_num = float(temp_str)
                            if -200 <= temp_num <= 200:
                                cleaned_item[temp_field] = int(temp_num)
                            else:
                                logger.debug(f"Temperature out of range: {temp_num}")
                                cleaned_item[temp_field] = None
                        except (ValueError, TypeError):
                            logger.debug(f"Could not convert temperature: '{temp_str}'")
                            cleaned_item[temp_field] = None
                    
                    # Validate numeric values
                    elif isinstance(temp_value, (int, float)):
                        if not (-200 <= temp_value <= 200):
                            logger.debug(f"Numeric temperature out of range: {temp_value}")
                            cleaned_item[temp_field] = None
                        else:
                            cleaned_item[temp_field] = int(temp_value)
            
            # Clean other string fields
            for field in ['condition', 'windSpeed', 'windDir']:
                if field in cleaned_item and isinstance(cleaned_item[field], str):
                    value = cleaned_item[field].strip()
                    if value in invalid_patterns:
                        cleaned_item[field] = ""
            
            # Ensure precipitation is numeric
            if 'precip' in cleaned_item:
                try:
                    if cleaned_item['precip'] is None:
                        cleaned_item['precip'] = 0
                    elif isinstance(cleaned_item['precip'], str):
                        if cleaned_item['precip'].strip() in invalid_patterns:
                            cleaned_item['precip'] = 0
                        else:
                            cleaned_item['precip'] = max(0, min(100, float(cleaned_item['precip'])))
                    else:
                        cleaned_item['precip'] = max(0, min(100, float(cleaned_item['precip'])))
                except (ValueError, TypeError):
                    cleaned_item['precip'] = 0
            
            cleaned_data.append(cleaned_item)
        
        self.meowhourly = cleaned_data
        logger.debug(f"Cleaned hourly data: {len(cleaned_data)} items processed")


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
