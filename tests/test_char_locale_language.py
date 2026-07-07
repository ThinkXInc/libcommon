# tests/test_char_locale_language.py
#
# T-L4: locale / language。
# Locale.get(存在キー×2言語 / 欠損キー / 欠損lang / locale_args 展開)、to_json_string の安定性、
# Language.lang_label_map。

import json

import pytest

from golden_utils import assert_golden, make_locale

from libcommon.language import Language


def test_locale_get_existing_two_langs():
    loc = make_locale()
    assert_golden('locale/get_required_en', loc.get('required', 'en'))
    assert_golden('locale/get_required_ja', loc.get('required', 'ja'))


def test_locale_get_missing_key_raises_keyerror():
    loc = make_locale()
    with pytest.raises(KeyError):
        loc.get('__no_such_key__', 'en')
    # 例外メッセージには絶対パス(__file_paths__)が含まれ非可搬なため型のみ凍結
    assert_golden('locale/get_missing_key', {'raises': 'KeyError'})


def test_locale_get_missing_lang_raises_valueerror():
    loc = make_locale()
    with pytest.raises(ValueError):
        loc.get('required', '__no_such_lang__')
    assert_golden('locale/get_missing_lang', {'raises': 'ValueError'})


def test_locale_get_locale_args_expansion():
    loc = make_locale()
    # 'max_length' の en は "... no more than $0 characters ..." を含む → $0 を置換
    assert_golden('locale/get_max_length_args_en', loc.get('max_length', 'en', locale_args=['128']))


def test_locale_to_json_string_stability():
    loc = make_locale()
    s1 = loc.to_json_string()
    s2 = loc.to_json_string()
    assert s1 == s2  # 決定的
    data = json.loads(s1)
    # 可搬な指紋: トップレベルキーのソート済み一覧 + 総数(内容全体の巨大ゴールデン化は避ける)
    assert_golden('locale/to_json_string_fingerprint', {
        'top_keys_sorted': sorted(data.keys()),
        'key_count': len(data),
    })


def test_language_lang_label_map_full():
    assert_golden('language/lang_label_map_full', Language.lang_label_map())


def test_language_lang_label_map_only():
    assert_golden('language/lang_label_map_only_en_ja', Language.lang_label_map(only=['en', 'ja']))
