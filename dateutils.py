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
import pytz
from pytz import timezone
from datetime import datetime, timedelta
import locale

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


def datetime_to_iso8061(date: datetime = None, tz=pytz.utc) -> str:
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

    return datetime.now(pytz.utc) + timedelta(hours=after_hours)


def timestamp_to_time_ago_text(start_time: float, lang: str) -> str:
    now = datetime.utcnow()
    start_time_dt = datetime.utcfromtimestamp(start_time)
    diff = now - start_time_dt

    if lang not in ["ja", "en", "es", "ar", "ru", "fr"]:
        lang = "en"

    if diff < timedelta(minutes=1):
        result = "just now" if lang == "en" else {
            "ja": "たった今",
            "es": "justo ahora",
            "ar": "الآن فقط",
            "ru": "только что",
            "fr": "à l'instant"
        }[lang]
    elif diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() // 60)
        if lang == "en":
            result = f"{minutes} minute ago" if minutes == 1 else f"{minutes} minutes ago"
        elif lang == "ja":
            result = f"{minutes}分前"
        elif lang == "es":
            result = f"hace {minutes} minuto" if minutes == 1 else f"hace {minutes} minutos"
        elif lang == "ar":
            result = f"منذ {minutes} دقيقة" if minutes == 1 else f"منذ {minutes} دقائق"
        elif lang == "ru":
            result = f"{minutes} минуту назад" if minutes == 1 else f"{minutes} минут назад"
        elif lang == "fr":
            result = f"il y a {minutes} minute" if minutes == 1 else f"il y a {minutes} minutes"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() // 3600)
        if lang == "en":
            result = f"{hours} hour ago" if hours == 1 else f"{hours} hours ago"
        elif lang == "ja":
            result = f"{hours}時間前"
        elif lang == "es":
            result = f"hace {hours} hora" if hours == 1 else f"hace {hours} horas"
        elif lang == "ar":
            result = f"منذ {hours} ساعة" if hours == 1 else f"منذ {hours} ساعات"
        elif lang == "ru":
            result = f"{hours} час назад" if hours == 1 else f"{hours} часов назад"
        elif lang == "fr":
            result = f"il y a {hours} heure" if hours == 1 else f"il y a {hours} heures"
    elif diff < timedelta(weeks=1):
        days = diff.days
        if lang == "en":
            result = f"{days} day ago" if days == 1 else f"{days} days ago"
        elif lang == "ja":
            result = f"{days}日前"
        elif lang == "es":
            result = f"hace {days} día" if days == 1 else f"hace {days} días"
        elif lang == "ar":
            result = f"منذ {days} يوم" if days == 1 else f"منذ {days} أيام"
        elif lang == "ru":
            result = f"{days} день назад" if days == 1 else f"{days} дней назад"
        elif lang == "fr":
            result = f"il y a {days} jour" if days == 1 else f"il y a {days} jours"
    elif diff < timedelta(days=30):
        weeks = diff.days // 7
        if lang == "en":
            result = f"{weeks} week ago" if weeks == 1 else f"{weeks} weeks ago"
        elif lang == "ja":
            result = f"{weeks}週間前"
        elif lang == "es":
            result = f"hace {weeks} semana" if weeks == 1 else f"hace {weeks} semanas"
        elif lang == "ar":
            result = f"منذ {weeks} أسبوع" if weeks == 1 else f"منذ {weeks} أسابيع"
        elif lang == "ru":
            result = f"{weeks} неделю назад" if weeks == 1 else f"{weeks} недель назад"
        elif lang == "fr":
            result = f"il y a {weeks} semaine" if weeks == 1 else f"il y a {weeks} semaines"
    elif diff < timedelta(days=365):
        months = diff.days // 30
        if lang == "en":
            result = f"{months} month ago" if months == 1 else f"{months} months ago"
        elif lang == "ja":
            result = f"{months}ヶ月前"
        elif lang == "es":
            result = f"hace {months} mes" if months == 1 else f"hace {months} meses"
        elif lang == "ar":
            result = f"منذ {months} شهر" if months == 1 else f"منذ {months} أشهر"
        elif lang == "ru":
            result = f"{months} месяц назад" if months == 1 else f"{months} месяцев назад"
        elif lang == "fr":
            result = f"il y a {months} mois"
    else:
        years = diff.days // 365
        if lang == "en":
            result = f"{years} year ago" if years == 1 else f"{years} years ago"
        elif lang == "ja":
            result = f"{years}年前"
        elif lang == "es":
            result = f"hace {years} año" if years == 1 else f"hace {years} años"
        elif lang == "ar":
            result = f"منذ {years} سنة" if years == 1 else f"منذ {years} سنوات"
        elif lang == "ru":
            result = f"{years} год назад" if years == 1 else f"{years} лет назад"
        elif lang == "fr":
            result = f"il y a {years} an" if years == 1 else f"il y a {years} ans"

    return result


if __name__ == "__main__":
    current_datetime = datetime.now()
    iso8061 = datetime_to_iso8061(date=current_datetime)
    print(f'datetime: {current_datetime}, convert to iso8061: {iso8061}')
    print(f'iso8061: {iso8061}, convert to datetime: {iso8061_to_datetime(iso8061)}')