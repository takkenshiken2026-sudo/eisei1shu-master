#!/usr/bin/env bash
# GitHub Actions 用: eisei1shu 生成パイプライン（greenfield 整理中は validate_csv を除外）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY="${PYTHON:-python3}"
if ! "$PY" -c "import yaml" 2>/dev/null; then
  "$PY" -m pip install --quiet pyyaml
fi
"$PY" tools/validate_guide_exam_facts.py --skip-greenfield-pending
"$PY" tools/apply_site_config.py
"$PY" tools/csv_to_exam_site_past_js.py
"$PY" tools/csv_to_exam_site_ichimondou_js.py
"$PY" tools/build_past_question_pages.py
"$PY" tools/build_practice_ichimon_pages.py
"$PY" tools/build_article_pages.py
"$PY" tools/build_guide_retire_redirects.py
"$PY" tools/build_glossary_pages.py
"$PY" tools/build_hub_retire_redirects.py
"$PY" tools/build_sitemap.py
"$PY" tools/inject_adsense_head.py
"$PY" tools/validate_guide_index_picks.py
"$PY" tools/validate_internal_links.py
"$PY" tools/validate_site_integration.py
bash tools/prepare_public_site.sh
