#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""glossary_terms.csv 本文に混入した <table class="seo-info-table"> を除去する。

ビルド側でも seo_section_body_html が表を処理しますが、重複テンプレ表と
エスケープ露出を防ぐため CSV 正本から削除します。

  python3 tools/strip_glossary_inline_html_tables.py --dry-run
  python3 tools/strip_glossary_inline_html_tables.py
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.seo_body_markup import strip_inline_seo_tables  # noqa: E402

GLOSSARY_CSV = ROOT / "data" / "glossary_terms.csv"

TEXT_COLS = (
    "definition",
    "term_detail_body",
    "explanation",
    "article_lead",
    "summary_body",
    "common_mistakes",
    "faq_1_answer",
    "faq_2_answer",
    "faq_3_answer",
    "faq_4_answer",
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not GLOSSARY_CSV.is_file():
        print(f"missing {GLOSSARY_CSV}", file=sys.stderr)
        return 1

    with GLOSSARY_CSV.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames or [])
        rows = list(reader)

    changed_cells = 0
    changed_rows = 0
    for row in rows:
        row_changed = False
        for col in TEXT_COLS:
            if col not in row:
                continue
            old = row.get(col) or ""
            if "<table" not in old.lower():
                continue
            new = strip_inline_seo_tables(old)
            if new != old:
                row[col] = new
                changed_cells += 1
                row_changed = True
        if row_changed:
            changed_rows += 1

    print(f"strip tables: {changed_cells} cell(s) in {changed_rows} row(s)")
    if args.dry_run:
        return 0

    if changed_cells:
        with GLOSSARY_CSV.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
