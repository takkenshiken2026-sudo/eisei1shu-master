#!/usr/bin/env bash
# GitHub Pages 用に公開ファイルだけを public_site/ に集約する。
# 事前に python3 tools/csv_to_eisei1_master.py と python3 tools/build_question_pages.py を実行済みであること。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/public_site"
rm -rf "$OUT"
mkdir -p "$OUT"
mkdir -p "$OUT/docs"
cd "$ROOT"
for f in \
  index.html \
  about.html \
  privacy-terms.html \
  site-pages.css \
  site-analytics.js \
  CNAME \
  robots.txt \
  sitemap.xml \
  .nojekyll \
  eisei1-master-data.js \
  eisei1-data-glossary.js \
  eisei1-data-original.js
do
  if [[ ! -e "$f" ]]; then
    echo "prepare_public_site.sh: 必須ファイルがありません: $f" >&2
    exit 1
  fi
  cp "$f" "$OUT/"
done
for f in docs/glossary-article-slugs.json docs/glossary-terms-checklist.csv docs/dai1shu-glossary-terms-master.csv; do
  if [[ ! -e "$f" ]]; then
    echo "prepare_public_site.sh: 必須ファイルがありません: $f" >&2
    exit 1
  fi
  cp "$f" "$OUT/docs/"
done
if [[ ! -d q ]]; then
  echo "prepare_public_site.sh: q/ がありません。先に python3 tools/build_question_pages.py を実行してください。" >&2
  exit 1
fi
cp -R q "$OUT/"
if [[ -d "$ROOT/articles" ]]; then
  cp -R "$ROOT/articles" "$OUT/articles"
else
  echo "prepare_public_site.sh: 警告: articles/ がありません（試験ガイドが公開されません）。" >&2
fi
if [[ -d "$ROOT/terms" ]]; then
  cp -R "$ROOT/terms" "$OUT/terms"
  python3 "$ROOT/tools/generate_terms_index_html.py" \
    --slug-json "$ROOT/docs/glossary-article-slugs.json" \
    --csv "$ROOT/docs/glossary-terms-checklist.csv" \
    --terms-dir "$OUT/terms" \
    --out "$OUT/terms/index.html" \
    --base "https://eisei1shu-master.jp"
  python3 "$ROOT/tools/generate_terms_sitemap.py" \
    --terms-dir "$OUT/terms" \
    --out "$OUT/sitemap-terms.xml" \
    --base "https://eisei1shu-master.jp"
fi
bash "$ROOT/tools/verify_supabase_url_in_html.sh" "$OUT/index.html"
n="$(find "$OUT" -type f | wc -l | tr -d ' ')"
echo "prepare_public_site.sh: $OUT に $n ファイルを配置しました。"
