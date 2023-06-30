#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# helpers/dateutils.py
#
# usage:
# from heplers.dateutils import datetime_to_iso8061, iso8061_to_datetime
#
# *ISO8601
# 2020-12-28T15:11:00.0000+09:00 (UTC以外)
# 2020-12-28T15:11:00.0000Z (UTC)
#
# *Basic rules
# - The server will return the ISO 8061 format string in UTC time as
#   "YYYY-MM-DDTHH:mm:ss.SSSS+timezone" in the device's time zone.
# - The device will send the ISO 8061 format string in the device's time zone.
# - The database will store all datetime in UTC no matter which area it is sent from.
#
import sys
import os
from flask import jsonify
from pytz import timezone
from datetime import datetime, timedelta
sys.path.append('../')
from api.api_response import ErrorResponse, ErrorCode

ISO8061_FORMAT = "%Y-%m-%d'T'%H:%M:%S.%f%z"

class InvalidISOFormatError(Exception):
    def __init__(self, iso_formatted_string):
        self.iso_formatted_string = iso_formatted_string

    def __error_obj__(self):
        error_response = ErrorResponse(
            {
                'code': ErrorCode.INVALID_PARAMETER.value,
                'reason': ErrorCode.INVALID_PARAMETER.name,
                'message': f'{self.iso_formatted_string} is invalid as iso formatted timestamp.'
            }
        )
        return jsonify({'saved_data': None, 'error': error_response.json()}), 400

    def __str__(self):
        return repr(f'{self.iso_formatted_string} is invalid as iso formatted timestamp.')


def datetime_to_iso8061(date=None, tz="Asia/Tokyo"):
    date_with_timezone = date.astimezone(timezone(tz))  # return the user's local time
    iso_formatted = datetime.strftime(date_with_timezone, ISO8061_FORMAT)
    return iso_formatted


def iso8061_to_datetime(iso_formatted_string):

    # temporary measures
    # TODO: delete this code
    if iso_formatted_string[10] == "T":
        iso_formatted_string = iso_formatted_string.replace("T", "'T'")
    iso_formatted_string = iso_formatted_string.replace(" 0900", "+0900")

    try:
        date_with_timezone = datetime.strptime(
            iso_formatted_string, ISO8061_FORMAT)
        date_utc = date_with_timezone.astimezone(
            timezone("UTC"))  # always save as UTC
    except ValueError as e:
        raise InvalidISOFormatError(iso_formatted_string)
    else:
        return date_utc


def expiration_datetime(after_hours=48):
    return datetime.now() + timedelta(hours=after_hours)

if __name__ == "__main__": # Function Test
    datetime_string = datetime.now()
    iso8061 = "2021-01-31'T'16:25:08.309648+0900"
    print('datetime: {0}, convert to iso8061: {1}'.format(datetime_string, datetime_to_iso8061(date=datetime_string)))
    print('iso8061: {0}, convert to datetime: {1}'.format(iso8061, iso8061_to_datetime(iso8061)))
