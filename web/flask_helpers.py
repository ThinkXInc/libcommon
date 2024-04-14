# libcommon/web/flask_helpers.py
from typing import Optional
from flask import request, g
import re
from functools import wraps, partial

from config import Config, check_config
from models.data.user import User, UnauthorizedAccessError, UserNotFoundError

from libcommon.language import Language
from libcommon.locale import Locale
from libcommon.validator import Validator, ValidationType

from libcommon.web.session import Session
from libcommon.web.http_response_formatter import ValidationErrorFormat, ValidationErrorsFormat
from libcommon.web.validation_errors import RequiredFieldsNotSatisfiedFormat, \
InvalidEmailFormatErrorFormat, MaxLengthExceededErrorFormat, \
InvalidFormatErrorFormat, RegexMatchFailedErrorFormat
from libcommon.web.http_errors import InvalidContentTypeAPIErrorFormat, \
UnexpectedAPIErrorFormat, ForbiddenAPIErrorFormat, ResourceNotFoundAPIErrorFormat, \
BadRequestAPIErrorFormat, UnauthorizedAPIErrorFormat, RateLimitExceededAPIErrorFormat

# Set logger
from libcommon.logger import Logger
from libcommon.color import *

logger = Logger()
logger.setLevel(logger.DEBUG)

REQUIRED_KEYS = [
    'DEFAULT_LANG',
]
check_config(Config, REQUIRED_KEYS)

DEFAULT_LANG = Config.DEFAULT_LANG
LANG_NAME_MAP = Language.lang_label_map(only=['en', 'ja', 'zh'])

def language_wrapper(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        logger.debug(f"Entering language_wrapper with URL path: {request.path}")
        # Step 1: Look at the URL
        path_parts = request.path.split('/')
        url_lang = path_parts[1] if len(path_parts) > 1 else None

        # Step 2: Check if the 2nd part of the URL is in LANG_NAME_MAP
        if url_lang and url_lang in LANG_NAME_MAP.keys():
            lang = url_lang
            logger.debug(f"Language set from URL: {lang}")
        else:
            # Step 3: If not, fallback to kwargs or DEFAULT_LANG
            lang = kwargs.get('lang', DEFAULT_LANG)
            logger.debug(f"Language set from default or kwargs: {lang}")

        # Step 4: Set the chosen language
        lang_name = LANG_NAME_MAP.get(lang, LANG_NAME_MAP.get(DEFAULT_LANG))
        kwargs['lang'] = lang
        kwargs['lang_name'] = lang_name

        return func(*args, **kwargs)
    return decorated_function

def content_type_check_json(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        content_type = request.headers.get('Content-Type', '')
        logger.debug(f"Checking content type of request: {content_type}")
        if request.headers['Content-Type'] not in \
                ('application/json', 'application/json; charset=utf-8'):
            lang = kwargs.get('lang', DEFAULT_LANG)  # default to 'en' if 'lang' is not provided
            logger.debug(f"Invalid content type, expected 'application/json', got: {content_type}")
            return InvalidContentTypeAPIErrorFormat(
                lang=lang).http_response()
        return f(*args, **kwargs)
    return wrapper

def required_fields_check(required_fields):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            logger.debug(f"Checking required fields: {required_fields}")
            json_data = request.json
            if json_data is None:
                lang = kwargs.get('lang', DEFAULT_LANG)  # default to 'en' if 'lang' is not provided
                return InvalidContentTypeAPIErrorFormat(
                    lang=lang).http_response()
                
            errors = []
            for field_name in required_fields:
                value = json_data.get(field_name)
                if value is None or not Validator.check(value, ValidationType.required):
                    lang = kwargs.get('lang', DEFAULT_LANG)  # default to 'en' if 'lang' is not provided
                    errors.append(RequiredFieldsNotSatisfiedFormat(
                        field_name=field_name,
                        value=value,
                        lang=lang))
                    logger.debug(f"Field error added: {field_name}, {value}")
            g.errors = errors
            return f(*args, **kwargs)
        return wrapper
    return decorator

def required_query_params(required_params):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            logger.debug(f"Validating required query parameters: {required_params}")
            query_params = request.args
            errors = []
            # Validate presence and non-emptiness of required query parameters
            for param in required_params:
                value = query_params.get(param)
                if value is None or value == '':
                    lang = kwargs.get('lang', 'en')  # default to 'en' if 'lang' is not provided
                    errors.append(RequiredFieldsNotSatisfiedFormat(
                        field_name=param,
                        value=value,
                        lang=lang
                    ))
                    logger.debug(f"Missing or empty query parameter: {param}, value: {value}")

            # Check if there were any errors collected
            if errors:
                return handle_query_param_errors(errors, lang)

            return f(*args, **kwargs)
        return wrapper
    return decorator

def format_check(field_name, expected_type):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            json_data = request.json
            value = json_data.get(field_name)
            if not isinstance(value, expected_type):
                lang = kwargs.get('lang', DEFAULT_LANG)
                g.errors.append(InvalidFormatErrorFormat(
                    field_name=field_name,
                    value=str(value),
                    lang=lang))
                logger.debug(f"Invalid format for field: {field_name}, expected type: {expected_type.__name__}, got: {type(value).__name__}")
            return f(*args, **kwargs)
        return wrapper
    return decorator

def length_check(field_name, min_length, max_length):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            json_data = request.json
            value = json_data.get(field_name, "")
            lang = kwargs.get('lang', DEFAULT_LANG)
            logger.debug(f"Checking length of field: {field_name}, min: {min_length}, max: {max_length}, current length: {len(value)}")

            # Check for minimum length
            if len(value) < min_length:
                g.errors.append(MinLengthNotReachedErrorFormat(
                    field_name=field_name,
                    value=value,
                    lang=lang))
                logger.debug(f"Field {field_name} is below minimum length: {len(value)}")

            # Check for maximum length
            elif len(value) > max_length:
                g.errors.append(MaxLengthExceededErrorFormat(
                    field_name=field_name,
                    value=value,
                    lang=lang))
                logger.debug(f"Field {field_name} exceeds maximum length: {len(value)}")

            return f(*args, **kwargs)
        return wrapper
    return decorator

def regex_check(field_name, regex_pattern, locale_key):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            json_data = request.json
            value = json_data.get(field_name)
            if value and not re.match(regex_pattern, value):
                lang = kwargs.get('lang', DEFAULT_LANG)
                g.errors.append(RegexMatchFailedErrorFormat(
                    field_name=field_name,
                    value=value,
                    lang=lang,
                    locale_key=locale_key))
                logger.debug(f"Regex check failed for field: {field_name}, pattern: {regex_pattern}, value: {value}")
            return f(*args, **kwargs)
        return wrapper
    return decorator

def validate_request(lang, locale) -> Optional[ValidationErrorFormat]:
    errors = g.get('errors', [])
    if errors:
        logger.debug(f"{errors} validation errors found.")
        return ValidationErrorsFormat(
            errors=errors,  # ValidationErrorFormat objects
            message=locale.get('validation_error', lang))
    logger.debug("No validation errors, request is valid.")
    return None

# A generic function to handle errors
def handle_error(error, error_class):
    @language_wrapper
    def inner_handle_error(*args, **kwargs):
        lang = kwargs.get('lang', DEFAULT_LANG)  # Now dynamic
        error_instance = error_class(lang=lang, field_name='')
        logger.error(red(f"{error_class.__name__} '{error_instance.message}'"))
        return error_instance.http_response()
    return inner_handle_error(error)

def session_helper(f):
    """

    Additionally, add error handlers in the Flask app instance.

        @app.errorhandler(UnauthorizedAccessError)
        def handle_unauthorized_access(error):
            return UnauthorizedAPIErrorFormat(lang=Config.DEFAULT_LANG, message=str(error)).http_response()

        @app.errorhandler(UserNotFoundError)
        def handle_user_not_found(error):
            return UnauthorizedAPIErrorFormat(lang=Config.DEFAULT_LANG, message=str(error)).http_response()
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = Session.user_id()
        if not user_id:
            logger.error(red('No user ID found in session.'))
            raise UnauthorizedAccessError("User must be logged in to access this resource.")

        user = User.objects(id=user_id).first()
        if not user:
            logger.error(red(f'User not found with ID: {user_id}'))
            raise UserNotFoundError("User not found.")

        logger.info(green(f'User found: {user.email}'))
        return f(user=user, *args, **kwargs)

    return decorated_function
