from libcommon.response.api_response import ErrorCode, ValidationError
from config import Config
from libcommon.locale import Locale

LOCALE_FILE = 'validation_errors.json'

class RequiredFieldsNotSatisfied(ValidationError):
    __http_error__ = ErrorCode.BAD_REQUEST
    __default_locale_key__ = 'required'

    def __init__(self, field_name, value, lang, locale=None, locale_key=None, *args):
        super().__init__(
            field_name,
            value,
            locale if locale else Locale(LOCALE_FILE),
            locale_key if locale_key else self.__default_locale_key__,
            lang, 
            *args)


class InvalidEmailFormatError(ValidationError):
    __http_error__ = ErrorCode.BAD_REQUEST
    __default_locale_key__ = 'email_format'

    def __init__(self, field_name, value, lang, locale=None, locale_key=None, *args):
        super().__init__(
            field_name,
            value,
            locale if locale else Locale(LOCALE_FILE),
            locale_key if locale_key else self.__default_locale_key__,
            lang, 
            *args)


class MaxLengthExceededError(ValidationError):
    __http_error__ = ErrorCode.BAD_REQUEST
    __default_locale_key__ = 'max_length'

    def __init__(self, field_name, value, lang, locale=None, locale_key=None, *args):
        super().__init__(
            field_name,
            value,
            locale if locale else Locale(LOCALE_FILE),
            locale_key if locale_key else self.__default_locale_key__,
            lang, 
            *args)