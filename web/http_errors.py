from libcommon.web.http_response_formatter import APIErrorFormat, ErrorCode
from libcommon.web.locale_helper import get_locale_text

LOCALE_FILE = 'errors.json'  # must be in libcommon/locales/

class UnexpectedAPIErrorFormat(APIErrorFormat):
    def __init__(self, lang: str, field_name: str = '', message: str = None):
        message = message if message else get_locale_text(LOCALE_FILE, 'unexpected_error', lang)
        super().__init__(field_name=field_name, code=ErrorCode.INTERNAL_SERVER_ERROR, message=message)

class InvalidContentTypeAPIErrorFormat(APIErrorFormat):
    def __init__(self, lang: str, field_name: str = '', message: str = None):
        message = message if message else get_locale_text(LOCALE_FILE, 'invalid_content_type', lang)
        super().__init__(field_name=field_name, code=ErrorCode.UNSUPPORTED_MEDIA_TYPE, message=message)

class ForbiddenAPIErrorFormat(APIErrorFormat):
    def __init__(self, lang: str, field_name: str = '', message: str = None):
        message = message if message else get_locale_text(LOCALE_FILE, 'forbidden', lang)
        super().__init__(field_name=field_name, code=ErrorCode.FORBIDDEN, message=message)

class ResourceNotFoundAPIErrorFormat(APIErrorFormat):
    def __init__(self, lang: str, field_name: str = '', message: str = None):
        message = message if message else get_locale_text(LOCALE_FILE, 'resource_not_found', lang)
        super().__init__(field_name=field_name, code=ErrorCode.NOT_FOUND, message=message)

class BadRequestAPIErrorFormat(APIErrorFormat):
    def __init__(self, lang: str, field_name: str = '', message: str = None):
        message = message if message else get_locale_text(LOCALE_FILE, 'bad_request', lang)
        super().__init__(field_name=field_name, code=ErrorCode.BAD_REQUEST, message=message)

class UnauthorizedAPIErrorFormat(APIErrorFormat):
    def __init__(self, lang: str, field_name: str = '', message: str = None, redirect_url=None):
        message = message if message else get_locale_text(LOCALE_FILE, 'unauthorized', lang)
        super().__init__(field_name=field_name, code=ErrorCode.UNAUTHORIZED, message=message, extra_data={'redirect_url': redirect_url})

class RateLimitExceededAPIErrorFormat(APIErrorFormat):
    def __init__(self, lang: str, field_name: str = '', message: str = None):
        message = message if message else get_locale_text(LOCALE_FILE, 'rate_limit_exceeded', lang)
        super().__init__(field_name=field_name, code=ErrorCode.TOO_MANY_REQUESTS, message=message)

class IncorrectPasswordAPIErrorFormat(APIErrorFormat):
    def __init__(self, lang: str, field_name: str = 'password', message: str = None):
        default_message = get_locale_text(LOCALE_FILE, 'incorrect_password', lang)
        super().__init__(field_name=field_name, code=ErrorCode.UNAUTHORIZED, message=message or default_message)

class UserAlreadyExistsErrorFormat(APIErrorFormat):
    def __init__(self, lang: str, field_name: str = 'email', message: str = None):
        default_message = get_locale_text(LOCALE_FILE, 'user_already_exists', lang)
        super().__init__(field_name=field_name, code=ErrorCode.CONFLICT, message=message or default_message)

class GoogleOauthTokenErrorFormat(APIErrorFormat):
    def __init__(self, error_message: str, code: ErrorCode, field_name: str = 'token'):
        super().__init__(field_name=field_name, code=code, message=error_message)

class InvalidPasswordFormatErrorFormat(APIErrorFormat):
    def __init__(self, lang: str, message: str = None):
        default_message = get_locale_text(LOCALE_FILE, 'invalid_password_format', lang)
        super().__init__(field_name='password', code=ErrorCode.BAD_REQUEST, message=message or default_message)