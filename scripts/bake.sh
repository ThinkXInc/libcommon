#!/usr/bin/env bash
#
# scripts/bake.sh — vendoring bake(L-8)
#
# Usage: bake.sh <tag> <dest_dir>
#   このリポジトリを <tag> で clone → .git 除去 → VERSION(tag + tree sha256)生成 →
#   <dest_dir>/libcommon へ配置する。
#
# tree sha256 は __pycache__ / *.pyc を必ず除外して算出する(import・テスト実行で生成される
# 非追跡物であり、含めると再照合が偽陽性 mismatch になる。計画 v1.8 / D-21)。
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "usage: bake.sh <tag> <dest_dir>" >&2
  exit 2
fi

TAG="$1"
DEST="$2"
LIBNAME="libcommon"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # libcommon リポジトリ root(scripts/ の親)
TARGET="$DEST/$LIBNAME"

mkdir -p "$DEST"
rm -rf "$TARGET"                                         # 再実行のため dest 配下のみ掃除

git clone --quiet "$SRC" "$TARGET"
git -C "$TARGET" checkout --quiet "$TAG"
rm -rf "$TARGET/.git"                                    # git 履歴を除去(vendoring)

# 開発専用物を焼き込みツリーから除外(P3-L8)。根拠: (a) attic の死コード等を全消費者に
# 再配布しない、(b) vendored 配下の CLAUDE.md は消費者リポジトリで作業する将来セッションの
# in-context を汚染する(ネスト読込)。VERSION は下で生成するため残る。
for _dev in tests tutorials attic scripts \
            refactor_plan.md findings.md CLAUDE.md CHANGELOG.md ruff.toml pyrightconfig.json; do
  rm -rf "${TARGET:?}/${_dev}"
done

# tree sha256(__pycache__ / *.pyc 除外)。ファイル毎ハッシュを sort して単一ハッシュに畳む。
# 算出は上記除外後のツリーに対して行う(消費者間 byte 同一性の再現条件を維持)。
TREE_SHA="$(cd "$TARGET" && find . -type f \
  -not -path '*/__pycache__/*' -not -name '*.pyc' \
  | LC_ALL=C sort | xargs shasum -a 256 | shasum -a 256 | cut -d' ' -f1)"

printf 'version: %s\ntree_sha256: %s\n' "$TAG" "$TREE_SHA" > "$TARGET/VERSION"

echo "baked ${LIBNAME}@${TAG} -> ${TARGET}"
echo "tree_sha256: ${TREE_SHA}"
