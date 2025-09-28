"""
Manual tests package for wxmeow weather application.

This package contains manual test files and development artifacts that require
human interaction or visual verification. These tests complement the automated
test suite by providing:

- HTML files for browser-based testing of charts and UI components
- Python scripts for debugging and development workflow
- Working versions of files for reference during development

Manual tests are organized into:
- html/: Standalone HTML files for browser testing
- scripts/: Python development and debugging scripts

These tests are preserved for:
1. Debugging complex visual or interactive issues
2. Development of new chart features
3. Cross-browser compatibility testing
4. Reference during refactoring or feature development

Usage:
    # Run Python debug scripts from project root
    python tests/manual/scripts/debug_charts.py

    # Open HTML tests in browser (with app running)
    open tests/manual/html/test_fixes.html

Note: These tests require the main wxmeow application to be running
for proper asset loading and API access.
"""
