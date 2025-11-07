"""Application configuration with Docker secrets support."""

from pydantic import BaseModel, Field
from functools import lru_cache
from typing import List
import os


class Settings(BaseModel):
    """Application settings with environment variable and secrets support."""

    # Application
    app_name: str = Field(default="HeyPico Maps API")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    # Google Maps API
    google_maps_api_key: str = Field(default="")

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    # API Configuration
    api_timeout: int = Field(default=10, description="API request timeout in seconds")
    max_results: int = Field(default=10, description="Maximum results to return")

    @classmethod
    def from_env(cls) -> "Settings":
        """
        Load settings from environment variables and Docker secrets.

        Checks for GOOGLE_MAPS_API_KEY_FILE environment variable
        and loads the key from that file if it exists.
        Falls back to environment variables.
        """
        settings_dict = {}

        # Load API key from Docker secret file
        secret_file = os.getenv("GOOGLE_MAPS_API_KEY_FILE")
        if secret_file and os.path.exists(secret_file):
            try:
                with open(secret_file, 'r') as f:
                    api_key = f.read().strip()
                    if api_key:
                        settings_dict["google_maps_api_key"] = api_key
                        print(f"✓ Loaded API key from secret file: {secret_file}")
            except Exception as e:
                print(f"✗ Error loading secret file {secret_file}: {e}")

        # Load other settings from environment
        if app_name := os.getenv("APP_NAME"):
            settings_dict["app_name"] = app_name
        if debug := os.getenv("DEBUG"):
            settings_dict["debug"] = debug.lower() in ("true", "1", "yes")
        if log_level := os.getenv("LOG_LEVEL"):
            settings_dict["log_level"] = log_level
        if api_timeout := os.getenv("API_TIMEOUT"):
            settings_dict["api_timeout"] = int(api_timeout)
        if max_results := os.getenv("MAX_RESULTS"):
            settings_dict["max_results"] = int(max_results)

        # Handle CORS origins (convert comma-separated string to list)
        if cors_origins := os.getenv("CORS_ORIGINS"):
            settings_dict["cors_origins"] = [origin.strip() for origin in cors_origins.split(",")]

        return cls(**settings_dict)


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Using lru_cache ensures settings are loaded only once,
    improving performance for repeated calls.
    """
    return Settings.from_env()
