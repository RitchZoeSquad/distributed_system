import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
import json
from config import Config
import traceback
import sys
from pythonjsonlogger import jsonlogger

class Logger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(f"{Config.PC_ID}.{name}")
        self.logger.setLevel(logging.INFO)
        
        # Create formatters
        json_formatter = jsonlogger.JsonFormatter(
            fmt='%(asctime)s %(name)s %(levelname)s %(message)s %(pc_id)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - [%(levelname)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Ensure log directory exists
        os.makedirs('/app/logs', exist_ok=True)
        
        # File handler with rotation for JSON logs
        json_handler = RotatingFileHandler(
            filename=f"/app/logs/pc5_serp_{datetime.now().strftime('%Y%m%d')}.json",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        json_handler.setFormatter(json_formatter)
        self.logger.addHandler(json_handler)
        
        # File handler with rotation for plain text logs
        text_handler = RotatingFileHandler(
            filename=f"/app/logs/pc5_serp_{datetime.now().strftime('%Y%m%d')}.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        text_handler.setFormatter(simple_formatter)
        self.logger.addHandler(text_handler)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(simple_formatter)
        self.logger.addHandler(console_handler)
        
        # Error file handler
        error_handler = RotatingFileHandler(
            filename=f"/app/logs/pc5_serp_errors_{datetime.now().strftime('%Y%m%d')}.log",
            maxBytes=10*1024*1024,
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(simple_formatter)
        self.logger.addHandler(error_handler)

    def _format_message(self, message: str, extra: dict = None) -> dict:
        """Format message with extra data"""
        log_data = {
            'message': message,
            'pc_id': Config.PC_ID,
            'service': 'serp',
            'timestamp': datetime.now().isoformat()
        }
        if extra:
            log_data.update(extra)
        return log_data

    def info(self, message: str, query: str = None, extra: dict = None):
        """Log info message"""
        if query:
            extra = extra or {}
            extra['query'] = query
        self.logger.info(json.dumps(self._format_message(message, extra)))

    def error(self, message: str, query: str = None, exc_info: bool = True, extra: dict = None):
        """Log error message with stack trace"""
        if exc_info:
            extra = extra or {}
            extra['traceback'] = traceback.format_exc()
        if query:
            extra = extra or {}
            extra['query'] = query
        self.logger.error(json.dumps(self._format_message(message, extra)))

    def warning(self, message: str, query: str = None, extra: dict = None):
        """Log warning message"""
        if query:
            extra = extra or {}
            extra['query'] = query
        self.logger.warning(json.dumps(self._format_message(message, extra)))

    def debug(self, message: str, query: str = None, extra: dict = None):
        """Log debug message"""
        if query:
            extra = extra or {}
            extra['query'] = query
        self.logger.debug(json.dumps(self._format_message(message, extra)))

    def critical(self, message: str, query: str = None, extra: dict = None):
        """Log critical message"""
        if query:
            extra = extra or {}
            extra['query'] = query
        self.logger.critical(json.dumps(self._format_message(message, extra)))

    def exception(self, message: str, query: str = None, extra: dict = None):
        """Log exception message"""
        extra = extra or {}
        extra['exc_info'] = True
        if query:
            extra['query'] = query
        self.logger.exception(json.dumps(self._format_message(message, extra)))