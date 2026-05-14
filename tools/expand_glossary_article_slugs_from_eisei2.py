#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eisei2 の glossary-article-slugs と用語CSVを照合し、eisei1 の docs/glossary-article-slugs.json に
「現行の部分一致（キー6文字以上）では付かないが、eisei2 記事HTMLが存在し、かつ最長キーが一意に決まる」
用語→スラッグだけを追記する（既存キーは上書きしない）。

推奨フロー:
  python3 tools/expand_glossary_article_slugs_from_eisei2.py --dry-run
  python3 tools/expand_glossary_article_slugs_from_eisei2.py
  python3 tools/sync_terms_from_eisei2.py
  python3 tools/glossary_csv_to_embed_js.py
  bash tools/prepare_public_site.sh
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_EISEI2_DEFAULT = Path.home() / "Desktop" / "eisei2shu-master"

FIRST_CLASS_SKIP_SLUGS = frozenset(
    {
        "dai2shu-eisei-kanrisha",
        "sogo-matome-suuchi",
    }
)

# 一意マッチで誤爆しやすいスラッグ（拡張候補から除外）
DEFAULT_BLOCK_SLUGS_FOR_UNIQUE = frozenset(
    {
        "sagyoshunin-sha",
        "eisei-kanrisha",
    }
)

CAT_ORDER = (
    "関係法令（有害業務）",
    "関係法令（有害以外）",
    "労働衛生（有害業務）",
    "労働衛生（有害以外）",
    "労働生理",
    "",
)


def load_eisei2_slug_map(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    pairs = re.findall(r'"((?:\\.|[^"\\])*)"\s*:\s*"((?:\\.|[^"\\])*)"', text)
    out: dict[str, str] = {}
    for raw_k, raw_v in pairs:
        k = json.loads('"' + raw_k + '"')
        v = json.loads('"' + raw_v + '"')
        if k not in out:
            out[k] = v
    return out


def best_eisei2_key_default(term: str, slug_map: dict[str, str], e2_terms: Path) -> str | None:
    """sync_terms_from_eisei2.py と同じ（キー6文字以上の最長一致）。"""
    if term in slug_map:
        slug = slug_map[term]
        if slug in FIRST_CLASS_SKIP_SLUGS:
            return None
        if (e2_terms / f"{slug}.html").is_file():
            return term
    best_k: str | None = None
    best_len = -1
    for k, slug in slug_map.items():
        if slug in FIRST_CLASS_SKIP_SLUGS:
            continue
        if len(k) < 6:
            continue
        if k not in term:
            continue
        if not (e2_terms / f"{slug}.html").is_file():
            continue
        if len(k) > best_len:
            best_len = len(k)
            best_k = k
    return best_k


def unique_longest_key(
    term: str,
    slug_map: dict[str, str],
    e2_terms: Path,
    min_key_len: int,
    block_slugs: frozenset[str],
) -> tuple[str, str] | None:
    """用語文字列に含まれる eisei2 キーのうち最長が一意なら (キー, スラッグ) を返す。"""
    cands: list[tuple[int, str, str]] = []
    for k, slug in slug_map.items():
        if slug in FIRST_CLASS_SKIP_SLUGS or slug in block_slugs:
            continue
        if len(k) < min_key_len:
            continue
        if k not in term:
            continue
        if not (e2_terms / f"{slug}.html").is_file():
            continue
        cands.append((len(k), k, slug))
    if not cands:
        return None
    m = max(c[0] for c in cands)
    tops = [c for c in cands if c[0] == m]
    if len(tops) != 1:
        return None
    return tops[0][1], tops[0][2]


def existing_slug_resolves(term: str, existing: dict, e2_terms: Path) -> bool:
    sl = existing.get(term)
    if not isinstance(sl, str):
        return False
    sl = sl.strip()
    if not sl or sl in FIRST_CLASS_SKIP_SLUGS:
        return False
    return (e2_terms / f"{sl}.html").is_file()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--eisei2-root",
        type=Path,
        default=_EISEI2_DEFAULT,
        help="eisei2shu-master のルート（既定: ~/Desktop/eisei2shu-master）",
    )
    ap.add_argument(
        "--min-unique-key-len",
        type=int,
        default=5,
        help="一意最長マッチに使う eisei2 キーの最小文字数（既定: 5）",
    )
    ap.add_argument(
        "--block-slugs",
        type=str,
        default=",".join(sorted(DEFAULT_BLOCK_SLUGS_FOR_UNIQUE)),
        help="一意マッチから除外するスラッグ（カンマ区切り。空で除外なし）",
    )
    ap.add_argument("--dry-run", action="store_true", help="JSON を書き換えず候補のみ表示")
    args = ap.parse_args()

    block_slugs: frozenset[str] = frozenset()
    if (args.block_slugs or "").strip():
        block_slugs = frozenset(s.strip() for s in args.block_slugs.split(",") if s.strip())

    e2_root = args.eisei2_root.expanduser()
    e2_slug_path = e2_root / "docs" / "glossary-article-slugs.json"
    e2_terms = e2_root / "terms"
    if not e2_slug_path.is_file():
        print(f"見つかりません: {e2_slug_path}", file=sys.stderr)
        sys.exit(1)

    slug_map = load_eisei2_slug_map(e2_slug_path)
    csv_path = _REPO / "docs/glossary-terms-checklist.csv"
    slug_json_path = _REPO / "docs/glossary-article-slugs.json"
    existing = json.loads(slug_json_path.read_text(encoding="utf-8"))
    if not isinstance(existing, dict):
        print("glossary-article-slugs.json がオブジェクト形式ではありません", file=sys.stderr)
        sys.exit(1)

    rows: list[tuple[str, str]] = []
    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            cat = (row.get("カテゴリ") or "").strip()
            term = (row.get("用語") or "").strip()
            if term:
                rows.append((cat, term))

    def cat_key(cat: str) -> tuple[int, str]:
        try:
            return (CAT_ORDER.index(cat), cat)
        except ValueError:
            return (len(CAT_ORDER), cat)

    proposals: list[tuple[str, str, str, str]] = []
    for cat, term in sorted(rows, key=lambda r: (cat_key(r[0]), r[1])):
        if existing_slug_resolves(term, existing, e2_terms):
            continue
        if best_eisei2_key_default(term, slug_map, e2_terms):
            continue
        u = unique_longest_key(term, slug_map, e2_terms, args.min_unique_key_len, block_slugs)
        if not u:
            continue
        _k, slug = u
        if "パワ" in term and slug == "eisei-iinkai":
            continue
        proposals.append((cat, term, slug, u[0]))

    print(f"新規追提案: {len(proposals)} 件（min_unique_key_len={args.min_unique_key_len}）")
    for cat, term, slug, k in proposals[:40]:
        print(f"  [{cat}] {term!r} -> {slug}.html (key={k!r})")
    if len(proposals) > 40:
        print(f"  … 他 {len(proposals) - 40} 件")

    if args.dry_run:
        print("(dry-run: glossary-article-slugs.json は未更新)")
        return

    merged = dict(existing)
    added = 0
    for cat, term, slug, _k in proposals:
        if term in merged:
            continue
        merged[term] = slug
        added += 1
    slug_json_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"glossary-article-slugs.json に追加: {added} 件 -> {slug_json_path}")


if __name__ == "__main__":
    main()
