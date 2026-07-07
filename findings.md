# findings.md — libcommon + quantz-web リファクタリング(Phase 2)

規範: `refactor_plan.md`(libcommon + quantz-web 計画書 v1.6)。
報告ルール §6: 修正せず「ファイル:行 / 事実 / 発見項目ID」で1行記録。解釈は書かない。
本ファイルは Phase 3(バグ修正計画)の入力。Security exception 該当は本ファイルに流さず即停止・人間へ報告する。

---

## L-0a 前提検証(転記のみ)

- L-0a: 計画 v1.1 で検証済み(kazukiotsukacom 消費ゼロ / truetech は thinkx 内)。

---

## §1.5 既知の潜在バグ・問題(計画書 §1.5 表からの転記)

| # | ファイル:行 | 事実 | 扱い(計画上) |
|---|---|---|---|
| F-1 | quantz-web `models/data/material_v1.py` L9 | 存在しないモジュール `libcommon.response.errors` を import(実行されれば ImportError) | Q-3 で修正 |
| F-2 | `web/session.py` L186, L204 | `Session.user_id() -> int` / `start(cls, user_id: int)` の型ヒントが嘘(実体は MongoDB ObjectId の str) | L-7 で修正([改修]面) |
| F-3 | `dateutils.py` L50, L71 | 公開関数名が `iso8061`(正: ISO 8601)。typo が公開 API に固定 | L-6 で正名追加+旧名エイリアス維持 |
| F-4 | `web/flask_helpers.py` L45 | `AVAILABLE_LANGS` がハードコード(`# TODO: use Config.AVAILABLE_LANGS` と作者マーク済み) | L-1 の初期化 API に吸収 |
| F-5 | `web/flask_helpers.py` L294以降 | `google_oauth_token_check` 内で `g.setdefault('errors',[])` と `g.errors.append` の二流儀が混在。except 経路で `g.errors` 未初期化だと AttributeError になりうる | L-2 で現挙動を凍結、修正は L-1 改修に内包 |
| F-6 | grep 実測(quantz-web 21箇所 + libcommon 内部) | `from libcommon.color import *` のスター import | 記録のみ。一斉修正は範囲外 |
| F-7 | thinkx `flask_helper.py`(69行) | thinkx が libcommon とは別に独自 flask_helper を保持(分岐した規約) | 記録のみ。統合判断は次期 |
| F-8 | `dateutils.py` L66, L51–63 | `datetime_to_iso8061` の引数デフォルトが naive な `datetime.now()`(tzinfo なし)。多地域分散のタイムゾーン整合目標に違反。docstring も自己矛盾(本文 Asia/Tokyo、シグネチャ pytz.utc、例 +09:00) | L-5 で正名関数側のみ修正(旧名は挙動保存) |
| F-9 | `dateutils.py` L115–116 | `timestamp_to_time_ago_text`(quantz-web が消費する唯一の dateutils 関数)が `datetime.utcnow()` / `datetime.utcfromtimestamp()` を使用。両者は Python 3.12 で deprecated | L-5 で内部実装のみ置換(外部挙動はゴールデン不変で証明) |

注(転記範囲): L-0b 指示文は「F-1〜F-7 を転記」と記すが、同じ v1.1 改訂が §1.5 表に F-8/F-9 を追加している(指示文の文面が追随していない内部齟齬)。上位=§1.5 表に従い F-1〜F-9 全件を転記した(superset・欠落回避)。

---

## 実行時の環境差分・文書差分(D-21 記録。挙動不変の最小置換)

- E-1(文書): libcommon 計画書の実ファイル名は `refactor_plan.md`。ルート CLAUDE.md ルーティング表と計画書 §8 指示文は `LIBCOMMON_QUANTZ_REFACTORING_PLAN.md` / `LIBCOMMON_PLAN.md` と記載。オーナー確認により実ファイル `refactor_plan.md` を規範として採用。CLAUDE.md の記載修正は人間のみ(実行者は記録のみ)。
- E-2(ブランチ): 規範(CLAUDE.md D-14・Phase 1 実績 simplicity)は `refactor/2026`。libcommon・quantz-web の実ブランチは `2026refactor`(`origin/2026refactor` に既 push 済み)。オーナー裁定「`2026refactor` が正・D-14 の `refactor/2026` 表記が陳腐化」。よって計画書内の `refactor/2026` / `refactor/plan-v1` は `2026refactor` と読み替え。改名・新規 push は行わない。CLAUDE.md/DECISIONS の書き換えは人間のみ。
- E-3(Python): デフォルト `python3` は 3.9.2rc1(計画の床 3.10+ 未満)。`/usr/local/bin/python3.10`(3.10.16)を明示使用して床を満たす(D-21 パス明示)。exact ピンからの逸脱ではない(3.10+ は床)。
- E-4(依存置換): `pytz==6.0` は存在しない(pytz は日付版数制。利用可能: 2024.1〜2026.2)。最近版として `pytz==2026.2` を exact ピン。本コードの pytz 消費は `utc`/`Asia/Tokyo` のみで日本は DST 無しのため挙動不変。requirements-dev.txt に固定。他のピンは計画指定どおり全一致。
- E-5(計画書の未コミット差分): libcommon・quantz-web 両ワークツリーに `refactor_plan.md` の v1.1→v1.6 更新が未コミットで存在(`M refactor_plan.md`)。計画書は実行者にとって読み取り専用のため編集せず、実行者のコミットにも含めない(明示パス add)。v1.6 更新の commit 要否は人間判断。
- E-6(venv 生成の環境的癖): cwd がリポジトリ直下のとき `python3.10 -m venv <path>` が `Error: No module named 'libcommon'` で失敗(`python3.10 -c` 単体は正常)。回避として `python3.10 -c "import venv; venv.create(<abspath>, with_pip=True, clear=True)"` で `.venv` を生成(成功・Python 3.10.16 / pip 24.3.1)。ensurepip は `-I` isolated 実行で cwd 非依存。原因の根治は範囲外・記録のみ。
- E-7(gitignore): `.gitignore` は `venv/` のみ無視し `.venv/`(計画が使うパス)を無視しなかった。L-0b 環境衛生として `.venv/` を追加。

---

## L-0c 実行時の新発見・環境記録

- N-1(新発見・構造): `locale.py`(リポジトリ直下のトップレベルモジュール)が Python 標準ライブラリ `locale` を shadow する。リポジトリ root が sys.path[0] に載る状況(例: repo root から `python -m pytest`。`-m` は cwd を先頭に追加)では、標準 `import locale`(calendar / pytest ブートストラップ等が内部で行う)が `libcommon/locale.py` に解決され、その先頭の `from libcommon.language import Language` が失敗して `ModuleNotFoundError: No module named 'libcommon'` になる。E-6 の gremlin の真因。→ Phase 3 仕分け対象。
- N-2(新発見・非推奨): `web/http_response_formatter.py:54, 56` が pydantic V2 で非推奨の `Field(..., example=...)` 追加キーワードを使用(PydanticDeprecatedSince20 警告)。非ブロッキング。→ Phase 3 仕分け対象。
- N-3(新発見・死荷重): `tests/mongobase_test.py:10–13` / `tests/modelbase_test.py:10–16` が不在モジュール(`nose`, `tools.*`, `general.*`)を import し収集不能(§1.6 記載の「mongo 系2ファイル」の実体はレガシー死テスト)。→ Phase 3 仕分け対象(削除 or 再実装)。
- E-8(依存ギャップ・オーナー承認): `web/google_oauth_helper.py:1` の `from google.oauth2 import id_token` / `from google.auth.transport import requests` が要求する **google-auth** と、その transport が実際に使う **requests** が L-0b ピン一覧から欠落。flask_helpers の smoke import を通す唯一の障壁だったため、オーナー承認のうえ実ライブラリを exact 導入: `google-auth==2.55.1`, `requests==2.34.2`(transitive: cryptography==49.0.0 / cffi / pycparser / pyasn1 / pyasn1_modules / certifi / urllib3 / charset-normalizer / idna)。requirements-dev.txt に固定。google 機能は特性テストで行使されないため挙動不変。
- E-9(実行標準・D-21): pytest 起動を **console-script `./.venv/bin/pytest <明示テストファイル>`** に標準化(`python -m pytest` でも `pytest tests/` の暗黙 glob でもない)。理由: (a) repo root からの `-m` は N-1 の locale shadow を誘発、(b) `tests/` glob は N-3 の死テストを収集してエラーになる。計画の完了条件 `pytest tests/ -k smoke_import` に対する挙動不変の明示パス置換。L-0c 完了確認: `./.venv/bin/pytest tests/test_smoke_import.py -k smoke_import` → 2 passed。

---

## L-0d 実行時の新発見(特性テストで実測。すべて Phase 3 仕分け対象)

- N-4(新発見・バグ): `dateutils.py:50, 67` `datetime_to_iso8061(date, tz=pytz.utc)` の `date.astimezone(timezone(tz))` は `pytz.timezone` が文字列を要求するため、既定 `tz=pytz.utc`(tzinfo オブジェクト)では `AttributeError: 'UTC' object has no attribute 'upper'`。**引数無し呼び出しは現状壊れている**(文字列 tz='UTC'/'Asia/Tokyo' は正常)。特性テスト `dateutils/iso8061_default_tz` で AttributeError を凍結。
- N-5(新発見・F821/実行時 NameError。L-0e の ruff で正式記録予定): `web/flask_helpers.py` に未定義名参照が複数。`handle_query_param_errors`(L166)→ `required_query_params` は必須クエリ欠落時に NameError。`MinLengthNotReachedErrorFormat`(L207・未 import)→ `length_check` は min 未満で NameError。`ErrorCode`(L301 ほか)・`locale`(L304)→ `google_oauth_token_check` は NameError。特性テストで NameError を凍結(`decorators/required_query_missing_nameerror`)。
- N-6(新発見・単位バグ): `web/session.py:103` `get_redis_expiration_time` が `timedelta(days=Config.REDIS_SESSION_EXPIRATION_TIME_SEC)` を返す。設定値の単位は秒(*_SEC)だが `days=` に渡している(3600 秒設定なら 3600 **日**の有効期限)。
- N-7(新発見・整合): `web/session.py:223–225` `Session.start` は `sessions:{user_id}`(sadd)と `user_id:{sid}`(set)のみ書き、`session:{sid}` を書かない。`session.py:257–264` `count` は `session:{sid}` 不在の sid を `srem` して除去する。→ save_session を経ない `Session.start` 直後の `count()` は常に 0(特性テスト `session/after_start` で実測凍結: start 直後キー=`sessions:user123`+`user_id:<SID>`、count 後=`user_id:<SID>` のみ、count=0)。
- N-8(新発見・実行時 NameError): `dateutils.py:92` `iso8061_to_datetime` の except 経路が commented-out の `InvalidISOFormatError` を参照 → 不正入力時に NameError(正常な往復は `dateutils/roundtrip` で凍結済み)。

---

## L-0e 床(ruff + pyright)で silence した pre-existing 債務(一括記録)

完了条件: `ruff check .` / `pyright` とも exit 0(達成)。修正はせず隔離のみ(修正は各[改修]項目 / Phase 3)。設定は `ruff.toml` / `pyrightconfig.json`。

- E-10(ruff, select=["F","E9"]。導入前 151 件を隔離):
  - global ignore `F403`/`F405`(11+76=87件): `from libcommon.color import *`(F-6)が全体に蔓延し、真の未定義名検出を F405 に化けさせる。一斉修正は §5 範囲外。**この結果、星 import を持つファイルでは F821 floor が実質無効**(既知の限界。F-6 修正まで残る)。
  - exclude: `vector_database`(§5 スモークのみ・~48件)、`tests/mongobase_test.py`・`tests/modelbase_test.py`(N-3 死テスト)、`tutorials`(ドキュメント notebook)。
  - per-file-ignores(pre-existing 分をファイル単位で隔離。他所では有効): celery(F401,F841)/ config_helper(F401)/ dateutils(F401,F821,F841)/ discord(F401,F821)/ enumlocale(F841)/ mongobase(F401,F722,F821,F841)/ mongomodel(F401)/ web/api_response_v1(F401,F821)/ web/errors_v1(F401)/ web/flask_helpers(F401)/ web/google_oauth_helper(F541)/ web/http_response_formatter(F401)/ web/session(F541)。
- E-11(pyright basic。導入前 44 errors を隔離):
  - exclude: `web`(計画: まず web/ 以外)/ `tests` / `tutorials` / `vector_database` / `dateutils.py` / `discord.py` / `mongobase.py`(残余 undefined-variable を持つファイル)。
  - global rule off(pre-existing 型精度債務): `reportArgumentType`(20)/ `reportAttributeAccessIssue`(13)/ `reportReturnType`(4)/ `reportCallIssue`(2)。`reportMissingImports`/`reportMissingModuleSource` off(§1.4 レイヤ逆転: `config`/`models`/`google` 未解決。L-1 で解消予定)。
  - `reportUndefinedVariable` は ON 維持(床信号)。残 5 warnings は `validator.py` の `TypeVar T` 単一使用(非致命・記録のみ)。
- N-9(新発見・F821): `discord.py:22` `send_to_discord` 未定義(§5 対象外)。
- N-10(新発見・F821): `mongobase.py:243` `cursor` 未定義、`mongobase.py:779` `pd`(pandas)未定義(§5 対象外)。
- N-11(新発見・F821): `web/api_response_v1.py:184` `key` 未定義(L-4「判断」領域・消費0)。
- N-12(新発見・F722): `mongobase.py:243` forward annotation の構文エラー(§5 対象外)。

---

## L-1 依存注入化(核心・[改修])の記録

- 決定(オーナー承認 2026-07-07): 完了条件#1(app_stub 無しの素の import)は L-1 署名対象2ファイル(session.py/flask_helpers.py)だけでは達成不能 — import 連鎖の `locale.py`([凍結])・`web/locale_helper.py`・`web/google_oauth_helper.py` も `from config import Config` に依存するため。オーナー裁定により **L-1 スコープを連鎖3モジュールへ拡張**(挙動保存・ゴールデン不変を絶対条件)して de-config した。
- 署名フォーム拡張(挙動保存): `RedisSessionInterface.__init__` は計画署名の host/port/db に加え **expiration_time_sec も引数化**(get_redis_expiration_time が旧 `Config.REDIS_SESSION_EXPIRATION_TIME_SEC` を参照していたため。config 除去の必要な帰結)。**N-6(days/秒の単位バグ)は「修正」せず**値の出所のみ付け替え(`timedelta(days=self.expiration_time_sec)` を維持。修正は Phase 3)。
- F-5(change 3): §1.5 の定義どおり `google_oauth_token_check` 内に限定して `g.errors.append` → `g.setdefault('errors', []).append` に統一。他デコレータの g.errors 挙動は不変(T-L2 の順序依存ゴールデンは不変)。N-5 の未定義名(ErrorCode/locale)は L-1 対象外・不変(Phase 3)。
- 連鎖 de-config(挙動保存): `locale.py` は `_DEFAULT_LANG='en'`+`configure_locale()`(getlang のフォールバックのみ・T-L4 非行使)。`locale_helper.py` は既定 `lang='en'`(呼出側は常に lang 明示)。`google_oauth_helper.py` は `_client_id`+`configure_google_oauth()`(特性テスト非行使)。
- E-12(完了条件#2 の残差・D-21 記録): `grep 'from config import|from models' libcommon/web/` は **live chain で 0件**だが、死コード `web/errors_v1.py:2` と `web/[DEPRECATE]api_errors.py:59` の2件が残る。両者は消費0の死コードで **L-3(api_errors 削除)/ L-4(errors_v1 attic)で除去**され、その時点で literally 0件になる。#2 の意図(消費される連鎖の脱 config)は達成済み。
- 完了条件結果: #1 素の import exit 0 ✅ / #3 特性テスト新 API 経由・ゴールデン不変 68 passed ✅ / #4 app_stub 撤去後 green ✅ / #5 ruff・pyright exit 0 ✅ / #2 上記 E-12。
