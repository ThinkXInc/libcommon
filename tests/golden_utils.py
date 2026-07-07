# tests/golden_utils.py
#
# 特性テスト(L-0d)の共通基盤。
# ドクトリン(大原則1・simplicity 0-3 と同一): 期待値を推測で書かない。
# **初回実行の実測値を tests/golden/<name>.json に書き出して固定**し、以降はそれと厳密比較する。
#
# ゴールデンには絶対パス・時刻など環境依存値を混入させない(例外は型のみ凍結する等、
# 各テスト側で正規化する)。

import json
import os

from flask import Flask

from libcommon.locale import Locale, COMMON_LOCALES_FILE_PATHS

GOLDEN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'golden')


def _normalize(obj):
    """JSON ラウンドトリップで安定化(キー順を固定、非 JSON 値は str 化)。"""
    return json.loads(json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str))


def assert_golden(name, actual):
    """初回: actual をゴールデンとして書き出して pass。以降: ゴールデンと厳密一致を要求。"""
    path = os.path.join(GOLDEN_DIR, name + '.json')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    actual = _normalize(actual)
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(actual, f, ensure_ascii=False, indent=2, sort_keys=True)
        return
    with open(path, encoding='utf-8') as f:
        expected = json.load(f)
    assert actual == expected, (
        f"golden mismatch: {name}\n  expected={expected}\n  actual={actual}"
    )


def make_app():
    """特性テスト用の最小 Flask アプリ(jsonify / request / g / session の文脈を供給)。"""
    app = Flask('libcommon_char_tests')
    app.config['SECRET_KEY'] = 'characterization-test-secret'
    app.config['SESSION_COOKIE_NAME'] = 'session'
    return app


def make_locale():
    """libcommon 同梱ロケール(errors / validation_errors / api_response)を統合した Locale。

    get_locale_text / validate_request が使うのと同じ3ファイル。
    """
    return Locale(list(COMMON_LOCALES_FILE_PATHS))
