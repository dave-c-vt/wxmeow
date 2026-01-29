#!/usr/bin/env python3
"""
Simple test script to verify Flask app initialization and routing is working correctly.
This serves as a sanity check for the refactored app structure.
"""

import sys
import os
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent.parent.absolute()
sys.path.append(str(project_root))

from wxmeow import app


def test_app_instance():
    """Test that the app instance was created successfully."""
    assert app is not None, "App instance not created"
    print("[OK] App instance created successfully")


def test_blueprint_registration():
    """Test that both blueprints are registered with the app."""
    blueprint_names = [bp.name for bp in app.blueprints.values()]

    print(f"📋 Registered blueprints: {', '.join(blueprint_names)}")

    assert "views" in blueprint_names, "Views blueprint not registered"
    assert "api" in blueprint_names, "API blueprint not registered"

    print("[OK] Both blueprints registered successfully")


def test_routes():
    """Test that routes from both blueprints are registered."""
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append(f"{rule.rule} [{','.join(rule.methods)}]")

    print(f"📋 Registered routes:")
    for route in sorted(routes):
        print(f"  - {route}")

    # Check for expected routes
    view_routes_exist = any(route.startswith("/wx/") for route in routes)
    api_routes_exist = any(route.startswith("/api/") for route in routes)

    assert view_routes_exist, "View routes not found"
    assert api_routes_exist, "API routes not found"

    print("[OK] Routes from both blueprints registered successfully")


if __name__ == "__main__":
    print("🔍 Testing Flask application initialization...\n")

    try:
        test_app_instance()
        test_blueprint_registration()
        test_routes()
        print(
            "\nAll tests passed! The refactored app structure is working correctly."
        )
    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {str(e)}")
        sys.exit(1)
