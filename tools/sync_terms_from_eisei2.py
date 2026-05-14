#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eisei2shu-master の用語記事 HTML を第一種向けに置換し、eisei1shu-master/terms/ にコピーする。
docs/glossary-article-slugs.json に、docs/glossary-terms-checklist.csv の用語名でエントリを追加する。

マッチング:
  1) eisei2 の glossary-article-slugs.json のキーと CSV「用語」が完全一致
  2) それ以外は、CSV「用語」が eisei2 のキーを部分文字列として含み、キー長が最長のものを採用
除外スラッグ: 第二種総まとめ・第二種資格記事のみなど（FIRST_CLASS_SKIP_SLUGS）
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


def load_eisei2_slug_map(path: Path) -> dict[str, str]:
    """JSON の重複キーは最後の値が勝つが、ここではファイルを素解析して先勝ちにする。"""
    text = path.read_text(encoding="utf-8")
    pairs = re.findall(r'"((?:\\.|[^"\\])*)"\s*:\s*"((?:\\.|[^"\\])*)"', text)
    out: dict[str, str] = {}
    for raw_k, raw_v in pairs:
        k = json.loads('"' + raw_k + '"')
        v = json.loads('"' + raw_v + '"')
        if k not in out:
            out[k] = v
    return out


def transform_html(html: str) -> str:
    s = html
    s = s.replace("第二種衛生管理者試験", "第一種衛生管理者試験")
    s = s.replace("二衛マスター", "一衛マスター")
    s = s.replace("https://dai2shu-eisei.example", "https://eisei1shu-master.jp")
    s = s.replace('"name": "第二種衛生管理者"', '"name": "第一種衛生管理者"')
    s = s.replace("第二種衛生管理者", "第一種衛生管理者")
    return s


def best_eisei2_key(term: str, slug_map: dict[str, str], e2_terms: Path) -> str | None:
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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--eisei2-root",
        type=Path,
        default=_EISEI2_DEFAULT,
        help="eisei2shu-master のルート（既定: ~/Desktop/eisei2shu-master）",
    )
    ap.add_argument("--dry-run", action="store_true", help="書き込まず件数のみ表示")
    args = ap.parse_args()

    e2_root: Path = args.eisei2_root.expanduser()
    e2_slug_path = e2_root / "docs" / "glossary-article-slugs.json"
    e2_terms = e2_root / "terms"
    if not e2_slug_path.is_file():
        print(f"見つかりません: {e2_slug_path}", file=sys.stderr)
        sys.exit(1)

    slug_map = load_eisei2_slug_map(e2_slug_path)
    csv_path = _REPO / "docs" / "glossary-terms-checklist.csv"
    rows: list[tuple[str, str]] = []
    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            cat = (row.get("カテゴリ") or "").strip()
            term = (row.get("用語") or "").strip()
            if term:
                rows.append((cat, term))

    term_to_slug: dict[str, str] = {}
    slug_sources: dict[str, set[str]] = {}
    for _cat, term in rows:
        k2 = best_eisei2_key(term, slug_map, e2_terms)
        if not k2:
            continue
        slug = slug_map[k2]
        term_to_slug[term] = slug
        slug_sources.setdefault(slug, set()).add(term)

    slug_json_path = _REPO / "docs" / "glossary-article-slugs.json"
    existing = json.loads(slug_json_path.read_text(encoding="utf-8"))
    if not isinstance(existing, dict):
        print("glossary-article-slugs.json がオブジェクト形式ではありません", file=sys.stderr)
        sys.exit(1)

    out_terms_dir = _REPO / "terms"
    out_terms_dir.mkdir(parents=True, exist_ok=True)

    written = 0
    for slug in sorted(slug_sources.keys()):
        src = e2_terms / f"{slug}.html"
        dst = out_terms_dir / f"{slug}.html"
        body = transform_html(src.read_text(encoding="utf-8"))
        if not args.dry_run:
            dst.write_text(body, encoding="utf-8")
        written += 1

    merged = dict(existing)
    for term, slug in term_to_slug.items():
        merged[term] = slug

    if not args.dry_run:
        slug_json_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"用語→スラッグ: {len(term_to_slug)} 件")
    print(f"ユニーク HTML: {written} 本（eisei2 から変換）")
    if args.dry_run:
        print("(dry-run: ファイル未更新)")


if __name__ == "__main__":
    main()
