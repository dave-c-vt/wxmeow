#!/usr/bin/env python3
"""
Test script for the wxmeow simple styling functionality.

This script tests that the simple styling is working correctly without
complex theme functionality.

Usage:
    python test_theme.py
"""

import sys
import os
from pathlib import Path
import unittest

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent.parent.absolute()
sys.path.append(str(project_root))

from wxmeow import app as flask_app


class SimpleThemeTest(unittest.TestCase):
    """Test cases for simple theme functionality"""

    def setUp(self):
        """Set up test client"""
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

    def test_simple_styles_loaded(self):
        """Test that simple CSS styles are loaded"""
        with self.client as c:
            response = c.get("/")
            html = response.data.decode()
            self.assertIn('href=/home/blackcap/gits/wxmeow/wxmeow/static/styles_simple.css', response.data.decode())

    def test_no_theme_attributes(self):
        """Test that no complex theme attributes are present"""
        with self.client as c:
            response = c.get("/")
            html = response.data.decode()
            # Should not have theme switcher elements
            self.assertNotIn('data-theme=', html)
            self.assertNotIn('theme-toggle', html)
            self.assertNotIn('theme-icon', html)

    def test_chart_functionality_preserved(self):
        """Test that chart JavaScript is still included"""
        with self.client as c:
            response = c.get("/")
            html = response.data.decode()
            # Chart script should be present
            self.assertIn('temperature-chart.js', html)

    def test_simple_cat_styling(self):
        """Test that basic cat-themed elements are present"""
        with self.client as c:
            response = c.get("/")
            html = response.data.decode()
            # Should have the cat faces
            self.assertIn('^.^___/', html)
            self.assertIn('\\___^.^', html)


if __name__ == "__main__":
    unittest.main()
