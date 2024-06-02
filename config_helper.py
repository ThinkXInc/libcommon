import os
import logging
from enum import Enum
from datetime import datetime
from os.path import dirname, abspath, join
from dotenv import load_dotenv
# Set logger
from libcommon.logger import Logger
logger = Logger('config.py')
logger.setLevel(logger.DEBUG)
from libcommon.color import *

class EnvironmentNotSpecified(Exception):
    pass

class MissingKeyError(Exception):
    """Raised when a required key is missing from .env file."""
    pass

def check_config(config, required_keys):
    """Function to check if all required configuration keys exist and are not None."""
    # Assuming `red` and `bold` are defined functions that color the text
    missing_or_none_keys = [key for key in required_keys if not hasattr(config, key) or getattr(config, key) is None]
    
    for key in required_keys:
        if hasattr(config, key):
            value = getattr(config, key)
            if value is None:
                # Log with error highlighting if value is None
                logger.error(red(f"Config.{key} is set but its value is None."))
            else:
                # Log with standard highlighting for info
                logger.debug(yellow(f"Config.{key}: {value}"))
        else:
            # Log missing keys with error highlighting
            logger.error(red(f"Config key '{key}' is missing."))

    if missing_or_none_keys:
        error_message = f"Missing or None configuration keys: {', '.join(missing_or_none_keys)}"
        logger.error(red(error_message))
        raise MissingKeyError(red(error_message))


