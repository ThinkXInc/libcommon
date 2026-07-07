# tests/conftest.py
#
# L-1 後の配線。libcommon は host アプリの config / models.data.user に import 時依存しなく
# なったため、app_stub は不要になった(L-0c 足場の撤去。完了条件#4)。
#  1) sys.path: libcommon リポジトリの親(ワークスペース root)を置き、
#     `import libcommon.web.session` を namespace package として解決可能にする(D-21 明示)。
#  2) redis を fakeredis へ monkeypatch。Session.configure() / RedisSessionInterface() が
#     生成する redis 接続を差し替える(実 redis に繋がない)。

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))            # .../libcommon/tests
_REPO = os.path.dirname(_HERE)                                # .../libcommon
_WORKSPACE = os.path.dirname(_REPO)                           # .../thinkx-system(親)

if _WORKSPACE not in sys.path:
    sys.path.insert(0, _WORKSPACE)

import redis
import fakeredis

# プロセス内で共有する単一の fake サーバ(session の読み書きが一貫するように)
_FAKE_SERVER = fakeredis.FakeServer()


class _FakeConnectionPool:
    """redis.ConnectionPool の差し替え。接続はせず引数を保持するだけ。"""

    def __init__(self, *args, **kwargs):
        self.kwargs = kwargs


def _fake_client(*args, **kwargs):
    """StrictRedis / Redis の差し替え。共有 fake サーバに繋いだ fakeredis を返す。"""
    return fakeredis.FakeStrictRedis(server=_FAKE_SERVER)


redis.ConnectionPool = _FakeConnectionPool
redis.StrictRedis = _fake_client
redis.Redis = _fake_client

import pytest


@pytest.fixture
def fake_redis_server():
    """特性テスト(T-L3)が共有 fake サーバへアクセスするためのフィクスチャ。"""
    return _FAKE_SERVER
