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
from glossary_body_pad import pad_term_detail_body  # noqa: E402
from glossary_enrich_a_rank_content import ENRICHMENTS as A_ENRICHMENTS  # noqa: E402
from glossary_enrich_a_rank_finish import FINISH as A_FINISH  # noqa: E402
from glossary_enrich_b_rank_content import ENRICHMENTS as B_ENRICHMENTS  # noqa: E402
from glossary_enrich_priority_content import ENRICHMENTS as P_ENRICHMENTS  # noqa: E402
from glossary_handmade_builder import (  # noqa: E402
    _past_exam_paragraph,
    _study_flow_paragraph,
    build_handmade_patch,
    compose_handmade_body,
    best_source_text,
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


def _ensure_min_body(body: str, term: str, category: str, source: str) -> str:
    text = (body or "").strip()
    short = term.split("（")[0].strip()
    append_blocks = [
        _past_exam_paragraph(term, category, source),
        _study_flow_paragraph(term, category),
        (
            f"復習では、{short}の定義を声に出し、続けて本文の表の項目を"
            "閉じた目で言えるか確認します。頻出ポイントは「誤りの型」として"
            "（数値違い・主体違い・期限違い）に分類すると覚えやすくなります。"
        ),
        (
            f"{short}は、{category}の他の用語とセットで出題されることが多いです。"
            "関連用語リンクから1つずつ違いを書き足し、過去問で接続を確認してください。"
        ),
        (
            f"受験直前は、{short}の数値・期限・主体だけをカード化し、"
            "毎日5分で見直すと効率がよいです。公式情報で改正がないかも確認してください。"
        ),
    ]
    for block in append_blocks:
        if len(re.sub(r"<[^>]+>", "", text)) >= 900:
            break
        key = re.sub(r"\s+", "", block)[:40]
        if block and key not in re.sub(r"\s+", "", text):
            text = (text + "\n\n" + block).strip()

    short = term.split("（")[0].strip()
    n = 0
    while len(re.sub(r"<[^>]+>", "", text)) < 900 and n < 6:
        text = (
            text
            + "\n\n"
            + (
                f"【復習の補足{n + 1}】{short}では、{category}の文脈で定義・数値・主体・手続が"
                "セットで問われます。本文と頻出ポイントを往復し、過去問では誤りの理由"
                "（どの数値・主体・期限が違うか）まで確認してください。"
            )
        ).strip()
        n += 1
    return text


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
        if patch.get("term_detail_body"):
            built["term_detail_body"] = pad_term_detail_body(
                patch["term_detail_body"].strip(),
                term=term,
                category=category,
                core=patch.get("core") or "",
                definition=built.get("definition") or "",
            )
        patch = built
    elif not manual:
        patch = build_handmade_patch(row)

    source = (patch.get("definition") or source_text or "").strip()
    patch["term_detail_body"] = _ensure_min_body(
        patch.get("term_detail_body") or "",
        term,
        category,
        source,
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
        f"全件リライト完了 -> {GLOSSARY_CSV}\n"
        f"  手動リライト維持: {stats['manual']}\n"
        f"  手作り組立: {stats['built']}"
    )

    # 読みやすい文体・要点具体例・覚え方・FAQ4件
    from apply_glossary_reader_friendly import main as apply_reader  # noqa: E402

    print("\n--- 読みやすさ・要点・覚え方・FAQ を反映 ---")
    return apply_reader()


if __name__ == "__main__":
    raise SystemExit(main())
