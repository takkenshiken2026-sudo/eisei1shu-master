#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重要度A用語の本文を glossary_enrich_a_rank_content.ENRICHMENTS で上書きする。

  python3 tools/apply_glossary_a_rank_enrichment.py
  python3 tools/apply_glossary_a_rank_enrichment.py --dry-run
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GLOSSARY_CSV = ROOT / "data" / "glossary_terms.csv"

sys.path.insert(0, str(ROOT / "tools"))
from glossary_enrich_a_rank_content import ENRICHMENTS  # noqa: E402
from glossary_enrich_a_rank_finish import FINISH  # noqa: E402
from glossary_body_pad import pad_term_detail_body  # noqa: E402

for _slug, _patch in FINISH.items():
    if _slug in ENRICHMENTS:
        ENRICHMENTS[_slug].update(_patch)

_BATCH_BY_SLUG: dict[str, dict] = {}
import json
from pathlib import Path

_batch = json.loads(
    (Path(__file__).resolve().parent.parent / "data" / "glossary_add50_batch.json").read_text(
        encoding="utf-8"
    )
)
for _item in _batch:
    if _item.get("importance") == "A":
        _BATCH_BY_SLUG[_item["slug"]] = _item

for _slug, _patch in ENRICHMENTS.items():
    _item = _BATCH_BY_SLUG.get(_slug, {})
    if _patch.get("term_detail_body"):
        _patch["term_detail_body"] = pad_term_detail_body(
            _patch["term_detail_body"],
            term=_item.get("term") or _slug,
            category=_item.get("category") or "",
            core=_item.get("core") or "",
            definition=_patch.get("definition") or _item.get("definition") or "",
        )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    # validate slugs exist in csv
    with GLOSSARY_CSV.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
        fieldnames = rows[0].keys() if rows else []
        by_slug = {(r.get("slug") or "").strip(): r for r in rows if (r.get("slug") or "").strip()}

    not_found = [s for s in ENRICHMENTS if s not in by_slug]
    if not_found:
        print("CSVにないslug:", ", ".join(not_found), file=sys.stderr)
        return 1

    updated = 0
    for slug, patch in ENRICHMENTS.items():
        row = by_slug[slug]
        for key, val in patch.items():
            if key not in fieldnames:
                continue
            if (row.get(key) or "").strip() != val.strip():
                row[key] = val
                updated += 1
        # explanation 列は exam_points と同期（一覧用）
        if patch.get("exam_points"):
            row["explanation"] = patch["exam_points"]
        # short_def を definition 先頭から再生成
        if patch.get("definition"):
            d = patch["definition"].strip()
            term = (row.get("term") or "").strip()
            if d.startswith("「"):
                row["short_def"] = d[:200] + ("…" if len(d) > 200 else "")
            else:
                row["short_def"] = f"「{term}」は、{d.split('。')[0]}。"

    if args.dry_run:
        print(f"更新フィールド数（セル単位）: {updated} / 用語数: {len(ENRICHMENTS)}")
        return 0

    with GLOSSARY_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    print(f"更新: {len(ENRICHMENTS)} 語 -> {GLOSSARY_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
