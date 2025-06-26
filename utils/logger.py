import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import json

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage()
        }
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'action'):
            log_data['action'] = record.action
        if hasattr(record, 'order_id'):
            log_data['order_id'] = record.order_id
            
        return json.dumps(log_data, ensure_ascii=False)

def setup_logger(name: str = "bot", level: int = logging.INFO) -> logging.Logger:
    """Setup logger with structured formatting"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(StructuredFormatter())
    logger.addHandler(console_handler)
    
    # File handler
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    file_handler = logging.FileHandler(log_dir / f"{name}.log", encoding='utf-8')
    file_handler.setFormatter(StructuredFormatter())
    logger.addHandler(file_handler)
    
    return logger

def setup_module_logger(module_name: str) -> logging.Logger:
    """Setup logger for specific module"""
    return setup_logger(f"bot.{module_name}")

# Main logger
logger = setup_logger()

def log_user_action(user_id: int, action: str, **kwargs):
    """Log user action with context"""
    logger.info(f"User action: {action}", extra={
        'user_id': user_id,
        'action': action,
        **kwargs
    })

def log_error(error: Exception, context: Dict[str, Any] = None):
    """Log error with context"""
    logger.error(f"Error occurred: {str(error)}", extra=context or {}, exc_info=True)