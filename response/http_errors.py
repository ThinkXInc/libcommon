from libcommon.response.api_response import ErrorCode, APIError
from config import Config
from libcommon.locale import Locale

# locale object with errors.json
locale = Locale('http_errors.json')


class InvalidContentType(APIError):
    __http_error__ = ErrorCode.UNSUPPORTED_MEDIA_TYPE

    def __init__(self, lang):
        super().__init__(locale, 'invalid_content_type', lang)


class ForbiddenError(APIError):
    __http_error__ = ErrorCode.FORBIDDEN  # Assuming ErrorCode.FORBIDDEN.value is 403

    def __init__(self, field_name, lang):
        super().__init__(field_name, locale, 'forbidden', lang)


class ResourceNotFoundError(APIError):
    __http_error__ = ErrorCode.NOT_FOUND  # Assuming ErrorCode.NOT_FOUND.value is 404

    def __init__(self, field_name, lang):
        super().__init__(field_name, locale, 'resource_not_found', lang)


class BadRequestError(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST  # Assuming ErrorCode.BAD_REQUEST.value is 400

    def __init__(self, field_name, lang):
        super().__init__(field_name, locale, 'bad_request', lang)


class UnauthorizedError(APIError):
    __http_error__ = ErrorCode.UNAUTHORIZED  # Assuming ErrorCode.UNAUTHORIZED.value is 401

    def __init__(self, field_name, lang):
        super().__init__(field_name, locale, 'unauthorized', lang)
