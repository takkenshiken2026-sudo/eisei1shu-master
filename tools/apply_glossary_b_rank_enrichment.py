#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重要度B用語（追加50の29語）を glossary_enrich_b_rank_content で上書きする。"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GLOSSARY_CSV = ROOT / "data" / "glossary_terms.csv"

sys.path.insert(0, str(ROOT / "tools"))
from glossary_enrich_b_rank_content import ENRICHMENTS  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    with GLOSSARY_CSV.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
        fieldnames = list(rows[0].keys()) if rows else []
        by_slug = {(r.get("slug") or "").strip(): r for r in rows if (r.get("slug") or "").strip()}

    not_found = [s for s in ENRICHMENTS if s not in by_slug]
    if not_found:
        print("CSVにないslug:", ", ".join(not_found), file=sys.stderr)
        return 1

    for slug, patch in ENRICHMENTS.items():
        row = by_slug[slug]
        for key, val in patch.items():
            if key not in fieldnames:
                continue
            row[key] = val
        if patch.get("exam_points"):
            row["explanation"] = patch["exam_points"]
        if patch.get("definition"):
            d = patch["definition"].strip()
            term = (row.get("term") or "").strip()
            if d.startswith("「"):
                row["short_def"] = d[:200] + ("…" if len(d) > 200 else "")
            else:
                row["short_def"] = f"「{term}」は、{d.split('。')[0]}。"

    if args.dry_run:
        print(f"用語数: {len(ENRICHMENTS)}")
        return 0

    with GLOSSARY_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    print(f"更新: {len(ENRICHMENTS)} 語 -> {GLOSSARY_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
