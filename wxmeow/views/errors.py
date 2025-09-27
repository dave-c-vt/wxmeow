import logging
from flask import render_template
from werkzeug.exceptions import NotFound, InternalServerError
from wxmeow.views import views_bp
import logging

# Get logger directly to avoid circular imports
logger = logging.getLogger("wxmeow")


@views_bp.app_errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    return render_template("base.html", title="Page Not Found - 404"), 404


@views_bp.app_errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return render_template(
        "base.html",
        title="Server Error - 500",
        wxmeow={
            "wxmeow": "<h2>Server Error</h2><p>Sorry, something went wrong on our end. Please try again later!</p>",
            "futuremeow": "",
        },
    ), 500


@views_bp.app_errorhandler(Exception)
def unhandled_exception(error):
    """Handle unhandled exceptions."""
    logger.error(f"Unhandled exception: {error}")
    return render_template(
        "base.html",
        title="Unexpected Error",
        wxmeow={
            "wxmeow": "<h2>Unexpected Error</h2><p>Sorry, something unexpected happened. Our weather cats are investigating!</p>",
            "futuremeow": "",
        },
    ), 500
