import os
from typing import List, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv
from pathlib import Path
import logging

load_dotenv()

@dataclass
class Config:
    """Bot configuration"""
    
    # Bot settings
    BOT_TOKEN: str = os.getenv('BOT_TOKEN')
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN environment variable is required")
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/dbname")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_USER: str = os.getenv("DB_USER", "user")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "password")
    DB_NAME: str = os.getenv("DB_NAME", "dbname")
    
    # Admin settings
    ADMIN_IDS: List[int] = field(default_factory=lambda: [
        int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") 
        if x.strip().isdigit()
    ])
    
    # Language settings
    DEFAULT_LANGUAGE: str = os.getenv("DEFAULT_LANGUAGE", "ru")
    AVAILABLE_LANGUAGES: List[str] = field(default_factory=lambda: ["uz", "ru"])
    
    # Group settings
    ZAYAVKA_GROUP_ID: int = field(default_factory=lambda: int(os.getenv("ZAYAVKA_GROUP_ID", "0")))
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_REQUESTS: int = int(os.getenv('RATE_LIMIT_REQUESTS', '30'))
    RATE_LIMIT_WINDOW: int = int(os.getenv('RATE_LIMIT_WINDOW', '60'))
    
    # File upload settings
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "50")) * 1024 * 1024  # 50MB
    ALLOWED_FILE_TYPES: List[str] = field(default_factory=lambda: [
        "image/jpeg", "image/png", "image/gif", "image/webp",
        "application/pdf", "text/plain", "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ])
    
    # Cache settings
    CACHE_TTL: int = int(os.getenv('CACHE_TTL', '300'))  # 5 minutes
    
    # Logging settings
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOGS_DIR: Path = Path(os.getenv("LOGS_DIR", "logs"))
    LOG_FILE_MAX_SIZE: int = int(os.getenv('LOG_FILE_MAX_SIZE', 10 * 1024 * 1024))
    LOG_BACKUP_COUNT: int = int(os.getenv('LOG_BACKUP_COUNT', 5))
    DEVELOPMENT: bool = os.getenv('DEVELOPMENT', 'True').lower() == 'true'
    
    # Webhook settings (for production)
    WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "")
    WEBHOOK_PATH: str = os.getenv("WEBHOOK_PATH", "/webhook")
    WEBHOOK_PORT: int = int(os.getenv('WEBHOOK_PORT', '8080'))
    
    # Business logic settings
    AUTO_ASSIGN_TECHNICIANS: bool = os.getenv("AUTO_ASSIGN_TECHNICIANS", "false").lower() == "true"
    NOTIFICATION_ENABLED: bool = os.getenv("NOTIFICATION_ENABLED", "true").lower() == "true"
    
    # Pagination settings
    DEFAULT_PAGE_SIZE: int = int(os.getenv("DEFAULT_PAGE_SIZE", "10"))
    MAX_PAGE_SIZE: int = int(os.getenv("MAX_PAGE_SIZE", "50"))
    
    ZAYAVKA_GROUP_ID: int = int(os.getenv("ZAYAVKA_GROUP_ID", "0"))
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is required")
        
        if not self.ADMIN_IDS:
            raise ValueError("At least one ADMIN_ID is required")
        
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL is required")
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in self.ADMIN_IDS
    
    def is_dev_mode(self) -> bool:
        """Check if running in development mode"""
        return os.getenv("DEV_MODE", "false").lower() == "true"
    
    def get_log_level(self) -> int:
        """Get numeric log level"""
        return getattr(logging, self.LOG_LEVEL.upper(), logging.INFO)

# Create global config instance
config = Config()

# Export for backward compatibility
BOT_TOKEN = config.BOT_TOKEN
DATABASE_URL = config.DATABASE_URL
ADMIN_IDS = config.ADMIN_IDS
ZAYAVKA_GROUP_ID = config.ZAYAVKA_GROUP_ID

# Environment-specific configurations
class DevelopmentConfig(Config):
    """Development configuration"""
    def __init__(self):
        super().__init__()
        self.LOG_LEVEL = "DEBUG"
        self.CACHE_TTL = 60  # Shorter cache for development

class ProductionConfig(Config):
    """Production configuration"""
    def __init__(self):
        super().__init__()
        self.LOG_LEVEL = "INFO"
        self.RATE_LIMIT_ENABLED = True

class TestingConfig(Config):
    """Testing configuration"""
    def __init__(self):
        super().__init__()
        self.LOG_LEVEL = "DEBUG"
        self.DATABASE_URL = "sqlite:///test.db"
        self.RATE_LIMIT_ENABLED = False

# Factory function to get appropriate config
def get_config() -> Config:
    """Get configuration based on environment"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionConfig()
    elif env == "testing":
        return TestingConfig()
    else:
        return DevelopmentConfig()

# Additional configuration helpers
def load_config_from_file(file_path: str) -> dict:
    """Load configuration from file"""
    import json
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

def validate_config(config_obj: Config) -> List[str]:
    """Validate configuration and return list of errors"""
    errors = []
    
    if not config_obj.BOT_TOKEN:
        errors.append("BOT_TOKEN is required")
    
    if not config_obj.ADMIN_IDS:
        errors.append("At least one ADMIN_ID is required")
    
    if not config_obj.DATABASE_URL:
        errors.append("DATABASE_URL is required")
    
    if config_obj.DEFAULT_LANGUAGE not in config_obj.AVAILABLE_LANGUAGES:
        errors.append(f"DEFAULT_LANGUAGE must be one of {config_obj.AVAILABLE_LANGUAGES}")
    
    if config_obj.RATE_LIMIT_REQUESTS <= 0:
        errors.append("RATE_LIMIT_REQUESTS must be positive")
    
    if config_obj.RATE_LIMIT_WINDOW <= 0:
        errors.append("RATE_LIMIT_WINDOW must be positive")
    
    if config_obj.MAX_FILE_SIZE <= 0:
        errors.append("MAX_FILE_SIZE must be positive")
    
    if config_obj.DEFAULT_PAGE_SIZE <= 0:
        errors.append("DEFAULT_PAGE_SIZE must be positive")
    
    if config_obj.MAX_PAGE_SIZE < config_obj.DEFAULT_PAGE_SIZE:
        errors.append("MAX_PAGE_SIZE must be >= DEFAULT_PAGE_SIZE")
    
    return errors

# Configuration constants
class ConfigConstants:
    """Configuration constants"""
    
    # Default values
    DEFAULT_TIMEOUT = 30
    DEFAULT_RETRY_COUNT = 3
    DEFAULT_BATCH_SIZE = 100
    
    # Limits
    MAX_MESSAGE_LENGTH = 4096
    MAX_CAPTION_LENGTH = 1024
    MAX_CALLBACK_DATA_LENGTH = 64
    
    # File types
    IMAGE_TYPES = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    DOCUMENT_TYPES = [
        "application/pdf", "text/plain", "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
    
    # Status codes
    SUCCESS = 200
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    INTERNAL_ERROR = 500

# Export main config
__all__ = ['config', 'Config', 'get_config', 'validate_config', 'ConfigConstants']
