#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""glossary_terms.csv に summary_body, faq_3, faq_4 列を追加する。"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "data" / "glossary_terms.csv"

NEW_COLS = [
    "summary_body",
    "faq_3_question",
    "faq_3_answer",
    "faq_4_question",
    "faq_4_answer",
]

# slug の直前に FAQ 列を挿入
INSERT_BEFORE = "slug"


def main() -> None:
    with CSV.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
        old_fields = list(rows[0].keys()) if rows else []

    fields: list[str] = []
    for c in old_fields:
        if c == INSERT_BEFORE:
            for nc in NEW_COLS:
                if nc not in fields:
                    fields.append(nc)
        if c not in fields:
            fields.append(c)

    for nc in NEW_COLS:
        if nc not in fields:
            fields.append(nc)

    for row in rows:
        for nc in NEW_COLS:
            row.setdefault(nc, "")

    with CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    print(f"列を更新: {CSV}")
    print("追加列:", ", ".join(NEW_COLS))


if __name__ == "__main__":
    main()
