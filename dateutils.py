#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# helpers/dateutils.py
#
# Usage:
# from helpers.dateutils import datetime_to_iso8061, iso8061_to_datetime, expiration_datetime
#
# Example:
# current_datetime = datetime.now()
# iso_date = datetime_to_iso8061(current_datetime)
# converted_datetime = iso8061_to_datetime(iso_date)
# expiration_date = expiration_datetime(72)
#

import sys
from flask import jsonify
from pytz import timezone
from datetime import datetime, timedelta
sys.path.append('../')
#from libcommon.response.api_response import ErrorResponse, ErrorCode


#class InvalidISOFormatError(Exception):
#    """Exception raised for invalid ISO 8061 formatted strings.
#
#    Attributes:
#        iso_formatted_string -- the invalid ISO 8061 string that caused the exception
#    """
#    
#    def __init__(self, iso_formatted_string):
#        self.iso_formatted_string = iso_formatted_string
#
#    def __error_obj__(self):
#        """Constructs an error object for JSON response."""
#        error_response = ErrorResponse({
#            'code': ErrorCode.INVALID_PARAMETER.value,
#            'reason': ErrorCode.INVALID_PARAMETER.name,
#            'message': f'{self.iso_formatted_string} is invalid as iso formatted timestamp.'
#        })
#        return jsonify({'data': None, 'error': error_response.json()}), 400
#
#    def __str__(self):
#        return repr(f'{self.iso_formatted_string} is invalid as iso formatted timestamp.')


def datetime_to_iso8061(date: datetime = None, tz="Asia/Tokyo") -> str:
    """Converts a datetime object to its ISO 8061 string representation.

    Parameters:
    - date: datetime object to be converted. Uses current date and time if not provided.
    - tz: The timezone to convert to before formatting. Default is "Asia/Tokyo".

    Returns: 
    - ISO 8061 formatted string of the date.

    Example:
    >>> datetime_to_iso8061(datetime(2021, 1, 31, 16, 25, 8, 309648))
    '2021-01-31T16:25:08.309648+09:00'
    """
    
    if not date:
        date = datetime.now()
    date_with_timezone = date.astimezone(timezone(tz))
    return date_with_timezone.isoformat()


def iso8061_to_datetime(iso_formatted_string: str) -> datetime:
    """Converts an ISO 8061 string to its datetime object representation.

    Parameters:
    - iso_formatted_string: The ISO 8061 string to be converted.

    Returns: 
    - datetime object representing the input string.

    Raises:
    - InvalidISOFormatError: If the input string is not a valid ISO 8061 format.

    Example:
    >>> iso8061_to_datetime('2021-01-31T16:25:08.309648+09:00')
    datetime.datetime(2021, 1, 31, 16, 25, 8, 309648, tzinfo=<UTC>)
    """
    
    try:
        date_with_timezone = datetime.fromisoformat(iso_formatted_string)
        date_utc = date_with_timezone.astimezone(timezone("UTC"))
    except ValueError as e:
        raise InvalidISOFormatError(iso_formatted_string)
    else:
        return date_utc


def expiration_datetime(after_hours=48):
    """Returns the datetime after a certain number of hours from now.

    Parameters:
    - after_hours: Number of hours from now for the expiration. Default is 48.

    Returns: 
    - datetime object of the expiration time.

    Example:
    >>> expiration_datetime(72)
    datetime.datetime(2023, 9, 25, 7, 45, 12, 345678)  # Example time
    """

    return datetime.now() + timedelta(hours=after_hours)


if __name__ == "__main__":
    current_datetime = datetime.now()
    iso8061 = datetime_to_iso8061(date=current_datetime)
    print(f'datetime: {current_datetime}, convert to iso8061: {iso8061}')
    print(f'iso8061: {iso8061}, convert to datetime: {iso8061_to_datetime(iso8061)}')