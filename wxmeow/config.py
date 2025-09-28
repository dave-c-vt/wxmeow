#!/usr/bin/env python3
"""
Configuration module for wxmeow weather application.

This module handles loading and managing configuration from environment variables
and .env files. It provides centralized access to all application settings.
"""

import os
from pathlib import Path
from typing import Optional, Union, Any
from dotenv import load_dotenv


class Config:
    """Configuration class for wxmeow application."""

    def __init__(self):
        """Initialize configuration by loading environment variables."""
        # Load .env file if it exists
        self._load_env_file()

        # Application settings
        self.FLASK_APP = self._get_env("FLASK_APP", "wxmeow")
        self.FLASK_ENV = self._get_env("FLASK_ENV", "development")
        self.SECRET_KEY = self._get_env("SECRET_KEY", "dev-key-change-in-production")
        self.DEBUG = self._get_bool_env("DEBUG", False)

        # Server settings
        self.FLASK_HOST = self._get_env("FLASK_HOST", "127.0.0.1")
        self.FLASK_PORT = self._get_int_env("FLASK_PORT", 5000)
        self.EXTERNAL_PORT = self._get_int_env("EXTERNAL_PORT", 8000)
        self.INTERNAL_PORT = self._get_int_env("INTERNAL_PORT", 5000)
        self.CONTAINER_NAME = self._get_env("CONTAINER_NAME", "wxmeow-app")

        # Weather data storage settings
        self.PICKLE_DIR = self._get_path_env("PICKLE_DIR", ".pkl")
        self.PICKLE_MAX_AGE = self._get_int_env("PICKLE_MAX_AGE", 600)  # 10 minutes
        self.PICKLE_AUTO_CLEANUP = self._get_bool_env("PICKLE_AUTO_CLEANUP", True)

        # Weather API settings
        self.WEATHER_API_TIMEOUT = self._get_int_env("WEATHER_API_TIMEOUT", 30)
        self.WEATHER_API_MAX_RETRIES = self._get_int_env("WEATHER_API_MAX_RETRIES", 3)
        self.DEFAULT_LOCATION = self._get_env("DEFAULT_LOCATION", "Boston, MA")

        # Logging configuration
        self.LOG_LEVEL = self._get_env("LOG_LEVEL", "INFO")
        self.LOG_FILE = self._get_env("LOG_FILE", "log_wxmeow.log")
        self.LOG_REQUESTS = self._get_bool_env("LOG_REQUESTS", False)

        # Chart and UI settings
        self.CHART_DAYS = self._get_int_env("CHART_DAYS", 7)
        self.CHART_REFRESH_INTERVAL = self._get_int_env("CHART_REFRESH_INTERVAL", 300)
        self.CHART_ANIMATIONS = self._get_bool_env("CHART_ANIMATIONS", True)

        # Security settings
        self.SESSION_TIMEOUT = self._get_int_env("SESSION_TIMEOUT", 60)
        self.CSRF_ENABLED = self._get_bool_env("CSRF_ENABLED", True)

        # Performance settings
        self.CACHING_ENABLED = self._get_bool_env("CACHING_ENABLED", True)
        self.CACHE_TIMEOUT = self._get_int_env("CACHE_TIMEOUT", 300)

        # Health check settings
        self.HEALTH_CHECK_PATH = self._get_env("HEALTH_CHECK_PATH", "/health")
        self.HEALTH_CHECK_INTERVAL = self._get_int_env("HEALTH_CHECK_INTERVAL", 30)

        # Development settings
        self.AUTO_RELOAD = self._get_bool_env("AUTO_RELOAD", True)
        self.SHOW_ERROR_DETAILS = self._get_bool_env("SHOW_ERROR_DETAILS", False)

        # Backup settings
        self.BACKUP_ENABLED = self._get_bool_env("BACKUP_ENABLED", False)
        self.BACKUP_DIR = self._get_path_env("BACKUP_DIR", "backups")
        self.BACKUP_RETENTION_DAYS = self._get_int_env("BACKUP_RETENTION_DAYS", 30)

        # Ensure pickle directory exists
        self._ensure_pickle_directory()

    def _load_env_file(self):
        """Load environment variables from .env file if it exists."""
        env_file = Path(".env")
        if env_file.exists():
            load_dotenv(env_file)

    def _get_env(self, key: str, default: str = "") -> str:
        """Get string environment variable with default."""
        return os.getenv(key, default)

    def _get_int_env(self, key: str, default: int) -> int:
        """Get integer environment variable with default."""
        try:
            return int(os.getenv(key, str(default)))
        except (ValueError, TypeError):
            return default

    def _get_bool_env(self, key: str, default: bool) -> bool:
        """Get boolean environment variable with default."""
        value = os.getenv(key, "").lower()
        if value in ("true", "1", "yes", "on"):
            return True
        elif value in ("false", "0", "no", "off"):
            return False
        return default

    def _get_path_env(self, key: str, default: str) -> Path:
        """Get path environment variable with default."""
        path_str = os.getenv(key, default)
        return Path(path_str)

    def _ensure_pickle_directory(self):
        """Ensure the pickle directory exists."""
        if not self.PICKLE_DIR.exists():
            self.PICKLE_DIR.mkdir(parents=True, exist_ok=True)

    def get_pickle_path(self, filename: str) -> Path:
        """Get full path for a pickle file."""
        return self.PICKLE_DIR / filename

    def get_flask_config(self) -> dict:
        """Get Flask configuration dictionary."""
        return {
            "SECRET_KEY": self.SECRET_KEY,
            "DEBUG": self.DEBUG,
            "ENV": self.FLASK_ENV,
            "TESTING": self.FLASK_ENV == "testing",
        }

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.FLASK_ENV == "production"

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.FLASK_ENV == "development"

    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.FLASK_ENV == "testing"

    def __repr__(self) -> str:
        """String representation of configuration (without sensitive data)."""
        safe_attrs = [
            "FLASK_ENV",
            "FLASK_HOST",
            "FLASK_PORT",
            "PICKLE_DIR",
            "LOG_LEVEL",
            "DEFAULT_LOCATION",
            "CHART_DAYS",
        ]
        attrs = []
        for attr in safe_attrs:
            if hasattr(self, attr):
                value = getattr(self, attr)
                attrs.append(f"{attr}={value}")
        return f"Config({', '.join(attrs)})"


# Global configuration instance
config = Config()


def get_config() -> Config:
    """Get the global configuration instance."""
    return config


def reload_config() -> Config:
    """Reload configuration from environment variables."""
    global config
    config = Config()
    return config


# Convenience functions for common config access patterns
def get_pickle_dir() -> Path:
    """Get the pickle directory path."""
    return config.PICKLE_DIR


def get_pickle_max_age() -> int:
    """Get the maximum age for pickle files in seconds."""
    return config.PICKLE_MAX_AGE


def get_default_location() -> str:
    """Get the default weather location."""
    return config.DEFAULT_LOCATION


def is_production() -> bool:
    """Check if running in production mode."""
    return config.is_production()


def get_flask_config() -> dict:
    """Get Flask configuration dictionary."""
    return config.get_flask_config()


if __name__ == "__main__":
    # Print configuration for debugging
    print("wxmeow Configuration:")
    print("=" * 40)
    print(f"Environment: {config.FLASK_ENV}")
    print(f"Debug Mode: {config.DEBUG}")
    print(f"Pickle Directory: {config.PICKLE_DIR}")
    print(f"Default Location: {config.DEFAULT_LOCATION}")
    print(f"Log Level: {config.LOG_LEVEL}")
    print(f"Chart Days: {config.CHART_DAYS}")
    print("=" * 40)
