from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any
import json
import os
from pathlib import Path

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables, .env file, and config files.
    Uses config.json as base and overrides with config.dev.json in development mode.
    """
    PROJECT_NAME: str = "MediaVault Manager"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "Media management system with Jellyfin integration"
    DEBUG: bool = False
    
    # API settings
    API_BASE_URL: str = "http://localhost:8000"
    
    # Media settings
    MEDIA_ROOT: str = ""
    ALLOWED_EXTENSIONS: set = {"jpg", "jpeg", "png", "gif", "mp4", "mp3"}
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB
    
    # File type definitions
    FILE_TYPES: Dict[str, list] = {
        "video": ["mp4", "mkv", "avi", "mov", "wmv", "flv", "mpeg", "mpg", "m4v", "webm"],
        "audio": ["mp3", "m4a", "aac", "wav"],
        "subtitles": ["srt", "ass", "ssa", "vtt", "sub"]
    }
    
    # Jellyfin settings
    JELLYFIN: Dict[str, str] = {
        "url": "",
        "api_key": ""
    }

    # Media Library settings
    MEDIA_LIBRARY: Dict[str, Any] = {}

    # Media Merge settings
    MEDIA_MERGE: Dict[str, str] = {
        "user": "1000",
        "group": "1000"
    }

    # Cache settings
    MEDIA_CACHE: Dict[str, Any] = {
        "cache_path": "/srv/disks/media-ssd/media",
        "storage_paths": []
    }

    # Task settings
    TASKS: Dict[str, Any] = {
        "sync": {
            "enabled": True,
            "interval": 1
        }
    }

    def __init__(self, **data):
        # First load production config as base
        try:
            with open("config.json", 'r') as f:
                prod_config = json.load(f)
                data.update(prod_config)
        except FileNotFoundError:
            print("Warning: Production configuration file config.json not found")
        except json.JSONDecodeError:
            print("Warning: Invalid JSON in production configuration file config.json")
        
        # Then override with dev config if in development mode
        env = os.getenv("ENV", "dev")
        # if env == "dev":
        #     try:
        #         with open("config.dev.json", 'r') as f:
        #             dev_config = json.load(f)
        #             # Deep merge the configurations
        #             self._deep_merge(data, dev_config)
        #     except FileNotFoundError:
        #         print("Warning: Development configuration file config.dev.json not found")
        #     except json.JSONDecodeError:
        #         print("Warning: Invalid JSON in development configuration file config.dev.json")
        
        super().__init__(**data)

    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """Deep merge two dictionaries, with source values taking precedence."""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value

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

# Initialize settings
settings = Settings() 