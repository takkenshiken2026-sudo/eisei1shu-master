#!/usr/bin/env python3
"""
複数の urlset 形式サイトマップから <loc> を集約し、1 本の sitemap.xml に書き出す。
<lastmod> は同一 URL に複数ある場合、日付として新しい方を採用する。
"""
from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _parse_date(s: str) -> tuple[int, int, int] | None:
    s = s.strip()
    parts = s[:10].split("-")
    if len(parts) != 3:
        return None
    try:
        return int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        return None


def _newer_lastmod(a: str | None, b: str | None) -> str | None:
    if not a:
        return b
    if not b:
        return a
    da, db = _parse_date(a), _parse_date(b)
    if da and db:
        return b if db > da else a
    return b


def _collect(path: Path) -> dict[str, str | None]:
    """loc -> そのファイル内で分かる lastmod（無ければ None）"""
    try:
        tree = ET.parse(path)
    except ET.ParseError as e:
        raise SystemExit(f"XML 解析エラー {path}: {e}") from e
    root = tree.getroot()
    out: dict[str, str | None] = {}
    for el in root:
        if _local_name(el.tag) != "url":
            continue
        loc_text: str | None = None
        lastmod: str | None = None
        for child in el:
            ln = _local_name(child.tag)
            if ln == "loc" and child.text:
                loc_text = " ".join(child.text.split())
            elif ln == "lastmod" and child.text:
                lastmod = child.text.strip()
        if not loc_text:
            continue
        if loc_text in out:
            out[loc_text] = _newer_lastmod(out[loc_text], lastmod)
        else:
            out[loc_text] = lastmod
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, required=True, help="出力 sitemap.xml")
    p.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        help="マージ元の sitemap（重複 loc は統合）",
    )
    args = p.parse_args()
    merged: dict[str, str | None] = {}
    for inp in args.inputs:
        if not inp.is_file():
            print(f"merge_sitemap_xmls.py: 入力がありません: {inp}", file=sys.stderr)
            sys.exit(1)
        chunk = _collect(inp)
        for loc, lm in chunk.items():
            if loc not in merged:
                merged[loc] = lm
            else:
                merged[loc] = _newer_lastmod(merged[loc], lm)

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for loc in sorted(merged.keys()):
        lines.append("  <url>")
        lines.append(f"    <loc>{xml_escape(loc)}</loc>")
        lm = merged[loc]
        if lm:
            lines.append(f"    <lastmod>{xml_escape(lm)}</lastmod>")
        lines.append("    <changefreq>monthly</changefreq>")
        lines.append("  </url>")
    lines.append("</urlset>")
    out: Path = args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"merge_sitemap_xmls.py: {len(merged)} URLs -> {out}")


if __name__ == "__main__":
    main()
