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
from wxmeow.weather_query import ApiError, LocationError, DataParsingError
from wxmeow.location_service import get_coordinates, GeocodeError
from flask import current_app

# Get logger
logger = logging.getLogger("wxmeow")


# List of weather-related emojis to use for recent locations
WEATHER_EMOJIS = [
    "☀️",
    "🌤️",
    "⛅",
    "🌥️",
    "☁️",
    "🌦️",
    "🌧️",
    "⛈️",
    "🌩️",
    "🌨️",
    "❄️",
    "🌬️",
    "💨",
    "🌪️",
    "🌫️",
    "🌈",
    "☂️",
    "☔",
    "⚡",
    "❄️",
    "☃️",
    "⛄",
    "🔥",
    "💧",
    "🌊",
    "🏖️",
    "🌅",
    "🌇",
    "🌆",
    "🌃",
]


def get_location_history():
    """Get the location history from the session."""
    return session.get("location_history", [])


def get_theme_preference():
    """Get the user's theme preference from cookies."""
    theme = request.cookies.get("theme")
    if not theme:
        # Default to light mode if no preference is set
        theme = "light"
    return theme


def add_to_location_history(location, display_name=None):
    """Add a location to the history, maintaining only the 5 most recent unique locations."""
    history = get_location_history()

    # Create a new entry with emoji
    new_entry = {
        "location": location,
        "display_name": display_name or location,
        "emoji": random.choice(WEATHER_EMOJIS),
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

    # Get location history
    location_history = get_location_history()

    # Get theme preference
    theme = get_theme_preference()

    return render_template(
        "base.html",
        title="MEOWCAST!!",
        form=form,
        location_history=location_history,
        theme=theme,
    )


@views_bp.route("/wx/<location>")
def weather(location: str):
    if not location:
        return redirect(url_for("views.index"))

    # Default picture to handle cases where we don't have weather data
    pic = pick_pic()
    # Generate full URL for the static file
    pic_url = url_for("static", filename=f"catpics/{pic}")

    # Check if we can find coordinates for this location
    try:
        # Validate the location before fetching weather data
        coords = get_coordinates(location)
        if not coords:
            logger.warning(f"No coordinates found for location: {location}")
            error_html = f"<h2>Location Not Found</h2><p>We couldn't find coordinates for '{location}'. Please try a more specific location like 'Chicago, IL' or a zip code.</p>"
            return render_template(
                "base.html",
                title=f"Location Not Found - {location}",
                wxmeow={"wxmeow": error_html, "futuremeow": ""},
                pic=pic_url,
            )
    except GeocodeError as ge:
        logger.error(f"Geocoding service error: {str(ge)}")
        error_html = f"<h2>Location Service Unavailable</h2><p>We're having trouble with our location service. Please try again with a zip code or lat/lon coordinates.</p>"
        return render_template(
            "base.html",
            title=f"Service Error - {location}",
            wxmeow={"wxmeow": error_html, "futuremeow": ""},
            pic=pic_url,
        )
    except Exception as e:
        logger.error(f"Location validation error: {str(e)}")
        # Continue and let the weather query handle it

    try:
        # Create the wxmeow object for this location
        meow = wxmeow(location)

        # Only try to get a weather-specific picture if we have valid weather data
        if hasattr(meow, "meowobs") and meow.meowobs != "unknown":
            try:
                pic = pick_pic(weather=meow.meowobs)
                pic_url = url_for("static", filename=f"catpics/{pic}")
            except Exception as e:
                logger.error(
                    f'Couldn\'t get picture for weather: "{meow.meowobs}": {str(e)}'
                )
                logger.debug(traceback.format_exc())

        # Log what we found (or didn't find)
        weather_desc = getattr(meow, "meowobs", "unknown")
        temp = getattr(meow, "meowtemp", "??")
        place = getattr(meow, "meowplace", location)

        # Add this location to the history
        add_to_location_history(location, place)

        logger.debug(f"Weather for {location}: {place} - {weather_desc} {temp}F")

        # Return the template with weather data
        return render_template(
            "base.html",
            title=place,
            wxmeow=meow,
            pic=pic_url,
            theme=get_theme_preference(),
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
            pic=pic_url,
            theme=get_theme_preference(),
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
            pic=pic_url,
            theme=get_theme_preference(),
            location=location,
        )


@views_bp.errorhandler(404)
def not_found(error: Exception):
    return render_template("base.html", title="oops!", theme=get_theme_preference())


@views_bp.route("/test/autocomplete")
def test_autocomplete():
    """Test page for the location autocomplete functionality."""
    return render_template("test_autocomplete.html", theme=get_theme_preference())


@views_bp.route("/test/chart")
def test_chart():
    """Test page for the hourly temperature chart functionality."""
    location = request.args.get("location", "Chicago, IL")
    return render_template(
        "test_chart.html", location=location, theme=get_theme_preference()
    )


@views_bp.route("/api/hourly/<location>")
def api_hourly_data(location: str):
    """API endpoint to get hourly weather data for charts."""
    try:
        # Create weather object to get hourly data
        weather = wxmeow(location)

        # Return the processed hourly data
        if hasattr(weather, "meowhourly") and weather.meowhourly:
            return jsonify(weather.meowhourly)
        else:
            # Return empty array if no hourly data
            return jsonify([])

    except Exception as e:
        logger.error(f"Error getting hourly data for {location}: {str(e)}")
        return jsonify({"error": "Failed to get hourly data"}), 500


@views_bp.route("/set-theme/<theme>")
def set_theme(theme):
    """Set the user's theme preference and redirect back."""
    response = redirect(request.referrer or url_for("views.index"))
    # Set theme cookie to expire in 1 year
    response.set_cookie("theme", theme, max_age=31536000, samesite="Lax")
    return response
