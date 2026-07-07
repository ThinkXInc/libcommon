# tests/app_stub — 仮設足場(L-0c / TEMPORARY SCAFFOLD)

これは **仮設足場** である。恒久資産ではない。

## 目的
libcommon の `web/flask_helpers.py` と `web/session.py` は、host アプリの
`config`(`from config import Config, check_config`)と `models.data.user`
(`from models.data.user import User, ...`)に **import 時依存** している(計画書 §1.4 の
レイヤ逆転。flask_helpers.py L8 には作者自身の `# NEEDSFIX: don't depend on data.user`)。
この依存のため、libcommon は単独 import できず、改修前の挙動を凍結するテストも書けない。

この足場は、その host 依存をテスト内で最小スタブに差し替え、**改修前(現状)の
flask_helpers / session を import 可能にする**ためだけに存在する。

## 中身(本番挙動の権威ではない)
- `config.py` — `Config`(被 import モジュールが起動時に check_config で要求する全キーを充足)と
  `check_config`(欠落 or None で `MissingKeyError`。実 config_helper と同契約)。
- `models/data/user.py` — `User`(`objects(...).first()` の形状のみ偽装)、
  `UnauthorizedAccessError`、`UserNotFoundError`。

## 撤去条件(重要)
**L-1(依存注入化)の完了条件でこの足場は縮退・撤去される。** L-1 後、libcommon は
host の `config`/`models.data.user` に import 時依存しなくなるため、本ディレクトリは不要になる。
