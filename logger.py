# libcommon/logger.py
#
# Logger Utility for Custom Logging Format
# 
# This module provides a custom logger that formats log messages based on their severity.
# Configurations for the logging formats can be found and modified in the config.py module.
# 
# Usage:
#
#     from logger import Logger
# 
#     logger = Logger('ModuleName')
#     logger.setLevel(logger.DEBUG)
#
#     logger.debug("This is a debug message.")
#     logger.info("This is an info message.")
#     logger.warning("This is a warning message.")
#     logger.error("This is an error message.")
# 
# Configuration:
#     Modify the log formats by changing the LOGGER_FORMAT_* constants in the config.py module.
#
# Example:
#
#   from libcommon import INFO
#
#   class Config:
#       LOG_LEVEL = INFO
#       LOGGER_FORMAT_DEBUG = '[%(levelname)s] [%(name)s] %(message)s'
#       LOGGER_FORMAT_INFO = '%(message)s'
#       LOGGER_FORMAT_WARNING = '[WARNING] [%(name)s] %(message)s'
#       LOGGER_FORMAT_ERROR = '[ERROR] [%(name)s] %(message)s'


import logging
import inspect

DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL

DEFAULT_LOG_LEVEL = logging.INFO

class LevelBasedFormatter:
    def __init__(self, formatters, default_formatter):
        self._formatters = formatters
        self._default_formatter = default_formatter

    def format(self, record):
        formatter = self._formatters.get(record.levelno, self._default_formatter)
        return formatter.format(record)

class Logger:
    """
    Custom Logger that uses level-based formatting.
    """
    
    # Default log formats
    DEFAULT_FORMAT_DEBUG = '[%(levelname)s] [%(name)s] %(message)s'  # %(message) is replaced by "[%(funcName):%(lineno)] %(message)"
    DEFAULT_FORMAT_INFO = '%(message)s'
    DEFAULT_FORMAT_WARNING = '[WARNING] [%(name)s] %(message)s'
    DEFAULT_FORMAT_ERROR = '[ERROR] [%(asctime)s] [%(name)s] %(message)s'

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        
        from config import Config
        # Use formats from Config if they exist, otherwise fall back to default formats
        debug_format = logging.Formatter(getattr(Config, 'LOGGER_FORMAT_DEBUG', self.DEFAULT_FORMAT_DEBUG))
        info_format = logging.Formatter(getattr(Config, 'LOGGER_FORMAT_INFO', self.DEFAULT_FORMAT_INFO))
        warning_format = logging.Formatter(getattr(Config, 'LOGGER_FORMAT_WARNING', self.DEFAULT_FORMAT_WARNING))
        error_format = logging.Formatter(getattr(Config, 'LOGGER_FORMAT_ERROR', self.DEFAULT_FORMAT_ERROR))
        
        formatter = LevelBasedFormatter({
            logging.DEBUG: debug_format,
            logging.INFO: info_format,
            logging.WARNING: warning_format,
            logging.ERROR: error_format,
            logging.CRITICAL: error_format
        }, logging.Formatter('%(message)s'))

        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(DEFAULT_LOG_LEVEL)
        self.logger.propagate = False

    def setLevel(self, level=None):
        # Import Config here to avoid circular import
        from config import Config

        if level is None:
            level = getattr(Config, 'LOG_LEVEL', DEFAULT_LOG_LEVEL)

        self.logger.setLevel(level)

    def _get_caller_details(self):
        """Get details of the caller method for logging purposes."""
        frame = inspect.currentframe()
        try:
            # Move up two frames: one for _get_caller_details and one for the debug/info/warning/error method
            frame_info = inspect.getouterframes(frame)[2]
            function_name = frame_info.function
            lineno = frame_info.lineno
            return function_name, lineno
        finally:
            del frame

    def debug(self, message):
        function_name, lineno = self._get_caller_details()
        self.logger.debug(f"[{function_name}:{lineno}] {message}")

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        function_name, lineno = self._get_caller_details()
        self.logger.warning(f"[{function_name}:{lineno}] {message}")

    def error(self, message):
        function_name, lineno = self._get_caller_details()
        self.logger.error(f"[{function_name}:{lineno}] {message}")

    @property
    def DEBUG(self):
        return logging.DEBUG

    @property
    def INFO(self):
        return logging.INFO

    @property
    def WARNING(self):
        return logging.WARNING

    @property
    def ERROR(self):
        return logging.ERROR
