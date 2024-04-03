# libcommon/web/flask_helpers.py
from typing import Optional
from flask import request, g
from functools import wraps, partial

from config import Config, check_config
from models.data.user import User, UnauthorizedAccessError, UserNotFoundError

from libcommon.language import Language
from libcommon.locale import Locale
from libcommon.validator import Validator, ValidationType

from libcommon.web.session import Session
from libcommon.web.http_response_formatter import ValidationErrorFormat, ValidationErrorsFormat
from libcommon.web.validation_errors import RequiredFieldsNotSatisfiedFormat, \
InvalidEmailFormatErrorFormat, MaxLengthExceededErrorFormat
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
        # Step 1: Look at the URL
        path_parts = request.path.split('/')
        url_lang = path_parts[1] if len(path_parts) > 1 else None

        # Step 2: Check if the 2nd part of the URL is in LANG_NAME_MAP
        if url_lang and url_lang in LANG_NAME_MAP.keys():
            lang = url_lang
        else:
            # Step 3: If not, fallback to kwargs or DEFAULT_LANG
            lang = kwargs.get('lang', DEFAULT_LANG)

        # Step 4: Set the chosen language
        lang_name = LANG_NAME_MAP.get(lang, LANG_NAME_MAP.get(DEFAULT_LANG))
        kwargs['lang'] = lang
        kwargs['lang_name'] = lang_name

        return func(*args, **kwargs)
    return decorated_function

def content_type_check_json(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if request.headers['Content-Type'] not in \
                ('application/json', 'application/json; charset=utf-8'):
            lang = kwargs.get('lang', DEFAULT_LANG)  # default to 'en' if 'lang' is not provided
            return InvalidContentTypeAPIErrorFormat(
                lang=lang).http_response()
        return f(*args, **kwargs)
    return wrapper

def required_fields_check(required_fields):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
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

            g.errors = errors
            return f(*args, **kwargs)
        return wrapper
    return decorator

def validate_request(lang, locale) -> Optional[ValidationErrorFormat]:
    errors = g.get('errors', [])
    if errors:
        return ValidationErrorsFormat(
            errors=errors,  # ValidationErrorFormat objects
            message=locale.get('unexpected_error', lang
        ))
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
