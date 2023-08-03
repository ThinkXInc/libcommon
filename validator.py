#!/usr/local/bin/python
# -*- coding:utf-8 -*-

# libcommon/validator.py

# Validator class provides static methods for various data validations including 
# required check, maximum length check, and format checks for email, password, telephone, and postal code.
# It supports validation against predefined Regex patterns and also supports type checking for the provided value.

# Usage:
# - Required validation: 
#       Validator.check(value, ValidationType.required)

# - Maximum length validation: 
#       Validator.check(value, ValidationType.max_length)

# - Email format validation: 
#       Validator.check(value, ValidationType.email)

# - Password format validation: 
#       Validator.check(value, ValidationType.password)

# - Telephone format validation: 
#       Validator.check(value, ValidationType.tel)

# - Postal code format validation: 
#       Validator.check(value, ValidationType.postal_code)

# - Additional type validation: 
#       Validator.check(value, ValidationType.required, str)


import re
from typing import TypeVar, Optional

T = TypeVar('T')

class ValidationType:
    required = 'required'
    max_length = 'max_length'
    email = 'email'
    password = 'password'
    tel = 'tel'
    postal_code = 'postal_code'

class RegexType:
    email = re.compile(r'^(([^<>()[\]\.,;:\s@\"]+(\.[^<>()[\]\.,;:\s@\"]+)*)|(\".+\"))@(([^<>()[\]\.,;:\s@\"]+\.)+[^<>()[\]\.,;:\s@\"]{2,})$', re.I)
    password = re.compile(r'^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])[0-9a-zA-Z]{8,}$')
    postal_code = re.compile(r'^(?:[A-Z0-9]+([- ]?[A-Z0-9]+)*)?$')
    tel = re.compile(r'^[\+]?[(]?[0-9]{2,3}[)]?[-\s\.]?[0-9]{4,6}[-\s\.]?[0-9]{4,6}$', re.I)


class Validator:
    """
    Perform a validation check on a given value based on the validation type and optionally the required type.

    Args:
        value (T): The value to validate.
        validation_type (str): The type of validation to perform.
        required_type (Optional[type]): If provided, the function checks if the value is of this type.

    Returns:
        bool: True if the validation passes, False otherwise. If the required type is provided and the value is not of this type, it also returns False.

    Usage examples:
    >>> Validator.check("notanemail", ValidationType.email)
    False
    >>> Validator.check("test@example.com", ValidationType.email)
    True
    >>> Validator.check("", ValidationType.required)
    False
    >>> Validator.check("This string is too long.", ValidationType.max_length, str)
    True
    """

    @staticmethod
    def check(value: T, validation_type: str, required_type: Optional[type] = None) -> bool:
        if value is not None and required_type and not isinstance(value, required_type):
            return False  # Value is not None and doesn't match the required type

        if validation_type == ValidationType.required:
            return Validator._validate_not_null_or_empty(value)
        elif validation_type == ValidationType.max_length:
            return Validator._validate_max_length(value)
        elif validation_type == ValidationType.email:
            return Validator._validate_format(value, RegexType.email)
        elif validation_type == ValidationType.password:
            return Validator._validate_format(value, RegexType.password)
        elif validation_type == ValidationType.tel:
            return Validator._validate_format(value, RegexType.tel)
        elif validation_type == ValidationType.postal_code:
            return Validator._validate_format(value, RegexType.postal_code)
        else:
            return False

    @staticmethod
    def _validate_not_null_or_empty(value: T) -> bool:
        return value is not None and value != ''

    @staticmethod
    def _validate_max_length(value: T, max_length: int = 9999999) -> bool:
        return len(value) <= max_length

    @staticmethod
    def _validate_format(value: T, regex: re.Pattern) -> bool:
        return regex.match(value) is not None
