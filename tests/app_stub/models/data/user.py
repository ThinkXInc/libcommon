# tests/app_stub/models/data/user.py
#
# 仮設足場(L-0c)。flask_helpers が `from models.data.user import ...` で host アプリの
# データ層に import 時依存する(§1.4 / F-4 の NEEDSFIX マーク)ため、テスト内で断ち切る
# 最小スタブ。**L-1 の依存注入化が完了したら不要になり撤去される。**
#
# flask_helpers.session_helper は `User.objects(id=user_id).first()` の形で消費する。
# import を通し、その呼び出し形状を満たす最小の偽装のみを提供する(本番挙動の権威ではない)。


class UnauthorizedAccessError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


class _Query:
    """`User.objects(...)` の戻り値の最小偽装。`.first()` のみを持つ。"""

    def __init__(self, result=None):
        self._result = result

    def first(self):
        return self._result


class User:
    """models.data.user.User の最小スタブ。"""

    def __init__(self, id=None, email=None):
        self.id = id
        self.email = email

    @classmethod
    def objects(cls, **kwargs):
        # 既定では該当なし(.first() -> None)。特性テストで必要なら差し替える。
        return _Query(None)
