#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docs/eisei1_ichimon_itto.csv から
  - SEO 用の静的ページ ichimon/（個別 URL）
  - アプリ用 eisei1-data-ichimon.js（ICHI_MON_ROWS）
  - sitemap-ichimon.xml
を生成する。

例:
  python3 tools/build_ichimon_pages.py
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import html
import json
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

SUBJECT_TO_FIELD: dict[str, str] = {
    "関係法令(有害業務に係るもの)": "law",
    "関係法令(有害業務に係るもの以外のもの)": "law",
    "労働衛生(有害業務に係るもの)": "rights",
    "労働衛生(有害業務に係るもの以外のもの)": "rights",
    "労働生理": "limit",
}

FIELD_LABEL_JA = {"law": "関係法令", "rights": "労働衛生", "limit": "労働生理"}


def load_rows(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8-sig")
    return list(csv.DictReader(text.splitlines()))


def slug_for_id(stable_id: str) -> str:
    d = hashlib.sha256(stable_id.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(d).decode("ascii").rstrip("=")


def meta_description(text: str, limit: int = 155) -> str:
    one = re.sub(r"\s+", " ", text).strip()
    if len(one) <= limit:
        return one
    return one[: limit - 1] + "…"


def public_url(base_url: str, site_prefix: str, rel_path: str) -> str:
    base = base_url.rstrip("/")
    pfx = (site_prefix or "").strip("/").strip()
    rel_path = rel_path.lstrip("/")
    if pfx:
        return f"{base}/{pfx}/{rel_path}"
    return f"{base}/{rel_path}"


def rel_to_root_from_ichimon_s(rel_file: Path) -> str:
    """ichimon/s/x.html → ../../index.html"""
    depth = len(rel_file.parent.parts)
    return "/".join([".."] * depth) + "/index.html"


def rel_to_site_css(rel_file: Path) -> str:
    depth = len(rel_file.parent.parts)
    return "/".join([".."] * depth) + "/site-pages.css"


def build_detail_html(
    *,
    slug: str,
    js_id: str,
    field: str,
    subject_ja: str,
    statement: str,
    correct_maru: bool,
    exp: str,
    canonical: str,
    rel_path: Path,
    prev_slug: str | None,
    next_slug: str | None,
    title_mid: str,
    top_page_url: str,
    hub_canonical: str,
) -> str:
    root_idx = rel_to_root_from_ichimon_s(rel_path)
    css_href = rel_to_site_css(rel_path)
    hub_rel = "/".join([".."] * len(rel_path.parent.parts)) + "/ichimon/index.html"

    title = f"{title_mid}｜一衛マスター（第一種衛生管理者試験）"
    desc = meta_description(statement)
    stem_html = html.escape(statement).replace("\n", "<br>\n")
    exp_html = html.escape(exp).replace("\n", "<br>\n")
    ans_line = (
        "この記述は<strong>正しい</strong>ため、正答は<strong>○</strong>です。"
        if correct_maru
        else "この記述は<strong>誤り</strong>とされるため、正答は<strong>×</strong>です。"
    )

    nav_prev = ""
    if prev_slug:
        nav_prev = f'<a class="ichi-nav-prev" href="{html.escape(prev_slug)}.html">← 前</a>'
    nav_next = ""
    if next_slug:
        nav_next = f'<a class="ichi-nav-next" href="{html.escape(next_slug)}.html">次 →</a>'

    json_ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "@id": canonical + "#webpage",
                "url": canonical,
                "name": title,
                "description": desc,
                "inLanguage": "ja-JP",
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": 1,
                        "name": "トップ",
                        "item": top_page_url,
                    },
                    {
                        "@type": "ListItem",
                        "position": 2,
                        "name": "一問一答一覧",
                        "item": hub_canonical,
                    },
                    {"@type": "ListItem", "position": 3, "name": title_mid},
                ],
            },
        ],
    }

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{html.escape(canonical)}">
<meta property="og:type" content="article">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{html.escape(canonical)}">
<meta name="twitter:card" content="summary">
<script defer src="/site-analytics.js"></script>
<link rel="stylesheet" href="{html.escape(css_href)}">
<script type="application/ld+json">
{json.dumps(json_ld, ensure_ascii=False, indent=2)}
</script>
</head>
<body class="q-static-body">
<header class="q-static-header">
  <p class="q-static-brand"><a href="{html.escape(root_idx)}">一衛マスター</a>（第一種衛生管理者試験）</p>
  <nav aria-label="パンくず">
    <ol class="q-breadcrumb">
      <li><a href="{html.escape(root_idx)}">トップ</a></li>
      <li><a href="{html.escape(hub_rel)}">一問一答一覧</a></li>
      <li aria-current="page">{html.escape(title_mid)}</li>
    </ol>
  </nav>
</header>
<main class="q-static-main">
  <p class="q-meta"><span class="q-id">ID: <code>{html.escape(js_id)}</code></span> · <span>{html.escape(FIELD_LABEL_JA[field])}</span> · <span>{html.escape(subject_ja)}</span></p>
  <h1 class="q-h1">{html.escape(title_mid)}</h1>
  <p class="ichi-nav-row">{nav_prev}{nav_next}</p>
  <section class="q-block" aria-labelledby="ichi-stem-h">
    <h2 id="ichi-stem-h" class="q-h2">問題（○×の一文）</h2>
    <div class="q-stem">{stem_html}</div>
  </section>
  <section class="q-block q-answer" aria-labelledby="ichi-ans-h">
    <h2 id="ichi-ans-h" class="q-h2">正答</h2>
    <p>{ans_line}</p>
  </section>
  <section class="q-block" aria-labelledby="ichi-exp-h">
    <h2 id="ichi-exp-h" class="q-h2">解説</h2>
    <div class="q-exp">{exp_html}</div>
  </section>
  <p class="q-app-link"><a href="{html.escape(root_idx)}#ichimondou">アプリで一問一答を演習する</a></p>
</main>
<footer class="q-static-footer">
  <p><small>学習用サンプル。出題・法令の最新情報は公式で確認してください。</small></p>
</footer>
</body>
</html>
"""


def write_hub(
    hub_path: Path,
    grouped: dict[str, list[tuple[str, str, str]]],
    base_url: str,
    site_prefix: str,
    total: int,
) -> None:
    hub_rel = Path("ichimon/index.html")
    root_idx = rel_to_root_from_ichimon_s(hub_rel)
    css_href = rel_to_site_css(hub_rel)
    canonical = public_url(base_url, site_prefix, "ichimon/")

    meta_desc = (
        f"第一種衛生管理者試験向けの一問一答（○×）を静的ページとして掲載しています。全{total}件。"
        " 検索・共有に使える個別URLです。"
    )

    sections: list[str] = []
    for subj, items in grouped.items():
        lis = []
        for title_anchor, slug, _js_id in items:
            href = f"s/{html.escape(slug)}.html"
            lis.append(f'      <li><a href="{href}">{html.escape(title_anchor)}</a></li>')
        sections.append(
            f'  <section class="q-block" aria-labelledby="{html.escape(slugify_heading_id(subj))}">\n'
            f'    <h2 id="{html.escape(slugify_heading_id(subj))}" class="q-h2">{html.escape(subj)}（{len(items)}件）</h2>\n'
            f"    <ul class=\"ichi-hub-ul\">\n" + "\n".join(lis) + "\n    </ul>\n  </section>"
        )

    body = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>一問一答一覧（静的ページ）｜一衛マスター</title>
<meta name="description" content="{html.escape(meta_desc)}">
<link rel="canonical" href="{html.escape(canonical)}">
<script defer src="/site-analytics.js"></script>
<link rel="stylesheet" href="{html.escape(css_href)}">
</head>
<body class="q-static-body">
<header class="q-static-header">
  <p class="q-static-brand"><a href="{html.escape(root_idx)}">一衛マスター</a>（第一種衛生管理者試験）</p>
  <nav aria-label="パンくず">
    <ol class="q-breadcrumb">
      <li><a href="{html.escape(root_idx)}">トップ</a></li>
      <li aria-current="page">一問一答一覧</li>
    </ol>
  </nav>
</header>
<main class="q-static-main">
  <h1 class="q-h1">一問一答一覧（静的）</h1>
  <p>CSV 正本に基づく一問一答 <strong>{total}</strong> 件の個別ページです。各ページに問題文・正答・解説を記載しています。</p>
  <p class="q-app-link"><a href="{html.escape(root_idx)}#ichimondou">学習アプリで一問一答を開始</a></p>
{chr(10).join(sections)}
</main>
<footer class="q-static-footer">
  <p><small>学習用サンプル。出題・法令の最新情報は公式で確認してください。</small></p>
  <p><small><a href="/sitemap-ichimon.xml">サイトマップ（一問一答のみ）</a></small></p>
</footer>
</body>
</html>
"""
    hub_path.write_text(body, encoding="utf-8")


def slugify_heading_id(subj: str) -> str:
    h = hashlib.sha256(subj.encode("utf-8")).hexdigest()[:12]
    return f"sec-{h}"


def main() -> None:
    ap = argparse.ArgumentParser(description="一問一答 CSV から ichimon/ と JS を生成")
    ap.add_argument(
        "--base-url",
        default="https://eisei1shu-master.jp",
        help="canonical / sitemap 用",
    )
    ap.add_argument("--site-prefix", default="", help="GitHub Pages プロジェクトサイト時")
    ap.add_argument(
        "--csv",
        type=Path,
        default=None,
        help="既定: docs/eisei1_ichimon_itto.csv",
    )
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    csv_path = args.csv or (repo_root / "docs" / "eisei1_ichimon_itto.csv")
    if not csv_path.exists():
        print(f"CSV が見つかりません: {csv_path}", file=sys.stderr)
        sys.exit(1)

    rows = load_rows(csv_path)
    base_url = args.base_url.rstrip("/")
    site_prefix = args.site_prefix.strip("/").strip()

    ichimon_root = repo_root / "ichimon"
    s_dir = ichimon_root / "s"
    if ichimon_root.exists():
        shutil.rmtree(ichimon_root)
    s_dir.mkdir(parents=True)

    parsed: list[dict] = []
    for i, row in enumerate(rows):
        sid = (row.get("id") or "").strip()
        if not sid:
            print(f"id 欠落 行 {i + 2}", file=sys.stderr)
            sys.exit(1)
        subject = (row.get("科目") or "").strip()
        field = SUBJECT_TO_FIELD.get(subject)
        if not field:
            print(f"不明な科目: {subject!r} 行 {i + 2}", file=sys.stderr)
            sys.exit(1)
        statement = (row.get("問題") or "").strip()
        if not statement:
            print(f"問題 欠落 行 {i + 2}", file=sys.stderr)
            sys.exit(1)
        raw_ans = (row.get("答え") or "").strip()
        if raw_ans == "○":
            correct_maru = True
        elif raw_ans == "×":
            correct_maru = False
        else:
            print(f"答えが ○/× 以外: {raw_ans!r} 行 {i + 2}", file=sys.stderr)
            sys.exit(1)
        exp = (row.get("解説") or "").strip()
        year = (row.get("開催年数") or "").strip()
        month = (row.get("開催月") or "").strip()
        qn = (row.get("元問番号") or "").strip()
        slug = slug_for_id(sid)
        js_id = f"ichi_{slug}"
        title_mid = f"{year}・{month}・{FIELD_LABEL_JA[field]} 問{qn}（一問一答）"
        parsed.append(
            {
                "stable_id": sid,
                "slug": slug,
                "js_id": js_id,
                "field": field,
                "subject_ja": subject,
                "statement": statement,
                "correctAnswer": correct_maru,
                "exp": exp,
                "year": year,
                "month": month,
                "qn": qn,
                "title_mid": title_mid,
            }
        )

    sitemap_urls: list[str] = []
    sitemap_urls.append(public_url(base_url, site_prefix, "ichimon/"))

    js_payload: list[dict] = []
    grouped: dict[str, list[tuple[str, str, str]]] = defaultdict(list)

    top_page_url = public_url(base_url, site_prefix, "index.html")
    hub_canonical = public_url(base_url, site_prefix, "ichimon/")

    n = len(parsed)
    for i, p in enumerate(parsed):
        slug = p["slug"]
        prev_slug = parsed[i - 1]["slug"] if i > 0 else None
        next_slug = parsed[i + 1]["slug"] if i + 1 < n else None
        rel_path = Path("ichimon") / "s" / f"{slug}.html"
        canonical = public_url(base_url, site_prefix, f"ichimon/s/{slug}.html")
        sitemap_urls.append(canonical)

        title_anchor = meta_description(p["statement"], 72)
        grouped[p["subject_ja"]].append((title_anchor, slug, p["js_id"]))

        html_body = build_detail_html(
            slug=slug,
            js_id=p["js_id"],
            field=p["field"],
            subject_ja=p["subject_ja"],
            statement=p["statement"],
            correct_maru=p["correctAnswer"],
            exp=p["exp"],
            canonical=canonical,
            rel_path=rel_path,
            prev_slug=prev_slug,
            next_slug=next_slug,
            title_mid=p["title_mid"],
            top_page_url=top_page_url,
            hub_canonical=hub_canonical,
        )
        (s_dir / f"{slug}.html").write_text(html_body, encoding="utf-8")

        js_payload.append(
            {
                "id": p["js_id"],
                "slug": slug,
                "field": p["field"],
                "subjectJa": p["subject_ja"],
                "statement": p["statement"],
                "correctAnswer": p["correctAnswer"],
                "exp": p["exp"],
                "publicPath": f"/ichimon/s/{slug}.html",
            }
        )

    write_hub(ichimon_root / "index.html", grouped, base_url, site_prefix, len(parsed))

    js_path = repo_root / "eisei1-data-ichimon.js"
    js_path.write_text(
        "/* Auto-generated by tools/build_ichimon_pages.py — do not edit by hand */\n"
        "window.ICHI_MON_ROWS = "
        + json.dumps(js_payload, ensure_ascii=False)
        + ";\n",
        encoding="utf-8",
    )

    sm_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for u in sorted(set(sitemap_urls)):
        sm_lines.append("  <url>")
        sm_lines.append(f"    <loc>{xml_escape(u)}</loc>")
        sm_lines.append("    <changefreq>monthly</changefreq>")
        sm_lines.append("  </url>")
    sm_lines.append("</urlset>")
    (repo_root / "sitemap-ichimon.xml").write_text("\n".join(sm_lines) + "\n", encoding="utf-8")

    print(f"ichimon: {n} 件 + index.html + {js_path.name} + sitemap-ichimon.xml → {ichimon_root}")


if __name__ == "__main__":
    main()
