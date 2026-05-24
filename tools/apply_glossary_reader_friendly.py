#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用語詳細記事を読みやすい文体にし、要点（具体例）・覚え方・FAQ4件を全件反映する。

  python3 tools/migrate_glossary_csv_columns.py   # 初回のみ
  python3 tools/apply_glossary_reader_friendly.py
  python3 tools/build_all.py
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GLOSSARY_CSV = ROOT / "data" / "glossary_terms.csv"

sys.path.insert(0, str(ROOT / "tools"))
from glossary_reader_content import build_reader_patch  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    with GLOSSARY_CSV.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
        fieldnames = list(rows[0].keys()) if rows else []

    updated = 0
    for row in rows:
        patch = build_reader_patch(row)
        changed = False
        for k, v in patch.items():
            if k not in fieldnames:
                fieldnames.append(k)
            if (row.get(k) or "").strip() != v.strip():
                row[k] = v
                changed = True
        if changed:
            updated += 1

    if args.dry_run:
        print(f"更新予定: {updated} / {len(rows)} 語")
        return 0

    with GLOSSARY_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    print(f"反映完了: {updated} / {len(rows)} 語 -> {GLOSSARY_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
