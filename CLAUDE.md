# libcommon 開発規約

## このライブラリの性質(変更禁止)
- 全 ThinkX web サービスが共有する契約層。**単独で import 可能・単独でテスト可能**を必ず維持する。
  ホストアプリの config / models への import を書いてはならない(ruff/pyright と
  tests/test_smoke_import.py が検出する)。アプリ固有の値・オブジェクトは
  configure_flask_helpers() / Session.configure() / make_session_helper() で注入する。

## 上位契約
- PROTOCOL.md(ThinkX Auth Protocol v1)が APIErrorFormat の出力形状
  {field_name, code, message, reason} と成功外形 {code, message} に依存している。
  この外形の変更は「追加のみ」(PROTOCOL.md §6)。tests/test_protocol_anchors.py が錨。

## レスポンスの正典
- 現役契約は pydantic フォーマット族(http_response_formatter + http_errors +
  http_successes + validation_errors)。例外 raise 型の族は attic/ に退避済み。
  新しいエラー型は APIErrorFormat のサブクラスとして http_errors.py に追加する。

## デコレータの正典的積層順(上から)
  route → language_wrapper → content_type_check_json → required_fields_check →
  (regex_check / format_check / length_check)* → ハンドラ本体冒頭で validate_request
  順序依存の実挙動は tests/golden/ に凍結されている。

## 検証コマンド(変更時は全て green にしてからコミット)
- pytest / ruff check . / pyright
- 依存は requirements-dev.txt の exact ピン。無断アップグレード禁止。

## 禁止事項
- ホストアプリへの import(config, models 等)。
- APIErrorFormat / SuccessFormat の既存キーの削除・改名・型変更。
- attic/ の無断復帰。バグ発見時は findings.md に記録(挙動のついで修正禁止)。
