#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# api/helpers/api_response.py
#
# This file provides classes for handling API responses and errors.
#
# - SuccessCode, ErrorCode
#       Enum classes representing HTTP response status codes.
#
# - ResponseBase
#       Base class for generating JSON response bodies.
#
# - SuccessResponse, ErrorResponse
#       Derived from ResponseBase. Generate success and error responses respectively.
#
# - APIError
#       Exception class for API errors. It uses ErrorCode for status and locale for the error message.
#   
#       usage:
#           raise APIError('field_name', locale, 'error_key', 'en', *args)
#
# - APIErrors
#       Exception class for multiple API errors. It uses a list of APIError instances.
#
#       usage:
#           errors = [
#                       APIError('field_name1', locale, 'error_key1', 'en'),
#                       APIError('field_name2', locale, 'error_key2', 'en')
#                       ]
#           return APIErrors(errors, 'en').http_response()
#
# - APISuccess
#       Class for API success response. It uses SuccessCode for status and locale for the success message.
#
#       usage:
#           return APISuccess(data, 'en').http_response()
#

import sys
from flask import jsonify
sys.path.append('../')
from typing import List, Optional
from libcommon.locale import Locale
from libcommon.modelbase import ModelBase
from enum import Enum


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


class ResponseBase(ModelBase):
    __validators__ = {
    }

    def json(self, excludes=[]):
        d = {}
        for key, val in self.items():
            d[key] = val
        return {x: d[x] for x in d if x not in excludes}

    
class SuccessResponse(ResponseBase):
    """Success Response Format
    NOTE: Currently not used. because writing json in each handler is more obvious.

    return jsonify({
        'data': user.response_json(),
        'user_id': user_id,
        'success': {
            'code': 201,
            'message': 'new user created.'
        } // <= create here
    }), 201
    """
    __structure__ = {
        'code': int,
        'message': str
    }
    __required_fields__ = ["saved_data", "success"]
    __default_values__ = {
        'saved_data': None
    }


class ErrorResponse(ResponseBase):
    """A class that defines the format of an error response.

    NOTE: This class wraps only the 'error' part because writing json in each Error is more explicit.
    When returning a response from the API, the 'saved_data' is user-specific, and the 'error' part
    is generated using this class.

    For example, a response can be:
        jsonify({
            'saved_data': user.response_json(),
            'error': {
                'key': 'user_id',
                'code': ErrorCode.BAD_REQUEST.value,
                'reason': 'BAD_REQUEST',
                'message': f'{user_id} is invalid as user_id.'
            } 
        }), ErrorCode.BAD_REQUEST.value

    Args:
        __structure__ (dict): A dictionary defining the structure of the error response. The keys are
                              the field names, and the values are the expected types for these fields.
        __required_fields__ (list): A list of fields that must be present in the error response.
        __default_values__ (dict): A dictionary defining default values for optional fields.
        __validators__ (dict): A dictionary defining validator functions for the fields.

    Methods:
        json(excludes): Returns a dictionary representation of the error response, excluding specified fields.
        json_key(): Returns a string representation of the class name in snake_case format.

    Example:
        error_response = ErrorResponse({
            'key': 'user_id',
            'code': ErrorCode.BAD_REQUEST.value,
            'reason': 'BAD_REQUEST',
            'message': f'{user_id} is invalid as user_id.'
        })

        error_response.key() -> "error_response"
    """
    __structure__ = {
        'key': str,
        'code': int,
        'reason': str,
        'message': str
    }
    __required_fields__ = ["code", "message"]
    __default_values__ = {}


class ValidationError(Exception):
    """
    Raised when there's a validation error in the application.

    Methods:
        __init__(self, key, value, locale, locale_key, lang, *args): Constructor method.
        __error__(self) -> dict: Returns the error as a dictionary.
        __str__(self): Returns a string representation of the error message.

    Examples:
        error = ValidationError('email', '', locale, 'required', 'en')
        print(error.__error__())
        >> {
            'field_name': 'email',
            'value': '',
            'message': 'This field is required'
            }
    """
    

    def __init__(
            self,
            field_name,
            value,
            locale: Locale,
            locale_key: str,
            lang: str,
            locale_args: List[str] = None):
        self.field_name = key
        self.value = value
        self.locale = locale
        self.locale_key = locale_key
        self.lang = lang
        self.message = self.locale.get(self.locale_key, self.lang, locale_args if locale_args else [])
        
    def __error__(self) -> dict:
        return {
            'field_name': self.field_name,
            'value': self.value,
            'message': self.message
        }

    def __str__(self):
        return repr(self.message)


class APIError(Exception):
    """
    A custom API Error class that is used for raising application-specific errors.
    Inherits from both the base Exception class and a custom ResponseFunctions class.

    Attributes:
        __field_name__ (str): The key associated with the error.
        __message__ (str): The localized error message.
        __http_error__ (ErrorCode): The HTTP error code associated with the error.
    
    Methods:
        __init__(self, key, value, locale, locale_key, lang, *args): Constructor method.
        __error__(self) -> dict: Returns the error as a dictionary.
        __error_obj__(self) -> tuple: Returns a tuple with the error in JSON format and its HTTP status code.
        __str__(self): Returns a string representation of the error message.

    Examples:
        error = APIError('first_name', '123', locale, 'INVALID_ID', 'en')
        print(error.__error__())
        >> {
            'field_name': 'first_name',
            'code': 400,
            'reason': 'BAD_REQUEST',
            'message': 'The first name 123 is invalid.'
           }

        print(error.__error_obj__())
        >> (
                {
                    'field_name': 'first_name',
                    'code': 400,
                    'reason': 'BAD_REQUEST',
                    'message': 'The first_name 123 is invalid.'
                }, 
                400
            )

        print(error)
        >> 'The first_name 123 is invalid.'
    """
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(
            self,
            lang: str,
            locale: Locale = None,
            locale_key: str = None,
            field_name: str = None,
            locale_args: List[str] = None):

        print(f'....____.........{locale_args}')

        self.lang = lang
        self.locale = locale
        self.locale_key = locale_key if locale_key else self.__default_locale_key__
        self.__field_name__ = field_name if field_name else ''
        self.__message__ = self.locale.get(self.locale_key, self.lang, locale_args if locale_args else [])
       
    def __error__(self) -> dict:
        return {
                'field_name': self.__field_name__,
                'code': self.__http_error__.value,
                'reason': self.__http_error__.name,
                'message': self.__message__
               }

    def http_response(self) -> tuple:
        error_response = ErrorResponse(self.__error__())
        return error_response.json(), self.__http_error__.value

    def __str__(self):
        return repr(self.__message__)


class APIErrors():
    """
    A custom exception class to handle API errors.

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
            "code": 400,
            "reason": "BAD_REQUEST",
            "message": "An error occurred while processing the request."
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
        self.errors = errors
        self.__message__ = message
    
    def http_response(self):
        error_response = ErrorResponse(
            {
                'code': ErrorCode.BAD_REQUEST.value,
                'reason': ErrorCode.BAD_REQUEST.name,
                'message': self.__message__
            }
        )
        error_dicts = [e.__error__() for e in self.errors]
        print(error_dicts)
        error_response['errors'] = error_dicts
        return error_response.json(), ErrorCode.BAD_REQUEST.value

    def __str__(self):
        return repr(self.__message__)


class APISuccess():
    """
    A class to represent a successful API response.

    Args:
        response_data (Any): The data that was successfully processed.
        message (str): The success message.

    Attributes:
        __response_data__ (Any): The data that was successfully processed.
        __message__ (str): The success message localized based on the 'lang' attribute.
        __http_success__ (SuccessCode): The HTTP success code.

    Methods:
        http_response(): Returns a JSON representation of the success response.
        __str__(): Returns a string representation of the success message.

    Response Example:
        {
            "first_name": "Gates"
            "status": "success",
            "code": 200,
            "message": "The request was processed successfully."
        }
    """
    __http_success__ = SuccessCode.OK

    def __init__(self, response_data, message):
        self.__response_data__ = response_data
        self.__message__ = message
        
    def http_response(self) -> tuple:
        response = {
            **self.__response_data__,
            'status': 'success',
            'code': self.__http_success__.value,
            'message': self.__message__
        }
        return jsonify(response), self.__http_success__.value

    def __str__(self):
        return repr(self.__message__)

