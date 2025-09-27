from flask import Blueprint

# Create a Blueprint for API endpoints
api_bp = Blueprint("api", __name__, url_prefix="/api")

# Import all API modules to register routes with the Blueprint
from . import weather


# Function to register blueprint with the app
def init_app(app):
    app.register_blueprint(api_bp)
