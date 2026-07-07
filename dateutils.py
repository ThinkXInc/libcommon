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
from datetime import datetime, timedelta, timezone as _tz
import locale

# --- 時刻ドクトリン(L-5) -------------------------------------------------------
# 保存・演算は常に **aware UTC**(tzinfo 付き)で行う。表示時のみ対象タイムゾーンへ変換する。
# 新規コードで naive な datetime を作らない。datetime ⇄ ISO8601 文字列 ⇄ epoch数値 は
# 正名関数(datetime_to_iso8601 / iso8601_to_datetime / datetime_to_epoch / epoch_to_datetime)
# で相互変換する。旧名(*8061* = ISO 8601 の typo)は現挙動保存のため残置(下記コメント参照)。
# -------------------------------------------------------------------------------

sys.path.append('../')
#from libcommon.response.api_response import ErrorResponse, ErrorCode


class InvalidISOFormatError(ValueError):
    """Raised when an ISO-formatted timestamp string cannot be parsed (N-8).

    ValueError のサブクラス。iso8061_to_datetime の except 経路が送出する。既存の
    `except ValueError` 呼び出し側でも捕捉できるよう ValueError から派生する。
    """


# typo alias, kept for compatibility; naive-now default preserved(現挙動保存。新規は datetime_to_iso8601 を使う)
def datetime_to_iso8061(date: datetime = None, tz=pytz.utc) -> str:
    """Deprecated: use datetime_to_iso8601 (aware-UTC default, L-5 正名版).

    N-4: 既定 tz=pytz.utc(tzinfo オブジェクト)での引数付き呼び出しは、文字列前提の
    pytz.timezone に不適合で AttributeError を送出したまま(互換のため凍結・挙動不変)。

    Converts a datetime object to its ISO 8061 string representation.

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
    """Deprecated: use iso8601_to_datetime (L-5 正名版). 旧名は ISO 8601 の typo。

    Converts an ISO 8061 string to its datetime object representation.

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


# typo alias, kept for compatibility(現挙動保存。新規は iso8601_to_datetime を使う)
# ↑ 旧 iso8061_to_datetime は上に定義済み。以下は正名版(L-5 追加)。


def datetime_to_iso8601(date: datetime = None, tz=pytz.utc) -> str:
    """datetime → ISO 8601 文字列(正名版)。

    ドクトリン: 既定は **aware UTC**。date=None のとき aware UTC の現在時刻を用いる
    (旧 8061 版の naive `datetime.now()` 既定=F-8 をここで解消)。naive な date は
    UTC とみなして aware 化してから tz へ変換する。tz は tzinfo でも文字列でも受ける。
    """
    if date is None:
        date = datetime.now(pytz.utc)
    if isinstance(tz, str):
        tz = timezone(tz)
    if date.tzinfo is None:
        date = pytz.utc.localize(date)
    return date.astimezone(tz).isoformat()


def iso8601_to_datetime(s: str) -> datetime:
    """ISO 8601 文字列 → aware UTC datetime(正名版)。

    tz 指定の無い文字列は UTC とみなす。戻りは常に aware UTC。
    """
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    return dt.astimezone(pytz.utc)


def datetime_to_epoch(dt: datetime) -> float:
    """datetime → epoch 秒(float)。naive は UTC とみなす。"""
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    return dt.timestamp()


def epoch_to_datetime(ts: float) -> datetime:
    """epoch 秒 → aware UTC datetime。"""
    return datetime.fromtimestamp(ts, tz=_tz.utc)


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
    # L-5(F-9): deprecated な naive-UTC API を aware UTC(now(_tz.utc)/fromtimestamp(tz=_tz.utc))に置換。
    # now も start も aware UTC なので diff は同値 → 外部挙動(=T-L5 ゴールデン)は不変。
    now = datetime.now(_tz.utc)
    start_time_dt = datetime.fromtimestamp(start_time, tz=_tz.utc)
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