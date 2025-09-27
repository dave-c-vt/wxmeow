from flask import Blueprint

# Create a Blueprint for views
views_bp = Blueprint("views", __name__, template_folder="../templates")

# Import all view modules to register routes with the Blueprint
from . import main, errors


# Function to register blueprint with the app
def init_app(app):
    app.register_blueprint(views_bp)
