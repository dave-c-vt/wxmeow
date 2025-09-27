from flask import Flask
import logging
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

    return app


# Create the application instance
app = create_app()
