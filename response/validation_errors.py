from libcommon.response.api_response import ErrorCode, APIError
from config import Config
from libcommon.locale import Locale

# locale object with errors.json
locale = Locale('validation_errors.json')


class RequiredFieldsNotSatisfied(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, field_name, lang):
        super().__init__(field_name, locale, 'required', lang)

class InvalidEmailFormatError(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, field_name, lang):
        super().__init__(field_name, locale, 'email_format', lang)

class MaxLengthExceededError(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, field_name, lang, maxlen):
        super().__init__(field_name, locale, 'max_length', lang, [maxlen])