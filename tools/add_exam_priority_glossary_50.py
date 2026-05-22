#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
試験頻出・重要キーワードを優先した用語50件を data/glossary_terms.csv に追加し、
docs/dai1shu-glossary-terms-master.csv 等へ同期する。

  python3 tools/add_exam_priority_glossary_50.py
  python3 tools/add_exam_priority_glossary_50.py --dry-run
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GLOSSARY_CSV = ROOT / "data" / "glossary_terms.csv"
MASTER = ROOT / "docs" / "dai1shu-glossary-terms-master.csv"
CHECKLIST = ROOT / "docs" / "glossary-terms-checklist.csv"
BATCH_JSON = ROOT / "data" / "glossary_add50_batch.json"
TAG = "第一種衛生管理者"
READING = "（読み未登録）"

MIRRORS = [
    ROOT / "public_site" / "docs" / "dai1shu-glossary-terms-master.csv",
    ROOT / "public_site" / "docs" / "glossary-terms-checklist.csv",
]

CAT_ORDER = [
    "関係法令（有害業務）",
    "関係法令（有害以外）",
    "労働衛生（有害業務）",
    "労働衛生（有害以外）",
    "労働生理",
]


def clamp_def(s: str, max_len: int = 200) -> str:
    s = re.sub(r"。+", "。", s.strip())
    if len(s) <= max_len:
        return s
    cut = max_len - 1
    while cut > 60 and s[cut] not in "、。；":
        cut -= 1
    return s[:cut] + "…" if cut > 60 else s[: max_len - 1] + "…"


def build_short_def(term: str, body: str) -> str:
    m = re.match(r"^「[^」]+」(?:とは、|は、)([^。]+[。])", body)
    if m:
        return f"「{term}」{m.group(1)}"
    first = body.split("。")[0].strip()
    if first.startswith("「"):
        return first + "。"
    return f"「{term}」は、{first}。"


def master_desc(cat: str, term: str, core: str) -> str:
    if "法令" in cat:
        return (
            f"「{term}」とは、{core}を中心に、法令が使用者などに課す義務や届出・記録、"
            f"運用上の役割などを整理するときに使う語です。"
            f"具体的な要件や対象は、関係規則・告示で示されています。"
        )
    if cat.startswith("労働衛生"):
        norm = term.replace("・", "、")
        return (
            f"「{term}」とは、作業環境、職場の健康課題に関する労働衛生の説明において、"
            f"「{norm}」とは、{core}を手がかりに、ばく露評価・対策の優先順位・管理区分などを"
            f"説明するときに使う語です。有害環境と対策・管理の対応を語るときに位置づけられます。"
        )
    return (
        f"「{term}」とは、{core}に関してからだのしくみや変化、疾患の成り立ちを説明するときに使う語です。"
        f"解剖・生理・病態のどこに焦点があるかで語の意味が決まります。"
    )


def faq_pair(term: str) -> tuple[str, str, str, str]:
    q1 = f"{term}は第一種衛生管理者試験で重要ですか？"
    a1 = (
        "重要です。用語の定義だけでなく、対象・義務・数値・関連制度との違いが"
        "選択肢で入れ替えられることがあります。本文の頻出ポイントと誤りやすい点を確認してください。"
    )
    q2 = "公式情報も確認した方がよいですか？"
    a2 = (
        "はい。本記事は学習用の要点整理です。法令改正や正式な運用は、"
        "e-Gov法令検索・厚生労働省・試験実施団体の公式情報で受験前に確認してください。"
    )
    return q1, a1, q2, a2


def row_from_item(item: dict) -> dict[str, str]:
    term = item["term"].strip()
    cat = item["category"].strip()
    imp = item.get("importance", "B").strip()
    slug = item["slug"].strip()
    core = item["core"].strip()
    definition = clamp_def(item["definition"].strip())
    short_def = clamp_def(build_short_def(term, definition))
    detail = item["detail"].strip()
    exam_points = item.get("exam_points", [])
    if isinstance(exam_points, list):
        exam_points = "; ".join(exam_points)
    mistakes = item.get("mistakes", "").strip()
    memory = item.get("memory", "").strip()
    related = "; ".join(item.get("related", []))
    legal = "; ".join(item.get("legal_basis", []))
    title = f"{term}とは？試験で問われる要点・注意点を整理【第一種衛生管理者試験】"
    lead = definition
    q1, a1, q2, a2 = faq_pair(term)
    return {
        "term": term,
        "reading": READING,
        "category": cat,
        "tags": TAG,
        "short_def": short_def,
        "definition": definition,
        "related_terms": related,
        "legal_basis": legal,
        "importance": imp,
        "explanation": exam_points or definition,
        "article_title": title,
        "article_lead": lead,
        "term_detail_body": detail,
        "exam_points": exam_points,
        "common_mistakes": mistakes,
        "memory_tip": memory,
        "example_question": "",
        "example_answer": "",
        "faq_1_question": q1,
        "faq_1_answer": a1,
        "faq_2_question": q2,
        "faq_2_answer": a2,
        "slug": slug,
    }


def load_batch() -> list[dict]:
    if not BATCH_JSON.is_file():
        print(f"見つかりません: {BATCH_JSON}", file=sys.stderr)
        sys.exit(1)
    raw = json.loads(BATCH_JSON.read_text(encoding="utf-8"))
    if not isinstance(raw, list) or len(raw) != 50:
        print(f"バッチ件数は50件である必要があります（現在: {len(raw) if isinstance(raw, list) else 0}）", file=sys.stderr)
        sys.exit(1)
    return raw


def sync_master(rows: list[dict[str, str]]) -> None:
    existing: list[list[str]] = []
    if MASTER.is_file():
        with MASTER.open(encoding="utf-8-sig", newline="") as f:
            r = csv.reader(f)
            header = next(r, None)
            if header != ["カテゴリ", "用語", "解説"]:
                print("マスターCSVのヘッダーが想定と異なります", file=sys.stderr)
                sys.exit(1)
            existing = list(r)

    keys = {(r[0], r[1]) for r in existing if len(r) >= 2}
    for row in rows:
        key = (row["category"], row["term"])
        if key in keys:
            continue
        desc = master_desc(row["category"], row["term"], row["definition"][:80])
        existing.append([row["category"], row["term"], desc])
        keys.add(key)

    cat_idx = {c: i for i, c in enumerate(CAT_ORDER)}
    existing.sort(key=lambda r: (cat_idx.get(r[0], 999), r[1]))

    for path in (MASTER, CHECKLIST, *MIRRORS):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["カテゴリ", "用語", "解説"])
            w.writerows(existing)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    batch = load_batch()
    new_rows = [row_from_item(item) for item in batch]

    if not GLOSSARY_CSV.is_file():
        print(f"見つかりません: {GLOSSARY_CSV}", file=sys.stderr)
        return 1

    with GLOSSARY_CSV.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        existing = list(reader)

    existing_terms = {(r.get("term") or "").strip() for r in existing}
    existing_slugs = {(r.get("slug") or "").strip() for r in existing if (r.get("slug") or "").strip()}

    to_add: list[dict[str, str]] = []
    for row in new_rows:
        if row["term"] in existing_terms:
            print(f"スキップ（既存）: {row['term']}", file=sys.stderr)
            continue
        if row["slug"] in existing_slugs:
            print(f"スキップ（slug重複）: {row['slug']}", file=sys.stderr)
            continue
        to_add.append(row)
        existing_terms.add(row["term"])
        existing_slugs.add(row["slug"])

    if len(to_add) != 50:
        print(
            f"警告: 追加予定 {len(to_add)} 件（50件想定）。重複スキップがあった可能性があります。",
            file=sys.stderr,
        )

    if args.dry_run:
        for r in to_add[:5]:
            print(r["term"], r["category"], r["slug"], len(r["term_detail_body"]))
        print(f"... ほか {max(0, len(to_add) - 5)} 件 / 合計追加 {len(to_add)} 件")
        return 0

    merged = existing + to_add
    with GLOSSARY_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(merged)

    sync_master(to_add)
    print(f"glossary_terms.csv: +{len(to_add)} 件（合計 {len(merged)} 件）")
    print(f"マスター同期: {MASTER}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
