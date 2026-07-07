# tests/test_char_decorators.py
#
# T-L2: デコレータ挙動。language_wrapper / content_type_check_json / required_fields_check /
# regex_check / format_check / length_check / required_query_params を付けたダミーハンドラで
# 正常系・異常系の応答(JSON, status)を凍結。正典的積層順(quantz-web accounts.py の実例と
# 同順: language_wrapper → content_type_check_json → required_fields_check → regex_check)で1本、
# 順序を崩した場合の順序依存性(g.errors 未初期化 → AttributeError)も凍結する。

import pytest
from flask import jsonify

from golden_utils import assert_golden, make_app, make_locale

from libcommon.web.flask_helpers import (
    language_wrapper, content_type_check_json, required_fields_check,
    regex_check, format_check, length_check, required_query_params, validate_request,
    configure_flask_helpers,
)

# L-1: 依存注入。旧モジュール定数(Config 由来 + F-4 の AVAILABLE_LANGS ハードコード)と
# 同値を注入し、外部挙動(=ゴールデン)を保存する。
configure_flask_helpers(
    default_lang='en',
    available_langs=['en', 'ja', 'zh', 'ru', 'es', 'ar', 'fr'],
    basic_auth_username='testuser',
    basic_auth_password='testpass',
)

LOCALE = make_locale()
EMAIL_RE = r'^[^@\s]+@[^@\s]+\.[^@\s]+$'

app = make_app()


# ---- ルート定義(正典的積層順を含む) ----

@app.route('/lw/<lang>/echo')
@language_wrapper
def lw_echo(lang, lang_name):
    return jsonify({'lang': lang, 'lang_name': lang_name}), 200


@app.route('/ct/<lang>/post', methods=['POST'])
@language_wrapper
@content_type_check_json
def ct_post(lang, lang_name):
    return jsonify({'ok': True}), 200


@app.route('/rf/<lang>/create', methods=['POST'])
@language_wrapper
@content_type_check_json
@required_fields_check(['email', 'password'])
@regex_check('email', EMAIL_RE, 'email_format')
def rf_create(lang, lang_name):
    verr = validate_request(lang, LOCALE)
    if verr:
        return verr.http_response()
    return jsonify({'ok': True}), 200


@app.route('/fc/<lang>/post', methods=['POST'])
@language_wrapper
@content_type_check_json
@format_check('age', int)
def fc_post(lang, lang_name):
    verr = validate_request(lang, LOCALE)
    if verr:
        return verr.http_response()
    return jsonify({'ok': True}), 200


client = app.test_client()


def _resp_golden(name, resp):
    body = resp.get_json(silent=True)
    assert_golden(name, {'status': resp.status_code, 'body': body})


# ---- language_wrapper ----

def test_language_wrapper_valid():
    _resp_golden('decorators/lw_valid_en', client.get('/lw/en/echo'))


def test_language_wrapper_unsupported_aborts_404():
    resp = client.get('/lw/xx/echo')
    # 未対応言語は abort(404)。本文は Werkzeug の HTML なので status のみ凍結。
    assert_golden('decorators/lw_unsupported', {'status': resp.status_code})


# ---- content_type_check_json ----

def test_content_type_json_ok():
    _resp_golden('decorators/ct_ok', client.post('/ct/en/post', json={}))


def test_content_type_wrong_415():
    resp = client.post('/ct/en/post', data='{}', content_type='text/plain')
    _resp_golden('decorators/ct_wrong', resp)


# ---- required_fields_check + regex_check(正典順) ----

def test_canonical_all_valid():
    resp = client.post('/rf/en/create', json={'email': 'a@b.co', 'password': 'secret'})
    _resp_golden('decorators/canonical_valid', resp)


def test_canonical_missing_password():
    resp = client.post('/rf/en/create', json={'email': 'a@b.co'})
    _resp_golden('decorators/canonical_missing_password', resp)


def test_canonical_invalid_email():
    resp = client.post('/rf/en/create', json={'email': 'bad', 'password': 'secret'})
    _resp_golden('decorators/canonical_invalid_email', resp)


# ---- format_check ----

def test_format_check_ok():
    _resp_golden('decorators/format_ok', client.post('/fc/en/post', json={'age': 5}))


def test_format_check_wrong_type():
    _resp_golden('decorators/format_wrong_type', client.post('/fc/en/post', json={'age': 'notint'}))


# ---- 順序依存性(崩した積層) ----

def test_length_check_without_prior_init_raises_attributeerror():
    # length_check は g.errors を初期化せず append する(F-5 圏の順序依存)。
    # required_fields_check を前段に置かない崩し順では g.errors 未初期化 → AttributeError。
    @length_check('name', 2, 5)
    def h(lang=None, lang_name=None):
        return 'x'

    with app.test_request_context('/', method='POST', json={'name': 'toolong'}):
        with pytest.raises(AttributeError):
            h(lang='en')
    assert_golden('decorators/length_no_init_attributeerror', {'raises': 'AttributeError'})


# ---- required_query_params(未定義 handle_query_param_errors 参照 = 実行時 NameError) ----

def test_required_query_params_present_ok():
    @required_query_params(['q'])
    def h(lang=None, lang_name=None):
        return jsonify({'ok': True})

    with app.test_request_context('/?q=hello', method='GET'):
        resp = h(lang='en')
    assert_golden('decorators/required_query_present', {'body': resp.get_json(silent=True)})


def test_required_query_params_missing_raises_nameerror():
    # 欠落時 `handle_query_param_errors`(flask_helpers に未定義)を呼ぶ → NameError。findings 参照。
    @required_query_params(['q'])
    def h(lang=None, lang_name=None):
        return jsonify({'ok': True})

    with app.test_request_context('/?nope=1', method='GET'):
        with pytest.raises(NameError):
            h(lang='en')
    assert_golden('decorators/required_query_missing_nameerror', {'raises': 'NameError'})
