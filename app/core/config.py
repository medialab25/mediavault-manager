from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI Jinja2 Project"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "A FastAPI project with Jinja2 templating"
    
    # Media settings
    MEDIA_ROOT: str = "media"
    ALLOWED_EXTENSIONS: set = {"jpg", "jpeg", "png", "gif", "mp4", "mp3"}
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings() 