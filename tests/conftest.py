# tests/conftest.py
#
# L-0c 仮設足場の配線。
#  1) sys.path を明示構成(D-21: 暗黙探索に依存しない):
#       - app_stub を **先頭** に置き、host アプリの `config` / `models.data.user` を
#         スタブへ解決させる(libcommon 同梱の config.py より先に勝たせる)。
#       - libcommon リポジトリの **親**(ワークスペース root)を path に置き、
#         `import libcommon.web.session` を namespace package として解決可能にする。
#  2) redis を fakeredis へ monkeypatch してから libcommon.web.session を import する。
#     session.py はクラス本体(import 時)で `redis.ConnectionPool(...)` と
#     `StrictRedis(connection_pool=...)` を実行するため、**import より前** に差し替える。

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))            # .../libcommon/tests
_APP_STUB = os.path.join(_HERE, 'app_stub')                   # .../libcommon/tests/app_stub
_REPO = os.path.dirname(_HERE)                                # .../libcommon
_WORKSPACE = os.path.dirname(_REPO)                           # .../thinkx-system (親)

# 親を先に入れ、その後 app_stub を先頭へ(最終順: [app_stub, workspace, ...])
if _WORKSPACE not in sys.path:
    sys.path.insert(0, _WORKSPACE)
if _APP_STUB not in sys.path:
    sys.path.insert(0, _APP_STUB)

import redis
import fakeredis

# プロセス内で共有する単一の fake サーバ(session の読み書きが一貫するように)
_FAKE_SERVER = fakeredis.FakeServer()


class _FakeConnectionPool:
    """redis.ConnectionPool の差し替え。接続はせず引数を保持するだけ。"""

    def __init__(self, *args, **kwargs):
        self.kwargs = kwargs


def _fake_client(*args, **kwargs):
    """StrictRedis / Redis の差し替え。共有 fake サーバに繋いだ fakeredis を返す。

    connection_pool 等の kwargs は無視する(fake サーバ経由で一貫させる)。
    """
    return fakeredis.FakeStrictRedis(server=_FAKE_SERVER)


# session.py / RedisSessionInterface の import 時副作用より前に差し替える。
# session.py L33 の `from redis import StrictRedis, Redis` はこの時点の値を束縛する。
redis.ConnectionPool = _FakeConnectionPool
redis.StrictRedis = _fake_client
redis.Redis = _fake_client

import pytest


@pytest.fixture
def fake_redis_server():
    """特性テスト(L-0d T-L3)が共有 fake サーバへアクセスするためのフィクスチャ。"""
    return _FAKE_SERVER
