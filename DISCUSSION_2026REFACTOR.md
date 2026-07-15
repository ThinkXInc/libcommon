# libcommon 2026refactor に関する討議記録(QA)

日付: 2026-07-15
文脈: M トラック(monorepo 取り込み)M-0 の最中、オーナーが libcommon リファクタの妥当性を
確認するために発した一連の質問と、実コードに基づく回答を記録する。実測は下記コミットに対して
行った。これは討議の記録であり規範ではない(規範は `refactor_plan.md` / `CLAUDE.md`)。

- 討議時点の 2026refactor HEAD: `d486f9e`
- QA が対象にした焼き込み版: libcommon `v2.1.0`(コミット `8168044`)
- 焼き込み先(6箇所)の `VERSION.tree_sha256`: 全一致 `ab534a69ddb3ade5634253bc0d8b0c1bd6ea4e215a856b4320eb9b60b5495b04`

---

## サマリー

- libcommon のリファクタ済み版(v2.1.0)は **6つの vendoring 先すべてに無加工で焼き込み済み**で、
  tree hash が全一致している(= 全消費者が同一実体を持つことが機械的に保証)。
- ルート適用面の**デコレーター群のインターフェース(名前・引数・積層順)は保存**されている。
  消費者 `main.py` がほぼ不変なのはこのため。変わったのは起動足場の2点のみ:
  (a) 起動時に `Session.configure()` / `configure_flask_helpers()` を1回呼ぶ、
  (b) `session_helper` だけファクトリ経由に変わった。
- `session_helper` だけ大きく変わったのは、それが **L-1(依存注入化・レイヤ逆転解消)の核心**
  だったから。他デコレーターは Config 定数を注入に移すだけで済んだが、session_helper は
  ホストアプリの User モデルへの構造的な import 時依存を抱えていた。
- 一方で **2件の実発見**(vector_database がテスト網の外 / DEFAULT_LANG の fallback 不整合)を
  検出。いずれも M(コピー)ではなく **libcommon Phase 3 の管轄**。

---

## 前提事実(実測)

### 焼き込み先と一致

全6箇所に libcommon 全体(`web/` + 各ユーティリティ + `vector_database/`)が焼き込まれ、
`VERSION.tree_sha256` は全一致(`ab534a69...`)。

- `thinkx/web-server/libcommon`
- `kazukiotsukacom/web-server/libcommon`
- `auth/web-server/libcommon`
- `quantz-web/web-server/libcommon`
- `quantz-web/vectordb_server/libcommon`
- `quantz-web/web-server/llm/libcommon`

### リファクタの完了状態

- Phase 1/2(挙動保存リファクタ)は完了・タグ `v2.0.0` / `v2.1.0`。
- 2026refactor HEAD は `v2.1.0` の1コミット先(findings 記録 `P3-R1 ... stop for review`)。
- Phase 3(バグ修正 = `bugfix_plan.md`)は進行中。

---

## QA

### Q1. リファクタ済み libcommon が quantz-web / thinkx 等に焼かれているのか

**A. YES。** v2.1.0(`8168044`)が上記6箇所に無加工コピー、tree hash 全一致。焼き込みは
libcommon 全体を含む。

### Q2. vector_database(最も挙動が繊細)はテストされているのか

**A. 自動テストの網には入っていない**(懸念は妥当)。

- `vector_database/` は焼き込みに含まれる(全消費者に存在)。
- しかし **pytest 特性テスト(`tests/`)に vector_database のテストは無い**。特性テストが
  凍結しているのは `dateutils / decorators / formats / locale・language / session /
  validator・color・logger` のみ(`tests/golden/` 参照)。
- `vector_database/test_vector_database.py` は存在するが**スクリプト型の手動統合テスト**で、
  モジュールレベルで実副作用を実行し、`device='cuda:2'`(GPU 必須)/ `host='localhost',
  port=6333`(稼働中 Qdrant 必須)/ `all-mpnet-base-v2` DL を要求する。`conftest`/CI からは
  呼ばれない(`tests/` からの参照ゼロを grep 実測)。
- libcommon リファクタ(L-1〜L-8 / N-x)の作業項目に vector_database は**含まれない**。
  コードは変わっておらず、焼き込みで運ばれただけ。
- → 「最も繊細なのに自動テストで守られていない」は正しい。**発見#1** として記録。

### Q3. main.py がほぼ不変 = デコレーター IF はほぼ不変か

**A. YES、ほぼ不変。**

ルート適用面のデコレーター群は名前・引数・積層順とも保存(`language_wrapper /
requires_auth / content_type_check_json / required_fields_check / required_query_params /
format_check / length_check / regex_check / google_oauth_token_check / validate_request`)。
CLAUDE.md の正典積層順も不変。

変わったのは起動足場だけで2点:

- (a) 起動時に1回だけ注入呼び出しが増えた(`quantz-web/web-server/init_flask_app.py:17-21`):
  ```python
  Session.configure(Config.REDIS_SESSION_HOST, Config.REDIS_SESSION_PORT, Config.REDIS_SESSION_DB_NUMBER)
  configure_flask_helpers(Config.DEFAULT_LANG, Config.SUPPORTED_LANGS,
                          Config.BASIC_AUTH_USERNAME, Config.BASIC_AUTH_PASSWORD)
  ```
- (b) `session_helper` だけファクトリ経由に(Q4)。ルートに付ける `@session_helper` の見た目は
  不変で、生成箇所(`app_session.py`)が変わっただけ。

旧 `from config import Config` / `from models.data.user import ...` の libcommon→ホスト逆 import は
消え、値は上記注入で渡る。

### Q4. session_helper だけ大きく変わった理由を説明できるか

**A. これが L-1(本リファクタの核心)そのもの。**

- **旧**: `session_helper` は libcommon 内で `models.data.user`(ホストアプリのモデル)を
  **import 時に直接参照** → **レイヤ逆転**。libcommon の単独 import・単独テスト・vendoring 後の
  独立検証が不可能だった。
- **新**(`web/flask_helpers.py:277-299`): `make_session_helper(user_loader, on_no_session,
  on_user_not_found)` という**ファクトリ**。アプリが自分の User 取得関数と例外を注入する。
  libcommon 側は `user_id → user_loader(user_id) → f(user=user, ...)` と流すだけで、ホストの型を
  知らない。消費者は `app_session.py` で1回組み立て、各ルートは従来どおり `@session_helper`。
- **`Session` クラスも DI 化**(`web/session.py:180-189`): 旧はクラス属性で ConnectionPool を
  生成(import 時 Redis 前提)→ 新は `Session.configure(host, port, db)` を起動時に呼ぶ明示
  初期化。未 configure なら `_r()` が `RuntimeError`。
- Phase 3 のバグ修正が同居: expiration の days→**seconds** 修正(N-6)、`start()` が
  `session:{sid}` を TTL 付きプレースホルダで先行作成し `count()` が live を反映(N-7)。

→ 他デコレーターは「Config 定数 → configure_flask_helpers に移す」だけで済んだが、
session_helper だけはホスト User モデルへの構造的依存があったため、注入ファクトリという形の
変更が必要だった。だから「ここだけ大きく変わった」。

### Q5. global で DEFAULT_LANG 等をセットしている。Google 規約の禁じ手では?やむを得ないのか

**A. 意図的な割り切り。「やむを得ない」ではなく「今回のスコープでは据え置いた」。**

`web/flask_helpers.py:35-48` は module-global(`DEFAULT_LANG` 等)を `configure_flask_helpers()`
の `global` 文で1回セットする形。

- Google Python Style Guide 上、可変なモジュールグローバルは避けるべき、は事実。これは該当する。
- ただし今回の**リファクタの目的は「レイヤ逆転の解消」であって「global 撲滅」ではない**。
  「Config を import」→「起動時に module global へ1回注入」への移行は、テスト時に configure で
  差し替え可能になり import 時副作用が消える点で**旧来より改善**。
- 完全に消すなら、デコレーター群を `current_app.config` 参照に書き換える必要があり、それは積層・
  挙動に触れる別スコープの変更。→ **global 完全排除は次期候補**。

### Q6(+続き). DEFAULT_LANG のセット経路は二流あるのか。.env 未設定なら消費側が勝手にセットか

**A.(A) libcommon へ入る経路は1本。(B) DEFAULT_LANG は .env 由来ではなくハードコード。
(C) 本当の「二流れ」はデコレーター内 fallback にある(潜在バグ)。**
  global、の1本。configure 前は global は `None`。libcommon 側に「依存前に個別セット」の第2
  経路は無い。
- **(B)** 消費者 `config.py` は `load_dotenv()` で **secret 類**(`FLASK_APP_SECRET_KEY` 等)を
  読むが、`DEFAULT_LANG` は .env のキーではない:
  - `quantz-web/web-server/config.py:169` → `DEFAULT_LANG = 'en'`(ハードコード)、
    `SUPPORTED_LANGS`(:160)もハードコード
  - `auth/web-server/config.py:8-9` → `DEFAULT_LANG = 'en'` / `AVAILABLE_LANGS = ['en','ja']`
    (ハードコード)
  → 「.env にセットしていなければ消費側が勝手にセット」ではなく、**最初から .env 管轄外で
  消費者 Config が明示的に既定値 `'en'` を持つ**(実行時の暗黙フォールバックではない)。
- **(C)** libcommon デコレーターの fallback に不整合がある。多くは
  `kwargs.get('lang', DEFAULT_LANG)`(global 尊重)だが、**2箇所だけリテラル `'en'` を直書き**:
  - `required_query_params` … `web/flask_helpers.py:170` → `kwargs.get('lang', 'en')`
  - `format_check` … `web/flask_helpers.py:194` → `kwargs.get('lang', 'en')`
  現状 `DEFAULT_LANG='en'` なので露見しないが、将来 DEFAULT_LANG を 'ja' 等に変えると
  この2デコレーターだけ 'en' に分岐して不整合になる。→ **発見#2** として記録。

---

## 発見(findings 候補・libcommon Phase 3 管轄)

> 本セッションは M トラック(monorepo 取り込み)。1セッション=1計画の規律により、実行者は
> ここで libcommon コードに手を入れない。下記は正式には libcommon `findings.md` に転記して
> Phase 3 で扱う対象(オーナー判断)。

### 発見#1: vector_database が特性テスト網の外

`vector_database/` は焼き込みに含まれ全消費者に配布されているが、`tests/` の特性テストは
これを一切カバーしない。唯一の `vector_database/test_vector_database.py` は GPU(`cuda:2`)+
稼働 Qdrant(:6333)+ モデル DL を要求するスクリプト型手動テストで CI 非対象。最も繊細な
モジュールが自動テストで保護されていない。コード自体はリファクタで未変更。

### 発見#2: DEFAULT_LANG の fallback 不整合(`'en'` 直書き)

`web/flask_helpers.py:170`(`required_query_params`)と `:194`(`format_check`)が
`kwargs.get('lang', 'en')` とリテラル `'en'` を直書きしており、他デコレーターの
`kwargs.get('lang', DEFAULT_LANG)` と不整合。`DEFAULT_LANG != 'en'` の環境でこの2経路だけ
言語が 'en' に分岐する潜在バグ。

### 補足(発見でなく設計判断の記録): global 注入の割り切り

`configure_flask_helpers()` による module-global 注入は、レイヤ逆転解消を優先し global 撲滅を
次期に回した意図的トレードオフ(Q5)。この割り切りが `refactor_plan.md` / `findings.md` に
明記されているかは未確認 — 未記載なら記録推奨。

---

## 次アクション

- 上記 QA と発見の記録は本ファイルで完了。
- **発見#1 / #2 の `findings.md` 転記と対応は libcommon Phase 3 の別セッションで行う**
  (M セッションでは着手しない)。
- M トラックは M-0 の承認待ち → 承認後 M-1(器の作成)へ。