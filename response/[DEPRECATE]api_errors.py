#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# [DEPRECATED]
#
# NOTE: 
#  Now all objects are in migration:
#  - general format and base class : api/response/api_response.py
#  - specific error format : api/response/validation_errors.py
#  - specific success format : api/response/successes.py
#
#
# api/responses/api_errors.py
#
# InvalidFormatError
# SaveError
# InvalidUserIDError
# InvalidNameError
# InvalidEmailFormatError
# InvalidPasswordFormat
# InvalidContentType
# InvalidCountryError
# InvalidOrganizationNameError
# InvalidOrganizationTypeError
# EmailNotCorrespondingError
# ConfirmationCodeNotCorresponding
# MailValidationCodeNotCorrespondingError
# UserAlreadyExistsError
# OrganizationMemberAlreadyExistsError
# OrganizationMemberCannotResignAdminRoleError
# OrganizationKeynameAlreadyExistError
# TargetMemberNotFoundError
# UserNotFoundError
# SessionDoesntExistError
# OrganizationNotFoundError
# OrganizationMemberNotFoundError
# ContentNotFoundError
# InvalidNameLength
# InvalidTitleLength
# InvalidTextLength
# InvalidDescriptionLength
# PasswordIncorrectError
# InvalidTimestampError
# InvalidLatLonError
# InvalidFacilityIDError
# InvalidQuestionIDError
# InvalidAnswerError
# InvalidAudioContentIDError
# InvalidXYError
# InvalidItemType
# InvalidCheckInPanelIDError
# InvalidLanguage
# EmailSentFailed
#

import re
from flask import jsonify
from general.api_response import ErrorResponse, ErrorCode
from config import Config
from libcommon.locale import Locale

# locale object with errors.json
locale = Locale(f'{Config.LOCALES_ROOT}/errors.json')
# the function message(key, lang, *args)
message = locale.message


# camelcase to snake case
def snake(name):
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()


# General Errors

class ValidationError(Exception):
    def __init__(self, errors, lang="en"):
        self.errors = errors
        self.__message__ = message(
            snake(self.__class__.__name__), lang)
    
    def __error_obj__(self):
        error_response = ErrorResponse(
            {
                'code': ErrorCode.BAD_REQUEST.value,
                'reason': ErrorCode.BAD_REQUEST.name,
                'message': self.__message__
            }
        )
        error_dicts = [e.__error__() for e in self.errors]
        print(error_dicts)
        return jsonify({
            'saved_data': None,
            'error': error_response.json(),
            'errors': error_dicts,  # list(map(lambda d: d.json(), error_dicts))
            }), ErrorCode.BAD_REQUEST.value

    def __str__(self):
        return repr(self.__message__)


class APIError(Exception):
    __key__ = ''
    __message__ = ''
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, key, value):
        self.value = value
        self.__key__ = key
        self.__message__ = ''
        
    def __error__(self) -> dict:
        return {
                'key': self.__key__,
                'code': self.__http_error__.value,
                'reason': self.__http_error__.name,
                'message': self.__message__
               }

    def __error_obj__(self) -> tuple:
        error_response = ErrorResponse(self.__error__())
        return jsonify(
            {
                'saved_data': None,
                'error': error_response.json()
            }), self.__http_error__.value

    def __str__(self):
        return repr(self.__message__)


# Specific Error Patterns

class RequiredFieldsNotSatisfied(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, key, value, lang="en"):
        self.__key__ = key
        self.value = value
        self.__message__ = message(
            snake(self.__class__.__name__), lang, value)


class InvalidFormatError(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, key, value, lang="en"):
        self.__key__ = key
        self.value = value
        self.__message__ = message(
            snake(self.__class__.__name__), lang, value, self.__key__)


class NameTooLongError(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, key, value, maxlen, lang="en"):
        self.__key__ = key
        self.value = value
        self.maxlen = maxlen
        self.__message__ = self.__message__ = message(
            snake(self.__class__.__name__), lang, self.maxlen, value)


class SaveError(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, key, name, error, lang="en"):
        self.__key__ = key
        self.name = name
        self.error = error
        self.__message__ = self.__message__ = message(
            snake(self.__class__.__name__), lang, self.name, error)


class InvalidValueError(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, key, value, lang="en"):
        self.__key__ = key 
        self.value = value
        self.__message__ = message(
            snake(self.__class__.__name__), lang, value, key)


class InvalidUserIDError(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, key, value, lang="en"):
        self.__key__ = key 
        self.value = value
        self.__message__ = message(
            snake(self.__class__.__name__), lang, value)


class InvalidNameError(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, key, value, lang="en"):
        self.__key__ = key 
        self.value = value
        self.__message__ = message(
            snake(self.__class__.__name__), lang, value)


class InvalidEmailFormatError(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, key, value, lang="en"):
        self.__key__ = key
        self.value = value
        self.__message__ = message(
            snake(self.__class__.__name__), lang, value)


class InvalidZipCodeFormatError(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, key, value, lang="en"):
        self.__key__ = key
        self.value = value
        self.__message__ = message(
            snake(self.__class__.__name__), lang, value)


class InvalidTelCountryCodeFormatError(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, key, value, lang="en"):
        self.__key__ = key
        self.value = value
        self.__message__ = message(
            snake(self.__class__.__name__), lang, value)


class InvalidTelFormatError(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, key, value, lang="en"):
        self.__key__ = key
        self.value = value
        self.__message__ = message(
            snake(self.__class__.__name__), lang, value)


class InvalidLatLngFormatError(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, key, value, lang="en"):
        self.__key__ = key
        self.value = value
        self.__message__ = message(
            snake(self.__class__.__name__), lang, value)


class PasswordContainsNoAlphabetError(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, key, value, lang="en"):
        self.__key__ = key
        self.value = value
        self.__message__ = message(
            snake(self.__class__.__name__), lang, value)


class PasswordContainsNoNumberError(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, key, value, lang="en"):
        self.__key__ = key
        self.value = value
        self.__message__ = message(
            snake(self.__class__.__name__), lang, value)


class InvalidPasswordFormatError(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, key, value, lang="en"):
        self.__key__ = key
        self.value = value
        self.__message__ = message(
            snake(self.__class__.__name__), lang, value)


class ConfirmationPasswordNotCorrespondingError(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, key, value, lang="en"):
        self.__key__ = key
        self.value = value
        self.__message__ = message(
            snake(self.__class__.__name__), lang, value)


class InvalidContentType(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, value, lang="en"):
        self.value = value
        self.__message__ = message(
            snake(self.__class__.__name__), lang, value)


class InvalidCountryError(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, key, value, lang="en"):
        self.__key__ = key
        self.value = value
        self.__message__ = message(
            snake(self.__class__.__name__), lang, value)


class InvalidOrganizationNameError(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, key, value, lang="en"):
        self.__key__ = key
        self.value = value
        self.__message__ = message(
            snake(self.__class__.__name__), lang, value)


class InvalidOrganizationTypeError(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, key, value, lang="en"):
        self.__key__ = key
        self.value = value
        self.__message__ = message(
            snake(self.__class__.__name__), lang, value)


class EmailNotCorrespondingError(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, key, value, lang="en"):
        self.__key__ = key
        self.value = value
        self.__message__ = message(
            snake(self.__class__.__name__), lang, value)


class ConfirmationCodeNotCorrespondingError(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, key, value, lang="en"):
        self.__key__ = key
        self.value = value
        self.__message__ = message(
            snake(self.__class__.__name__), lang)


class MailValidationCodeNotCorrespondingError(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, key, value, lang="en"):
        self.__key__ = key
        self.value = value
        self.__message__ = message(
            snake(self.__class__.__name__), lang)


class UserAlreadyExistsError(APIError):
    __http_error__ = ErrorCode.CONFLICT

    def __init__(self, key, value, lang='en'):
        self.__key__ = key
        self.value = value
        self.__message__ = message(
            snake(self.__class__.__name__), lang, value)


class OrganizationMemberAlreadyExistsError(APIError):
    __http_error__ = ErrorCode.CONFLICT

    def __init__(self, key, value, lang="en"):
        self.__key__ = key
        self.value = value
        self.__message__ = message(
            snake(self.__class__.__name__), lang, value)


class UserNotFoundError(APIError):
    __http_error__ = ErrorCode.NOT_FOUND

    def __init__(self, key, lang="en"):
        self.__key__ = key 
        self.__message__ = message(
            snake(self.__class__.__name__), lang, key)


class OrganizationNotFoundError(APIError):
    __http_error__ = ErrorCode.NOT_FOUND

    def __init__(self, key, lang="en"):
        self.__key__ = key 
        self.__message__ = message(
            snake(self.__class__.__name__), lang, key)


class OrganizationMemberNotFoundError(APIError):
    __http_error__ = ErrorCode.NOT_FOUND

    def __init__(self, key, lang="en"):
        self.__key__ = key 
        self.__message__ = message(
            snake(self.__class__.__name__), lang, key)


class AddressNotFoundError(APIError):
    __http_error__ = ErrorCode.NOT_FOUND

    def __init__(self, key, lang="en"):
        self.__key__ = key 
        self.__message__ = message(
            snake(self.__class__.__name__), lang, key)


class OrganizationMemberPermissionDeniedError(APIError):
    __http_error__ = ErrorCode.FORBIDDEN

    def __init__(self, user_id, action, lang="en"):
        self.user_id = user_id
        self.action = action
        self.__message__ = message(
            snake(self.__class__.__name__), lang, user_id, action)


class OrganizationMemberCannotResignAdminRoleError(APIError):
    __http_error__ = ErrorCode.FORBIDDEN

    def __init__(self, user_id, lang="en"):
        self.user_id = user_id
        self.__message__ = message(
            snake(self.__class__.__name__), lang, user_id)


class OrganizationKeynameAlreadyExistError(APIError):
    __http_error__ = ErrorCode.CONFLICT

    def __init__(self, keyname, lang="en"):
        self.__key__name = keyname 
        self.__message__ = message(
            snake(self.__class__.__name__), lang, keyname)


class TargetMemberNotFoundError(APIError):
    __http_error__ = ErrorCode.NOT_FOUND

    def __init__(self, _id, lang="en"):
        self._id = _id
        self.__message__ = message(
            snake(self.__class__.__name__), lang, _id)


class ContentNotFoundError(APIError):
    __http_error__ = ErrorCode.NOT_FOUND

    def __init__(self, index, language, lang="en"):
        self.index = index
        self.language = language
        self.__message__ = message(
            snake(self.__class__.__name__), lang, index, language)


class SessionDoesntExistError(APIError):
    __http_error__ = ErrorCode.UNAUTHORIZED

    def __init__(self, lang="en"):
        self.__message__ = message(
            snake(self.__class__.__name__), lang)


class PasswordIncorrectError(APIError):
    __http_error__ = ErrorCode.UNAUTHORIZED

    def __init__(self, key, value, email, lang="en"):
        self.__key__ = key
        self.value = value
        self.email = email
        self.__message__ = message(
            snake(self.__class__.__name__), lang, email)


class PreviousPasswordIncorrectError(APIError):
    __http_error__ = ErrorCode.NOT_FOUND

    def __init__(self, key, value, email, lang="en"):
        self.__key__ = key
        self.value = value
        self.email = email
        self.__message__ = message(
            snake(self.__class__.__name__), lang, email)


class NewPasswordsNotCorrespondingError(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, key, value, lang="en"):
        self.__key__ = key
        self.value = value
        self.__message__ = message(
            snake(self.__class__.__name__), lang, key)


class InvalidPasswordResetCodeError(APIError):
    __http_error__ = ErrorCode.UNAUTHORIZED

    def __init__(self, key, value, lang="en"):
        self.__key__ = key
        self.value = value
        self.__message__ = message(
            snake(self.__class__.__name__), lang, key)


class InvalidTimestampError(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, key, value, lang="en"):
        self.__key__ = key
        self.value = value
        self.__message__ = message(
            snake(self.__class__.__name__), lang, value)


class InvalidLatLonError(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, lat, lon, lang="en"):
        self.lat = lat
        self.lon = lon
        self.__message__ = message(
            snake(self.__class__.__name__), lang, lat, lon)


class InvalidFacilityIDError(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, _id, lang="en"):
        self._id = _id 
        self.__message__ = message(
            snake(self.__class__.__name__), lang, _id)


class InvalidQuestionIDError(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, _id, lang="en"):
        self._id = _id 
        self.__message__ = message(
            snake(self.__class__.__name__), lang, _id)
        '{self.question_id} is invalid as question_id.'


class InvalidAnswerError(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST
    def __init__(self, key, value, lang="en"):
        self.__key__ = key
        self.value = value
        '{self.answer} is invalid as answer.'


class InvalidAudioContentIDError(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, _id, lang="en"):
        self._id = _id 
        self.__message__ = message(
            snake(self.__class__.__name__), lang, _id)


class InvalidPlaybackRateError(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, key, value, lang="en"):
        self.__key__ = key
        self.value = value
        self.__message__ = message(
            snake(self.__class__.__name__), lang, key, value)


class InvalidCheckInPanelIDError(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, _id, lang="en"):
        self._id = _id 
        self.__message__ = message(
            snake(self.__class__.__name__), lang, _id)


class InvalidXYError(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, x, y, lang="en"):
        self.x = x
        self.y = y
        self.__message__ = message(
            snake(self.__class__.__name__), lang, x, y)


class ItemNotFound(APIError):
    __http_error__ = ErrorCode.NOT_FOUND

    def __init__(self, _id, lang="en"):
        self._id = _id 
        self.__message__ = message(
            snake(self.__class__.__name__), lang, _id)


class StoreInfoNotFound(APIError):
    __http_error__ = ErrorCode.NOT_FOUND

    def __init__(self, _id, lang="en"):
        self._id = _id 
        self.__message__ = message(
            snake(self.__class__.__name__), lang, _id)


class InvalidItemType(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, key, value, lang="en"):
        self.__key__ = key
        self.value = value
        self.__message__ = message(
            snake(self.__class__.__name__), lang, value)


class InvalidIndex(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, key, value, lang="en"):
        self.__key__ = key
        self.value = value
        self.__message__ = message(
            snake(self.__class__.__name__), lang, value)


class InvalidNameLength(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, key, value, min_len, max_len, lang="en"):
        self.__key__ = key
        self.value = value
        self.min = min_len
        self.max = max_len
        self.__message__ = message(
            snake(self.__class__.__name__), lang, value, min_len, max_len)


class InvalidTitleLength(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, key, value, min_len, max_len, lang="en"):
        self.__key__ = key
        self.value = value
        self.min = min_len
        self.max = max_len
        self.__message__ = message(
            snake(self.__class__.__name__), lang, value, min_len, max_len)


class InvalidTextLength(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, key, value, min_len, max_len, lang="en"):
        self.__key__ = key
        self.value = value
        self.min = min_len
        self.max = max_len
        self.__message__ = message(
            snake(self.__class__.__name__), lang, value, min_len, max_len)


class InvalidDescriptionLength(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, key, value, min_len, max_len, lang="en"):
        self.__key__ = key
        self.value = value
        self.min = min_len
        self.max = max_len
        self.__message__ = message(
            snake(self.__class__.__name__), lang, value, min_len, max_len)


class InvalidLanguage(APIError):
    __http_error__ = ErrorCode.BAD_REQUEST

    def __init__(self, key, value, lang="en"):
        self.__key__ = key
        self.value = value
        self.__message__ = message(
            snake(self.__class__.__name__), lang, value)


class EmailSentFailed(APIError):
    __http_error__ = ErrorCode.BAD_GATEWAY

    def __init__(self, key, value, error, lang="en"):
        self.__key__ = key
        self.value = value
        self.error = error
        self.__message__ = message(
            snake(self.__class__.__name__), lang, value, error)