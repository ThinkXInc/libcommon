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

# tree sha256(__pycache__ / *.pyc 除外)。ファイル毎ハッシュを sort して単一ハッシュに畳む。
TREE_SHA="$(cd "$TARGET" && find . -type f \
  -not -path '*/__pycache__/*' -not -name '*.pyc' \
  | LC_ALL=C sort | xargs shasum -a 256 | shasum -a 256 | cut -d' ' -f1)"

printf 'version: %s\ntree_sha256: %s\n' "$TAG" "$TREE_SHA" > "$TARGET/VERSION"

echo "baked ${LIBNAME}@${TAG} -> ${TARGET}"
echo "tree_sha256: ${TREE_SHA}"
