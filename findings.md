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

---

## L-3 死荷重削除の記録

- E-13(完了条件の submodule 残差・D-21 記録): `web/[DEPRECATE]api_errors.py`(705行)を `git rm`。消費者ゼロを実測確認済み('api_errors' の全ヒットはファイル自身のコメント `# api/responses/api_errors.py` のみで、import する消費者は皆無)。libcommon 内 grep は 0件。ただし完了条件 grep `grep -rn 'api_errors' libcommon quantz-web thinkx` は **quantz-web の submodule スナップショット3件**(`web-server/libcommon`・`vectordb_server/libcommon`・`web-server/llm/libcommon` 内の同ファイル)を拾う。これらは編集禁止の vendored スナップショットで **Q-6 の vendoring カットオーバーで更新**される。live 消費者0(#L-3 の意図)は達成。

---

## Track Q 着手前の環境調査(Q-1 の前提・D-21 記録)

- E-14(Q-1 環境・macOS 固有制約): quantz-web `web-server/requirements.txt` は **132 パッケージで、Linux/CUDA 専用の ML スタックを含む**: `vllm==0.2.0` / `triton==2.0.0` / `xformers==0.0.22` / `nvidia-cuda-*-cu11`(11個)/ `ray==2.7.0` / `torch==2.0.1` / `transformers` 等。これらは **darwin(macOS)に wheel が無く導入不能**。したがって full requirements のインストールは本ホストで不可。
  - **feasibility の要**: main.py + 全 blueprint(accounts/studio/create/materials/payments/interviews/basic_configs/sample_sites/develop/deploy)+ init_flask_app + models/data/user を実測 grep した結果、**web アプリの import 連鎖は torch/vllm/transformers/xformers/ray/qdrant を一切 import しない(ML フリー)**。ML スタックは `llm/`(別 submodule)・celery worker 側の専有。
  - **したがって Q-1 は curated サブセット(flask/mongoengine/pymongo/msgpack/pydantic/python-dotenv/redis/requests/stripe/boto3/Flask-HTTPAuth/google-auth/dnspython/jsonschema/PyYAML/pika/pycryptodome 等の web 用のみ)で feasible**。ML/CUDA/Linux-only パッケージは test venv から除外し、その旨を記録する(Phase 1 の eslint・E-4 pytz と同じ「導入不能は最近似 or 除外+記録」方針)。full install を試みない。
  - main.py の import 時副作用: `config`(Config/check_config)/ `init_mongodb`(モジュールレベル `mongoengine.connect`)/ 各 blueprint。Q-1 の conftest は main import 前に `mongoengine.connect` を mongomock で monkeypatch + fakeredis + `config_test.py`(全必須キー)を要する(計画 v1.3 の注入機構どおり)。
  - **順序(§8)**: Q-1 スキップ不可(L-4 以降は Q-3 に依存)。Track Q の環境立ち上げが次の焦点。

---

## Q-1 テストプロセス起動可能化の記録

- 結果: `pytest tests/ -k test_app_imports` → **1 passed**(`from main import app` 成功、~1.3s、安定)。
- curated venv: scratchpad 外部に構築(repo 非コミット)。再現用に **`web-server/tests/requirements-test.txt`**(ML/CUDA 除外の web サブセット、exact ピン)をコミット。**除外した Linux/CUDA-only(E-14): vllm / triton / xformers / nvidia-cuda-*-cu11(11個)/ ray / torch / transformers / xformers / accelerate / datasets / optimum / vllm / fastapi 系(vectordb API)/ uvicorn**。full requirements への切替はしない(D-16: 本物のインフラは AWS 移行 STEP2)。
- 注入(conftest。src 変更ゼロ): (1) `sys.modules['config'] = config_test`(全必須キー+直接アクセスキーを網羅。metaclass catch-all は不使用 — optional な `getattr(config,X,default)` を壊さないため)、(2) redis→fakeredis、(3) `mongoengine.connect`→mongomock、(4) `boto3.client/resource`→MagicMock、(5) `vectordb_server.*`(path 外の別コンポーネント)を meta path finder で mock 解決。
- N-13(新発見・import 時副作用): `mails/send_mail.py` が**モジュール import 時に SES 経由でテストメールを2通送信**(Mail Client Test 1/2。`libcommon/mail.py` の `boto3.client('ses')`)。本番 creds では**アプリ起動/import のたびに実メール送信**。テストでは boto3 mock で遮断。boto3 リトライで import が数分ハングする実害も観測。→ Phase 3(import 時副作用の除去)。
- config_test が 70 の静的抽出を超えて必要とした直接アクセス/追加 check_config キー: SUPPORTED_LANGS / GENERAL_CREDIT_PER_RESPONSE / INTERVIEW_CREDIT_PER_RESPONSE / MONTHLY_FREE_CREDIT / PAYMENT_MAX_RETRIES / PAYMENT_RETRY_DELAY / SENDER / REPLY_TO / SES_AWS_REGION / MAIL_NOREPLY / MAIL_SYSTEM / GOOGLE_OAUTH_CLIENT_ID / BASIC_AUTH_USERNAME / BASIC_AUTH_PASSWORD(後3者は submodule libcommon 旧版由来)。

---

## Q-2 ルート総なめ + API 3型スナップショットの記録

- ルート総なめ(`tests/golden/route_sweep.json`): 72 GET ルート、status 分布 **200×39 / 302×21 / 401×4 / 404×2 / 500×6**(2回実行で安定=決定的)。テンプレは相対パス `views/templates`(cwd 依存)のため conftest で `os.chdir(web-server)` して本番同等に解決(→ 39 ルートが描画 200)。このスイートが以後の全変更 + AWS 移行 STEP2 の受け入れ試験を兼ねる。
- 残 6×500 ルート(現状凍結・Phase 3 仕分け): `/<lang>/getstarted`(TemplateNotFound `test/get_started.html`)、`/<lang>/interview/demo`、`/interviews/<id>/add/<client_id>`、`/v1/<lang>/interviews/<id>`、`/v1/<lang>/users/verify_link`、`/v1/users/verify_link`(欠落テンプレ + ダミー id/token のデータ経路エラー混在)。
- API 3型形状(`tests/golden/api_shape_*.json`): 型3 バリデーション `{code, errors, message, reason}`/400、型2 単体エラー `{field_name, code, message, reason}`/415 は live エンドポイント `/v1/en/users/create` から。型1 成功 `{code, message, user}`/200 は認証 live が harness 不可のため同一 SuccessFormat クラスの http_response() を app 文脈で凍結。
- N-14(新発見・genuine バグ): `accounts.py:323` `users_create` が `request.json["email"]` を**検証前に直接アクセス** → email 欠落(空 json 等)で KeyError → 500。required_fields_check より前に落ちるため、本来のバリデーション 400 応答に到達しない。→ Phase 3。
- E-15(harness 制約・D-21 記録): `models/data/user.py:294` `create_new` の一部クエリ経路を **mongomock が "Special options not supported"(NotImplementedError)で拒否** → signup 成功・認証済み経路が harness 下で実行不能。Q-2 の成功型は契約形状源(format クラス)から凍結して回避。実 MongoDB(AWS 移行 STEP2)では実行可の見込み。

---

## Q-3 壊れた import 修正(F-1)の記録

- F-1 の dead/alive 判定(計画要請): `models/data/material_v1.py` は **web-server のどこからも import されない dead ファイル**(live な model は `material.py`。material_v1 は旧 v1・0 importer。Q-1 で app import が成功したのはこのため)。ただしファイル内では `ProcessingError`/`ResourceNotFoundError` を 7 箇所で使用(return 値)。
- 対応(計画 L-4 注記どおり: errors_v1 に import を直さず material_v1 側をフォーマット族へ寄せる): `web/http_errors` の `BadRequestAPIErrorFormat`(ProcessingError 相当)/ `ResourceNotFoundAPIErrorFormat`(ResourceNotFoundError 相当)へ写像。メッセージは `locale.get(<key>, lang, locale_args=...)`。dead ファイルゆえ app 挙動・Q-2 ゴールデンに無影響(Q-2 5 passed・不変を確認)。
- E-16(完了条件の submodule 残差・D-21 記録): `grep -rn 'libcommon.response' quantz-web` は **live app code で 0件**(material_v1.py 修正で達成)。残 14 件は全て編集禁止の vendored/submodule 領域: `web-server/libcommon/`・`vectordb_server/libcommon/`・`web-server/llm/libcommon/`(libcommon 旧スナップショットの `celery.py`/`errors_v1.py`/`dateutils.py`)+ `web-server/llm/queue_server/task_handler.py`(llm submodule 自体)。いずれも **Q-6 の vendoring / 各 submodule 更新で解消**。#F-1 の意図(live の壊れた import 除去)は達成。
- 派生記録(Phase 3 候補): libcommon 原本にも `celery.py` が `libcommon.response.successes/errors`(非実在)を import する疑い(submodule コピーに同型)。celery は §5 対象外(スモークのみ)だが、libcommon 側の壊れた import として Phase 3 で確認・仕分け。

---

## L-4 例外族の attic 退避の記録

- 既定判断(オーナー未反転)どおり `web/api_response_v1.py`(368行)/ `web/errors_v1.py`(131行)を **`attic/` へ `git mv`**。消費者ゼロを実測確認(非 self 参照 0件)。errors_v1 は `libcommon.response.api_response`(非実在)+ `from config import Config` の二重壊れだが dead ゆえ退避で足りる。
- `attic/README.md` に退避理由(例外 raise 型の二重定義・v2 統合判断待ち)を記録。**attic は検証の床から除外**: ruff `extend-exclude` と pyright `exclude` に `attic` を追加し、web/ 側の stale per-file-ignore(api_response_v1/errors_v1)を削除。
- 完了条件: attic 以外で `grep 'api_response_v1|errors_v1'` 0件 ✅ / pytest 73 passed ✅ / ruff・pyright exit 0 ✅。E-12(L-1 で残った web/errors_v1 の `from config import`)は本項目の退避で live web/ から消滅。

---

## L-5 dateutils 正名化 + 時刻ドクトリンの記録

- 正名関数を追加(旧 `*8061*` は typo=ISO **8601**。旧名は現挙動保存で残置): `datetime_to_iso8601`(既定 aware UTC。date=None で `datetime.now(pytz.utc)` → **F-8 を正名側で解消**。tz は tzinfo/文字列両対応)、`iso8601_to_datetime`(戻り aware UTC)。
- epoch 対を追加: `datetime_to_epoch`(naive は UTC とみなす)/ `epoch_to_datetime`(aware UTC)。→ datetime ⇄ ISO8601 ⇄ epoch の三点相互変換が閉じる(往復同一性を T-L5 で凍結)。
- F-9: `timestamp_to_time_ago_text` の内部を deprecated な naive-UTC API から aware UTC(`now(timezone.utc)`/`fromtimestamp(tz=timezone.utc)`)へ置換。**now/start とも aware UTC で diff 同値 → 外部挙動不変**(T-L5 の time_ago ゴールデン不変で機械証明。git 上で既存ゴールデン無変更を確認)。`grep 'utcnow|utcfromtimestamp' dateutils.py` 0件。
- モジュール冒頭に UTC ドクトリンを明文化(保存・演算は aware UTC、表示時のみ変換、新規で naive を作らない)。
- 残置(現挙動保存ゆえ・Phase 3): 旧 `datetime_to_iso8061` の既定 tz=pytz.utc は AttributeError(N-4)、旧 `iso8061_to_datetime` の異常系は未定義 `InvalidISOFormatError`(N-8)。いずれも旧名の現挙動として凍結済み。
- 完了条件: 正名/epoch 往復・新既定 UTC 直接アサート・旧名現挙動 pytest green(76 passed)/ 旧ゴールデン不変 ✅ / grep 0件 ✅ / pyright exit 0 ✅。

---

## L-6 Session の型と契約の精密化の記録

- F-2 の型ヒントの嘘を修正(挙動不変・型と docstring のみ): `user_id() -> Optional[str]`、`start(user_id: str)`、`count(user_id: str)`、`get_user_id_from_session_id() -> Optional[str]`(user_id は MongoDB ObjectId の str)。`from typing import Optional` 追加。
- Session クラス docstring に **Redis キー体系(逆引き)** を明文化: `session:{sid}`=本体 / `sessions:{user_id}`=sid 集合(逆引き・多端末カウント用)/ `user_id:{sid}`=逆引きマップ。auth プロトコル §2 手順6 の「ローカルセッション」がこのクラスである旨をコメント参照。
- 完了条件: T-L3 ゴールデン不変(76 passed・git 上で無変更確認)✅ / ruff・pyright exit 0 ✅。注: session.py は web/ にあり pyright 除外(L-0e の「まず web/ 以外」)のため、型修正は correctness 目的で gate 非強制。web/ の型検査有効化は次期(L-0e の phasing)。

---

## L-7 / L-8 の記録

- L-7: `libcommon/CLAUDE.md`(契約の機械可読化)を計画全文どおり作成。**権限ブロック→解決の記録**: `.claude/settings.json` の `Write(CLAUDE.md)`/`Edit(CLAUDE.md)` が gitignore 形式で任意階層の CLAUDE.md に一致し libcommon/CLAUDE.md も阻んだ。オーナーが root 限定(`/CLAUDE.md`)へ緩和して解禁(settings は実行者不可侵のため人間が変更。D-21 停止→承認の流れ)。
- L-8: `scripts/bake.sh <tag> <dest>`(clone→tag checkout→.git 除去→VERSION 生成→配置)を作成。**tree sha256 は `__pycache__`/`*.pyc` を除外**(v1.8)。ハッシュツールは macOS 互換で `shasum -a 256`(計画例示の `sha256sum` は macOS に無いため。挙動同値=SHA-256、findings 記録)。mechanics 検証: bake 先で `import libcommon.web.flask_helpers, libcommon.web.session` 成功(原則7=単独 import 可能を bake 先でも証明)。v2.0.0 タグを全ゲート green 時点で付与。
