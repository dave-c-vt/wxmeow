import traceback
import math
from datetime import datetime
from flask import jsonify, request, current_app
from werkzeug.exceptions import BadRequest, NotFound, InternalServerError
import json

# Import logger directly to avoid circular import
import logging
from wxmeow.api import api_bp
from wxmeow.wx2json_noaa import wxmeow
from wxmeow.weather_query import ApiError, LocationError, DataParsingError
from wxmeow.location_service import get_coordinates, GeocodeError, location_service

# Get logger
logger = logging.getLogger("wxmeow")


@api_bp.route("/weather/<location>", methods=["GET"])
def get_weather(location: str):
    """
    Get weather data for a given location.

    Returns:
        JSON object with weather data
    """
    logger.info(f"API request for weather at {location}")
    if not location:
        return jsonify({"error": "No location provided"}), 400

    # Try to validate location first
    try:
        # Check if we can geocode this location
        coords = get_coordinates(location)
        if not coords:
            return jsonify(
                {
                    "error": "Invalid location",
                    "message": f"Could not find coordinates for: {location}",
                }
            ), 404

    except GeocodeError as ge:
        return jsonify({"error": "Geocoding error", "message": str(ge)}), 503
    except Exception as e:
        logger.error(f"Error validating location '{location}': {str(e)}")

    try:
        # Create the wxmeow object for this location
        meow = wxmeow(location)

        # Extract the relevant weather data
        weather_data = {
            "location": getattr(meow, "meowplace", location),
            "current": {
                "condition": getattr(meow, "meowobs", "unknown"),
                "temperature": getattr(meow, "meowtemp", None),
                "feels_like": getattr(meow, "meowfeels", None),
                "humidity": getattr(meow, "meowhumidity", None),
                "wind": {
                    "speed": getattr(meow, "meowwindspeed", None),
                    "direction": getattr(meow, "meowwinddir", None),
                    "gusts": getattr(meow, "meowwindgust", None),
                },
                "pressure": getattr(meow, "meowpressure", None),
                "pressure_trend": getattr(meow, "meowpressuretrend", None),
                "visibility": getattr(meow, "meowvis", None),
                "dewpoint": getattr(meow, "meowdew", None),
                "updated": getattr(meow, "meowobstime", None),
            },
        }

        # Add forecast data if available
        if hasattr(meow, "meowforecast") and meow.meowforecast:
            forecast_data = []
            try:
                if isinstance(meow.meowforecast, str):
                    forecast_items = json.loads(meow.meowforecast)
                else:
                    forecast_items = meow.meowforecast

                for item in forecast_items:
                    forecast_data.append(
                        {
                            "date": item.get("date", ""),
                            "condition": item.get("condition", ""),
                            "temperature": {
                                "high": item.get("high", None),
                                "low": item.get("low", None),
                            },
                            "precipitation": item.get("precip", None),
                        }
                    )

                weather_data["forecast"] = forecast_data
            except (json.JSONDecodeError, AttributeError, TypeError) as e:
                logger.error(f"Error processing forecast data: {str(e)}")
                weather_data["forecast"] = "Error processing forecast data"

        # Add hourly forecast if available
        logger.info(
            f"Checking for hourly data. Has meowhourly: {hasattr(meow, 'meowhourly')}"
        )
        if hasattr(meow, "meowhourly"):
            hourly_data = []
            try:
                logger.info(
                    f"Hourly data type: {type(meow.meowhourly)}, value: {meow.meowhourly}"
                )
                if isinstance(meow.meowhourly, str):
                    try:
                        hourly_items = json.loads(meow.meowhourly)
                        logger.info(
                            f"Parsed hourly data from JSON string: {len(hourly_items)} items"
                        )
                    except (json.JSONDecodeError, TypeError) as e:
                        # Try to extract from string that might be in array format [{"key": "value"}]
                        try:
                            # Remove any surrounding brackets and try parsing again
                            cleaned_string = meow.meowhourly.strip("[]'\"")
                            hourly_items = json.loads(f"[{cleaned_string}]")
                            logger.info(
                                f"Recovered hourly data after cleaning: {len(hourly_items)} items"
                            )
                        except:
                            hourly_items = []
                            logger.warning(
                                f"Failed to parse hourly data JSON string: {str(e)}"
                            )
                elif isinstance(meow.meowhourly, list):
                    hourly_items = meow.meowhourly
                    logger.info(
                        f"Using hourly data list directly: {len(hourly_items)} items"
                    )
                else:
                    hourly_items = []
                    logger.warning(
                        f"Unexpected hourly data type: {type(meow.meowhourly)}, using empty list"
                    )

                for item in hourly_items:
                    if not isinstance(item, dict):
                        logger.warning(f"Skipping non-dict hourly item: {type(item)}")
                        continue

                    # Get temperature from either 'temp' or 'temperature' field
                    temp = item.get("temp")
                    if temp is None:
                        temp = item.get("temperature")

                    # Ensure temperature is a number
                    try:
                        if temp is not None:
                            temp = float(temp)
                    except (ValueError, TypeError):
                        # Use a reasonable default temperature if conversion fails
                        temp = 70
                        logger.warning(
                            f"Invalid temperature value: {item.get('temp') or item.get('temperature')}, using default"
                        )

                    # Make sure we have a valid time
                    time_value = item.get("time", "")
                    if not time_value:
                        # Use current time + index as fallback
                        time_value = datetime.now().isoformat()
                        logger.warning(
                            f"Missing time value in hourly item, using current time"
                        )

                    # Get precipitation from either field
                    precip = item.get("precip")
                    if precip is None:
                        precip = item.get("precipitation")

                    hourly_item = {
                        "time": time_value,
                        "temperature": temp,
                        "temp": temp,  # Include both for compatibility
                        "condition": item.get("condition", ""),
                        "precipitation": precip,
                        "precip": precip,  # Include both for compatibility
                        "wind": {
                            "speed": item.get("windSpeed", None),
                            "direction": item.get("windDir", None),
                        },
                        "icon": item.get("icon", ""),
                    }
                    hourly_data.append(hourly_item)

                # Ensure we have at least some data
                if not hourly_data:
                    logger.warning("No valid hourly data points found")
                    # Instead of generating dummy data, return empty array for now
                    hourly_data = []

                weather_data["hourly_forecast"] = hourly_data
                logger.info(
                    f"Successfully processed {len(hourly_data)} hourly forecast items"
                )
            except (json.JSONDecodeError, AttributeError, TypeError) as e:
                logger.error(f"Error processing hourly forecast data: {str(e)}")
                # Return empty array if no valid data instead of generating dummy data
                weather_data["hourly_forecast"] = []
                logger.info("No hourly data available - returning empty array")

                logger.error(f"Original error details: {str(e)}")
                logger.debug(traceback.format_exc())

        # Add debug information in development mode
        if current_app.debug:
            weather_data["_debug"] = {
                "hourly_count": len(weather_data.get("hourly_forecast", []))
                if isinstance(weather_data.get("hourly_forecast"), list)
                else 0,
                "has_meow_hourly": hasattr(meow, "meowhourly"),
                "timestamp": datetime.now().isoformat(),
            }

        return jsonify(weather_data)

    except LocationError as e:
        logger.error(f"Location error for {location}: {str(e)}")
        logger.debug(traceback.format_exc())
        return jsonify(
            {"error": "Location not found", "message": str(e), "location": location}
        ), 404

    except ApiError as e:
        logger.error(f"API error for {location}: {str(e)}")
        return jsonify({"error": "Weather service unavailable", "message": str(e)}), 503

    except DataParsingError as e:
        logger.error(f"Data parsing error for {location}: {str(e)}")
        return jsonify(
            {"error": "Error processing weather data", "message": str(e)}
        ), 500

    except Exception as e:
        logger.error(f"Unexpected error for {location}: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify(
            {
                "error": "Internal server error",
                "message": "An unexpected error occurred",
            }
        ), 500


@api_bp.route("/forecast/<location>", methods=["GET"])
def get_forecast(location: str):
    """
    Get forecast data for a given location.

    Returns:
        JSON object with forecast data
    """
    if not location:
        return jsonify({"error": "No location provided"}), 400

    # Try to validate location first
    try:
        # Check if we can geocode this location
        coords = get_coordinates(location)
        if not coords:
            return jsonify(
                {
                    "error": "Invalid location",
                    "message": f"Could not find coordinates for: {location}",
                }
            ), 404

    except GeocodeError as ge:
        return jsonify({"error": "Geocoding error", "message": str(ge)}), 503
    except Exception as e:
        logger.error(f"Error validating location '{location}': {str(e)}")

    try:
        # Create the wxmeow object for this location
        meow = wxmeow(location)

        # Extract the relevant forecast data
        forecast_data = {
            "location": getattr(meow, "meowplace", location),
            "daily_forecast": [],
        }

        # Process daily forecast
        if hasattr(meow, "meowforecast") and meow.meowforecast:
            try:
                if isinstance(meow.meowforecast, str):
                    forecast_items = json.loads(meow.meowforecast)
                else:
                    forecast_items = meow.meowforecast

                for item in forecast_items:
                    forecast_data["daily_forecast"].append(
                        {
                            "date": item.get("date", ""),
                            "condition": item.get("condition", ""),
                            "temperature": {
                                "high": item.get("high", None),
                                "low": item.get("low", None),
                            },
                            "precipitation": item.get("precip", None),
                        }
                    )
            except (json.JSONDecodeError, AttributeError, TypeError) as e:
                logger.error(f"Error processing forecast data: {str(e)}")
                forecast_data["daily_forecast"] = "Error processing forecast data"

        return jsonify(forecast_data)

    except LocationError as e:
        logger.error(f"Location error for {location}: {str(e)}")
        return jsonify(
            {"error": "Location not found", "message": str(e), "location": location}
        ), 404

    except ApiError as e:
        logger.error(f"API error for {location}: {str(e)}")
        return jsonify({"error": "Weather service unavailable", "message": str(e)}), 503

    except DataParsingError as e:
        logger.error(f"Data parsing error for {location}: {str(e)}")
        return jsonify(
            {"error": "Error processing weather data", "message": str(e)}
        ), 500

    except Exception as e:
        logger.error(f"Unexpected error for {location}: {str(e)}")
        logger.debug(traceback.format_exc())
        return jsonify(
            {
                "error": "Internal server error",
                "message": "An unexpected error occurred",
            }
        ), 500


@api_bp.errorhandler(BadRequest)
def handle_bad_request(e):
    logger.warning(f"Bad request: {str(e)}")
    return jsonify({"error": "Bad request", "message": str(e)}), 400


@api_bp.errorhandler(NotFound)
def handle_not_found(e):
    logger.warning(f"Not found: {str(e)}")
    return jsonify({"error": "Not found", "message": str(e)}), 404


@api_bp.errorhandler(InternalServerError)
def handle_server_error(e):
    logger.error(f"Server error: {str(e)}")
    return jsonify({"error": "Server error", "message": str(e)}), 500


@api_bp.route("/locations/suggest", methods=["GET"])
def suggest_locations():
    """
    Get location suggestions based on a partial query string.

    Query parameters:
        q: The query string (partial location name)
        limit: Maximum number of results to return (default: 5)

    Returns:
        JSON list of location suggestions
    """
    query = request.args.get("q", "")
    limit = request.args.get("limit", 5, type=int)

    if not query or len(query) < 3:
        return jsonify([])

    try:
        suggestions = location_service.get_suggestions(query, limit)
        return jsonify(suggestions)
    except Exception as e:
        logger.error(f"Error getting location suggestions: {e}")
        return jsonify({"error": str(e)}), 500


@api_bp.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"API unhandled exception: {str(e)}")
    error_type = e.__class__.__name__

    return jsonify(
        {
            "error": "Unexpected error",
            "message": "An unexpected error occurred",
            "type": error_type,
        }
    ), 500
