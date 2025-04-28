from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any
import json
import os
from pathlib import Path

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables, .env file, and config.json.
    Used throughout the application to access configuration values.
    Instantiated as 'settings' at the bottom of this file.
    """
    PROJECT_NAME: str = "MediaVault Manager"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "Media management system with Jellyfin integration"
    DEBUG: bool = False
    
    # Media settings
    MEDIA_ROOT: str = ""
    ALLOWED_EXTENSIONS: set = {"jpg", "jpeg", "png", "gif", "mp4", "mp3"}
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB
    
    # Jellyfin settings
    JELLYFIN: Dict[str, str] = {
        "url": "",
        "api_key": ""
    }

    # Media Library settings
    MEDIA_LIBRARY: Dict[str, str] = {
        "path": ""
    }
    
    def __init__(self, **data):
        env = os.getenv("ENV", "dev")
        # If ENV not set, default to "dev"
        if not env:
            env = "dev"
        config_file = f"config.{env}.json"
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                data.update(config)
        except FileNotFoundError:
            print(f"Warning: Configuration file {config_file} not found, using defaults")
        except json.JSONDecodeError:
            print(f"Warning: Invalid JSON in configuration file {config_file}, using defaults")
        
        super().__init__(**data)

    def __getattr__(self, name: str) -> Any:
        """Handle missing attributes"""
        return None

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