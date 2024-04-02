from flask import jsonify
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List

# Set logger
from libcommon.logger import Logger
logger = Logger()
logger.setLevel(logger.INFO)
from libcommon.color import *


class SuccessCode(Enum):
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    PARTIAL_INFORMATION = 203
    NO_CONTENT = 204  # The server successfully processed the request, and is not returning any content.

class ErrorCode(Enum):
    # 4xx
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    PAYMENT_REQUIRED = 402
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    TOO_MANY_REQUEST = 429
    UNSUPPORTED_MEDIA_TYPE = 415
    # 5xx
    INTERNAL_SERVER_ERROR = 500
    NOT_IMPLEMENTED = 501
    BAD_GATEWAY = 502

# Success
class SuccessFormat(BaseModel):
    data: Any
    code: SuccessCode
    message: str

    def response_json(self) -> dict:
        return jsonify({
            **self.data,
            'code': self.code.value,
            'message': self.message
        })

    def http_response(self) -> tuple:
        return self.response_json(), self.code.value

# Error
class APIErrorFormat(BaseModel):
    field_name: str = Field(default=None, example='user_id')  # Optional if you don't always need a key
    code: ErrorCode = ErrorCode.BAD_REQUEST
    message: str = Field(..., example='Error message here.')

    def response_json(self) -> tuple:
        return jsonify({
            'field_name': self.field_name,
            'code': self.code.value,
            'message': self.message,
            'reason': self.code.name
        })

    def http_response(self) -> tuple:
        return self.response_json(), self.code.value

# Validation Error
class ValidationErrorFormat(BaseModel):
    field_name: str
    value: str
    message: str

class ValidationErrorsFormat(BaseModel):
    errors: List[ValidationErrorFormat]
    code: ErrorCode = ErrorCode.BAD_REQUEST
    message: str

    def response_json(self) -> dict:
        return jsonify({
            'code': self.code.value,
            'reason': self.code.name,
            'message': self.message,
            'errors': [error.dict() for error in self.errors]
        })
    
    def http_response(self) -> tuple:
        return self.response_json(), self.code.value