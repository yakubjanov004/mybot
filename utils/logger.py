import logging
from logging.handlers import RotatingFileHandler
import os
import sys
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import json
import traceback

class ColoredFormatter(logging.Formatter):
    """Colored log formatter for console output"""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    console_output: bool = True,
    colored_output: bool = True
):
    """Setup logging configuration"""
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger()
    logger.setLevel(log_level.upper())

    # Remove existing handlers
    logger.handlers.clear()

    # Create formatter
    formatter = ColoredFormatter(
        '%(asctime)s - %(module)s - %(levelname)s - %(message)s'
    ) if colored_output else logging.Formatter(
        '%(asctime)s - %(module)s - %(levelname)s - %(message)s'
    )

    # Add console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Add file handler if log_file is specified
    if log_file:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

# Setup default logger
logger = setup_logging(log_level="INFO", log_file="logs/bot.log")

def log_async_function_call(func):
    """Decorator to log async function calls"""
    async def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        logger.debug(f"Calling async {func.__name__} with args={args}, kwargs={kwargs}")
        
        try:
            result = await func(*args, **kwargs)
            logger.debug(f"Async {func.__name__} returned: {result}")
            return result
        except Exception as e:
            logger.error(f"Error in async {func.__name__}: {str(e)}")
            raise
    
    return wrapper

# Performance logging
class PerformanceLogger:
    """Logger for performance monitoring"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(f"performance.{name}")
    
    def log_timing(self, operation: str, duration: float, **context):
        """Log operation timing"""
        self.logger.info(
            f"Operation: {operation}, Duration: {duration:.3f}s",
            extra={'operation': operation, 'duration': duration, **context}
        )
    
    def log_memory_usage(self, operation: str, memory_mb: float, **context):
        """Log memory usage"""
        self.logger.info(
            f"Operation: {operation}, Memory: {memory_mb:.2f}MB",
            extra={'operation': operation, 'memory_mb': memory_mb, **context}
        )

# Error tracking
class ErrorTracker:
    """Track and log errors with context"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(f"errors.{name}")
        self.error_counts = {}
    
    def track_error(self, error: Exception, context: dict = None):
        """Track error occurrence"""
        error_type = type(error).__name__
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        self.logger.error(
            f"Error: {error_type} - {str(error)}",
            extra={
                'error_type': error_type,
                'error_message': str(error),
                'error_count': self.error_counts[error_type],
                'context': context or {}
            },
            exc_info=True
        )
    
    def get_error_stats(self) -> dict:
        """Get error statistics"""
        return dict(self.error_counts)

# Export main functions
__all__ = [
    'setup_logging', 'setup_module_logger', 'LoggerMixin', 'StructuredLogger',
    'LogContext', 'get_logger', 'log_function_call', 'log_async_function_call',
    'PerformanceLogger', 'ErrorTracker'
]

def setup_module_logger(module_name: str, level: Optional[str] = None) -> logging.Logger:
    """Setup logger for specific module"""
    logger = logging.getLogger(module_name)
    
    if level:
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        logger.setLevel(numeric_level)
    
    return logger

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging with JSON output"""
    
    def format(self, record: logging.LogRecord) -> str:
        # Create base log data
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage()
        }
        
        # Add process and thread info for debugging
        if record.levelno >= logging.DEBUG:
            log_data.update({
                'process': record.process,
                'thread': record.thread
            })
        
        # Add extra fields if present
        extra_fields = ['user_id', 'action', 'zayavka_id', 'telegram_id', 'role', 'duration']
        for field in extra_fields:
            if hasattr(record, field):
                log_data[field] = getattr(record, field)
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        return json.dumps(log_data, ensure_ascii=False, default=str)

class ColoredConsoleFormatter(logging.Formatter):
    """Colored console formatter for better readability in development"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        # Add color to level name
        level_color = self.COLORS.get(record.levelname, '')
        reset_color = self.COLORS['RESET']
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        
        # Create formatted message
        message = f"{level_color}[{timestamp}] {record.levelname:8}{reset_color} "
        message += f"{record.name}:{record.funcName}:{record.lineno} - {record.getMessage()}"
        
        # Add exception info if present
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"
        
        return message

def setup_logger(name: str = "bot", level: int = None) -> logging.Logger:
    """Setup logger with both file and console handlers"""
    from config import config
    
    # Determine log level
    if level is None:
        level = config.get_log_level()
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Ensure logs directory exists
    config.LOGS_DIR.mkdir(exist_ok=True)
    
    # File handler with rotation
    log_file = config.LOGS_DIR / f"{name}.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=config.LOG_FILE_MAX_SIZE,
        backupCount=config.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(StructuredFormatter())
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Use colored formatter for development, structured for production
    if config.DEVELOPMENT:
        console_handler.setFormatter(ColoredConsoleFormatter())
    else:
        console_handler.setFormatter(StructuredFormatter())
    
    logger.addHandler(console_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger

def log_user_action(user_id: int, action: str, **kwargs):
    """Log user action with structured data"""
    extra_data = {
        'user_id': user_id,
        'action': action,
        **kwargs
    }
    logger.info(f"User action: {action}", extra=extra_data)

def log_database_operation(operation: str, table: str, duration: float = None, **kwargs):
    """Log database operation"""
    extra_data = {
        'action': f"db_{operation}",
        'table': table,
        **kwargs
    }
    if duration:
        extra_data['duration'] = duration
    
    logger.debug(f"Database {operation} on {table}", extra=extra_data)

def log_error_with_context(error: Exception, context: Dict[str, Any] = None):
    """Log error with additional context"""
    extra_data = context or {}
    logger.error(f"Error occurred: {str(error)}", extra=extra_data, exc_info=True)

def log_performance(operation: str, duration: float, **kwargs):
    """Log performance metrics"""
    extra_data = {
        'action': 'performance',
        'operation': operation,
        'duration': duration,
        **kwargs
    }
    
    # Log as warning if operation is slow
    if duration > 5.0:  # 5 seconds threshold
        logger.warning(f"Slow operation: {operation} took {duration:.2f}s", extra=extra_data)
    else:
        logger.info(f"Operation completed: {operation} in {duration:.2f}s", extra=extra_data)

# Context manager for performance logging
class LogPerformance:
    """Context manager for automatic performance logging"""
    
    def __init__(self, operation: str, **kwargs):
        self.operation = operation
        self.kwargs = kwargs
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            log_performance(self.operation, duration, **self.kwargs)

# Utility functions for common logging patterns
def log_handler_start(handler_name: str, user_id: int = None, **kwargs):
    """Log handler start"""
    extra_data = {'action': 'handler_start', 'handler': handler_name}
    if user_id:
        extra_data['user_id'] = user_id
    extra_data.update(kwargs)
    
    logger.debug(f"Handler started: {handler_name}", extra=extra_data)

def log_handler_end(handler_name: str, user_id: int = None, success: bool = True, **kwargs):
    """Log handler end"""
    extra_data = {
        'action': 'handler_end',
        'handler': handler_name,
        'success': success
    }
    if user_id:
        extra_data['user_id'] = user_id
    extra_data.update(kwargs)
    
    level = logging.INFO if success else logging.WARNING
    message = f"Handler {'completed' if success else 'failed'}: {handler_name}"
    logger.log(level, message, extra=extra_data)

def log_state_change(user_id: int, old_state: str, new_state: str, **kwargs):
    """Log FSM state change"""
    extra_data = {
        'action': 'state_change',
        'user_id': user_id,
        'old_state': old_state,
        'new_state': new_state,
        **kwargs
    }
    logger.debug(f"State change: {old_state} -> {new_state}", extra=extra_data)

def log_zayavka_action(zayavka_id: int, action: str, user_id: int = None, **kwargs):
    """Log zayavka-related action"""
    extra_data = {
        'action': f'zayavka_{action}',
        'zayavka_id': zayavka_id,
        **kwargs
    }
    if user_id:
        extra_data['user_id'] = user_id
    
    logger.info(f"Zayavka {action}: #{zayavka_id}", extra=extra_data)

# Export commonly used loggers
admin_logger = setup_module_logger("admin")
client_logger = setup_module_logger("client")
technician_logger = setup_module_logger("technician")
manager_logger = setup_module_logger("manager")
warehouse_logger = setup_module_logger("warehouse")
call_center_logger = setup_module_logger("call_center")
database_logger = setup_module_logger("database")
