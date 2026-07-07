# tests/test_smoke_import.py
#
# L-0c 完了条件: レガシー結合していた web モジュールが、仮設足場(conftest + app_stub)の下で
# 単独 import できることを凍結する。挙動は問わない — import が通ることだけを確認する。

def test_smoke_import_session():
    import libcommon.web.session as session_mod
    assert hasattr(session_mod, 'Session')
    assert hasattr(session_mod, 'RedisSessionInterface')


def test_smoke_import_flask_helpers():
    import libcommon.web.flask_helpers as flask_helpers_mod
    assert hasattr(flask_helpers_mod, 'make_session_helper')
    assert hasattr(flask_helpers_mod, 'configure_flask_helpers')
    assert hasattr(flask_helpers_mod, 'language_wrapper')
