#!/usr/bin/env python3
"""
terms/*.html から SEO 用の中間サイトマップを生成する（prepare_public_site で sitemap.xml にマージ）。
eisei-articles/dist/sitemap.xml はホストがプレースホルダのため、そのままコピーしないでください。
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--terms-dir", type=Path, required=True, help="公開用 terms ディレクトリ（*.html）")
    p.add_argument("--out", type=Path, required=True, help="出力する sitemap-terms.xml のパス")
    p.add_argument(
        "--base",
        default="https://eisei1shu-master.jp",
        help="絶対 URL のオリジン（末尾スラッシュなし）",
    )
    args = p.parse_args()
    terms_dir: Path = args.terms_dir
    out: Path = args.out
    base = str(args.base).rstrip("/")

    if not terms_dir.is_dir():
        raise SystemExit(f"terms-dir がディレクトリではありません: {terms_dir}")

    files = sorted(terms_dir.glob("*.html"))
    if not files:
        raise SystemExit(f"*.html がありません: {terms_dir}")

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for f in files:
        slug = f.name
        loc = f"{base}/terms/{slug}"
        try:
            mtime = dt.datetime.fromtimestamp(f.stat().st_mtime, tz=dt.timezone.utc)
            lastmod = mtime.date().isoformat()
        except OSError:
            lastmod = dt.date.today().isoformat()
        lines.append("  <url>")
        lines.append(f"    <loc>{html.escape(loc)}</loc>")
        lines.append(f"    <lastmod>{lastmod}</lastmod>")
        lines.append("    <changefreq>monthly</changefreq>")
        lines.append("    <priority>0.7</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"generate_terms_sitemap.py: {len(files)} URLs -> {out}")


if __name__ == "__main__":
    main()
