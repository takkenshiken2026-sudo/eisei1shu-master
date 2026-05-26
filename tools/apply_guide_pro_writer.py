#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""試験ガイド全件をプロ品質に更新する。

  python3 tools/apply_guide_pro_writer.py
  python3 tools/apply_guide_pro_writer.py --dry-run
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GUIDE_CSV = ROOT / "data" / "guide_articles.csv"

sys.path.insert(0, str(ROOT / "tools"))
from guide_pro_patches import build_guide_patch  # noqa: E402


def ensure_faq_columns(fieldnames: list[str]) -> list[str]:
    out = list(fieldnames)
    for col in (
        "faq_3_question",
        "faq_3_answer",
        "faq_4_question",
        "faq_4_answer",
    ):
        if col not in out:
            out.append(col)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    with GUIDE_CSV.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
        fieldnames = ensure_faq_columns(list(rows[0].keys()) if rows else [])

    for row in rows:
        patch = build_guide_patch(row)
        for k, v in patch.items():
            if v and str(v).strip():
                row[k] = v

    if args.dry_run:
        print(f"更新予定: {len(rows)} 本")
        return 0

    with GUIDE_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    print(f"試験ガイド プロ品質更新完了: {len(rows)} 本 -> {GUIDE_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
