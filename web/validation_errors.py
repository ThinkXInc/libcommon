from libcommon.web.http_response_formatter import ValidationErrorFormat
from libcommon.web.locale_helper import get_locale_text

LOCALE_FILE = 'validation_errors.json'  # must be in libcommon/locales/

class RequiredFieldsNotSatisfiedFormat(ValidationErrorFormat):
    def __init__(self, field_name: str, value: str, lang: str, message: str = None):
        # Fetch localized message if not provided
        message = message if message else get_locale_text(LOCALE_FILE, 'required', lang)
        super().__init__(field_name=field_name, value=value, message=message)

class InvalidEmailFormatErrorFormat(ValidationErrorFormat):
    def __init__(self, field_name: str, value: str, lang: str, message: str = None):
        # Fetch localized message if not provided
        message = message if message else get_locale_text(LOCALE_FILE, 'email_format', lang)
        super().__init__(field_name=field_name, value=value, message=message)

class MaxLengthExceededErrorFormat(ValidationErrorFormat):
    def __init__(self, field_name: str, value: str, lang: str, message: str = None):
        # Fetch localized message if not provided
        message = message if message else get_locale_text(LOCALE_FILE, 'max_length', lang)
        super().__init__(field_name=field_name, value=value, message=message)
