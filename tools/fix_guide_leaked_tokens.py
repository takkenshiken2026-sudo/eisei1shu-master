#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""試験ガイド CSV から内部用語・slug 英語化の漏れを一括修正する。

  python3 tools/fix_guide_leaked_tokens.py --dry-run
  python3 tools/fix_guide_leaked_tokens.py
  python3 tools/run_fix_guide_leaks_batch.py
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.guide_catalog_batch import (  # noqa: E402
    content_exam_label,
    faq_answer,
    field_name_for_slug,
    legacy_broken_field_english_variants,
    legacy_broken_field_topic,
    section_body,
    topic_from_row,
)

GUIDE_CSV = ROOT / "data" / "guide_articles.csv"

USER_FACING = (
    "lead",
    "user_intent",
    "meta_description",
    "action_items",
    *(f"section_{n}_heading" for n in range(1, 8)),
    *(f"section_{n}_body" for n in range(1, 8)),
    *(f"faq_{n}_question" for n in range(1, 5)),
    *(f"faq_{n}_answer" for n in range(1, 5)),
)

INTERNAL_TOKEN_RE = re.compile(
    r"action_items|scaffold_guide_article(?:\.py)?|guide_article_compose|"
    r"migrate_import_data(?:\.py)?|export_legacy_data_to_csv",
    re.I,
)

FIELD_SLUG_MARKER_RE = re.compile(r"（記事:field-[a-z0-9-]+）|（field-[a-z0-9-]+）")
# 編集パイプラインが残した内部参照（field-* 以外の試験ガイド slug 含む）
ARTICLE_SLUG_MARKER_RE = re.compile(r"（記事:[a-z0-9-]+）")
SLUG_PAREN_RE_CACHE: dict[str, re.Pattern[str]] = {}

USER_INTENT_TEMPLATE = re.compile(
    r"本記事を読むと、.+について、公式情報で確認すべき点と、このサイトでの学習の進め方が分かります。"
)

META_TEMPLATE = re.compile(r".+について、公式情報の確認方法と学習の進め方を整理します。")

SECTION_BOILER = re.compile(r".+について、「.+」の観点で整理します。")

FAQ_BOILER = re.compile(r".+に関する質問「.+」について、まず公式要項で最新の制度を確認してください。")

REVISION_REPLACEMENTS: list[tuple[str, str]] = [
    (r"scaffold_guide_article\.py", "ガイド記事テンプレート"),
    (r"guide_article_compose", "編集リライト"),
    (r"migrate_import_data\.py", "データ移行"),
    (r"export_legacy_data_to_csv", "レガシーデータ移行"),
]


def slug_english(slug: str) -> str:
    return slug.replace("-", " ")


def clean_revision_note(text: str) -> str:
    out = text
    for pattern, repl in REVISION_REPLACEMENTS:
        out = re.sub(pattern, repl, out, flags=re.I)
    out = re.sub(r"(専門家水準リライト（編集リライト）。\s*)+", "専門家水準リライト。 ", out)
    out = re.sub(r"\s+", " ", out).strip()
    return out


def slug_paren_marker_re(slug: str) -> re.Pattern[str]:
    if slug not in SLUG_PAREN_RE_CACHE:
        SLUG_PAREN_RE_CACHE[slug] = re.compile(rf"（{re.escape(slug)}）")
    return SLUG_PAREN_RE_CACHE[slug]


def strip_article_slug_markers(text: str, slug: str = "") -> str:
    if not text:
        return text
    out = ARTICLE_SLUG_MARKER_RE.sub("", text)
    out = FIELD_SLUG_MARKER_RE.sub("", out)
    if slug:
        out = slug_paren_marker_re(slug).sub("", out)
    out = re.sub(r"（記事:）", "", out)
    out = re.sub(r"[ \t　]{2,}", " ", out)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out


def replace_topic_phrases(text: str, slug: str, topic: str) -> str:
    if not text:
        return text
    eng = slug_english(slug)
    out = re.sub(re.escape(eng), topic, text, flags=re.I)
    broken = legacy_broken_field_topic(slug)
    if broken:
        out = out.replace(broken, topic)
    field_name = field_name_for_slug(slug)
    for eng_label in legacy_broken_field_english_variants(slug):
        out = out.replace(f"「{eng_label}」", f"「{field_name}」")
        out = out.replace(f"{eng_label}の", f"{field_name}の")
        out = out.replace(f"{eng_label}では", f"{field_name}では")
        out = out.replace(eng_label, field_name)
    out = out.replace("action_items", "行動チェックリスト")
    return strip_article_slug_markers(out, slug)


def fix_user_intent(row: dict[str, str], topic: str) -> str:
    return (
        f"本記事を読むと、{content_exam_label()}の{topic}について、"
        f"公式情報で確認すべき点と、このサイトでの学習の進め方が分かります。"
        f"読了後は行動チェックリストに沿って演習・用語確認まで進められる状態を目指します。"
    )


def fix_meta_description(row: dict[str, str], topic: str) -> str:
    return (
        f"{content_exam_label()}の{topic}について、公式情報の確認方法と学習の進め方を整理します。"
        f"受験前に押さえるべきポイントと、このサイトでの演習・用語解説の活用法を解説します。"
    )[:165]


def text_has_slug_marker(val: str, slug: str) -> bool:
    if ARTICLE_SLUG_MARKER_RE.search(val) or FIELD_SLUG_MARKER_RE.search(val):
        return True
    if slug and f"（{slug}）" in val:
        return True
    return False


def field_text_has_leak(val: str, slug: str, eng: str) -> bool:
    broken = legacy_broken_field_topic(slug)
    if (
        bool(INTERNAL_TOKEN_RE.search(val))
        or eng in val.lower()
        or (broken is not None and broken in val)
        or text_has_slug_marker(val, slug)
    ):
        return True
    for eng_label in legacy_broken_field_english_variants(slug):
        if eng_label in val:
            return True
    return bool(re.search(r"[a-z]{2,}(?:\s+[a-z]{2,})+", val))


def generic_text_has_leak(val: str, slug: str, eng: str) -> bool:
    return (
        bool(INTERNAL_TOKEN_RE.search(val))
        or eng in val.lower()
        or text_has_slug_marker(val, slug)
    )


def fix_row(row: dict[str, str]) -> bool:
    slug = (row.get("slug") or "").strip()
    if not slug:
        return False
    topic = topic_from_row(row)
    eng = slug_english(slug).lower()
    changed = False
    is_field = slug.startswith("field-")

    rev = row.get("revision_note") or ""
    cleaned_rev = clean_revision_note(rev)
    if cleaned_rev != rev:
        row["revision_note"] = cleaned_rev
        changed = True

    for col in USER_FACING:
        val = row.get(col) or ""
        if not val:
            continue

        cleaned = strip_article_slug_markers(replace_topic_phrases(val, slug, topic), slug)
        if cleaned != val:
            row[col] = cleaned
            changed = True
            val = cleaned

        has_leak = (
            field_text_has_leak(val, slug, eng)
            if is_field
            else generic_text_has_leak(val, slug, eng)
        )

        if col == "user_intent" and (has_leak or USER_INTENT_TEMPLATE.search(val)):
            new_val = fix_user_intent(row, topic)
            if new_val != val:
                row[col] = new_val
                changed = True
            continue

        if col == "meta_description" and (has_leak or META_TEMPLATE.search(val)):
            new_val = fix_meta_description(row, topic)
            if new_val != val:
                row[col] = new_val
                changed = True
            continue

        if not has_leak:
            continue

        new_val = replace_topic_phrases(val, slug, topic)

        if col.endswith("_body") and SECTION_BOILER.search(val):
            m = re.search(r"「([^」]+)」の観点", val)
            if m:
                new_val = section_body(m.group(1), topic)
        elif col.endswith("_answer") and FAQ_BOILER.search(val):
            qcol = col.replace("_answer", "_question")
            q = (row.get(qcol) or "").strip()
            if q:
                new_val = faq_answer(q, topic)

        if new_val != val:
            row[col] = new_val
            changed = True

    return changed


def load_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames or [])
        return fields, list(reader)


def save_rows(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    all_keys = list(fields)
    for row in rows:
        for key in row:
            if key not in all_keys:
                all_keys.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=all_keys, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def run(*, site_root: Path | None = None, dry_run: bool = False) -> int:
    root = site_root or ROOT
    path = root / "data" / "guide_articles.csv"
    if not path.is_file():
        print(f"missing {path}", file=sys.stderr)
        return 1

    fields, rows = load_rows(path)
    changed_rows = 0
    for row in rows:
        if fix_row(row):
            changed_rows += 1

    if dry_run:
        print(f"dry-run: would fix {changed_rows}/{len(rows)} rows in {path.name}")
        return 0

    if changed_rows:
        save_rows(path, fields, rows)
    print(f"fixed {changed_rows}/{len(rows)} rows in {path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Remove leaked internal tokens from guide CSV")
    parser.add_argument("--target", type=Path, default=ROOT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    return run(site_root=args.target.resolve(), dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
