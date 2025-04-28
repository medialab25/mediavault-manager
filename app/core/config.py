from pydantic_settings import BaseSettings
from typing import Optional
import json
from pathlib import Path

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables, .env file, and config.json.
    Used throughout the application to access configuration values.
    Instantiated as 'settings' at the bottom of this file.
    """
    PROJECT_NAME: str = "MediaVault Manager"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "A FastAPI project with Jinja2 templating"
    
    # Media settings
    MEDIA_ROOT: str = "media"
    ALLOWED_EXTENSIONS: set = {"jpg", "jpeg", "png", "gif", "mp4", "mp3"}
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB
    
    # Jellyfin settings
    JELLYFIN: dict = {
        "url": "http://localhost:8096",
        "api_key": ""
    }
    
    @classmethod
    def from_json(cls, json_file: str = "config.json") -> "Settings":
        """Load settings from a JSON file."""
        if Path(json_file).exists():
            with open(json_file, "r") as f:
                config_data = json.load(f)
            
            # Handle Jellyfin config separately
            if "jellyfin" in config_data:
                jellyfin_config = config_data.pop("jellyfin")
                config_data["JELLYFIN_URL"] = jellyfin_config.get("url", "http://localhost:8096")
                config_data["JELLYFIN_API_KEY"] = jellyfin_config.get("api_key", "")
            
            return cls(**config_data)
        return cls()
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Try to load from config.json first, fall back to default settings if not found
settings = Settings.from_json() 