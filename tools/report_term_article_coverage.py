#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用語CSVと glossary-article-slugs.json、eisei2 部分一致可否を突き合わせ、記事未リンク用語の件数を表示する。

  python3 tools/report_term_article_coverage.py
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_EISEI2_DEFAULT = Path.home() / "Desktop" / "eisei2shu-master"

FIRST = frozenset({"dai2shu-eisei-kanrisha", "sogo-matome-suuchi"})


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


def best_e2(term: str, slug_map: dict[str, str], e2_terms: Path) -> bool:
    if term in slug_map:
        slug = slug_map[term]
        if slug in FIRST:
            return False
        return (e2_terms / f"{slug}.html").is_file()
    for k, slug in slug_map.items():
        if slug in FIRST or len(k) < 6 or k not in term:
            continue
        if (e2_terms / f"{slug}.html").is_file():
            return True
    return False


def main() -> None:
    e2_root = _EISEI2_DEFAULT.expanduser()
    e2_map = load_eisei2_slug_map(e2_root / "docs" / "glossary-article-slugs.json")
    e2_terms = e2_root / "terms"
    e1_terms = _REPO / "terms"
    slug_path = _REPO / "docs" / "glossary-article-slugs.json"
    merged = json.loads(slug_path.read_text(encoding="utf-8"))
    if not isinstance(merged, dict):
        print("glossary-article-slugs.json がオブジェクトではありません", file=sys.stderr)
        sys.exit(1)

    rows: list[tuple[str, str]] = []
    with (_REPO / "docs/glossary-terms-checklist.csv").open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            t = (row.get("用語") or "").strip()
            if t:
                rows.append(((row.get("カテゴリ") or "").strip(), t))

    def has_file(term: str) -> bool:
        sl = merged.get(term)
        if not isinstance(sl, str):
            return False
        sl = sl.strip()
        if not sl:
            return False
        return (e1_terms / f"{sl}.html").is_file()

    linked = sum(1 for _, t in rows if has_file(t))
    e2_matchable = sum(1 for _, t in rows if not has_file(t) and best_e2(t, e2_map, e2_terms))
    no_match = len(rows) - linked - e2_matchable

    print("CSV 用語数:", len(rows))
    print("第一種 terms/ に記事HTMLがある用語（slug 解決）:", linked)
    print("記事HTMLは無いが、eisei2 の既定部分一致で取り込み可能な用語:", e2_matchable)
    print("上記以外（現状オリジナル執筆が必要な目安）:", no_match)


if __name__ == "__main__":
    main()
