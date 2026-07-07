# tests/app_stub/config.py
#
# 仮設足場(L-0c)。libcommon が host アプリの `config` モジュールに import 時依存する
# レイヤ逆転(§1.4)を、テスト内で断ち切るための最小スタブ。
# **L-1 の依存注入化が完了したら不要になり撤去される。** 本番挙動の権威ではない。
#
# ここで提供する Config は、被 import モジュールが起動時に check_config で要求する
# 全キー(実測で列挙)を埋めたテスト用設定:
#   - flask_helpers : DEFAULT_LANG / BASIC_AUTH_USERNAME / BASIC_AUTH_PASSWORD
#   - session       : REDIS_SESSION_HOST / REDIS_SESSION_PORT / REDIS_SESSION_DB_NUMBER /
#                     REDIS_SESSION_EXPIRATION_TIME_SEC
#   - locale        : DEFAULT_LANG
#   - google_oauth_helper : GOOGLE_OAUTH_CLIENT_ID


class MissingKeyError(Exception):
    """Raised when a required key is missing from config.

    実アプリの config_helper.check_config と同じ契約(欠落 or None で送出)を再現する。
    """
    pass


class Config:
    DEFAULT_LANG = 'en'

    BASIC_AUTH_USERNAME = 'testuser'
    BASIC_AUTH_PASSWORD = 'testpass'

    REDIS_SESSION_HOST = 'localhost'
    REDIS_SESSION_PORT = 6379
    REDIS_SESSION_DB_NUMBER = 0
    REDIS_SESSION_EXPIRATION_TIME_SEC = 3600

    GOOGLE_OAUTH_CLIENT_ID = 'test-google-oauth-client-id.apps.googleusercontent.com'


def check_config(config, required_keys):
    """Check that every required key exists on config and is not None.

    実アプリ config_helper.check_config の契約と同値: 欠落 or None のキーがあれば
    MissingKeyError を送出。ログ副作用(色付け)はテストでは不要なので持たない。
    """
    missing_or_none_keys = [
        key for key in required_keys
        if not hasattr(config, key) or getattr(config, key) is None
    ]
    if missing_or_none_keys:
        raise MissingKeyError(
            f"Missing or None configuration keys: {', '.join(missing_or_none_keys)}"
        )
