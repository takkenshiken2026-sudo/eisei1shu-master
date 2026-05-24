#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
glossary_terms.csv の definition を、マスターCSV・TERM_FACTS から厚い内容に同期する。

  python3 tools/sync_glossary_sources.py
  python3 tools/sync_glossary_sources.py --dry-run
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GLOSSARY_CSV = ROOT / "data" / "glossary_terms.csv"
MASTER = ROOT / "docs" / "dai1shu-glossary-terms-master.csv"

sys.path.insert(0, str(ROOT / "tools"))
from generate_glossary_long_descriptions import looks_like_generated_definition  # noqa: E402
from glossary_fact_lookup import resolve_fact_key  # noqa: E402
from rewrite_with_numbers import TERM_FACTS  # noqa: E402


def is_thin_template(defn: str) -> bool:
    d = (defn or "").strip()
    if len(d) < 160:
        return True
    if "説明において" in d and "使う語です" in d:
        return True
    if looks_like_generated_definition(d) and "まず、" in d and len(d) < 220:
        return True
    return False


def load_master() -> dict[str, str]:
    out: dict[str, str] = {}
    if not MASTER.is_file():
        return out
    with MASTER.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.reader(f):
            if len(row) >= 3 and row[0] != "カテゴリ":
                out[row[1].strip()] = row[2].strip()
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    master = load_master()
    with GLOSSARY_CSV.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
        fieldnames = list(rows[0].keys()) if rows else []

    from glossary_derive_content import short_def_from  # noqa: E402

    updated_fact = updated_master = 0
    for row in rows:
        term = (row.get("term") or "").strip()
        slug = (row.get("slug") or "").strip()
        defn = (row.get("definition") or "").strip()
        new_defn = defn

        fact_key = resolve_fact_key(term, slug)
        if fact_key:
            fact = TERM_FACTS[fact_key].strip()
            if len(fact) > len(defn) + 20 or is_thin_template(defn):
                new_defn = fact
                updated_fact += 1

        if new_defn == defn:
            md = master.get(term, "")
            if md and not is_thin_template(md) and len(md) > len(defn) + 30:
                new_defn = md
                updated_master += 1

        if new_defn != defn:
            row["definition"] = new_defn
            row["short_def"] = short_def_from(new_defn, term)

    if args.dry_run:
        print(f"TERM_FACTS で更新: {updated_fact}, マスターで更新: {updated_master}")
        return 0

    with GLOSSARY_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    print(
        f"同期完了 -> {GLOSSARY_CSV}\n"
        f"  TERM_FACTS: {updated_fact}\n"
        f"  マスター: {updated_master}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
