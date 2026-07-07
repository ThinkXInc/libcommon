# tests/test_char_dateutils.py
#
# T-L5: dateutils。datetime_to_iso8061 / iso8061_to_datetime の往復同一性・tz 引数、
# expiration_datetime(after_hours)、timestamp_to_time_ago_text の言語別出力
# (quantz-web が消費する唯一の関数)。
#
# 非決定な now 依存は相対 delta で決定化する(推測ではなく実測をバケットに固定)。

import time
from datetime import datetime

import pytz
import pytest

from golden_utils import assert_golden

from libcommon import dateutils as D

# 固定入力(UTC aware)
FIXED = datetime(2021, 1, 31, 16, 25, 8, 309648, tzinfo=pytz.utc)


def test_iso8061_default_tz_raises_attributeerror():
    # 既定 tz=pytz.utc(tzinfo オブジェクト)は文字列前提の pytz.timezone に不適合 → AttributeError
    # (findings 参照: 引数無し呼び出しは現状壊れている)
    with pytest.raises(AttributeError):
        D.datetime_to_iso8061(FIXED)
    assert_golden('dateutils/iso8061_default_tz', {'raises': 'AttributeError'})


def test_iso8061_utc_string():
    assert_golden('dateutils/iso8061_utc', D.datetime_to_iso8061(FIXED, tz='UTC'))


def test_iso8061_asia_tokyo():
    assert_golden('dateutils/iso8061_asia_tokyo', D.datetime_to_iso8061(FIXED, tz='Asia/Tokyo'))


def test_iso8061_roundtrip():
    iso = D.datetime_to_iso8061(FIXED, tz='Asia/Tokyo')
    back = D.iso8061_to_datetime(iso)
    assert back == FIXED  # UTC 等価に戻る
    assert_golden('dateutils/roundtrip', {
        'iso': iso,
        'back_iso': back.isoformat(),
        'equals_orig': back == FIXED,
    })


def test_iso8601_roundtrip_canonical():
    # 正名版: aware UTC の往復同一性
    iso = D.datetime_to_iso8601(FIXED)
    back = D.iso8601_to_datetime(iso)
    assert back == FIXED
    assert_golden('dateutils/iso8601_roundtrip', {'iso': iso, 'back_iso': back.isoformat(), 'equals': back == FIXED})


def test_iso8601_default_is_aware_utc():
    # 正名版の既定は aware UTC(F-8 を正名側で解消)。値は now() で非決定なので tz 性質を凍結。
    s = D.datetime_to_iso8601()
    parsed = D.iso8601_to_datetime(s)
    assert_golden('dateutils/iso8601_default_utc', {
        'ends_with_utc_offset': s.endswith('+00:00'),
        'tzinfo': str(parsed.tzinfo),
    })


def test_epoch_roundtrip():
    # datetime <-> epoch の往復同一性(戻りは aware UTC)
    ts = D.datetime_to_epoch(FIXED)
    back = D.epoch_to_datetime(ts)
    assert back == FIXED
    assert_golden('dateutils/epoch_roundtrip', {'epoch': ts, 'back_iso': back.isoformat(), 'equals': back == FIXED})


def test_expiration_datetime():
    e = D.expiration_datetime(72)
    now = datetime.now(pytz.utc)
    hours = round((e - now).total_seconds() / 3600)
    assert hours == 72
    assert_golden('dateutils/expiration', {'tzinfo': str(e.tzinfo), 'hours_from_now': hours})


AGO_CASES = [
    ('just_now', 1),
    ('minutes', 5 * 60),
    ('hours', 3 * 3600),
    ('days', 3 * 86400),
    ('weeks', 2 * 7 * 86400),
    ('months', 4 * 30 * 86400),
    ('years', 2 * 365 * 86400),
]
LANGS = ['en', 'ja', 'es', 'ar', 'ru', 'fr']


@pytest.mark.parametrize('bucket,delta', AGO_CASES)
def test_time_ago(bucket, delta):
    out = {}
    for lang in LANGS:
        start = time.time() - delta
        out[lang] = D.timestamp_to_time_ago_text(start, lang)
    assert_golden(f'dateutils/time_ago_{bucket}', out)


def test_time_ago_unsupported_lang_falls_back_to_en():
    start = time.time() - 5 * 60
    assert_golden('dateutils/time_ago_unsupported_lang', D.timestamp_to_time_ago_text(start, 'zzz'))
