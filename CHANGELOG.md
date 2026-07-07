# CHANGELOG

## v2.1.0 (2026-07-07) — Phase 3 bug fixes (bugfix_plan v1.1, Track L')

挙動変更(Red→Fix→Green。特性テストのゴールデンは各項目が名指しするもののみ更新)。

- **N-6** `web/session.py`: セッション有効期限を **秒** として解釈(旧: `get_redis_expiration_time`
  が `expiration_time_sec` を `timedelta(days=...)` に誤用 → 3600秒設定が3600日 TTL に化けていた)。
- **N-7** `web/session.py`: `Session.start` が TTL 付き `session:{sid}` プレースホルダを先行書込し、
  `Session.count()` が start 直後の live セッションを反映する(旧: count() が生成直後の sid を
  掃除して常に 0 を返していた)。
- **N-5** `web/flask_helpers.py`: エラー経路が `NameError` を送出せず適切なレスポンス外形を返す。
  `handle_query_param_errors`(ValidationErrors 族・400)を新設、`MinLengthNotReachedErrorFormat` と
  `ErrorCode` を import、google-oauth の missing-token 分岐を `GoogleOauthTokenErrorFormat.http_response()`
  (401)へ修正。新規のレスポンス外形は追加していない(PROTOCOL.md §6 準拠)。
- **N-8** `dateutils.py`: `iso8061_to_datetime` が不正入力に対し `InvalidISOFormatError`
  (`ValueError` サブクラス)を送出する(旧: 未定義参照による `NameError`)。旧名 `*8061*` 2関数に
  Deprecation 注記を追加(正名は `*8601*`)。N-4 の既定 tz `AttributeError` は互換のため凍結のまま。
- **N-2** `web/http_response_formatter.py`: 非推奨の `Field(..., example=...)` を
  `Field(..., json_schema_extra={'example': ...})` に置換(レスポンス外形は不変)。
- **N-3**: 死テスト(`tests/mongobase_test.py` / `tests/modelbase_test.py`)と、それらの stale な
  ruff exclude を削除。

### 次期送り(本サイクルでは未修正)

- **celery.py**(P3-L7): `import libcommon.celery` は失敗する(`libcommon.response` が非実在)が
  シンボルは live。現状 import に成功している消費者は存在せず、v2.1.0 での現状維持は退行ではない。
  修復は celery の実用途が確定した時点の設計判断(次期サイクル入力)。

### リリース時ゲート

pytest(E-9 明示テスト集合)76+ passed / ruff green / pyright 0 errors。
