# tests/test_char_session.py
#
# T-L3: Session(fakeredis)。Session.start(user_id) 後の redis キー構造(session:* と
# sessions:* 逆引き)、user_id() の戻り、clear() 後の状態、count()、
# get_user_id_from_session_id() を凍結。cookie ヘッダの発行有無も応答から凍結。
#
# sid は uuid4 で非決定なので、redis キー中の sid は '<SID>' に正規化して凍結する。

import pytest
from flask import session as flask_session

from golden_utils import assert_golden, make_app

from libcommon.web.session import Session, RedisSessionInterface

# L-1: 依存注入。旧クラス属性 pool(Config 由来)と同値を注入し、外部挙動を保存する。
# conftest が redis を fakeredis に差し替え済みなので、これは fake サーバに繋がる。
Session.configure('localhost', 6379, 0)

app = make_app()
USER_ID = 'user123'


def _redis():
    # L-1: Session._r() が注入済み fakeredis クライアントを返す。
    return Session._r()


def _scan_keys():
    return sorted(k.decode() if isinstance(k, bytes) else k for k in _redis().keys('*'))


@pytest.fixture(autouse=True)
def _flush():
    _redis().flushall()
    yield
    _redis().flushall()


def test_session_start_structure():
    with app.test_request_context():
        Session.start(USER_ID)
        sid = flask_session.sid
        # start 直後のキー構造(count() の副作用を挟まず撮る)
        keys_after_start = sorted(k.replace(sid, '<SID>') for k in _scan_keys())
        uid = Session.user_id()
        reverse = Session.get_user_id_from_session_id(sid)
        # count() は session:{sid} 未書込のため orphan sid を srem する副作用を持つ(実挙動)
        cnt = Session.count(USER_ID)
        keys_after_count = sorted(k.replace(sid, '<SID>') for k in _scan_keys())
    assert_golden('session/after_start', {
        'user_id': uid,
        'reverse_lookup': reverse,
        'count': cnt,
        'redis_keys_after_start': keys_after_start,
        'redis_keys_after_count': keys_after_count,
    })


def test_session_clear_state():
    with app.test_request_context():
        Session.start(USER_ID)
        Session.clear()
        uid_after = Session.user_id()
        keys_after = _scan_keys()
    assert_golden('session/after_clear', {
        'user_id_after': uid_after,
        'redis_keys_after': keys_after,
    })


def test_session_get_user_id_from_unknown_sid():
    with app.test_request_context():
        result = Session.get_user_id_from_session_id('no-such-sid')
    assert_golden('session/reverse_lookup_unknown', {'result': result})


def test_session_cookie_issued_via_interface():
    a = make_app()
    a.session_interface = RedisSessionInterface(host='localhost', port=6379, db=0, expiration_time_sec=3600)

    @a.route('/login')
    def login():
        Session.start(USER_ID)
        return 'ok'

    resp = a.test_client().get('/login')
    set_cookie = resp.headers.get('Set-Cookie')
    assert_golden('session/cookie_issued', {
        'status': resp.status_code,
        'set_cookie_present': set_cookie is not None,
        'cookie_name_present': 'session=' in (set_cookie or ''),
    })
