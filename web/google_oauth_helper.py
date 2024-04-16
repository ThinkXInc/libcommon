from google.oauth2 import id_token
from google.auth.transport import requests
from datetime import datetime

# Set logger
from libcommon.logger import Logger
logger = Logger('google oauth helper')
logger.setLevel(logger.DEBUG)
from libcommon.color import *

# Config
from config import Config, check_config
REQUIRED_KEYS_IN_CONFIG = [
    'GOOGLE_OAUTH_CLIENT_ID',
]
check_config(Config, REQUIRED_KEYS_IN_CONFIG)

CLIENT_ID = Config.GOOGLE_OAUTH_CLIENT_ID

# Errors
class InvalidTokenError(Exception):
    pass

class WrongIssuerError(Exception):
    pass

class ClientIDMismatchError(Exception):
    pass

class TokenExpiredError(Exception):
    pass

class EmailNotVerifiedError(Exception):
    pass


def verify_token(token):
    try:
        # Verify the integrity of token using google's public key, and decode its payload
        id_info = id_token.verify_oauth2_token(token, requests.Request(), CLIENT_ID)

        # Check issuer
        if id_info['iss'] not in ['https://accounts.google.com', 'accounts.google.com']:
            error_msg = f"Wrong issuer: {id_info['iss']} expected 'https://accounts.google.com'"
            logger.error(red(error_msg))
            raise WrongIssuerError(error_msg)

        # Check client ID
        if id_info['aud'] != CLIENT_ID:
            error_msg = f"Client ID mismatch: expected {CLIENT_ID}, got {id_info['aud']}"
            logger.error(red(error_msg))
            raise ClientIDMismatchError(error_msg)

        # Check if email is verified
        if not id_info.get('email_verified', False):
            error_msg = f"Email not verified in google oauth."
            logger.error(red(error_msg))
            raise EmailNotVerifiedError(error_msg)

        # Check token expiration
        if 'exp' in id_info and datetime.utcfromtimestamp(id_info['exp']) < datetime.utcnow():
            error_msg = "Token has expired in google oauth."
            logger.error(red(error_msg))
            raise TokenExpiredError(error_msg)

        logger.info(green('Google oauth token is valid and verified.'))
        return id_info

    except ValueError as e:
        error_msg = f"Invalid google oauth token: {str(e)}"
        logger.error(red(error_msg))
        raise InvalidTokenError(error_msg)
