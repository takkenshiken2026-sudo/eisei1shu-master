#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用語 CSV の exam_points / term_detail_body / explanation を品質修正する。"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.glossary_derive_content import derive_exam_points, derive_positive_exam_points
from tools.glossary_handmade_builder import best_source_text, exam_for_slug
from tools.knowledge_hub_seo import _MISTAKE_POINT_MARKERS, glossary_definition_body_text

CSV_PATH = ROOT / "data" / "glossary_terms.csv"


def _has_mistake_markers(text: str) -> bool:
    return any(marker in (text or "") for marker in _MISTAKE_POINT_MARKERS)


def fix_row(row: dict[str, str]) -> tuple[dict[str, str], bool]:
    term = (row.get("term") or "").strip()
    slug = (row.get("slug") or "").strip()
    category = (row.get("category") or "").strip()
    legal = (row.get("legal_basis") or "").strip()
    if not term or slug.endswith("-sample"):
        return row, False

    source, _ = best_source_text(row)
    changed = False
    new_row = dict(row)

    positive = derive_positive_exam_points(term, source, category, legal)
    mistakes = exam_for_slug(slug, term, source, category)

    if (row.get("exam_points") or "").strip() != positive:
        new_row["exam_points"] = positive
        changed = True

    current_expl = (row.get("explanation") or "").strip()
    if not current_expl or current_expl == (row.get("exam_points") or "").strip() or _has_mistake_markers(
        current_expl
    ):
        if current_expl != mistakes:
            new_row["explanation"] = mistakes
            changed = True

    cleaned_body = glossary_definition_body_text(new_row)
    if cleaned_body and (row.get("term_detail_body") or "").strip() != cleaned_body:
        new_row["term_detail_body"] = cleaned_body
        changed = True

    return new_row, changed


def main() -> None:
    if not CSV_PATH.is_file():
        raise SystemExit(f"missing: {CSV_PATH}")

    with CSV_PATH.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        header = list(reader.fieldnames or [])
        rows = list(reader)

    changed_rows = 0
    new_rows: list[dict[str, str]] = []
    for row in rows:
        fixed, changed = fix_row(row)
        if changed:
            changed_rows += 1
        new_rows.append(fixed)

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        writer.writerows(new_rows)

    print(f"updated {changed_rows}/{len(new_rows)} rows in {CSV_PATH.name}")


if __name__ == "__main__":
    main()
