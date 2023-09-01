from libcommon.response.api_response import ErrorCode, APIError, APIErrors
from config import Config
from libcommon.locale import Locale

LOCALE_FILE = 'errors.json'

class ProcessingError(APIError):
    __http_error__ = ErrorCode.INTERNAL_SERVER_ERROR
    __default_locale_key__ = 'processing_error'

    def __init__(self, lang, locale=None, locale_key=None, field_name='', *args):
        super().__init__(
            lang=lang, field_name=field_name, 
            locale=locale if locale else Locale(LOCALE_FILE),
            locale_key=locale_key if locale_key else self.__default_locale_key__, *args)


class InvalidContentType(APIError):
    __http_error__ = ErrorCode.UNSUPPORTED_MEDIA_TYPE
    __default_locale_key__ = 'invalid_content_type'

    def __init__(self, lang, locale=None, locale_key=None, field_name='', *args):
        super().__init__(
            lang, field_name, locale if locale else Locale(LOCALE_FILE),
            locale_key if locale_key else self.__default_locale_key__, *args)


class ForbiddenError(APIError):
    __http_error__ = ErrorCode.FORBIDDEN
    __default_locale_key__ = 'forbidden'

    def __init__(self, lang, locale=None, locale_key=None, field_name='', *args):
        super().__init__(
            lang, field_name, locale if locale else Locale(LOCALE_FILE),
            locale_key if locale_key else self.__default_locale_key__, *args
        )


class ResourceNotFoundError(APIError):
    __http_error__ = ErrorCode.NOT_FOUND
    __default_locale_key__ = 'resource_not_found'

    def __init__(self, lang, locale=None, locale_key=None, field_name='', *args):
        super().__init__(
            lang, field_name, locale if locale else Locale(LOCALE_FILE),
            locale_key if locale_key else self.__default_locale_key__, *args
        )


class BadRequestError(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST
    __default_locale_key__ = 'bad_request'

    def __init__(self, lang, locale=None, locale_key=None, field_name='', *args):
        super().__init__(
            lang, field_name, locale if locale else Locale(LOCALE_FILE),
            locale_key if locale_key else self.__default_locale_key__, *args
        )


class UnauthorizedError(APIError):
    __http_error__ = ErrorCode.UNAUTHORIZED
    __default_locale_key__ = 'unauthorized'

    def __init__(self, lang, locale=None, locale_key=None, field_name='', *args):
        super().__init__(
            lang, field_name, locale if locale else Locale(LOCALE_FILE),
            locale_key if locale_key else self.__default_locale_key__, *args
        )


class RateLimitExceeded(APIError):
    __http_error__ = ErrorCode.TOO_MANY_REQUEST
    __default_locale_key__ = 'rate_limit_exceeded'

    def __init__(self, lang, locale=None, locale_key=None, field_name='', *args):
        super().__init__(
            lang, field_name, locale if locale else Locale(LOCALE_FILE),
            locale_key if locale_key else self.__default_locale_key__, *args
        )


class ValidationErrors(APIErrors):
    """
    A custom exception class to handle validation errors.

    Args:
        errors (list): A list of error objects.
        message (str): The error message.

    Attributes:
        errors (list): A list of error objects.
        __message__ (str): The error message localized based on the 'lang' attribute.

    Methods:
        http_response(): Constructs a JSON response object for the errors.

    Response Example:
        {
            "saved_data": None,
            "error": {
                "code": 400,
                "reason": "BAD_REQUEST",
                "message": "One or more validation errors occurred."
            },
            "errors": [
                {
                    "key": "first_name",
                    "value": "Bill William Gates Junior",
                    "message": "The input must be no more than 20 characters in length."
                }
            ]
        }
    """
    def __init__(self, errors, message):
        super().__init__(errors, message)