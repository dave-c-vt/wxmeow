import traceback
import logging
import random

from flask import render_template, redirect, url_for, session, request

# Import logger directly to avoid circular import
from wxmeow.views import views_bp
from wxmeow.forms import wxlookup
from wxmeow.wx2json_noaa import wxmeow
from wxmeow.pics import pick_pic
from flask import jsonify
from wxmeow.weather_query import ApiError, LocationError, DataParsingError, is_canadian_location
from wxmeow.location_service import get_coordinates, GeocodeError
from flask import current_app

# Get logger
logger = logging.getLogger("wxmeow")


# Remove all emoji - use simple text descriptions instead
WEATHER_DESCRIPTIONS = [
    "clear",
    "partly-cloudy",
    "cloudy",
    "overcast", 
    "light-rain",
    "rain",
    "heavy-rain",
    "thunderstorm",
    "snow",
    "windy",
]


def get_location_history():
    """Get the location history from the session."""
    return session.get("location_history", [])


def add_to_location_history(location, display_name=None):
    """Add a location to the history, maintaining only the 5 most recent unique locations."""
    history = get_location_history()

    # Create a new entry without emoji
    new_entry = {
        "location": location,
        "display_name": display_name or location,
    }

    # Remove this location if it's already in history
    history = [entry for entry in history if entry["location"] != location]

    # Add new entry at the beginning
    history.insert(0, new_entry)

    # Keep only the 5 most recent
    history = history[:5]

    # Update session
    session["location_history"] = history
    return history


@views_bp.route("/", methods=["GET", "POST"])
def index():
    form = wxlookup()

    if form.validate_on_submit():
        logger.debug("form redirected!")
        return redirect(url_for("views.weather", location=form.location.data))

    # Get location history for display
    history = get_location_history()
    
    return render_template(
        "base.html",
        title="MEOWCAST!!",
        form=form,
        location_history=history,
    )


@views_bp.route("/wx/<location>")
def weather(location: str):
    if not location:
        return redirect(url_for("views.index"))

    # Default picture to handle cases where we don't have weather data
    pic = pick_pic()
    
    # Quick validation for obviously invalid locations
    if len(location.strip()) < 2:
        error_html = f"<h2>Invalid Location</h2><p>Please enter a valid location name.</p>"
        return render_template(
            "base.html",
            title=f"Invalid Location - {location}",
            wxmeow={"wxmeow": error_html, "futuremeow": ""},
            pic=pic,
        )

    # Validate location format early to avoid API calls for obviously bad input
    if not any(c.isalpha() for c in location):
        # No letters at all - likely garbage input
        error_html = f"<h2>Invalid Location Format</h2><p>Location must contain letters. Try 'Chicago, IL' or '60601'.</p>"
        return render_template(
            "base.html",
            title=f"Invalid Location - {location}",
            wxmeow={"wxmeow": error_html, "futuremeow": ""},
            pic=pic,
        )

    # Check if we can find coordinates for this location
    try:
        # Check if we can find coordinates for this location
        coords = get_coordinates(location)
        if not coords:
            logger.warning(f"No coordinates found for location: {location}")
            if is_canadian_location(location):
                error_html = f"<h2>Canadian Location</h2><p>Canadian weather data is available but currently limited. We're working to improve coverage for Canadian locations.</p><p>For now, try using specific coordinates or a nearby US location for detailed weather information.</p>"
            else:
                error_html = f"<h2>Location Not Found</h2><p>We couldn't find coordinates for '{location}'. Please try a more specific location like 'Chicago, IL' or a zip code.</p>"
            return render_template(
                "base.html",
                title=f"Location Not Found - {location}",
                wxmeow={"wxmeow": error_html, "futuremeow": ""},
                pic=pic,
            )
    except GeocodeError as ge:
        logger.error(f"Geocoding service error: {str(ge)}")
        error_html = f"<h2>Location Service Unavailable</h2><p>We're having trouble with our location service. Please try again with a zip code or lat/lon coordinates.</p>"
        return render_template(
            "base.html",
            title=f"Service Error - {location}",
            wxmeow={"wxmeow": error_html, "futuremeow": ""},
            pic=pic,
        )
    except Exception as e:
        logger.error(f"Location validation error: {str(e)}")
        # Continue and let the weather query handle it

    try:
        # For Canadian locations, try the Canadian weather service first  
        if is_canadian_location(location):
            logger.info(f"Detected Canadian location: {location}, trying Canadian weather sources")
            
            # For now, show a clean message for Canadian locations
            # The user specifically requested to not show the confusing forecast tables
            class CanadianLocationMessage:
                def __init__(self, location: str):
                    display_name = location.replace('_', ' ').title()
                    if ',' in display_name:
                        parts = display_name.split(',')
                        if len(parts) >= 2:
                            display_name = f"{parts[0].strip()}, {parts[1].strip().upper()}, Canada"
                    
                    self.wxmeow = f"""
                    <h1>{display_name}</h1>
                    <h2>Canadian Location</h2>
                    <p style="font-size: 1.2em; line-height: 1.6; max-width: 600px; margin: 20px auto;">
                        Weather data for Canadian locations is currently limited. We're working to add 
                        Environment and Climate Change Canada as a data source.
                    </p>
                    <p style="font-size: 1em; color: #666; max-width: 600px; margin: 20px auto;">
                        For now, please try using specific coordinates or a nearby US location for 
                        detailed weather information.
                    </p>
                    """
                    self.futuremeow = ""  # No confusing forecast table
                    
            canadian_msg = CanadianLocationMessage(location) 
            add_to_location_history(location, location.replace('_', ' ').title())
            
            return render_template(
                "base.html",
                title=f"{location} - Canadian Location",
                wxmeow=canadian_msg,
                pic=pic,
                location=location,
            )
        else:
            # Create the wxmeow object for this location
            meow = wxmeow(location, include_hourly=True)

        # Only try to get a weather-specific picture if we have valid weather data
        if hasattr(meow, "meowobs") and meow.meowobs != "unknown":
            try:
                pic = pick_pic(weather=meow.meowobs)
            except Exception as e:
                logger.error(
                    f'Couldn\'t get picture for weather: "{meow.meowobs}": {str(e)}'
                )
                logger.debug(traceback.format_exc())

        # Log what we found (or didn't find)
        weather_desc = getattr(meow, "meowobs", "unknown")
        temp = getattr(meow, "meowtemp", "??")
        place = getattr(meow, "meowplace", location)

        logger.debug(f"Weather for {location}: {place} - {weather_desc} {temp}F")

        # Add to location history on successful weather lookup
        try:
            add_to_location_history(location, place)
        except Exception as e:
            logger.warning(f"Could not add location to history: {str(e)}")

        # Return the template with weather data
        return render_template(
            "base.html",
            title=place,
            wxmeow=meow,
            pic=pic,
            location=location,
        )

    except (ApiError, LocationError, DataParsingError) as e:
        logger.error(f"Weather API error for {location}: {str(e)}")

        # Create a simple object with just the HTML message for error display
        class ErrorMessage:
            def __init__(self, html: str):
                self.wxmeow: str = html
                self.futuremeow: str = ""

        # Create a more user-friendly error message based on the type of error
        if isinstance(e, LocationError):
            error_html = f"<h2>Location Not Found</h2><p>We couldn't find weather data for '{location}'. Please try entering a city name (like 'Chicago, IL'), a zip code, or coordinates.</p>"
        elif isinstance(e, ApiError):
            error_html = f"<h2>Weather Service Unavailable</h2><p>Sorry, the weather service is temporarily unavailable. Please try again later.</p>"
        else:
            error_html = f"<h2>Weather Data Error</h2><p>We had trouble processing weather data for {location}.</p>"

        return render_template(
            "base.html",
            title=f"Weather Unavailable - {location}",
            wxmeow=ErrorMessage(error_html),
            pic=pic,
            location=location,
        )

    except Exception as e:
        logger.error(f"Unexpected error for {location}: {str(e)}")
        logger.debug(traceback.format_exc())

        class ErrorMessage:
            def __init__(self, html: str):
                self.wxmeow: str = html
                self.futuremeow: str = ""

        error_html = f"<h2>Meow-ch!</h2><p>Something unexpected happened while fetching weather for {location}.</p><p>Please try again later or try a different location.</p>"
        return render_template(
            "base.html",
            title=f"Weather Unavailable - {location}",
            wxmeow=ErrorMessage(error_html),
            pic=pic,
            location=location,
        )


@views_bp.errorhandler(404)
def not_found(error: Exception):
    return render_template("base.html", title="oops!")


@views_bp.route("/test/chart")
def test_chart():
    """Test page for the hourly temperature chart functionality."""
    location = request.args.get("location", "Chicago, IL")
    return render_template("test_chart.html", location=location)


@views_bp.route("/api/hourly/<location>")
def api_hourly_data(location: str):
    """API endpoint to get hourly weather data for charts."""
    try:
        # Create weather object to get hourly data (including hourly for charts)
        weather = wxmeow(location, include_hourly=True)

        # Return the processed hourly data
        if hasattr(weather, "meowhourly") and weather.meowhourly:
            return jsonify(weather.meowhourly)
        else:
            # Return empty array if no hourly data
            return jsonify([])

    except Exception as e:
        logger.error(f"Error getting hourly data for {location}: {str(e)}")
        return jsonify({"error": "Failed to get hourly data"}), 500



