#!/usr/bin/env python3
"""
Main entry point for the wxmeow weather application.

This module provides a command-line interface to run the Flask application
with various options and configurations.

Usage:
    python -m wxmeow [options]
    wxmeow [options]  # if installed via pip
"""

import argparse
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from wxmeow import create_app
    from wxmeow.config import get_config
except ImportError as e:
    print(f"Error importing wxmeow modules: {e}")
    sys.exit(1)


def main():
    """Main entry point for the wxmeow application."""
    parser = argparse.ArgumentParser(
        description="wxmeow - A Flask weather application with cat theme",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m wxmeow                    # Run with default settings
    python -m wxmeow --host 0.0.0.0     # Run on all interfaces
    python -m wxmeow --port 8080        # Run on port 8080
    python -m wxmeow --debug            # Run in debug mode
    python -m wxmeow --config           # Show current configuration
        """,
    )

    parser.add_argument(
        "--host", default=None, help="Host to bind to (overrides config/env)"
    )

    parser.add_argument(
        "--port", type=int, default=None, help="Port to bind to (overrides config/env)"
    )

    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    parser.add_argument(
        "--config", action="store_true", help="Show current configuration and exit"
    )

    parser.add_argument("--env-file", type=str, help="Path to .env file to load")

    parser.add_argument("--version", action="version", version="wxmeow 0.3.0")

    args = parser.parse_args()

    # Load custom env file if specified
    if args.env_file:
        env_path = Path(args.env_file)
        if env_path.exists():
            from dotenv import load_dotenv

            load_dotenv(env_path)
            print(f"Loaded environment from {env_path}")
        else:
            print(f"Warning: Environment file not found: {env_path}")

    # Get configuration
    config = get_config()

    # Show configuration if requested
    if args.config:
        print("wxmeow Configuration:")
        print("=" * 50)
        print(f"Environment: {config.FLASK_ENV}")
        print(f"Debug Mode: {config.DEBUG}")
        print(f"Host: {config.FLASK_HOST}")
        print(f"Port: {config.FLASK_PORT}")
        print(f"Pickle Directory: {config.PICKLE_DIR}")
        print(f"Max Pickle Age: {config.PICKLE_MAX_AGE}s")
        print(f"Default Location: {config.DEFAULT_LOCATION}")
        print(f"Log Level: {config.LOG_LEVEL}")
        print(f"Log File: {config.LOG_FILE}")
        print(f"Chart Days: {config.CHART_DAYS}")
        print(f"Chart Refresh: {config.CHART_REFRESH_INTERVAL}s")
        print(f"Caching Enabled: {config.CACHING_ENABLED}")
        print(f"Auto Cleanup: {config.PICKLE_AUTO_CLEANUP}")
        print("=" * 50)
        return

    # Create Flask application
    try:
        app = create_app()
    except Exception as e:
        print(f"Error creating Flask application: {e}")
        sys.exit(1)

    # Override host/port/debug from command line
    host = args.host or config.FLASK_HOST
    port = args.port or config.FLASK_PORT
    debug = args.debug or config.DEBUG

    # Print startup information
    print(f"Starting wxmeow weather application")
    print(f"   Environment: {config.FLASK_ENV}")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Debug: {debug}")
    print(f"   Pickle Directory: {config.PICKLE_DIR}")
    print(f"   URL: http://{host}:{port}")
    print("=" * 50)

    try:
        # Run the Flask development server
        app.run(
            host=host,
            port=port,
            debug=debug,
            use_reloader=config.AUTO_RELOAD and debug,
            threaded=True,
        )
    except KeyboardInterrupt:
        print("\nApplication stopped by user")
    except Exception as e:
        print(f"Error running application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
