# libcommon/web/flask_helpers.py
from typing import Optional
from flask import request, g, abort, Response
import re
from functools import wraps, partial

from libcommon.language import Language
from libcommon.locale import Locale
from libcommon.validator import Validator, ValidationType

from libcommon.web.session import Session
from libcommon.web.http_response_formatter import ValidationErrorFormat, ValidationErrorsFormat, ErrorCode
from libcommon.web.validation_errors import RequiredFieldsNotSatisfiedFormat, \
InvalidEmailFormatErrorFormat, MinLengthNotReachedErrorFormat, MaxLengthExceededErrorFormat, \
InvalidFormatErrorFormat, RegexMatchFailedErrorFormat
from libcommon.web.locale_helper import get_locale_text
from libcommon.web.http_errors import InvalidContentTypeAPIErrorFormat, \
UnexpectedAPIErrorFormat, ForbiddenAPIErrorFormat, ResourceNotFoundAPIErrorFormat, \
BadRequestAPIErrorFormat, UnauthorizedAPIErrorFormat, RateLimitExceededAPIErrorFormat, \
GoogleOauthTokenErrorFormat
from libcommon.web.google_oauth_helper import verify_token, \
InvalidTokenError, WrongIssuerError, ClientIDMismatchError, TokenExpiredError, \
EmailNotVerifiedError

# Set logger
from libcommon.logger import Logger
from libcommon.color import *

logger = Logger()
logger.setLevel(logger.DEBUG)

# 依存注入(L-1): アプリ起動時に configure_flask_helpers() を呼ぶ。
# 従来のモジュール定数(Config 依存)と F-4 の AVAILABLE_LANGS ハードコードをここに吸収。
# check_config 呼び出しは削除(検査責務はアプリ側 main.py にある)。
DEFAULT_LANG = None
AVAILABLE_LANGS = None
LANG_NAME_MAP = None
BASIC_AUTH_USERNAME = None
BASIC_AUTH_PASSWORD = None


def configure_flask_helpers(default_lang, available_langs, basic_auth_username, basic_auth_password):
    global DEFAULT_LANG, AVAILABLE_LANGS, LANG_NAME_MAP, BASIC_AUTH_USERNAME, BASIC_AUTH_PASSWORD
    DEFAULT_LANG = default_lang
    AVAILABLE_LANGS = available_langs
    LANG_NAME_MAP = Language.lang_label_map(only=available_langs)
    BASIC_AUTH_USERNAME = basic_auth_username
    BASIC_AUTH_PASSWORD = basic_auth_password

def language_wrapper(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        logger.debug(f"Entering language_wrapper with URL path: {request.path}")
        # Step 1: Look at the URL
        path_parts = request.path.strip('/').split('/')

        # Step 2: Check if the 2nd part of the URL is in LANG_NAME_MAP
        url_lang = None
        if len(path_parts) > 0 and path_parts[0] in LANG_NAME_MAP:
            url_lang = path_parts[0]
        elif len(path_parts) > 1 and path_parts[1] in LANG_NAME_MAP:
            url_lang = path_parts[1]

        if url_lang:
            lang = url_lang
            logger.debug(f"Language set from URL: {lang}")
        else:
            query_lang = request.args.get('lang', None)
            if query_lang:
                lang = query_lang
                logger.debug(f"Language set from Query String: {lang}")
            else:
                lang = kwargs.get('lang', DEFAULT_LANG)
                logger.debug(f"Language not found in url. set from default or kwargs: {lang}")

        if lang not in AVAILABLE_LANGS:
            logger.info(f"Attempted to access unsupported language: {lang}")
            abort(404) 

        # Step 4: Set the chosen language
        lang_name = LANG_NAME_MAP.get(lang, LANG_NAME_MAP.get(DEFAULT_LANG))
        kwargs['lang'] = lang
        kwargs['lang_name'] = lang_name

        return func(*args, **kwargs)
    return decorated_function


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        def check_auth(username, password):
            return username == BASIC_AUTH_USERNAME and password == BASIC_AUTH_PASSWORD

        def authenticate():
            return Response(
            'Could not verify your access level for that URL.\n'
            'You have to login with proper credentials', 401,
            {'WWW-Authenticate': 'Basic realm="Login Required"'})

        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

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

def handle_query_param_errors(errors, lang):
    """required_query_params の異常系を返す(N-5)。

    required_fields_check / validate_request と同じ ValidationErrors 族で 400 を返す。
    トップレベルの message は validate_request と同じ 'validation_error' ロケール文言。
    新しいレスポンス外形は作らない(既存フォーマット族の http_response のみ)。
    """
    return ValidationErrorsFormat(
        errors=errors,
        message=get_locale_text('validation_errors.json', 'validation_error', lang),
    ).http_response()

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
            if field_name in json_data:
                value = json_data[field_name]
                if not isinstance(value, expected_type):
                    lang = kwargs.get('lang', 'en')  # Default language
                    logger.debug(f"Request {request.method} {request.url} data: {request.json}")
                    logger.debug(yellow(f"Invalid format for field: {field_name}, expected type: {expected_type.__name__}, got: {type(value).__name__}"))
                    if not hasattr(g, 'errors'):
                        g.errors = []
                    g.errors.append(InvalidFormatErrorFormat(
                        field_name=field_name,
                        value=str(value),
                        lang=lang))
            else:
                logger.debug(f"Field '{field_name}' is missing in request data: {request.json}")
            logger.debug(f"Processing function {f.__name__} with args {args} and kwargs {kwargs}")
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
    logger.debug("validate request -> ok")
    return None

# A generic function to handle errors
def handle_error(error, error_class, lang):
    @language_wrapper
    def inner_handle_error(*args, **kwargs):
        lang = kwargs.get('lang', DEFAULT_LANG)  # Now dynamic
        error_instance = error_class(lang=lang, field_name='')
        logger.error(red(f"{error_class.__name__} '{error_instance.message}'"))
        return error_instance.http_response()
    return inner_handle_error(error)

def make_session_helper(user_loader, on_no_session, on_user_not_found):
    """依存注入版 session_helper(L-1)。

    アプリが自分の User 取得関数と例外を注入することで、libcommon が
    models.data.user に import 時依存するレイヤ逆転を解消する。

    args:
        - user_loader: (user_id: str) -> user | None。アプリが自分の User を注入する。
        - on_no_session: セッションが無い場合に送出する例外を返す callable。
        - on_user_not_found: user_loader が None を返した場合に送出する例外を返す callable。
    """
    def session_helper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user_id = Session.user_id()
            if not user_id:
                raise on_no_session()
            user = user_loader(user_id)
            if user is None:
                raise on_user_not_found()
            return f(user=user, *args, **kwargs)
        return decorated
    return session_helper

def google_oauth_token_check(field_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            logger.debug(f"Attempting to validate Google OAuth token from field '{field_name}'")
            token = request.json.get(field_name)
            if not token:
                error_format = GoogleOauthTokenErrorFormat(error_message='Missing token', code=ErrorCode.UNAUTHORIZED)
                logger.error(red(f"Missing token in field '{field_name}'"))
                # N-5: `locale` は本スコープに存在せず validate_request も呼べない。構築済み
                # error_format を既存の http_response で 401 として返す(短絡の意図を保存)。
                return error_format.http_response()

            try:
                # Verify the OAuth token and extract user info
                user_info = verify_token(token)
                kwargs['email'] = user_info['email']
                kwargs['google_id'] = user_info['sub']
                logger.debug(f"Token valid for email: {user_info['email']} with Google ID: {user_info['sub']}")
            except Exception as e:  # Capture all related exceptions
                if isinstance(e, InvalidTokenError):
                    error_format = GoogleOauthTokenErrorFormat(error_message=str(e), code=ErrorCode.UNAUTHORIZED)
                elif isinstance(e, WrongIssuerError) or isinstance(e, ClientIDMismatchError) or isinstance(e, EmailNotVerifiedError):
                    error_format = GoogleOauthTokenErrorFormat(error_message=str(e), code=ErrorCode.FORBIDDEN)
                elif isinstance(e, TokenExpiredError):
                    error_format = GoogleOauthTokenErrorFormat(error_message=str(e), code=ErrorCode.UNAUTHORIZED)
                else:
                    error_format = GoogleOauthTokenErrorFormat(error_message='An internal error occurred', code=ErrorCode.INTERNAL_SERVER_ERROR)
                logger.error(red(f"OAuth token validation failed: {str(e)}"))
                g.setdefault('errors', []).append(error_format)  # F-5: g.errors 二流儀を setdefault に統一

            return f(*args, **kwargs)
        return decorated_function
    return decorator