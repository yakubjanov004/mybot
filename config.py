import os
from dotenv import load_dotenv
from typing import List, Optional
import logging
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration management class"""
    
    # Bot configuration
    BOT_TOKEN: str = os.getenv("BOT_TOKEN")
    BOT_ID: str = os.getenv("BOT_ID")
    ADMIN_IDS: List[int] = [
        int(admin_id) for admin_id in os.getenv("ADMIN_IDS", "").split(',') 
        if admin_id.strip()
    ]
    ZAYAVKA_GROUP_ID: int = int(os.getenv("ZAYAVKA_GROUP_ID", "-1001234567890"))
    
    # Database configuration
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "alfaconnect_db")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "ulugbek202")
    
    # Performance settings
    DB_POOL_MIN_SIZE: int = int(os.getenv("DB_POOL_MIN_SIZE", "5"))
    DB_POOL_MAX_SIZE: int = int(os.getenv("DB_POOL_MAX_SIZE", "20"))
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "30"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Project directories
    BASE_DIR: Path = Path(__file__).parent
    LOCALES_DIR: Path = BASE_DIR / "locales"
    
    # Available languages
    AVAILABLE_LANGUAGES: List[str] = ["uz", "ru"]
    DEFAULT_LANGUAGE: str = "uz"
    
    @classmethod
    def validate(cls) -> None:
        """Validate configuration"""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is required")
        
        if not cls.ADMIN_IDS:
            logging.warning("No ADMIN_IDS configured")
        
        if not cls.DB_PASSWORD or cls.DB_PASSWORD == "postgres":
            logging.warning("Using default database password - not recommended for production")

# Create config instance
config = Config()

# Backward compatibility - export all necessary variables
BOT_TOKEN = config.BOT_TOKEN
BOT_ID = config.BOT_ID
ADMIN_IDS = config.ADMIN_IDS
ZAYAVKA_GROUP_ID = config.ZAYAVKA_GROUP_ID
DB_HOST = config.DB_HOST
DB_PORT = config.DB_PORT
DB_NAME = config.DB_NAME
DB_USER = config.DB_USER
DB_PASSWORD = config.DB_PASSWORD
DB_POOL_MIN_SIZE = config.DB_POOL_MIN_SIZE
DB_POOL_MAX_SIZE = config.DB_POOL_MAX_SIZE
RATE_LIMIT_REQUESTS = config.RATE_LIMIT_REQUESTS
RATE_LIMIT_WINDOW = config.RATE_LIMIT_WINDOW
LOG_LEVEL = config.LOG_LEVEL
BASE_DIR = config.BASE_DIR
LOCALES_DIR = config.LOCALES_DIR
AVAILABLE_LANGUAGES = config.AVAILABLE_LANGUAGES
DEFAULT_LANGUAGE = config.DEFAULT_LANGUAGE
