#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
glossary_terms.csv の用語詳細記事を SEO ガイドラインに沿って一括リッチ化する。

優先順位:
  1. glossary_enrich_a_rank_content / glossary_enrich_b_rank_content（手動リライト）
  2. rewrite_with_numbers.TERM_FACTS（数値・条文入り解説）
  3. 定義文から用語固有の試験ポイント・表を導出（汎用テンプレは使わない）

  python3 tools/sync_glossary_sources.py      # 定義をマスター・TERM_FACTS へ同期
  python3 tools/upgrade_glossary_term_articles.py
  python3 tools/upgrade_glossary_term_articles.py --dry-run
  python3 tools/upgrade_glossary_term_articles.py --force
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
from glossary_enrich_a_rank_content import ENRICHMENTS as A_ENRICHMENTS, _ep, _tbl  # noqa: E402
from glossary_enrich_a_rank_finish import FINISH as A_FINISH  # noqa: E402
from glossary_enrich_b_rank_content import ENRICHMENTS as B_ENRICHMENTS  # noqa: E402
from glossary_enrich_priority_content import ENRICHMENTS as P_ENRICHMENTS  # noqa: E402
from apply_glossary_from_term_facts import (  # noqa: E402
    EXAM_BY_SLUG,
    TABLE_BY_SLUG,
    _body_from_fact,
    build_patch as build_fact_patch,
)
from glossary_fact_lookup import resolve_fact_key  # noqa: E402
from generate_glossary_long_descriptions import (  # noqa: E402
    LEGACY_LEADING_PREFIXES,
    strip_legacy_leading_prefix,
)
from rewrite_with_numbers import TERM_FACTS  # noqa: E402
from glossary_derive_content import (  # noqa: E402
    derive_exam_points,
    derive_lead,
    derive_memory_tip,
    derive_mistakes,
    derive_table_from_text,
    is_generic_body,
    short_def_from,
)

EXAM_LABEL = "第一種衛生管理者試験"

# 手動リライトを上書きしない
MANUAL_ENRICHMENTS: dict[str, dict[str, str]] = {}
for _slug, _patch in A_ENRICHMENTS.items():
    MANUAL_ENRICHMENTS[_slug] = dict(_patch)
for _slug, _patch in A_FINISH.items():
    MANUAL_ENRICHMENTS.setdefault(_slug, {}).update(_patch)
for _slug, _patch in B_ENRICHMENTS.items():
    MANUAL_ENRICHMENTS[_slug] = dict(_patch)
for _slug, _patch in P_ENRICHMENTS.items():
    MANUAL_ENRICHMENTS[_slug] = dict(_patch)

SKIP_PREFIX = (
    "第一種衛生管理者試験では、",
    "学習の進め方としては、",
)

SLUG_TABLES: dict[str, str] = {
    "36-kyotei-jikangai-jogen": _tbl(
        ["区分", "上限・条件"],
        [
            ["原則（時間外）", "月45時間・年360時間"],
            ["特別条項", "年720時間以内・複数月平均80時間・単月100時間未満"],
            ["月45時間超", "年6回まで"],
            ["違反時", "6か月以下懲役または30万円以下罰金"],
        ],
    ),
}

GENERIC_EXAM_MARKERS = (
    "定義だけ暗記すれば十分",
    "測定・健診・保護具のどれか一方だけで十分",
    "試験非出題」→ 誤り; 「定義だけで十分",
)


def _norm(s: str) -> str:
    return (s or "").strip()


def needs_upgrade(row: dict[str, str]) -> bool:
    body = _norm(row.get("term_detail_body"))
    defn = _norm(row.get("definition"))
    ep = _norm(row.get("exam_points"))
    if not body or body == defn:
        return True
    if len(body) < 520:
        return True
    if any(body.startswith(p) for p in SKIP_PREFIX):
        return True
    if is_generic_body(body):
        return True
    if any(m in ep for m in GENERIC_EXAM_MARKERS):
        return True
    if not ep or ep.count(";") < 4:
        return True
    return False


def strip_pad_from_body(body: str) -> str:
    t = body
    for marker in ("\n\n【整理の軸】",):
        if marker in t:
            t = t.split(marker)[0]
    m = re.search(
        r"\n\n.{0,40}は、.{0,80}として押さえます。分野（",
        t,
    )
    if m:
        t = t[: m.start()]
    for pat in (
        r"\n\n.{0,60}として整理すると覚えやすい用語です。",
        r"\n\n試験では正しい説明に似せ、数値・対象者",
    ):
        m2 = re.search(pat, t)
        if m2:
            t = t[: m2.start()]
    return t.strip()


def strip_boilerplate(defn: str) -> str:
    t = strip_legacy_leading_prefix(defn)
    t = re.sub(
        r"「[^」]+」とは、[^。]+の説明において、",
        "",
        t,
        count=1,
    )
    t = re.sub(
        r"使う語です。まず、",
        "",
        t,
        count=1,
    )
    t = re.sub(
        r"説明するときに使う語です。",
        "",
        t,
        count=1,
    )
    return t.strip()


def resolve_table(term: str, text: str, *, slug: str = "") -> str:
    if slug and SLUG_TABLES.get(slug):
        return SLUG_TABLES[slug]
    if slug and TABLE_BY_SLUG.get(slug):
        return TABLE_BY_SLUG[slug]
    return derive_table_from_text(term, text)


def exam_for_row(slug: str, term: str, definition: str, category: str) -> str:
    if slug in EXAM_BY_SLUG:
        return EXAM_BY_SLUG[slug]
    return derive_exam_points(term, definition, category)


def article_title_for(term: str) -> str:
    short = term.split("（")[0].strip()
    if len(short) > 28:
        short = short[:26] + "…"
    return f"{short}とは？意味・試験ポイント・注意点【{EXAM_LABEL}】"


def faq_pair(term: str) -> tuple[str, str, str, str]:
    q1 = f"{term}は{EXAM_LABEL}で重要ですか？"
    a1 = (
        "重要です。用語の定義だけでなく、対象・義務・数値・関連制度との違いが"
        "選択肢で入れ替えられることがあります。本文の表と頻出ポイントを使って確認してください。"
    )
    q2 = "公式情報も確認した方がよいですか？"
    a2 = (
        "はい。本記事は学習用の要点整理です。法令改正や正式な運用は、"
        "e-Gov法令検索・厚生労働省・試験実施団体の公式情報で受験前に確認してください。"
    )
    return q1, a1, q2, a2


def legal_basis_from_text(text: str) -> str:
    found: list[str] = []
    for m in re.finditer(r"（([^）]*(?:法|令|則)[^）]{0,40})）", text):
        s = m.group(1).strip()
        if s and s not in found:
            found.append(s)
    return "; ".join(found[:4])


def apply_manual_patch(row: dict[str, str], patch: dict[str, str]) -> None:
    slug = _norm(row.get("slug"))
    term = _norm(row.get("term"))
    category = _norm(row.get("category"))
    core = _norm(patch.get("core") or "")
    for key, val in patch.items():
        if key == "core":
            continue
        row[key] = val
    if patch.get("term_detail_body"):
        body = strip_pad_from_body(patch["term_detail_body"])
        if "<table" not in body:
            tbl = resolve_table(term, row.get("definition", ""), slug=slug)
            if tbl:
                body = body.rstrip() + "\n\n" + tbl
        row["term_detail_body"] = pad_term_detail_body(
            body,
            term=term,
            category=category,
            core=core,
            definition=row.get("definition", ""),
        )
    if patch.get("exam_points"):
        row["explanation"] = patch["exam_points"]
    if patch.get("definition"):
        row["short_def"] = short_def_from(patch["definition"], term)
    row["article_title"] = article_title_for(term)
    if patch.get("article_lead"):
        row["article_lead"] = patch["article_lead"]
    elif not _norm(row.get("article_lead")):
        row["article_lead"] = derive_lead(term, row.get("definition", ""))


def enrich_from_fact(row: dict[str, str], fact_key: str) -> None:
    patch = build_fact_patch(row, fact_key)
    slug = _norm(row.get("slug"))
    term = _norm(row.get("term"))
    category = _norm(row.get("category"))
    defn = patch["definition"]
    patch["term_detail_body"] = strip_pad_from_body(patch["term_detail_body"])
    table = resolve_table(term, defn, slug=slug)
    if table and "<table" not in patch["term_detail_body"]:
        patch["term_detail_body"] = patch["term_detail_body"].rstrip() + "\n\n" + table
    patch["term_detail_body"] = pad_term_detail_body(
        patch["term_detail_body"],
        term=term,
        category=category,
        core=fact_key,
        definition=defn,
    )
    patch["exam_points"] = exam_for_row(slug, term, defn, category)
    patch["common_mistakes"] = derive_mistakes(term, defn, category)
    patch["memory_tip"] = derive_memory_tip(term, defn)
    for k, v in patch.items():
        row[k] = v
    row["short_def"] = short_def_from(defn, term)
    row["article_title"] = article_title_for(term)
    row["article_lead"] = derive_lead(term, defn)
    row["explanation"] = row["exam_points"]
    q1, a1, q2, a2 = faq_pair(term)
    row["faq_1_question"], row["faq_1_answer"] = q1, a1
    row["faq_2_question"], row["faq_2_answer"] = q2, a2
    legal = legal_basis_from_text(row["definition"])
    if legal and not _norm(row.get("legal_basis")):
        row["legal_basis"] = legal


def enrich_auto(row: dict[str, str]) -> None:
    term = _norm(row.get("term"))
    category = _norm(row.get("category"))
    defn = strip_boilerplate(_norm(row.get("definition")))
    if not defn:
        defn = f"「{term}」は{category}で押さえる用語です。"
    slug = _norm(row.get("slug"))
    table = resolve_table(term, defn, slug=slug)
    body = strip_pad_from_body(_body_from_fact(defn, table))
    body = pad_term_detail_body(body, term=term, category=category, core=term, definition=defn)
    exam = exam_for_row(slug, term, defn, category)
    row["definition"] = defn if defn.startswith("「") else f"「{term}」{defn.lstrip('「')}"
    row["term_detail_body"] = body
    row["exam_points"] = exam
    row["explanation"] = exam
    row["article_title"] = article_title_for(term)
    row["article_lead"] = derive_lead(term, defn)
    row["common_mistakes"] = derive_mistakes(term, defn, category)
    row["memory_tip"] = derive_memory_tip(term, defn)
    q1, a1, q2, a2 = faq_pair(term)
    row["faq_1_question"], row["faq_1_answer"] = q1, a1
    row["faq_2_question"], row["faq_2_answer"] = q2, a2
    legal = legal_basis_from_text(defn)
    if legal:
        row["legal_basis"] = legal
    row["short_def"] = short_def_from(defn, term)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="needs_upgrade を無視して全件再生成")
    args = ap.parse_args()

    with GLOSSARY_CSV.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
        fieldnames = list(rows[0].keys()) if rows else []

    stats = {"manual": 0, "facts": 0, "auto": 0, "skip": 0}

    for row in rows:
        slug = _norm(row.get("slug"))
        if not args.force and not needs_upgrade(row):
            stats["skip"] += 1
            continue

        if slug in MANUAL_ENRICHMENTS:
            apply_manual_patch(row, MANUAL_ENRICHMENTS[slug])
            stats["manual"] += 1
            continue

        fact_key = resolve_fact_key(_norm(row.get("term")), slug)
        if fact_key:
            enrich_from_fact(row, fact_key)
            stats["facts"] += 1
            continue

        enrich_auto(row)
        stats["auto"] += 1

    if args.dry_run:
        print(f"更新予定: manual={stats['manual']} facts={stats['facts']} auto={stats['auto']} skip={stats['skip']}")
        return 0

    with GLOSSARY_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    print(
        f"更新完了 -> {GLOSSARY_CSV}\n"
        f"  手動リライト: {stats['manual']}\n"
        f"  TERM_FACTS: {stats['facts']}\n"
        f"  自動構造化: {stats['auto']}\n"
        f"  スキップ: {stats['skip']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
