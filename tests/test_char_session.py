# tests/test_char_session.py
#
# T-L3: Session(fakeredis)。Session.start(user_id) 後の redis キー構造(session:* と
# sessions:* 逆引き)、user_id() の戻り、clear() 後の状態、count()、
# get_user_id_from_session_id() を凍結。cookie ヘッダの発行有無も応答から凍結。
#
# sid は uuid4 で非決定なので、redis キー中の sid は '<SID>' に正規化して凍結する。

import pytest
import redis
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
    Session.configure('localhost', 6379, 0)
    _redis().flushall()
    yield
    _redis().flushall()
    Session.configure('localhost', 6379, 0)


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


def test_negative_session_same_browser_starts_two_parallel_authentications():
    """05: 同一ブラウザで 2 つの認証を並行開始できる。"""
    with app.test_request_context():
        first = Session.browser_context_id()
        second = Session.browser_context_id()

    assert first == second


def test_negative_session_rotation_preserves_browser_context_id():
    """05: Session ローテーション後も browser_context_id を引き継ぐ。"""
    with app.test_request_context():
        browser_context_id = Session.browser_context_id()
        old_session_id = Session.id()

        Session.start(USER_ID, browser_context_id=browser_context_id)

        assert Session.id() != old_session_id
        assert Session.browser_context_id() == browser_context_id
        assert not _redis().exists(f'{Session.SESSION_PREFIX}{old_session_id}')


def test_negative_session_clear_current_revokes_only_current_browser():
    """05/D-17: clear_current は当該 Session だけを失効する。"""
    with app.test_request_context():
        Session.start(USER_ID)
        first_session_id = Session.id()

    with app.test_request_context():
        Session.start(USER_ID)
        second_session_id = Session.id()
        Session.clear_current()

    assert _redis().exists(f'{Session.SESSION_PREFIX}{first_session_id}')
    assert not _redis().exists(f'{Session.SESSION_PREFIX}{second_session_id}')
    assert _redis().sismember(f'{Session.SESSIONS_PREFIX}{USER_ID}', first_session_id)
    assert not _redis().sismember(f'{Session.SESSIONS_PREFIX}{USER_ID}', second_session_id)


def test_negative_session_revoke_all_revokes_every_browser():
    """05/D-17: revoke_all は実 Cookie を持つ全端末 Session を失効する。"""
    session_prefix = 'auth_session:'
    Session.configure('localhost', 6379, 0, prefix=session_prefix)
    a = make_app()
    a.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=True,
    )
    a.session_interface = RedisSessionInterface(
        host='localhost',
        port=6379,
        db=0,
        expiration_time_sec=3600,
        prefix=session_prefix,
    )

    @a.post('/signin')
    def signin():
        Session.start(USER_ID)
        return {'session_id': Session.id()}

    @a.get('/current-user')
    def current_user():
        return {'user_id': Session.user_id()}

    @a.post('/revoke-all')
    def revoke_all():
        Session.revoke_all(USER_ID)
        return '', 204

    first_client = a.test_client()
    second_client = a.test_client()
    first_response = first_client.post('/signin', base_url='https://auth.example')
    second_response = second_client.post('/signin', base_url='https://auth.example')
    session_ids = {
        first_response.get_json()['session_id'],
        second_response.get_json()['session_id'],
    }
    set_cookie = first_response.headers['Set-Cookie']

    assert len(session_ids) == 2
    assert 'Secure' in set_cookie
    assert 'HttpOnly' in set_cookie
    assert 'SameSite=Lax' in set_cookie
    assert 'Domain=' not in set_cookie
    assert first_client.get(
        '/current-user', base_url='https://auth.example'
    ).get_json() == {'user_id': USER_ID}
    assert second_client.get(
        '/current-user', base_url='https://auth.example'
    ).get_json() == {'user_id': USER_ID}

    revoke_response = first_client.post(
        '/revoke-all', base_url='https://auth.example'
    )
    deleted_cookie = revoke_response.headers['Set-Cookie']

    assert revoke_response.status_code == 204
    assert deleted_cookie.startswith('session=;')
    assert 'Max-Age=0' in deleted_cookie
    assert 'Path=/' in deleted_cookie
    assert 'Secure' in deleted_cookie
    assert 'HttpOnly' in deleted_cookie
    assert 'SameSite=Lax' in deleted_cookie
    assert first_client.get(
        '/current-user', base_url='https://auth.example'
    ).get_json() == {'user_id': None}
    assert second_client.get(
        '/current-user', base_url='https://auth.example'
    ).get_json() == {'user_id': None}
    for session_id in session_ids:
        assert not _redis().exists(f'{session_prefix}{session_id}')
        assert not _redis().exists(f'user_id:{session_id}')
    assert not _redis().exists(f'{Session.SESSIONS_PREFIX}{USER_ID}')


class FailingSessionRedis:
    def smembers(self, _key):
        raise redis.ConnectionError('session store unavailable')


class FailingSessionStartRedis:
    def sadd(self, _key, _value):
        raise redis.ConnectionError('session store unavailable')


class FailingSessionClearRedis:
    def srem(self, _key, _value):
        raise redis.ConnectionError('session store unavailable')


def test_session_start_propagates_redis_failure(monkeypatch):
    monkeypatch.setattr(Session, '_redis', FailingSessionStartRedis())

    with app.test_request_context():
        with pytest.raises(redis.ConnectionError, match='session store unavailable'):
            Session.start(USER_ID)


def test_session_clear_current_propagates_redis_failure(monkeypatch):
    monkeypatch.setattr(Session, '_redis', FailingSessionClearRedis())

    with app.test_request_context():
        flask_session[Session.SESSION_KEY] = USER_ID
        flask_session.sid = 'current-session-id'
        with pytest.raises(redis.ConnectionError, match='session store unavailable'):
            Session.clear_current()


def test_session_revoke_all_propagates_redis_failure(monkeypatch):
    monkeypatch.setattr(Session, '_redis', FailingSessionRedis())

    with app.test_request_context():
        with pytest.raises(redis.ConnectionError, match='session store unavailable'):
            Session.revoke_all(USER_ID)


def test_session_interface_rejects_mismatched_body_prefix():
    Session.configure('localhost', 6379, 0, prefix='session:')

    with pytest.raises(ValueError, match='Session body prefix mismatch'):
        RedisSessionInterface(
            host='localhost',
            port=6379,
            db=0,
            expiration_time_sec=3600,
            prefix='auth_session:',
        )


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


def test_session_key_ttl_uses_seconds():
    # N-6 (P3-L1): expiration_time_sec は「秒」。save_session が設定する session:{sid} の
    # TTL が設定値(3600秒)相当であることを直接アサートする。days 誤用なら ~3600日
    # (= 311,040,000 秒)になり、この範囲外で fail する(Red)。
    a = make_app()
    a.session_interface = RedisSessionInterface(host='localhost', port=6379, db=0, expiration_time_sec=3600)

    @a.route('/login')
    def login():
        Session.start(USER_ID)
        return 'ok'

    a.test_client().get('/login')

    session_keys = [k for k in _scan_keys() if k.startswith(Session.SESSION_PREFIX)]
    assert len(session_keys) == 1, f'expected exactly one session:* key, got {session_keys}'
    ttl = _redis().ttl(session_keys[0])
    assert 3590 <= ttl <= 3600, f'expected ~3600s TTL, got {ttl}'
