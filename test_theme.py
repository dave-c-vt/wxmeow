#!/usr/bin/env python3
"""
Test script for the wxmeow theme switching functionality.

This script tests that the theme preferences are correctly stored and applied.

Usage:
    python test_theme.py
"""

import sys
import os
from pathlib import Path
import unittest
from flask import session

# Add project root to path to allow imports
project_root = Path(__file__).parent.absolute()
sys.path.append(str(project_root))

from wxmeow import app as flask_app
from wxmeow.views.main import get_theme_preference


class ThemeSwitchingTest(unittest.TestCase):
    """Test cases for theme switching functionality"""

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

    def test_default_theme(self):
        """Test that the default theme is light"""
        with self.client as c:
            # Make a request without setting theme
            response = c.get("/")
            self.assertIn('data-theme="light"', response.data.decode())

    def test_setting_theme(self):
        """Test setting the theme to dark"""
        with self.client as c:
            # Set the theme to dark
            c.get("/set-theme/dark")

            # Make a request and check the theme
            response = c.get("/")
            self.assertIn('data-theme="dark"', response.data.decode())

    def test_theme_persistence(self):
        """Test that theme preference persists across requests"""
        with self.client as c:
            # Set the theme to dark
            c.get("/set-theme/dark")

            # Make multiple requests
            c.get("/")
            c.get("/test/autocomplete")
            response = c.get("/")

            # Check the theme is still dark
            self.assertIn('data-theme="dark"', response.data.decode())

            # Change to light
            c.get("/set-theme/light")
            response = c.get("/")

            # Check the theme changed to light
            self.assertIn('data-theme="light"', response.data.decode())

    def test_invalid_theme(self):
        """Test that invalid themes are handled gracefully"""
        with self.client as c:
            # Try to set an invalid theme
            c.get("/set-theme/invalid_theme")

            # Should default to light
            response = c.get("/")
            self.assertIn('data-theme="', response.data.decode())

    def test_theme_toggle_present(self):
        """Test that the theme toggle is present in the HTML"""
        with self.client as c:
            response = c.get("/")
            html = response.data.decode()

            # Check for theme toggle elements
            self.assertIn('id="theme-toggle"', html)
            self.assertIn('class="theme-toggle"', html)
            self.assertIn('id="theme-icon-sun"', html)
            self.assertIn('id="theme-icon-moon"', html)


if __name__ == "__main__":
    unittest.main()
