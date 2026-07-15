# Phase 3 バグ修正計画書 v1.1

対象: libcommon + quantz-web + simplicity(+ 再配布先: thinkx / kazukiotsukacom / auth)
作成日: 2026-07-07(v1.1 同日改訂)
v1.1 の変更点: P3-L8 に bake.sh の焼き込み範囲の痩身を追加(Phase 4b の実測観察を反映。
v2.1.0 の全消費者再焼きと同時に行うことで追加コストゼロ)。他の項目に変更なし。 / 正本はこのファイル1箇所(`libcommon/bugfix_plan.md`)。複製を置かない。
入力: simplicity `findings.md`(refactor/2026)+ libcommon `findings.md`(2026refactor)の全項目。
本計画の全行番号・コード引用は、両ブランチの現行 HEAD に対して計画作成者が実測突合済み。

---

## 大原則(実行者は最初にこれを読むこと)

1. **本計画は挙動変更計画である。** Phase 1・2 の「挙動保存」と逆であることを自覚せよ。
   各修正項目の型は Red → Fix → Green:
   (a) 現在のバグ挙動は Phase 1/2 の特性テストが**既に凍結している**(これが Red の証拠)。
   (b) 修正を適用する。
   (c) **意図した新挙動を新ゴールデン/新テストとして固定**する(これが Green)。
   更新してよいゴールデンは**各項目が名指しするもののみ**。lint ベースライン・route golden の
   diff が名指し分と正確に一致することを毎回確認する。想定外の差分=挙動を壊した=停止・報告。
2. **仕分けは §1 で確定済み。実行者は再仕分けしない。** 「修正」以外(凍結/次期)に善意で
   踏み込まない。作業中の新発見は findings 追記+人間判断(従来どおり。D-21/D-22 継続)。
3. 1項目=1コミット+push。ブランチは libcommon / quantz-web は `2026refactor` 継続。
   **simplicity は `refactor/2026` の HEAD から新ブランチ `2026refactor` を作成**して作業する
   (D-14 の統一名へ合流。完遂ブランチ refactor/2026 とタグは不変=D-24)。
4. **前提: Phase 2.5(静的サイト)と Phase 4b(auth 追随)が完了していること**(P3-0 で機械確認)。
   libcommon の修正は v2.1.0 として全消費先へ再配布する(Track R)ため、消費先が
   v2.0.0 で安定している状態から始める。
5. 依存は既存の exact ピンのまま。新規追加はしない。
6. Security exception(D-22)・パス明示(D-21)・完了条件 green で自動コミット+push、
   設計判断・想定外ゴールデン差分・Security は停止——Phase 2 後半と同じ運転規則を継続。

---

## 1. 仕分け表(findings 全項目。この表が確定判断であり再仕分け禁止)

### 1.1 修正する(→ §3 の作業項目)

| findings | 内容 | 項目 |
|---|---|---|
| N-6 | session.py L89 `timedelta(days=self.expiration_time_sec)` — 秒設定値を日に誤用(3600秒設定→3600日セッション) | P3-L1 |
| N-7 | `Session.start` が `session:{sid}` を書かず、`count()` が start 直後に常に 0 | P3-L2 |
| N-5 | flask_helpers の NameError 群(現行 L167 `handle_query_param_errors` 未定義 / L208 `MinLengthNotReachedErrorFormat` 未 import / L295–314 `ErrorCode` 未 import)— エラー経路が NameError で自壊 | P3-L3 |
| N-8 | dateutils `iso8061_to_datetime` の except 経路が未定義 `InvalidISOFormatError` を参照(不正入力→NameError) | P3-L4 |
| N-2 | http_response_formatter.py L54, L56 の pydantic 非推奨 `Field(example=)` | P3-L5 |
| N-3 | 死テスト2ファイル(tests/mongobase_test.py, tests/modelbase_test.py — 不在モジュール import で収集不能) | P3-L6 |
| Q-3派生 | libcommon 原本 `celery.py` の非実在モジュール `libcommon.response.*` import 疑い | P3-L7 |
| N-14 | quantz accounts.py L323 `users_create` が検証前に `request.json["email"]` 直接アクセス(空 json→KeyError→500。本来は 400 バリデーション) | P3-Q1 |
| N-13 | quantz `mails/send_mail.py` が **import 時に SES 実メール2通送信**(本番 creds で起動のたび送信+boto3 リトライで import ハング) | P3-Q2 |
| F-7 | simplicity controller L245 `Browswer` タイポ(hashchange のたび ReferenceError) | P3-S1 |
| T-06発見 | validator: `postal_code_format` の case 欠落(検証が全入力で無効)/ `_validateMaxLength` の null ガード欠落 / passwordFormat の到達不能重複行 | P3-S2 |
| F-9 | エラー経路の自壊3箇所(loading_base L21 ほか — スコープに無い `parentId` をメッセージが参照。実在するのは `$parent`) | P3-S3 |
| F-10 | file_upload_view: setter 引数 `showingstate` を `switch (state)` とタイポ(L295, L313)+ `currentCell` 未定義3箇所(L528–531) | P3-S4 |
| F-5(限定) | 実害スコープのみ: window/document への addEventListener 8箇所と setInterval 2箇所(effects.js L47 / **file_upload_view.js L484 はローカル変数握りで解放経路なし=確実な漏れ**)の解放監査と修正 | P3-S5 |
| F-8 | 非行頭トップレベル宣言のインデント正規化(title.js L20 ほか) | P3-S6 |

### 1.2 仕様として凍結する(修正しない。根拠つき決定)

| findings | 決定と根拠 |
|---|---|
| N-4 | 旧名 `datetime_to_iso8061` の既定 tz 呼び出し AttributeError — **凍結**。L-5 の決定どおり正は新名 `datetime_to_iso8601`(aware UTC 既定)であり、旧名はバグ込み互換エイリアス。P3-L4 の中で docstring に deprecation 注記のみ追加(挙動不変) |
| F-4 | controller の `constructor.name == "Wrapper"` 文字列比較 — Wrapper は attic 済みで**恒久的に不成立のデッド分岐**。minify しない前提(D-1 の concat 恒久)を仕様とし凍結 |
| F-6 | `==`/`var`/スター import — lint 警告ベースライン(321件/42件)が仕様。一斉変換は挙動リスク(既決) |
| TextFieldConfig 不在 | TextField は Config クラスを持たない現仕様として凍結(T-07 縮退済み。新設は機能設計=次期) |
| E-15 | mongomock の "Special options not supported" 制約 — harness の既知限界として凍結。実 MongoDB(AWS STEP2)で解消見込み |
| 401×4 / 404×2 ルート | route_sweep の現状値が仕様(認証必須・不在の正しい応答) |

### 1.3 次期送り(理由つき。本計画で触れると停止条件違反)

| findings | 理由 |
|---|---|
| notCorresponding の TypeError | **消費ゼロを実測確認**(validator.js 外に参照なし)。未実装機能の実装は機能設計であり、先回りしない(D-9 の精神) |
| F-1 / F-2 / F-11 | PositionMap 一族(MapPointer 不在・Config パラメータ取り落とし・未定義変数)。機能を復活させるか廃止するかはオーナーの機能判断。「PositionMap 再生」として一括次期 |
| N-1 | locale.py の stdlib shadow — 根治はモジュールリネーム=全消費先の import 変更(破壊的)。E-9 の実行標準(console-script pytest)が回避策として制度化済み。monorepo/v3 判断と同時に |
| 6×500 ルート | TemplateNotFound 2件はデッドルート疑い(テンプレ追加=機能実装、ルート削除=機能判断)。データ経路4件は harness のダミー id 由来の可能性。いずれも機能判断が要るため次期(現状は route golden に 500 として凍結済み) |
| N-9〜N-12 | discord / mongobase / api_response_v1(attic 済み)— §5 対象外モジュールまたは退避済み |
| F-7 の L265 | メソッド名 `_updatePageIndexInBrowswerURL` の typo — 内部一貫しており無害(定義と呼び出しが同名)。改名は次期の美観 |
| F-7(libcommon) | thinkx 独自 flask_helper.py の統合 — 既決の次期 |
| Notification の TS 衝突 | クラス改名は消費側破壊。tsconfig exclude の現状維持 |

### 1.4 計画内で処理済み(Phase 1/2 が既に解決。作業なし・確認のみ)

libcommon F-1(Q-3)/ F-2(L-6)/ F-3・F-8・F-9(L-5)/ F-4・F-5(L-1)/ quantz デバッグメール(Q-5a)。

---

## 2. P3-0 前提ゲート(最初に実行)

- **完了条件(全て機械確認):**
  1. ROADMAP で Phase 2.5 / 4b が完了済み(人間がチェック済みであること。未完なら着手しない)
  2. libcommon(2026refactor): pytest 73+ / ruff / pyright すべて exit 0、タグ v2.0.0 存在
  3. quantz-web(2026refactor): pytest(route sweep 含む)green
  4. simplicity: `refactor/2026` HEAD で build(dist sha 台帳一致)・test・lint・typecheck green を確認後、
     `git checkout -b 2026refactor` を作成して push
  5. findings.md 両方の HEAD を読み、本計画 §1 に載っていない **N-15 以降の新規項目が存在しないこと**を
     確認(存在した場合は着手前に人間へ報告——§1 の仕分けに人間が追記してから開始する)
- **コミット:** simplicity のブランチ作成のみ。

---

## 3. 作業項目(実行順: L' → Q' → R → S。トレースは §6)

### Track L'(libcommon。全項目で pytest/ruff/pyright green がコミット条件)

**P3-L1 [最優先] セッション有効期限の単位修正**
- 対象: `web/session.py` L89 `return timedelta(days=self.expiration_time_sec)`
- 変更: `days=` → `seconds=`。
- Green: 新テスト — `RedisSessionInterface(..., expiration_time_sec=3600)` で fakeredis の
  セッションキー TTL が 3600±数秒であることを直接アサート。既存 T-L3 ゴールデンに期限が
  含まれる場合は該当エントリのみ更新(diff で名指し一致を確認)。
- コミット: `fix(session): expiration uses seconds, not days (N-6)`

**P3-L2 Session.start / count の整合**
- 対象: `web/session.py`(start L223–225 相当 / count の掃除条件)
- 変更(この設計に確定): `Session.start` が `session:{sid}` キーを **TTL 付きプレースホルダ**
  (save_session と同じキー形式・空値可)で書く。count の掃除ロジックは不変。
- Green: 特性テスト `session/after_start` のゴールデンを意図更新 — start 直後のキー集合に
  `session:{sid}` が加わり、`count()==1`。他のセッション系ゴールデンは不変。
- コミット: `fix(session): start writes session:{sid} so count reflects live sessions (N-7)`

**P3-L3 flask_helpers のエラー経路 NameError 群の修復**
- 対象: `web/flask_helpers.py` L167 / L208 / L295–314(現行 HEAD 実測)
- 変更(各修正の到達形を指定):
  1. L167 `handle_query_param_errors(errors, lang)` — 未定義。`required_fields_check` の異常系と
     **同型**(ValidationErrorsFormat 系で 400 を http_response)に揃えた実装をこの関数として
     ファイル内に定義する。新規のレスポンス外形は作らない(原則: フォーマット族の既存形)。
  2. L208 `MinLengthNotReachedErrorFormat` — `web/validation_errors.py` に実在するか確認し、
     実在すれば import 追加のみ。無ければ同ファイルの既存クラス群と同型で追加(外形は
     {field_name, code, message, reason}=追加のみで PROTOCOL.md §6 に適合)して import。
  3. L295–314 `ErrorCode` — `http_response_formatter` から import 追加。同ブロックに他の
     未定義名(旧 N-5 の `locale` 等)が残っていれば同時に解決(実在シンボルへの import /
     引数化のみ。新設計禁止)。
- Green: 特性テストの NameError 凍結分(`decorators/required_query_missing_nameerror` ほか、
  該当ゴールデンを**名指しで列挙してから**)を意図した正常エラー応答(JSON, status)に差し替え。
  差し替え対象以外のデコレータゴールデンは不変。ruff の per-file-ignore(flask_helpers)から
  不要になった無効化を削除して床を回復。
- コミット: `fix(flask_helpers): error paths return proper formats instead of NameError (N-5)`

**P3-L4 iso8061_to_datetime の例外経路修復 + 旧名 deprecation 注記**
- 対象: `dateutils.py`(except 経路 / 旧名2関数の docstring)
- 変更: `class InvalidISOFormatError(ValueError)` を dateutils に定義し、except 経路で raise。
  旧名 `*8061*` 2関数の docstring 冒頭に「Deprecated: use *8601* (N-4: 既定 tz 呼び出しは
  壊れたまま互換凍結)」を追記(コード挙動は N-4 凍結のまま不変)。
- Green: 新テスト — 不正入力で `InvalidISOFormatError` が上がる(ValueError としても捕捉可能)。
  既存の roundtrip / iso8061_default_tz(AttributeError 凍結)ゴールデンは**不変**。
- コミット: `fix(dateutils): raise InvalidISOFormatError on bad input instead of NameError (N-8)`

**P3-L5 pydantic 非推奨 example= の置換**
- 対象: `web/http_response_formatter.py` L54, L56
- 変更: `Field(..., example='x')` → `Field(..., json_schema_extra={'example': 'x'})`。
- Green: T-L1 / 契約錨テストの**ゴールデン不変**(外形同一の機械証明)+ pytest 実行時に
  PydanticDeprecatedSince20 警告が消えること。
- コミット: `chore(formats): replace deprecated Field(example=) (N-2)`

**P3-L6 死テストの削除**
- 対象: `tests/mongobase_test.py` / `tests/modelbase_test.py`(N-3)
- 変更: `git rm` 2ファイル+ruff/pyright の exclude から該当2エントリを削除(設定の掃除)。
- Green: pytest / ruff / pyright green。
- コミット: `chore(tests): remove legacy dead tests (N-3)`

**P3-L7 celery.py の壊れた import の確認と最小修復**
- 対象: `celery.py`(Q-3 派生記録: `libcommon.response.successes/errors`(非実在)import 疑い)
- 変更: まず実在確認。壊れた import が実在し、かつ当該シンボルの使用が dead(モジュール内
  未使用)なら import 行削除のみ。使用が live なら**停止して人間報告**(celery は §5 対象外
  モジュールであり、live 修復は設計判断)。
- Green: `python -c "import libcommon.celery"` が素の venv で成功(または停止報告)。
- コミット: `fix(celery): drop import of nonexistent module (dead)` (該当時のみ)

**P3-L8 v2.1.0 タグ + bake.sh の焼き込み範囲の痩身**
- 変更1(bake.sh。Phase 4b 実測の反映): 焼き込みツリーから開発専用物を除外する —
  `tests/` `tutorials/` `attic/` `scripts/` `refactor_plan.md` `findings.md` `CLAUDE.md`
  `CHANGELOG.md` `ruff.toml` `pyrightconfig.json`(`.git` 除去と `.pyc`/`__pycache__` 除外は既存)。
  `VERSION` は残す。根拠: (a) attic の死コードを全消費者に再配布しない、(b) **vendored 配下の
  CLAUDE.md は消費者リポジトリで作業する将来セッションの in-context を汚染する**(ネスト読込)。
  tree hash の算出も同じ除外後ツリーに対して行う(消費者間 byte 同一性の再現条件を維持)。
- 変更2: CHANGELOG.md(新規・本計画の挙動変更一覧を §1.1 の表から転記)を追加。
- 完了条件: 全ゲート green / `bake.sh v2.1.0 /tmp/bake_test` の出力に上記除外物が**存在しない**こと
  / 素の import が bake 先で成功 / `git tag v2.1.0` + push(タグも push)。
- Track R の受け入れ(各消費者スモーク green)が、痩身後ツリーでも挙動不変であることの機械証明を兼ねる。
- コミット: `build: slim bake tree and tag v2.1.0`

### Track Q'(quantz-web)

**P3-Q1 users_create の検証前アクセス修正**
- 対象: `web-server/accounts.py` L323(現行)`request.json["email"]`
- 変更: email への直接アクセスを required_fields_check **通過後**の参照に移す(最小: 当該行を
  デコレータ検証が保証した後の位置へ/または `request.json.get("email")` でデバッグ判定を安全化。
  is_debug 判定という用途に照らし `.get` が最小)。
- Green: 新テスト — 空 JSON POST が **400 バリデーション形状**(型3)を返す。route/API ゴールデンの
  該当エントリのみ意図更新(500→400)。他ルート不変。
- コミット: `fix(accounts): no pre-validation access to request.json (N-14)`

**P3-Q2 import 時の実メール送信の除去**
- 対象: `web-server/mails/send_mail.py`(N-13: モジュールレベルで SES 送信2通)
- 変更: モジュールレベルの送信コードを関数化し `if __name__ == "__main__":` 配下へ移動
  (手動テスト用途を保存)。import 副作用ゼロに。
- Green: 新テスト — `import mails.send_mail` で boto3 の send 系呼び出しが 0 回(mock スパイ)。
  Q-2 スイート green・route ゴールデン不変。
- コミット: `fix(mails): remove import-time email side effect (N-13)`

### Track R(v2.1.0 の再配布。全て機械的)

**P3-R1 quantz-web へ再 bake** — `bake.sh v2.1.0` を `web-server/` と `vectordb_server/` へ。
VERSION 更新(.pyc 除外照合)。完了条件: Q-2 スイート green(P3-Q1 で更新済みゴールデンに一致)。
**P3-R2 thinkx / kazukiotsukacom へ再 bake** — 各サイトの S トラックスモーク(ルートゴールデン)
不変で受け入れ。
**P3-R3 auth へ再 bake** — auth テスト一式+規約ゲート green で受け入れ。
- 各1コミット: `build: rebake libcommon v2.1.0`

### Track S(simplicity。独立トラック。全項目で build+test+lint+typecheck green がコミット条件)

**P3-S1 Browswer タイポ修正**
- 対象: `src/view_controllers/input_page_view_controller.js` L245(現行実測)
- 変更: `Browswer.getValueFromHash` → `Browser.getValueFromHash`(この1識別子のみ。L265 の
  メソッド名は §1.3 のとおり触らない)。
- Green: ESLint ベースラインから該当1エントリのみ削除(lint_gate の diff が1件一致)。
  dist diff 1行。`evalInPage` で `typeof Browser.getValueFromHash === 'function'` は既存担保。
- コミット: `fix(controller): Browswer -> Browser typo (F-7)`

**P3-S2 Validator 3修正**
- 対象: `src/helpers/validator.js`(postal case / _validateMaxLength / passwordFormat 重複行)
- 変更: (1) switch に `postal_code_format` の case を telFormat の case と**同型**で追加
  (RegexType に郵便番号の定義が実在することを確認して配線。無ければ停止・報告=正規表現の
  新設は仕様判断)。(2) `_validateMaxLength` に null ガード — `_validateMinLength` の null の
  扱いを確認し**同型**に揃える。(3) passwordFormat の到達不能な2行目 `return this.errorMessage;`
  を削除。notCorresponding には触れない(§1.3)。
- Green: T-06 ゴールデンの該当エントリのみ意図更新(postal 正/誤入力・maxLength null)。
  他のバリデータエントリ不変。
- コミット: `fix(validator): wire postal_code_format, null-guard maxLength, drop dead line`

**P3-S3 エラー経路の自壊修正(F-9)**
- 対象: `loading_base.js` L21 / `gradient_loading_bar.js` L63 / `gradient_view_loader.js` L101
- 変更: console.error のメッセージから**スコープに実在しない変数を除去**し、実在する変数
  (loading_base では `$parent`)のみ、または固定文言に。エラー分岐の構造は不変。
- Green: ESLint ベースラインから該当3エントリのみ削除。dist diff は当該3行のみ。
- コミット: `fix(loading): error messages no longer reference out-of-scope vars (F-9)`

**P3-S4 file_upload_view の未定義変数修正(F-10)**
- 対象: `src/view_components/file_upload_view.js` L295, L313(`switch (state)` — setter の実引数は
  `showingstate`)、L528–531(`currentCell`)
- 変更: `switch (state)` → `switch (showingstate)`(L313 も同型のセッター引数へ)。`currentCell`
  3箇所はスコープ内の実在変数へ(周辺コードで実体を確認してから。候補が一意でなければ停止・報告)。
- Green: ESLint ベースラインから該当エントリのみ削除。dist diff 当該行のみ。
- コミット: `fix(file_upload_view): use in-scope variables (F-10)`

**P3-S5 リスナー/タイマー解放の限定監査(F-5 実害スコープ)**
- 対象: window/document への addEventListener 8箇所(grep 実測)+ setInterval 2箇所
  (`effects.js` L47 `flashIntervalId` / `file_upload_view.js` L484 `var identity = setInterval(scene, 50)`)
- 変更: 各箇所を列挙し、**解放経路(clear / removeEventListener / 対応する teardown)の無いもの**
  にのみ解放を追加。file_upload_view L484 はローカル変数握りで確実な漏れ — アニメーション完了
  条件で `clearInterval(identity)` する形へ(scene 内の終了分岐を確認して配線)。
  要素上のリスナーは対象外(要素の破棄とともに GC されるため。根拠として明記)。
- Green: 修正箇所ごとに、可能なものは jsdom テストで clear 呼び出しをスパイ検証。テスト不能な
  箇所は findings に「修正済み・手動根拠」を記録。全ゲート green。
- コミット: `fix: release window/document listeners and orphan intervals (F-5 scoped)`

**P3-S6 非行頭トップレベル宣言の正規化(F-8)**
- 対象: `title.js` L20 ほか(`grep -rn '^ [a-z]* *class ' src` 相当で全列挙)
- 変更: 行頭へのインデント除去のみ(空白差分)。
- Green: dist diff が空白のみ / 全ゲート green / gen_globals の出力不変。
- コミット: `style: normalize top-level declarations to column 0 (F-8)`

---

## 4. やらないことリスト

| 禁止 | 理由 |
|---|---|
| §1.2(凍結)・§1.3(次期)の全項目への着手 | 仕分けは確定済み(大原則2)。特に notCorresponding の実装・PositionMap 再生・6×500 ルートの機能修正・locale リネーム |
| 名指しされていないゴールデンの更新 | 挙動を壊した証拠と見なす(大原則1) |
| フォーマット族の既存キーの変更 | PROTOCOL.md §6(追加のみ)。P3-L3 の新フォーマット追加は「追加」なので適合 |
| 依存の追加・昇格 | 原則5 |
| simplicity の refactor/2026 ブランチ・タグへの変更 | D-24 / D-14 例外 |
| 「ついで」のリファクタリング・命名改善 | 本計画は §1.1 の修正のみ |

## 5. 発見事項

従来どおり findings.md へ(§6 形式・Security exception 即停止)。本計画で生じた新発見は
**修正せず**記録(次のバグ修正サイクルの入力)。

## 6. トレース検証(作成者による事前検証)

- 順序 L' → Q' → R → S の根拠: R(再配布)は L' 完了(v2.1.0)が前提。Q'(quantz の app 修正)は
  R1 と独立だが、P3-Q1 が route ゴールデンを更新するため **R1 の受け入れ(ゴールデン一致)より
  先に**確定している必要がある → Q' を R より前に置く。S(simplicity)は libcommon と完全独立
  のため最後(他トラックの失敗の影響を受けない位置)。
- P3-L1 と P3-L2 は同じ session.py を触るが独立の行(L89 / L223–225)で、ゴールデン更新対象も
  交差しない(TTL 値 / キー集合)。
- P3-L3 の per-file-ignore 削除は、修正後に F821 が再発しないことを ruff が機械保証する
  (床の回復。E-10 の既知限界=スター import ファイルの F405 化は本計画の範囲外のまま)。
- P3-Q1 のゴールデン更新(500→400)は P3-R1 の受け入れ条件に織り込み済み(更新後ゴールデンに一致)。
- 全項目の Green が Phase 1/2 で建てた床(pytest/ruff/pyright/ESLint ベースライン/route golden/
  dist 台帳)の上で機械判定される。人間の動作チェックは 0。
- §1 の網羅性: simplicity findings(F-1〜F-12+T-06/T-07 発見+R-04/R-05 記録)、libcommon
  findings(F-1〜F-9+N-1〜N-14+E-1〜E-16)の全項目が §1.1〜§1.4 のいずれかに現れることを
  作成時に照合済み。N-15 以降の追記有無は P3-0 が検査する。

## 7. 実行者への指示文(このままコピペ)

```
Phase 3(バグ修正計画)を開始する。規範: libcommon/bugfix_plan.md v1.0。
対象: libcommon + quantz-web + simplicity + 再配布先3系。
これは挙動変更計画である。大原則1(Red→Fix→Green、名指しゴールデンのみ更新)と
大原則2(§1 の仕分けを再仕分けしない)を最初に読み、P3-0 から §3 の実行順どおりに。
1項目=1コミット+push。完了条件 green で自動進行、以下は停止:
名指し外のゴールデン差分 / §1.2・§1.3 への着手が必要になった場合 / 修正の到達形が
計画の指定から外れる場合 / Security exception。
全完了後: 各リポジトリの全ゲート exit code、v2.1.0 の tree hash、更新した全ゴールデンの
一覧、findings 追記分を報告せよ。
```