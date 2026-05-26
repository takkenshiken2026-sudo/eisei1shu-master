#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
glossary_terms.csv 全件を手作り品質の構成でリライトする。

  python3 tools/sync_glossary_sources.py   # 推奨: 事前に定義を同期
  python3 tools/glossary_handmade_rewrite_all.py
  python3 tools/glossary_handmade_rewrite_all.py --dry-run
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GLOSSARY_CSV = ROOT / "data" / "glossary_terms.csv"

sys.path.insert(0, str(ROOT / "tools"))
from glossary_enrich_a_rank_content import ENRICHMENTS as A_ENRICHMENTS  # noqa: E402
from glossary_enrich_a_rank_finish import FINISH as A_FINISH  # noqa: E402
from glossary_enrich_b_rank_content import ENRICHMENTS as B_ENRICHMENTS  # noqa: E402
from glossary_enrich_priority_content import ENRICHMENTS as P_ENRICHMENTS  # noqa: E402
from glossary_handmade_builder import (  # noqa: E402
    build_handmade_patch,
    compose_handmade_body,
    best_source_text,
)
from glossary_pro_writer import (  # noqa: E402
    _exam_strategy,
    _expert_perspective,
    _strip_boilerplate_body,
    _workplace_narrative,
    build_pro_patch,
    ensure_pro_body_length,
)


def load_manual() -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for src in (A_ENRICHMENTS, A_FINISH, B_ENRICHMENTS, P_ENRICHMENTS):
        for slug, patch in src.items():
            out[slug] = dict(patch)
    return out


def _merge_bodies(primary: str, secondary: str) -> str:
    """段落単位で重複を除き結合（手動本文＋組立本文）。"""
    seen: set[str] = set()

    def norm(p: str) -> str:
        return re.sub(r"\s+", "", p)[:48]

    parts: list[str] = []
    for block in (primary + "\n\n" + secondary).split("\n\n"):
        b = block.strip()
        if not b:
            continue
        key = norm(re.sub(r"<[^>]+>", "", b))
        if key in seen:
            continue
        seen.add(key)
        parts.append(b)
    return "\n\n".join(parts)




def apply_patch(row: dict[str, str], patch: dict[str, str], manual: bool) -> None:
    term = (row.get("term") or "").strip()
    category = (row.get("category") or "").strip()
    manual_body = (patch.get("term_detail_body") or "").strip() if manual else None

    source_text, _ = best_source_text(row)

    if manual and manual_body:
        slug = (row.get("slug") or "").strip()
        composed = compose_handmade_body(
            term, category, source_text, slug=slug
        )
        merged_body = _merge_bodies(manual_body, composed)
        built = build_handmade_patch(row, use_manual_body=merged_body)
        for k, v in patch.items():
            if k == "core":
                continue
            if v and str(v).strip():
                built[k] = v
        patch = built
    elif not manual:
        patch = build_handmade_patch(row)

    slug = (row.get("slug") or "").strip()
    source = (patch.get("definition") or source_text or "").strip()
    kept_detail = (patch.get("term_detail_body") or "").strip() if manual else ""
    pro = build_pro_patch(row)
    for k, v in pro.items():
        if k == "core":
            continue
        if manual and k == "term_detail_body":
            continue
        if v and str(v).strip():
            patch[k] = v
    if manual and kept_detail:
        exam = patch.get("exam_points") or ""
        extras = "\n\n".join(
            [
                _expert_perspective(term, category, source),
                _workplace_narrative(term, category, source),
                _exam_strategy(term, category, exam),
            ]
        )
        patch["term_detail_body"] = ensure_pro_body_length(
            _strip_boilerplate_body(kept_detail + "\n\n" + extras),
            term,
            category,
            source,
            slug,
        )
    else:
        patch["term_detail_body"] = ensure_pro_body_length(
            patch.get("term_detail_body") or "",
            term,
            category,
            source,
            slug,
        )

    for k, v in patch.items():
        if k == "core":
            continue
        row[k] = v


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    manual = load_manual()
    with GLOSSARY_CSV.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
        fieldnames = list(rows[0].keys()) if rows else []

    stats = {"manual": 0, "built": 0}
    for row in rows:
        slug = (row.get("slug") or "").strip()
        if slug in manual:
            apply_patch(row, manual[slug], manual=True)
            stats["manual"] += 1
        else:
            apply_patch(row, {}, manual=False)
            stats["built"] += 1

    if args.dry_run:
        print(f"更新予定: 手動維持={stats['manual']} 自動組立={stats['built']}")
        return 0

    with GLOSSARY_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    print(
        f"全件プロ品質リライト完了 -> {GLOSSARY_CSV}\n"
        f"  手動リライト維持: {stats['manual']}\n"
        f"  手作り組立: {stats['built']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
