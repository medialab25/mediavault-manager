from pydantic_settings import BaseSettings
from typing import Optional
import json
from pathlib import Path

class CLISettings(BaseSettings):
    """
    CLI-specific settings loaded from environment variables, .env file, and cli_config.json.
    """
    API_BASE_URL: str = "http://127.0.0.1:8000"  # Default to localhost
    TIMEOUT: int = 300  # 5 minutes default timeout
    DEBUG: bool = False

    def __init__(self, **data):
        # First load CLI config as base
        try:
            with open("cli_config.json", 'r') as f:
                cli_config = json.load(f)
                data.update(cli_config)
        except FileNotFoundError:
            print("Warning: CLI configuration file cli_config.json not found")
        except json.JSONDecodeError:
            print("Warning: Invalid JSON in CLI configuration file cli_config.json")
        
        super().__init__(**data)

    @classmethod
    def from_json(cls, json_file: str = "cli_config.json") -> "CLISettings":
        """Load settings from a JSON file."""
        if Path(json_file).exists():
            with open(json_file, "r") as f:
                config_data = json.load(f)
            return cls(**config_data)
        return cls()
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Initialize CLI settings
cli_settings = CLISettings() 