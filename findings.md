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
