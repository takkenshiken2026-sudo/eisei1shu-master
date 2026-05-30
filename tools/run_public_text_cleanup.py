#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公開向けテキストの内部参照・英語 slug 漏れを一括修正し、build_all まで実行する。

  python3 tools/run_public_text_cleanup.py
  python3 tools/run_public_text_cleanup.py --dry-run
  python3 tools/run_public_text_cleanup.py --skip-build
"""

from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

GUIDE_CSV = ROOT / "data" / "guide_articles.csv"

LEAK_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("article_marker", re.compile(r"（記事:[a-z0-9-]+）")),
    ("slug_paren", re.compile(r"（[a-z]{2,}(?:-[a-z0-9]+)+）")),
    ("action_items", re.compile(r"action_items", re.I)),
    ("field_broken", re.compile(r"[a-z]{2,}の[a-z]{2,}(?:-[a-z0-9]+)+")),
    ("internal_tool", re.compile(r"scaffold_guide|guide_article_compose|migrate_import", re.I)),
]


def audit_guide_csv() -> dict[str, int]:
    counts: dict[str, int] = {name: 0 for name, _ in LEAK_PATTERNS}
    if not GUIDE_CSV.is_file():
        return counts
    with GUIDE_CSV.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        skip = {"slug", "writer", "reviewer", "sources", "fact_checked_at", "revision_note"}
        cols = [c for c in (reader.fieldnames or []) if c not in skip]
        for row in reader:
            blob = "\n".join((row.get(c) or "") for c in cols)
            for name, pat in LEAK_PATTERNS:
                if pat.search(blob):
                    counts[name] += 1
    return counts


def run_cmd(cmd: list[str], *, dry_run: bool) -> None:
    print("+", " ".join(cmd))
    if dry_run:
        return
    subprocess.run(cmd, cwd=ROOT, check=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-build", action="store_true")
    args = ap.parse_args()
    py = sys.executable

    before = audit_guide_csv()
    print("guide_articles.csv leak rows (before):", {k: v for k, v in before.items() if v})

    run_cmd([py, "tools/fix_guide_leaked_tokens.py"] + (["--dry-run"] if args.dry_run else []), dry_run=False)
    run_cmd(
        [py, "tools/guide_catalog_batch.py", "--fix-titles"] + (["--dry-run"] if args.dry_run else []),
        dry_run=False,
    )
    run_cmd(
        [py, "tools/fix_hub_public_leaks.py"] + (["--dry-run"] if args.dry_run else ["--apply"]),
        dry_run=False,
    )
    run_cmd(
        [py, "tools/strip_glossary_inline_html_tables.py"]
        + (["--dry-run"] if args.dry_run else []),
        dry_run=False,
    )

    after = audit_guide_csv()
    print("guide_articles.csv leak rows (after):", {k: v for k, v in after.items() if v})
    if any(after.values()):
        print("ERROR: guide CSV に漏れが残っています", file=sys.stderr)
        return 1

    if args.skip_build or args.dry_run:
        print("skip-build / dry-run: build_all は実行しません")
        return 0

    run_cmd([py, "tools/build_all.py"], dry_run=False)
    run_cmd(["bash", "tools/prepare_public_site.sh"], dry_run=False)
    print("OK: run_public_text_cleanup 完了")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
