import logging
import os
from datetime import datetime
from config import Config

class Logger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        
        if not self.logger.handlers:
            self.logger.setLevel(Config.LOG_CONFIG['level'])
            
            # Create logs directory if it doesn't exist
            log_dir = Config.LOG_CONFIG.get('directory', 'logs')
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            # Create file handler
            log_file = os.path.join(log_dir, f"{Config.PC_ID}_{name}.log")
            fh = logging.FileHandler(log_file)
            fh.setLevel(Config.LOG_CONFIG['level'])
            
            # Create console handler
            ch = logging.StreamHandler()
            ch.setLevel(Config.LOG_CONFIG['level'])
            
            # Create formatter
            formatter = logging.Formatter(Config.LOG_CONFIG['format'])
            fh.setFormatter(formatter)
            ch.setFormatter(formatter)
            
            # Add handlers to logger
            self.logger.addHandler(fh)
            self.logger.addHandler(ch)

    def info(self, message: str):
        self.logger.info(message)

    def error(self, message: str):
        self.logger.error(message)

    def warning(self, message: str):
        self.logger.warning(message)

    def debug(self, message: str):
        self.logger.debug(message)