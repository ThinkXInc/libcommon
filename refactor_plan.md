# libcommon + quantz-web リファクタリング計画書 v1.1

作成日: 2026-07-06(v1.1 同日改訂)/ 対象: libcommon(`master` HEAD)+ quantz-web(`master` HEAD、参照実装トラック)
実行環境の前提: Python 3.10以上、git、pip、Node.js(Q-5のJS確認時のみ)。
関連文書: PROTOCOL.md(ThinkX Auth Protocol v1・上位契約)/ simplicityリファクタリング計画書 v1.2(別トラック・混線禁止)

v1.1 の変更点: (1) L-0a の前提検証を計画作成時に実測完了(kazukiotsukacom の[改修]面消費ゼロを確認、truetech は thinkx 内と確認)— 実行者の作業から除外。(2) dateutils の実測検算により F-8(naive `datetime.now()` デフォルト=多地域分散目標に違反)・F-9(deprecated な `utcnow`/`utcfromtimestamp` の使用)を発見済み事実に追加し、L-5 を拡張。(3) config の pydantic-settings 化を「やらないこと」に明記(次期候補)。

---

## 大原則(実行者は最初にこれを読むこと)

1. **オラクルは本番ではなくテストである。** quantz-web は現在稼働していない。したがって simplicity 計画の「本番挙動=正解」は使えず、代わりに**特性テストとして凍結した挙動が正解**になる。凍結する前の挙動変更は検証不能なので禁止。
2. **変更には二つの等級があり、各作業項目に明記されている。**
   - **[凍結]** — 静的サイト群(thinkx 等)が消費している面。挙動保存。特性テストで固定してから触る(触るのは整理のみ)。
   - **[改修]** — 消費者が quantz-web のみと**実測で証明済み**の面(flask_helpers / session)。意図的な破壊的変更を許す。ここが本計画の存在理由: quantz-web が停止している今だけ、この面の改修コストが最小になる(戦略的な窓)。
3. **人間による動作確認は行わない・要求しない。** 全完了条件はコマンド実行と機械比較(pytest green / exit code / grep件数 / JSON形状一致)で判定する。
4. **1項目 = 1コミット。** 完了条件を満たせなければ「戻し方」で破棄し、中断して報告する。
5. **devDependencies / pip パッケージは exact バージョンでピンする**(`pip install pkg==X.Y.Z`、`~=`・無指定禁止)。
6. **PROTOCOL.md v1 は上位契約である。** `APIErrorFormat` の出力形状 `{field_name, code, message, reason}` と成功外形 `{code, message}` は auth プロトコル §5 がそのまま土台にしている。この外形は**凍結**(変更は追加のみ。PROTOCOL.md §6 の互換性ルールが libcommon にも適用される)。
7. **本計画の最重要ゴール: libcommon を単独で import 可能・単独でテスト可能にする。** 現状はアプリ側の `config.py` と `models/data/user.py` が sys.path に無いと import すら失敗する(§1.4)。これを解消しない限り、libcommon の全テストはアプリの骨格を偽造しないと書けず、vendoring 後の各サイトでの検証もできない。
8. **検証層の床:** ruff(F821 未定義名ほか)+ pyright(basic)+ pytest 特性テスト。JS 側の床(ESLint/jsdom)は simplicity 計画の管轄であり本計画では扱わない。

---

## 1. 現状理解

### 1.1 libcommon とは何か

全 ThinkX web サービスが共有する Python ライブラリ(5,165行)。消費形態は現在 git submodule(本計画完了後に vendoring へ移行する。→ L-9 / Q-6)。層は大きく: 汎用(logger/color/validator/language/locale/dateutils/cipher)、データ(mongobase/mongomodel/modelbase/redisbase)、web 契約層(`web/` 配下: レスポンス形式・デコレータ・セッション)、周辺(mail/discord/celery/vector_database)。

### 1.2 消費実態(実測。この表が[凍結]/[改修]の等級を決定する)

| libcommon モジュール | quantz-web | thinkx | 等級 |
|---|---|---|---|
| logger / color | 22 / 21+3 箇所 | 3 / 3 | [凍結] |
| locale / language / enumlocale | 11+4 / 11 | 2 / 2 | [凍結] |
| validator | 8 | 2 | [凍結] |
| http_errors / http_successes / validation_errors / http_response_formatter | 10 / 10 / 8 / 8 | 各1 | [凍結](原則6) |
| **web/flask_helpers** | 10 | **0**(thinkx は独自の `flask_helper.py` 69行を別途持つ) | **[改修]** |
| **web/session** | 8+2 | **0** | **[改修]** |
| dateutils | 3(`timestamp_to_time_ago_text` のみ) | 0 | [凍結+追加] |
| mongomodel / cipher / discord | 5 / 2 / 0 | 0 / 0 / 1 | 対象外(スモークのみ) |
| **web/api_response_v1 + errors_v1** | **0**(壊れた import 1件のみ→F-1) | **0** | 判断(L-5) |
| **web/[DEPRECATE]api_errors.py(705行)** | **0** | **0** | 削除(L-4) |

前提の検証(v1.1 で完了): kazukiotsukacom を実測した結果、[改修]面(flask_helpers / session / api_response_v1 / errors_v1 / api_errors)の消費は**ゼロ**(消費プロファイルは thinkx と同型: logger / color / validator / locale / language / フォーマット族 / mail)。truetech は独立リポジトリではなく thinkx 内(`web-server/` の truetechjapan 系アセット)であることも確認済み。**したがって[改修]面の消費者が quantz-web のみであることは、全消費者について実測で確定している。**

### 1.3 レスポンス層の二系統並立(実測)

- **現役契約 = pydantic フォーマット族**: `http_response_formatter.py`(90行: SuccessFormat / APIErrorFormat / ValidationErrorFormat / ValidationErrorsFormat)+ 具象クラス群(`http_errors.py` 57行 / `http_successes.py` 22行 / `validation_errors.py` 41行)。quantz-web・thinkx・PROTOCOL.md §5 の全てがこれを消費する。
- **死んだ並立系 = 例外族**: `api_response_v1.py`(368行)+ `errors_v1.py`(131行)。リポジトリ横断で消費者ゼロ(唯一の消費未遂が F-1 の壊れた import)。`SuccessCode`/`ErrorCode` Enum が formatter 側と**二重定義**されている。
- **死荷重**: `[DEPRECATE]api_errors.py`(705行)。参照ゼロ。web/ 配下の最大ファイルとしてリポジトリを読む者(人間・AI)の in-context 事前分布を毎回汚染している。

### 1.4 構造的問題の中核: レイヤ逆転と import 時副作用(作者自身がマーク済み)

- `web/flask_helpers.py` L7–8:
  `from config import Config, check_config` / `from models.data.user import User, ...  # NEEDSFIX: don't depend on data.user`
  **共有ライブラリがホストアプリの config とドメインモデルに依存している。** さらに L262 付近に `# FIXME: to avoid dependence to User, move this to session.py or a new file`。つまりこれは設計思想の欠陥ではなく、**作者が認識済みで完遂されなかった移行**である。本計画がそれを完遂する。
- `web/session.py` L36 `from config import Config` / L178–183: **クラス定義時(=import 時)に** `redis.ConnectionPool(host=Config.REDIS_SESSION_HOST, ...)` を生成。import するだけでアプリ config が必須になり、テストからの分離が構造的に不可能。
- 帰結: `python -c "import libcommon.web.flask_helpers"` は素の環境で **ImportError で落ちる**。libcommon は「独立した軽量なライブラリ」という設計目標に、この2ファイルだけが反している。

### 1.5 既知の潜在バグ・問題(**報告と修正の別を各項目に明記**)

| # | 事実 | 根拠 | 扱い |
|---|---|---|---|
| F-1 | quantz-web `models/data/material_v1.py` L9 が存在しないモジュール `libcommon.response.errors` を import(実行されれば ImportError) | grep 実測 | Q-3 で修正 |
| F-2 | `Session.user_id() -> int` / `start(cls, user_id: int)` の型ヒントが嘘(実体は MongoDB ObjectId の str。コーディングガイド自身が `str(user.id)` を指示) | session.py L186, L204 | L-7 で修正([改修]面) |
| F-3 | `dateutils` の公開関数名が `iso8061`(正: ISO **8601**)。typo が公開 API に固定されている | dateutils.py L50, L71 | L-6 で正名追加+旧名エイリアス維持 |
| F-4 | `flask_helpers.py` L45 `AVAILABLE_LANGS` がハードコード(`# TODO: use Config.AVAILABLE_LANGS` と作者マーク済み) | 同行 | L-1 の初期化 API に吸収 |
| F-5 | `google_oauth_token_check` 内で `g.setdefault('errors',[])` と `g.errors.append` の二流儀が混在し、except 経路では `g.errors` 未初期化だと AttributeError になりうる | flask_helpers.py L283以降 | L-2 特性テストで現挙動を凍結、修正は L-1 改修に内包 |
| F-6 | `from libcommon.color import *` のスター import が quantz-web に21箇所+libcommon 内部にも存在 | grep 実測 | 記録のみ(findings)。一斉修正は範囲外 |
| F-7 | thinkx が libcommon とは別に独自 `flask_helper.py`(69行)を保持(分岐した規約) | リポジトリ実測 | 記録のみ。統合判断は次期 |
| F-8 | `datetime_to_iso8061` の引数デフォルトが naive な `datetime.now()`(サーバのローカル時刻・tzinfo なし)。地域の異なるサーバで実行すると出力が変わり、「多地域分散でもタイムゾーン整合」という設計目標にこの1関数だけ違反。docstring も自己矛盾(本文は Asia/Tokyo と言い、シグネチャは pytz.utc、例は +09:00) | dateutils.py L66, L51–63 | L-5 で正名関数側のみ修正(旧名は挙動保存) |
| F-9 | `timestamp_to_time_ago_text`(quantz-web が消費する唯一の dateutils 関数)が `datetime.utcnow()` / `datetime.utcfromtimestamp()` を使用。両者は Python 3.12 で deprecated(将来削除予定) | dateutils.py L115–116 | L-5 で内部実装のみ置換(外部挙動はゴールデン不変で証明) |

### 1.6 テスト・検証の現状

libcommon: `tests/` に2ファイル(mongo 系のみ)。CI なし。lint なし。型検査なし。
quantz-web: テスト0件。`main.py` は import 時に MongoDB 接続・config 検査を行うため、そのままではテストプロセスで起動できない。
→ 両トラックとも、最初の仕事は**機械オラクルの建設**である(simplicity 計画と同型)。

### 1.7 auth プロトコルとの関係

本計画は auth を**実装しない**。ただし L-2 の契約テストに PROTOCOL.md §5 の錨(`APIErrorFormat` 出力形状)と §3 の外形(`code`/`message`)のスナップショットを含める。これにより、将来 auth と `auth_client` を実装するとき、libcommon 側の契約が既に機械固定されている状態を作る。

---

## 2. 安全網の構築(Track L 項目0)

### L-0a 前提検証: 未clone消費者の仮定チェック — **計画作成時に実測完了・実行者の作業なし**

kazukiotsukacom / truetech の検証は v1.1 改訂時に計画作成者が実施済み(§1.2 の結果を参照)。実行者はこの項目をスキップし、findings.md に「L-0a: 計画 v1.1 で検証済み(kazukiotsukacom 消費ゼロ / truetech は thinkx 内)」と1行転記するのみでよい。再確認したい場合の1コマンド(任意):
`grep -rn 'flask_helpers\|web.session' <kazukiotsukacom> --include='*.py' | grep -v libcommon`(期待: 0件)

### L-0b ブランチ・環境・findings 台帳

```bash
cd libcommon && git checkout -b refactor/plan-v1
python3 -m venv .venv && source .venv/bin/activate
pip install pytest==8.3.4 fakeredis==2.26.2 flask==3.1.0 pydantic==2.10.4 \
    msgpack==1.1.0 pytz==6.0 redis==5.2.1 ruff==0.9.2 pyright==1.1.391 mongomock==4.3.0
pip freeze > requirements-dev.txt
```
(バージョンは計画作成時の指定。インストール不能な場合は最も近い版に置換し findings に記録。)
- `findings.md` を新規作成し §1.5 の表 F-1〜F-7 を転記。
- **完了条件:** venv 内で `pytest --version` / `ruff --version` / `pyright --version` が成功。
- **コミット:** `chore: dev environment pin and findings ledger`

### L-0c アプリ骨格スタブ(現状の flask_helpers/session をテスト可能にする仮設足場)

§1.4 の通り、現状の flask_helpers / session はアプリ文脈なしで import できない。**改修前の挙動を凍結するため**、テスト専用の最小スタブを `tests/app_stub/` に作る:
- `tests/app_stub/config.py` — `Config` クラス(DEFAULT_LANG='en', BASIC_AUTH_USERNAME/PASSWORD, REDIS_SESSION_HOST='localhost' 等、check_config が要求する全キー)と `check_config(config, keys)` 関数。
- `tests/app_stub/models/data/user.py` — `User`(mongomock ベースの最小 MongoEngine 風 or `objects` を偽装したスタブ)、`UnauthorizedAccessError`、`UserNotFoundError`。
- `tests/conftest.py` — `sys.path.insert(0, 'tests/app_stub')` を **libcommon より先に**行い、`fakeredis` で `redis.ConnectionPool`/`StrictRedis` を monkeypatch してから `libcommon.web.session` を import するフィクスチャ。
- **このスタブは L-1 完了後に不要になり、L-1 の完了条件で縮退される**(仮設足場であることを README に明記)。
- **完了条件:** `pytest tests/ -k smoke_import` で `import libcommon.web.flask_helpers` と `import libcommon.web.session` が成功するテストが green。
- **コミット:** `test: app stub scaffold to put legacy-coupled modules under test`

### L-0d 特性テスト(現挙動の凍結。ゴールデンは初回実行の実測値)

方針は simplicity 計画 0-3 と同一: 期待値を推測で書かず、**一度実行した実際の値を記録して固定**。ゴールデンは `tests/golden/*.json`。

- **T-L1 フォーマット族の契約形状(原則6の錨)** — `SuccessFormat`・`APIErrorFormat`・`ValidationErrorsFormat` と、`http_errors.py`/`http_successes.py`/`validation_errors.py` の**全具象クラス**について、Flask テストアプリ内で `http_response()` を呼び、(JSON本文, HTTPステータス) を凍結。`APIErrorFormat` は `{field_name, code, message, reason}` の4キーが出ること(PROTOCOL.md §5 の土台)を明示アサート。
- **T-L2 デコレータ挙動** — Flask テストアプリに各デコレータ(`language_wrapper` / `content_type_check_json` / `required_fields_check` / `regex_check` / `format_check` / `length_check` / `required_query_params`)を付けたダミーハンドラを立て、正常系・異常系リクエストの応答(JSON, status)を凍結。**現在の正典的な積層順**(quantz-web `accounts.py` L315–322 の実例と同順)で1本、順序を意図的に崩した1本も凍結し、順序依存性を可視化する。
- **T-L3 Session(fakeredis)** — `Session.start(user_id)` 後の redis キー構造(`session:*` と `sessions:*` 逆引き)、`user_id()` の戻り、`clear()` 後の状態、`count()`、`get_user_id_from_session_id()` を凍結。cookie ヘッダの発行有無も応答から凍結。
- **T-L4 locale / language** — `Locale.get`(存在キー×2言語、欠損キー、locale_args 展開)、`to_json_string` の安定性、`Language.lang_label_map`。
- **T-L5 dateutils** — `datetime_to_iso8061`/`iso8061_to_datetime` の往復同一性、tz 引数、`expiration_datetime(after_hours)`、`timestamp_to_time_ago_text` の言語別出力(quantz-web が消費する唯一の関数)。
- **T-L6 validator / color / logger** — `Validator` 全 ValidationType の判定表、`color` の各関数が ANSI コードを含む文字列を返すこと、`Logger` が例外なく初期化できること。
- **完了条件:** `pytest` green(全T green)/ `tests/golden/` コミット済み。
- **コミット:** `test: characterization tests frozen for all consumed surfaces`

### L-0e 床: ruff + pyright

- `ruff.toml`: `select = ["F", "E9"]`(F821 未定義名を含む最小集合。スタイル系は入れない)。`pyrightconfig.json`: `"typeCheckingMode": "basic"`, `"include": ["libcommon"]`(まず web/ 以外)。
- **判断規則:** エラーは**修正せず** findings に記録し、`per-file-ignores` / `exclude` で明示的に黙らせて先へ進む(黙らせた事実も記録)。修正は各[改修]項目の中でのみ行う。
- **完了条件:** `ruff check .` / `pyright` とも exit 0。
- **コミット:** `chore: ruff and pyright gates (floor of verification layer)`

---

## 3. 作業項目リスト Track L(libcommon)

### L-1 [改修] 依存注入化: レイヤ逆転の解消(本計画の核心)

- **対象:** `web/flask_helpers.py` L7–8, L34–46, L264–290(session_helper)/ `web/session.py` L36, L172–183
- **問題:** §1.4 の通り。共有ライブラリがホストアプリの `config.py`・`models/data/user.py` に import 時依存し、単独 import・単独テスト・vendoring 後の独立検証が不可能。
- **変更(この形に確定する。実行者の再設計は不要):**
  1. `web/session.py`: クラス属性での ConnectionPool 生成(L178–183)を廃止し、明示初期化に置換:
     ```python
     class Session:
         _redis = None
         @classmethod
         def configure(cls, host: str, port: int, db: int) -> None:
             pool = redis.ConnectionPool(host=host, port=port, db=db)
             cls._redis = StrictRedis(connection_pool=pool)
         @classmethod
         def _r(cls):
             if cls._redis is None:
                 raise RuntimeError('Session.configure() must be called at app startup')
             return cls._redis
     ```
     `from config import Config` を削除。既存メソッド内の `cls.__redis` 参照を `cls._r()` に置換。`RedisSessionInterface.__init__` も host/port/db を引数で受ける形に変更(L74 付近の Pool 生成を引数化)。
  2. `web/flask_helpers.py`: `from config import ...` と `from models.data.user import ...` を削除(L7–8)。`session_helper` を**ファクトリに置換**:
     ```python
     def make_session_helper(user_loader, on_no_session, on_user_not_found):
         """user_loader: (user_id: str) -> user | None。アプリが自分の User を注入する。"""
         def session_helper(f):
             @wraps(f)
             def decorated(*args, **kwargs):
                 user_id = Session.user_id()
                 if not user_id:
                     raise on_no_session()
                 user = user_loader(user_id)
                 if user is None:
                     raise on_user_not_found()
                 return f(user=user, *args, **kwargs)
             return decorated
         return session_helper
     ```
     `requires_auth` の BASIC_AUTH 定数もモジュール定数から `configure_flask_helpers(default_lang, available_langs, basic_auth_username, basic_auth_password)` 初期化関数に吸収(F-4 の AVAILABLE_LANGS ハードコードも同時解消)。`check_config` 呼び出し(L34–39)は削除(検査責務はアプリ側 main.py に既にある)。
  3. F-5 の `g.errors` 二流儀は、この書き換えの中で `g.setdefault('errors', []).append(...)` に統一。
- **完了条件(順に全て):**
  1. **素の環境で** `python -c "import libcommon.web.flask_helpers, libcommon.web.session"` が exit 0(tests/app_stub を sys.path に入れずに実行)
  2. `grep -rn 'from config import\|from models' libcommon/web/` が 0 件
  3. T-L2/T-L3 の特性テストを新 API(`configure` / `make_session_helper`)経由に書き換えた上で、**ゴールデン(応答 JSON・redis キー構造)は不変**であること — 内部配線を変えても外部挙動が同一である証明
  4. `tests/app_stub/` から config.py / user.py を削除してもテストが green(足場の撤去)
  5. ruff / pyright exit 0
- **リスク/戻し方:** `git checkout -- libcommon/web/ tests/`。ゴールデン不一致=挙動を変えた、なので差分を精査。
- **依存:** L-0a〜L-0e
- **コミット:** `refactor: dependency injection for flask_helpers and session (removes app coupling)`

### L-2 [凍結] PROTOCOL.md 契約錨テスト

- **対象:** 新規 `tests/test_protocol_anchors.py`
- **変更:** T-L1 とは別に、PROTOCOL.md を仕様として明示参照するテストを置く: (a) `APIErrorFormat(...).response_json()` のキー集合が `{field_name, code, message, reason}` を含む、(b) 成功系の外形に `code`/`message` が必ず含まれる、(c) これらに `protocol_version` を**追加**しても既存キーが壊れない(dict 合成テスト)。ファイル冒頭コメントに「このテストが落ちる変更は PROTOCOL.md §6 違反」と明記。
- **完了条件:** pytest green。
- **依存:** L-1
- **コミット:** `test: protocol v1 shape anchors per PROTOCOL.md §5/§6`

### L-3 [削除] 死荷重の除去

- **対象:** `web/[DEPRECATE]api_errors.py`(705行)
- **問題:** 全リポジトリ横断で参照ゼロ(§1.3 実測)。
- **変更:** `git rm`。
- **完了条件:** `grep -rn 'api_errors' libcommon quantz-web thinkx --include='*.py' | grep -v Binary` が 0 件 / pytest・ruff・pyright green。
- **依存:** L-0d
- **コミット:** `chore: delete dead [DEPRECATE]api_errors.py (705 lines, zero consumers)`

### L-4 [判断] 例外族(api_response_v1 + errors_v1)の処遇

- **対象:** `web/api_response_v1.py`(368行)/ `web/errors_v1.py`(131行)
- **事実:** 消費者ゼロ(唯一の消費未遂は F-1 の壊れた import)。SuccessCode/ErrorCode Enum がフォーマット族と二重定義。
- **変更(既定の判断。オーナーが覆す場合のみ変更):** 両ファイルを `attic/` へ `git mv`(simplicity 計画 R-08 と同じ「削除でなく退避」方式)。`attic/README.md` に「例外 raise 型のレスポンス族。フォーマット族(現役契約)との統合判断は v2 設計時に行う」と記録。F-1 の修正(Q-3)は import 先を errors_v1 に直すのではなく、**material_v1.py 側をフォーマット族 or 標準例外に寄せる**(理由: 消費者1件のために499行+Enum二重定義を現役に留めるのは、二系統並立の再発)。
- **完了条件:** `attic/` へ移動済み / `grep -rn 'api_response_v1\|errors_v1' libcommon --include='*.py'` が attic 以外 0 件 / pytest green。
- **依存:** L-3、Q-3 と同一コミット群内で整合(Q-3 が先)。
- **コミット:** `chore: move unconsumed exception-family response modules to attic/`

### L-5 [凍結+追加] dateutils の正名化と時刻ドクトリンの完遂

- **対象:** `dateutils.py` L50–92, L114以降
- **設計目標(オーナー確認済み):** (a) サーバが複数地域に分散してもタイムゾーンが整合する、(b) datetime ⇄ ISO文字列 ⇄ epoch数値 をいつでも行き来できる、(c) 大元は共通化。現状は (a) に1関数の違反(F-8)、(b) に epoch 対の欠落、加えて deprecated API(F-9)がある。
- **変更:**
  1. 正名関数を新設: `datetime_to_iso8601(date=None, tz=pytz.utc)` / `iso8601_to_datetime(s)`。**新関数のデフォルトは aware UTC**(`date=None` のとき `datetime.now(pytz.utc)`)とし、F-8 を正名側で解消。旧名 `*8061*` は**現挙動のまま**残す(`# typo alias, kept for compatibility; naive-now default preserved` コメント付き。凍結面の挙動保存)。
  2. epoch 対を追加: `datetime_to_epoch(dt) -> float` / `epoch_to_datetime(ts) -> datetime`(戻りは aware UTC)。往復同一性テスト付き。これで (b) の三点相互変換が閉じる。
  3. `timestamp_to_time_ago_text` の内部実装から `utcnow()`/`utcfromtimestamp()` を除去し `datetime.now(timezone.utc)` / `datetime.fromtimestamp(ts, tz=timezone.utc)` に置換(F-9)。**外部挙動は T-L5 のゴールデン不変で証明**(差分計算は aware 同士でも同値)。
  4. モジュール docstring に UTC ドクトリンを明文化: 「保存・演算は常に aware UTC。表示時のみ対象タイムゾーンへ変換。naive datetime を新規コードで作らない」。
- **完了条件:** T-L5 拡張(正名往復・epoch往復・新デフォルトが UTC である直接アサート・旧名の現挙動凍結)で pytest green / 旧名を使う既存ゴールデン**不変** / `grep -n 'utcnow\|utcfromtimestamp' dateutils.py` 0件 / pyright exit 0。
- **リスク/戻し方:** `git checkout -- dateutils.py tests/`。ゴールデンが動いた場合は3の置換が同値でない証拠なので精査。
- **依存:** L-0d
- **コミット:** `feat: iso8601/epoch round-trip set with aware-UTC doctrine, deprecated APIs removed`

### L-6 [改修] Session の型と契約の精密化

- **対象:** `web/session.py` L186, L204 ほか
- **変更:** 型ヒントの嘘を修正(`user_id: int` → `str`、戻り `-> int` → `-> Optional[str]`)。`SESSION_PREFIX`/`SESSIONS_PREFIX`(逆引き)の意味論を docstring に明文化(コーディングガイドの記述をコードへ移す): 「`session:{sid}` → user_id / `sessions:{user_id}` → sid 集合(逆引き・多端末カウント用)」。auth プロトコル §2 手順6 の「ローカルセッション」がこのクラスであることをコメントで参照。
- **完了条件:** T-L3 ゴールデン不変 / pyright exit 0(型修正で新たなエラーが出た場合はそれ自体が発見なので findings 記録の上、正しい型に合わせる)。
- **依存:** L-1
- **コミット:** `fix: honest type hints and documented key semantics for Session`

### L-7 CLAUDE.md(契約の機械可読化)

- **対象:** 新規 `CLAUDE.md`(libcommon ルート)
- **変更:** 次の内容で作成(全文をこの通りに):

```markdown
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
```
- **完了条件:** ファイル存在・内容一致。
- **依存:** L-1〜L-6
- **コミット:** `docs: add CLAUDE.md contracts`

### L-8 タグ + bake スクリプト(vendoring 準備)

- **対象:** 新規 `scripts/bake.sh`、タグ
- **変更:** vendoring 議論で合意した手順をスクリプト化: `bake.sh <tag> <dest_dir>` = clone → タグ checkout → `.git` 除去 → `VERSION` ファイル生成(タグ + `git rev-parse` の tree hash)→ dest へ配置。全ゲート green を確認して `git tag v2.0.0`。
- **完了条件:** `bash scripts/bake.sh v2.0.0 /tmp/bake_test` で `/tmp/bake_test/libcommon/VERSION` が生成され、`python -c "import ..."` の単独 import が bake 先でも成功(原則7の最終証明)。
- **依存:** L-1〜L-7 全部
- **コミット:** `build: bake script and v2.0.0 tag for vendoring cutover`

---

## 4. 作業項目リスト Track Q(quantz-web = 参照実装)

> Track Q の目的は2つ: (1) L-1 の新初期化 API の**最初の消費者**として配線を実証する、(2) 将来の新規アプリが引用する**サンプルケース**としての品質に上げる。quantz-web は稼働していないため、オラクルは Q-1 で建てるテストのみである。

### Q-1 テストプロセスで起動可能にする

- **対象:** quantz-web `web-server/`(新規 `tests/` と `config_test.py`)
- **問題:** `main.py` が import 時に MongoDB 接続・config 検査を行い、テストから import できない。
- **変更:** `tests/conftest.py` で mongomock(mongoengine の `connect(..., mongo_client_class=mongomock.MongoClient)`)と fakeredis を差し込み、`config_test.py`(必要キーを全て埋めたテスト用 Config)を環境変数 or sys.path 先頭差し込みで選択させ、`from main import app` が成功するフィクスチャを作る。**src の変更は config 選択の仕組みが無い場合の最小限(環境変数 `QUANTZ_CONFIG` 分岐の追加)のみ許す。**
- **完了条件:** `pytest tests/ -k test_app_imports` green。
- **依存:** L-0b(共通 venv 資材)
- **コミット:** `test: quantz-web importable under test config (mongomock/fakeredis)`

### Q-2 ルート総なめスモーク + API 3型スナップショット

- **変更:** (a) `app.url_map` を列挙し、全 GET ルートに Flask test client でアクセスして (ルール, ステータス) 表をゴールデン凍結(200/302/401 いずれも「現状」として記録)。(b) 代表 API 3本(成功 / 単体エラー / バリデーション errors 配列 — コーディングガイドの3型)のレスポンス JSON 形状を凍結。
- **完了条件:** pytest green / `tests/golden/route_sweep.json` コミット済み。**このスイートが以後の全変更と、AWS 移行 STEP2 の受け入れ試験を兼ねる。**
- **依存:** Q-1
- **コミット:** `test: route sweep and 3-type API contract snapshots`

### Q-3 壊れた import の修正(F-1)

- **対象:** `models/data/material_v1.py` L9
- **変更:** `libcommon.response.errors` からの import を削除し、当該例外の用法を確認の上、(a) 使用箇所が dead なら参照ごと削除、(b) 生きているなら標準例外 or フォーマット族での送出に書き換え(L-4 の既定判断と整合)。どちらだったかを findings に記録。
- **完了条件:** `grep -rn 'libcommon.response' quantz-web` 0件 / Q-2 スイート green。
- **依存:** Q-2(オラクル先行)
- **コミット:** `fix: remove import of nonexistent libcommon.response module`

### Q-4 L-1 追随(新初期化 API への配線)

- **変更:** `main.py`(または `init_flask_app.py`)起動部に `Session.configure(Config.REDIS_SESSION_HOST, ...)` / `configure_flask_helpers(...)` を追加。`session_helper` の import を `make_session_helper(user_loader=lambda uid: User.objects(id=uid).first(), on_no_session=UnauthorizedAccessError, on_user_not_found=UserNotFoundError)` で生成したものに置換(全10ファイル。機械的置換)。
- **完了条件:** Q-2 スイート green(ルート表・API形状とも**ゴールデン不変**。配線変更が挙動を変えていない証明)/ libcommon 側 grep(`from config import`)0件のまま。
- **依存:** L-1, Q-2
- **コミット:** `refactor: wire new libcommon initialization API (reference implementation)`

### Q-5 サンプルケース品質(新規実装が引用する型を1箇所ずつ実証)

各小項目は独立コミット。**全テンプレ・全ハンドラへの一斉展開はしない**(範囲爆発防止。展開は次期)。
- **Q-5a** デバッグ用メールアドレス(`accounts.py` L335 付近の `dev1@thinkxinc.com` 等)を `Config.DEBUG_USER_EMAILS` へ移動。
- **Q-5b** `/v1/xxx` と `/v1/<lang>/xxx` の二重 route 登録を一発で行うヘルパ `route_with_lang(blueprint, path, **options)` を新設し、**accounts.py の signup/signin の2箇所だけ**置換して型を実証(完了条件: ルート表ゴールデン不変)。
- **Q-5c** PAGE_DATA 単一注入規約: `signup.html` のスカラ個別注入(L7–13)を `const PAGE_DATA = {{ page_data | tojson }};` 1点に集約し、`signup.js` の参照を追随(**このテンプレ1枚のみ**)。完了条件: jsdom か手動 grep でなく、Q-2 の GET /signup が 200 のまま+`PAGE_DATA` キー存在のアサート追加。
- **依存:** Q-4
- **コミット:** 各 `refactor(sample): ...`

### Q-6 vendoring カットオーバー

- **変更:** vendoring 合意事項の実施: (1) `web-server/libcommon` submodule を解体(`git submodule deinit` → `.gitmodules` 編集)、(2) `bake.sh v2.0.0 web-server/` で焼き込み(VERSION 付き)、(3) `.claude/settings.json` に `"deny": ["Edit(web-server/libcommon/**)"]` を追加(無言フォーク防止)、(4) vectordb_server 側 libcommon も同様。
- **完了条件:** clone 直後(`git submodule update` なし)に Q-2 スイートが green / VERSION の tree hash が bake 元と一致。
- **依存:** L-8, Q-4
- **コミット:** `build: vendor libcommon v2.0.0, retire submodule`

> thinkx への展開: thinkx は[凍結]面しか消費しないため**追随作業ゼロ**。任意のタイミングで bake.sh により v2.0.0 を焼くだけ(本計画の範囲外の1コマンド)。

---

## 5. やらないことリスト

| 禁止事項 | 理由 |
|---|---|
| auth サービスの実装・`auth_client` の実装 | 別計画。本計画は契約の錨(L-2)まで |
| mongobase / redisbase / celery / mail / vector_database の改修 | 消費面の優先4領域(http/locale/datetime/session)外。スモーク import のみ |
| スター import(F-6)の一斉修正、thinkx 独自 flask_helper(F-7)の統合 | 範囲爆発。findings 記録のみ |
| PAGE_DATA・route_with_lang の全面展開 | Q-5 で型を1箇所実証するに留める。展開は次期計画 |
| simplicity 計画との混線(quantz-web 内の JS/simplicity submodule への変更) | simplicity 計画 v1.2 の管轄。Q-5c は HTML テンプレと app JS のみ触る |
| フォーマット族の外形変更(キー削除・改名・型変更) | 原則6(PROTOCOL.md §6)違反 |
| Python バージョン昇格・依存の無断アップグレード | 原則5 |
| config.py の pydantic-settings 化・yaml 化などの設定機構の作り替え | 設計論として次期候補(オーナー判断待ち)。本計画では L-1 のプリミティブ引数注入までとし、実行者が善意で設定層を再設計しない |
| 「ついで」のバグ修正(findings 記録で代替) | 各項目の完了条件が検証不能になる |

## 6. 発見事項の報告ルール

simplicity 計画 §5 と同一: 修正せず `findings.md` に「ファイル:行 / 事実 / 発見項目ID」で1行追記。解釈を書かない。

## 7. トレース検証(作成者による事前検証の記録)

- L-0c の足場 → L-0d の凍結 → L-1 の改修 → 足場撤去、という順序により、「テストが無い状態で改修する」瞬間が存在しない(改修前に必ずゴールデンが存在する)。
- L-1 の完了条件3「ゴールデン不変」が成立するのは、依存注入が**配線の変更であって挙動の変更ではない**ため。ゴールデンが動いた場合は挙動を変えており、設計通りでない。
- L-4(例外族の attic 退避)は Q-3(壊れた import の解消)の後でなければ grep 完了条件が満たせない。依存に明記済み。
- Q-4 は L-1 の API を使うため L-1 完了が前提。Q-2 のゴールデンは Q-4 の前に凍結されている(配線変更の不変性を証明する順序)。
- Q-6(vendoring)は L-8(bake.sh + v2.0.0)と Q-4(新 API 追随)の両方の後。焼き込むのは追随済みコードが依存する版そのもの。
- 等級表(§1.2)の前提は v1.1 時点で全消費者(quantz-web / thinkx / kazukiotsukacom / truetech=thinkx内)について実測確定済み。実行時の再検証は不要(L-0a は転記のみ)。
- L-5 の3(deprecated API 置換)は[凍結]面への内部変更だが、完了条件「ゴールデン不変」により外部挙動の同値性が機械証明される — L-1 と同じ「配線は変えるが挙動は変えない」型。

## 8. 実行者への指示文(このままコピペして渡すこと)

```
あなたは libcommon と quantz-web のリファクタリング実行者です。
両リポジトリと本計画書(LIBCOMMON_PLAN.md)、PROTOCOL.md を渡します。以下を厳守してください。

1. まず「大原則」「§1 現状理解」「§5 やらないことリスト」を読む。
2. L-0b から始め(L-0a は検証済み・findings への転記のみ)、L-0b〜L-0e → L-1 → L-2 → L-3 → Q-1 → Q-2 → Q-3 → L-4 → L-5 → L-6
   → L-7 → L-8 → Q-4 → Q-5a → Q-5b → Q-5c → Q-6 の順に1項目ずつ実施する。
   順序の入替・スキップ・並行作業は禁止。
3. 1項目 = 1コミット。指定のコミットメッセージを使う。
4. 各項目の「完了条件」を全てコマンドで確認してからコミット。満たせない場合は
   「戻し方」で破棄し、試行と失敗の内容を報告して停止する。推測で進まない。
5. 変更等級を守る: [凍結] 面はゴールデン不変が絶対条件。[改修] 面も、完了条件に
   「ゴールデン不変」とある場合は外部挙動を変えてはならない。
6. 計画外の変更はしない。発見は findings.md に記録するだけにする(§6 の形式)。
7. 全項目完了後、全ゲート(pytest / ruff / pyright、両リポジトリ)の exit code、
   v2.0.0 の tree hash、findings.md の全内容を報告する。
```
