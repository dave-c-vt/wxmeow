#!/usr/bin/env python3
"""
Test script for the wxmeow location history functionality.

This script simulates user visits to different locations and checks
that the history is maintained correctly in the session.

Usage:
    python test_history.py
"""

import sys
import os
from pathlib import Path
import unittest
from flask import session

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent.parent.absolute()
sys.path.append(str(project_root))

from wxmeow import app as flask_app
from wxmeow.views.main import add_to_location_history, get_location_history


class LocationHistoryTest(unittest.TestCase):
    """Test cases for location history functionality"""

    def setUp(self):
        """Set up test client and enable sessions"""
        self.app = flask_app
        self.app.config["TESTING"] = True
        self.app.config["SECRET_KEY"] = "testing_key"
        self.client = self.app.test_client()
        self.client.testing = True

        # Create an application context
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Clean up after tests"""
        self.app_context.pop()

    def test_add_to_history(self):
        """Test adding locations to history"""
        with self.client.session_transaction() as sess:
            sess["location_history"] = []

        # Add locations one by one
        with self.client:
            self.client.get("/wx/Chicago")
            self.client.get("/wx/New%20York")
            self.client.get("/wx/Boston")

            # Check the session has the history in the right order
            history = session.get("location_history", [])
            self.assertEqual(len(history), 3)
            self.assertEqual(history[0]["location"], "Boston")
            self.assertEqual(history[1]["location"], "New York")
            self.assertEqual(history[2]["location"], "Chicago")

    def test_history_limit(self):
        """Test that history is limited to 5 entries"""
        with self.client:
            # Visit more than 5 locations
            locations = ["Chicago", "New York", "Boston", "Miami", "Seattle", "Austin"]
            for location in locations:
                self.client.get(f"/wx/{location}")

            # Check only the 5 most recent are stored
            history = session.get("location_history", [])
            self.assertEqual(len(history), 5)

            # Check the order (most recent first)
            for i, location in enumerate(reversed(locations[1:6])):
                self.assertEqual(history[i]["location"], location)

    def test_duplicate_locations(self):
        """Test that duplicate locations are moved to the front not duplicated"""
        with self.client:
            # Visit locations with a duplicate
            self.client.get("/wx/Chicago")
            self.client.get("/wx/New%20York")
            self.client.get("/wx/Boston")
            self.client.get("/wx/Chicago")  # Duplicate

            # Check Chicago is at the front and only appears once
            history = session.get("location_history", [])
            self.assertEqual(len(history), 3)
            self.assertEqual(history[0]["location"], "Chicago")

            # Check no duplicates
            locations = [entry["location"] for entry in history]
            self.assertEqual(len(locations), len(set(locations)))

    def test_location_storage(self):
        """Test that each location gets stored properly"""
        with self.client:
            self.client.get("/wx/Chicago")

            history = session.get("location_history", [])
            self.assertTrue("location" in history[0])
            self.assertEqual(history[0]["location"], "Chicago")

    def test_homepage_shows_history(self):
        """Test that the homepage shows the location history"""
        with self.client:
            # Visit some locations
            self.client.get("/wx/Chicago")
            self.client.get("/wx/New%20York")

            # Check homepage has history links
            response = self.client.get("/")
            html = response.data.decode("utf-8")

            # Check for both locations in the HTML
            # Note: Weather service returns actual station locations
            self.assertIn("Chicago", html)
            # New York coordinates resolve to Hoboken, NJ weather station
            self.assertIn("Hoboken", html)

            # Check for location-button class
            self.assertIn("location-button", html)


def simulate_user_browsing():
    """Simulate a user browsing different locations"""
    print("🔍 Simulating user browsing different locations...\n")

    # Create Flask test client
    client = flask_app.test_client()

    # List of locations to visit
    locations = [
        "Chicago",
        "New York",
        "San Francisco",
        "Miami",
        "Boston",
        "Seattle",  # This should push Chicago out of history
        "Chicago",  # This should move Chicago to front
    ]

    # Visit each location
    for location in locations:
        print(f"Visiting: {location}")
        client.get(f"/wx/{location}")

        # Get history from the session
        with client.session_transaction() as sess:
            history = sess.get("location_history", [])
            print(f"  Current history: {[entry['location'] for entry in history]}")

    print("\nSimulation complete!")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--simulate":
        simulate_user_browsing()
    else:
        unittest.main()
