from libcommon.response.api_response import ErrorCode, APIError
from config import Config
from libcommon.locale import Locale

LOCALE_FILE = 'validation_errors.json'

class RequiredFieldsNotSatisfied(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST
    __default_locale_key__ = 'required'

    def __init__(self, field_name, lang, locale=None, locale_key=None, *args):
        super().__init__(
            lang, 
            locale if locale else Locale(LOCALE_FILE),
            locale_key if locale_key else self.__default_locale_key__,
            field_name,
            *args)


class InvalidEmailFormatError(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST
    __default_locale_key__ = 'email_format'

    def __init__(self, field_name, lang, locale=None, locale_key=None, *args):
        super().__init__(
            lang, 
            locale if locale else Locale(LOCALE_FILE),
            locale_key if locale_key else self.__default_locale_key__,
            field_name,
            *args)


class MaxLengthExceededError(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST
    __default_locale_key__ = 'max_length'

    def __init__(self, field_name, lang, locale=None, locale_key=None, *args):
        super().__init__(
            lang, 
            locale if locale else Locale(LOCALE_FILE),
            locale_key if locale_key else self.__default_locale_key__,
            field_name,
            *args)