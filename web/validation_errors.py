from typing import Optional
from libcommon.web.http_response_formatter import ValidationErrorFormat
from libcommon.web.locale_helper import get_locale_text

LOCALE_FILE = 'validation_errors.json'  # must be in libcommon/locales/

class RequiredFieldsNotSatisfiedFormat(ValidationErrorFormat):
    def __init__(self, field_name: str, value: Optional[str], lang: str, message: str = None):
        # Fetch localized message if not provided
        message = message if message else get_locale_text(LOCALE_FILE, 'required', lang)
        super().__init__(field_name=field_name, value=value, message=message)

class InvalidEmailFormatErrorFormat(ValidationErrorFormat):
    def __init__(self, field_name: str, value: Optional[str], lang: str, message: str = None):
        # Fetch localized message if not provided
        message = message if message else get_locale_text(LOCALE_FILE, 'email_format', lang)
        super().__init__(field_name=field_name, value=value, message=message)

class MinLengthNotReachedErrorFormat(ValidationErrorFormat):
    def __init__(self, field_name: str, value: Optional[str], lang: str, message: str = None):
        # Fetch localized message if not provided
        message = message if message else get_locale_text(LOCALE_FILE, 'min_length', lang)
        super().__init__(field_name=field_name, value=value, message=message)

class MaxLengthExceededErrorFormat(ValidationErrorFormat):
    def __init__(self, field_name: str, value: Optional[str], lang: str, message: str = None):
        # Fetch localized message if not provided
        message = message if message else get_locale_text(LOCALE_FILE, 'max_length', lang)
        super().__init__(field_name=field_name, value=value, message=message)

class InvalidFormatErrorFormat(ValidationErrorFormat):
    def __init__(self, field_name: str, value: Optional[str], lang: str, message: str = None):
        message = message if message else get_locale_text(LOCALE_FILE, 'invalid_format', lang)
        super().__init__(field_name=field_name, value=value, message=message)

class RegexMatchFailedErrorFormat(ValidationErrorFormat):
    def __init__(self, field_name: str, value: Optional[str], lang: str, locale_key: str, message: str = None):
        if locale_key:
            message = get_locale_text(LOCALE_FILE, locale_key, lang)
        message = message if message else get_locale_text(LOCALE_FILE, 'regex_not_match', lang)
        super().__init__(field_name=field_name, value=value, message=message)
