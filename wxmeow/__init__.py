from flask import Flask
import logging
import os
import threading
import time
from os.path import dirname, join, realpath


log_file = "log_wxmeow.log"

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(log_file)
formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | [%(module)s:%(lineno)d] | %(message)s"
)

file_handler.setFormatter(formatter)

logger.addHandler(file_handler)


def _auto_refresh_loop() -> None:
    """Daemon thread: refresh stale cached forecasts every 30 minutes."""
    from wxmeow.refresh_meows import refresh_meows, _DEFAULT_REFRESH_SECONDS
    # Stagger the first run so startup isn't slowed down
    time.sleep(60)
    while True:
        try:
            refresh_meows(_DEFAULT_REFRESH_SECONDS)
        except Exception as e:
            logger.warning(f"Auto-refresh error: {e}")
        time.sleep(_DEFAULT_REFRESH_SECONDS)


def create_app():
    """Application factory function"""
    app = Flask(__name__, static_url_path=join(dirname(realpath(__file__)), "static/"))
    app.config["SECRET_KEY"] = "cats will always beat you to the weather"
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["PERMANENT_SESSION_LIFETIME"] = 31536000  # 1 year in seconds

    # Register blueprints
    from wxmeow.views import init_app as init_views
    from wxmeow.api import init_app as init_api

    init_views(app)
    init_api(app)

    # Start background refresh thread (only in the actual worker, not the reloader)
    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        t = threading.Thread(target=_auto_refresh_loop, daemon=True, name="wx-auto-refresh")
        t.start()
        logger.info("Auto-refresh background thread started")

    return app


# Create the application instance
app = create_app()
