#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV から SEO 用の静的問題ページ（docs/question-id-url-slug-spec.md）を生成する。

使用例:
  python3 tools/build_question_pages.py
  python3 tools/build_question_pages.py --base-url https://example.github.io/repo --site-prefix repo

出力:
  - q/past/.../index.html, q/orig/.../index.html
  - q/index.html（過去問一覧ハブ）
  - リポジトリ直下の sitemap.xml（トップ・固定ページ・q 配下。一問一答・用語は prepare で統合）
  - リポジトリ直下の robots.txt（Sitemap 行を上記に合わせて更新）
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import shutil
import sys
from xml.sax.saxutils import escape as xml_escape
from collections import defaultdict
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent

FORM_URL_EISEI = "https://forms.gle/3pD7fZ8TdppzAWR37"
SITE_COPYRIGHT_EISEI = "© 2026 一衛マスター"
SESSION_ORDER = ("cat90", "zenki", "koki", "apr", "oct")
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from question_slug_lib import (
    FIELD_MAP,
    era_slug_past,
    normalize_era,
    question_string_id_orig,
    question_string_id_past,
    relative_url_path_orig,
    relative_url_path_past,
    session_or_pool_slug,
)

FIELD_LABEL_JA = {"law": "関係法令", "rights": "労働衛生", "limit": "労働生理"}


def load_rows(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8-sig")
    return list(csv.DictReader(text.splitlines()))


def parse_row(row: dict, line_no: int) -> dict:
    科目 = (row.get("科目") or "").strip()
    field = FIELD_MAP.get(科目)
    if not field:
        raise ValueError(f"不明な科目: {科目!r}")

    era_raw = (row.get("開催年数") or "").strip()
    era_n = normalize_era(era_raw)
    is_orig = era_n == "オリジナル"

    month_raw = (row.get("開催月") or "").strip()
    sp = session_or_pool_slug(era_raw, month_raw)

    num = int(str(row.get("問番号") or "").strip())

    opts = [(row.get(f"({i})") or "").strip() for i in range(1, 6)]
    if not all(opts):
        raise ValueError("選択肢欠け")

    raw_ans = str(row.get("正答番号") or "").strip()
    if not raw_ans:
        raise ValueError("正答番号なし")
    ans1 = int(raw_ans)
    if not (1 <= ans1 <= 5):
        raise ValueError(f"正答番号が1〜5以外: {ans1}")

    text_q = (row.get("問") or "").strip()
    if not text_q:
        raise ValueError("問題文なし")

    exp_raw = (row.get("解説") or "").strip()
    exp = exp_raw if exp_raw else f"正解は選択肢{ans1}。解説テキストは CSV で未入力です。"

    if is_orig:
        era_slug = None
        group_key = ("orig", sp, field)
    else:
        era_slug = era_slug_past(era_raw)
        group_key = ("past", era_slug, sp, field)

    return {
        "is_orig": is_orig,
        "era_raw": era_raw,
        "era_n": era_n,
        "month_raw": month_raw,
        "session_or_pool": sp,
        "era_slug": era_slug,
        "field": field,
        "num": num,
        "text": text_q,
        "opts": opts,
        "ans_index0": ans1 - 1,
        "ans_display": str(ans1),
        "exp": exp,
        "group_key": group_key,
        "line_no": line_no,
    }


def compute_widths(rows: list[dict]) -> dict[tuple, int]:
    nums: dict[tuple, list[int]] = defaultdict(list)
    for r in rows:
        nums[r["group_key"]].append(r["num"])
    widths: dict[tuple, int] = {}
    for k, ns in nums.items():
        mx = max(ns)
        widths[k] = 3 if mx >= 100 else 2
    return widths


def format_qwidth(num: int, width: int) -> str:
    return str(num).zfill(width)


def rel_to_root_index(rel_file: Path) -> str:
    """q/past/r07/koki/law/03/index.html → ../../../../../../index.html"""
    depth = len(rel_file.parent.parts)
    if depth == 0:
        return "index.html"
    return "/".join([".."] * depth) + "/index.html"


def rel_to_site_css(rel_file: Path) -> str:
    depth = len(rel_file.parent.parts)
    if depth == 0:
        return "site-pages.css"
    return "/".join([".."] * depth) + "/site-pages.css"


def site_depth_to_root(rel_file: Path) -> int:
    return len(rel_file.parent.parts)


def href_repo_root(rel_file: Path, filename: str) -> str:
    d = site_depth_to_root(rel_file)
    if d == 0:
        return filename
    return "/".join([".."] * d) + "/" + filename


def href_q_index(rel_file: Path) -> str:
    """リポジトリ直下の q/index.html（過去問一覧）への相対パス。"""
    parts_n = len(rel_file.parent.parts)
    if parts_n <= 1:
        return "index.html"
    return "/".join([".."] * (parts_n - 1)) + "/index.html"


def render_static_q_footer(rel_file: Path, *, current_q_index: bool = False) -> str:
    cur = ' aria-current="page"' if current_q_index else ""

    def esc_href(dest: str) -> str:
        return html.escape(href_repo_root(rel_file, dest))

    return f"""<footer class="q-static-footer">
  <nav class="q-static-footer-nav" aria-label="サイトの他ページ">
    <a href="{esc_href("index.html")}">トップ</a>
    <a href="{esc_href("about.html")}">このサイトについて</a>
    <a href="{html.escape(href_q_index(rel_file))}"{cur}>過去問一覧</a>
    <a href="{esc_href("terms/index.html")}">用語集</a>
    <a href="{esc_href("articles/index.html")}">試験ガイド</a>
    <a href="{esc_href("related-sites.html")}">関連リンク</a>
    <a href="{esc_href("privacy-terms.html")}">プライバシー</a>
    <a href="{html.escape(FORM_URL_EISEI)}" target="_blank" rel="noopener noreferrer">お問い合わせ</a>
  </nav>
  <p><small>学習用サンプル。出題・法令の最新情報は公式で確認してください。</small></p>
  <p><small>{html.escape(SITE_COPYRIGHT_EISEI)}</small></p>
</footer>"""


def era_sort_tuple(era_slug: str) -> tuple[int, int]:
    if not era_slug:
        return (99, 0)
    kind = era_slug[0].lower()
    try:
        n = int(era_slug[1:])
    except ValueError:
        return (99, 0)
    if kind == "s":
        return (0, n)
    if kind == "h":
        return (1, n)
    if kind == "r":
        return (2, n)
    return (99, 0)


def session_sort_tuple(session: str) -> tuple[int, str]:
    if session in SESSION_ORDER:
        return (SESSION_ORDER.index(session), session)
    return (len(SESSION_ORDER), session)


def href_past_question_from_q_index(r: dict) -> str:
    rel = Path(
        relative_url_path_past(
            r["era_slug"], r["session_or_pool"], r["field"], r["qwidth"]
        )
    )
    return "/".join(rel.parts[1:])


def build_past_list_sections(parsed_rows: list[dict]) -> str:
    """q/index.html 本文: 開催回ごと・科目別の過去問リンク。"""
    past = [r for r in parsed_rows if not r["is_orig"]]
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in past:
        groups[(r["era_slug"], r["session_or_pool"])].append(r)
    sorted_keys = sorted(
        groups.keys(),
        key=lambda k: (era_sort_tuple(k[0]), session_sort_tuple(k[1])),
    )
    sections: list[str] = []
    field_order = ("law", "rights", "limit")
    for era_slug, session in sorted_keys:
        rows = groups[(era_slug, session)]
        sample = rows[0]
        heading = breadcrumb_label_past(sample["era_raw"], sample["month_raw"])
        sid = f"{html.escape(era_slug)}-{html.escape(session)}"
        subblocks: list[str] = []
        for fk in field_order:
            sub = [r for r in rows if r["field"] == fk]
            if not sub:
                continue
            sub.sort(key=lambda x: x["num"])
            label_ja = FIELD_LABEL_JA[fk]
            lis = "".join(
                f'<li><a href="{html.escape(href_past_question_from_q_index(r))}">第{r["num"]}問</a></li>'
                for r in sub
            )
            subblocks.append(
                f'<section class="q-session-field" aria-labelledby="sf-{sid}-{fk}">'
                f'<h3 id="sf-{sid}-{fk}" class="q-field-subhead">{html.escape(label_ja)}</h3>'
                f'<ol class="q-year-list">{lis}</ol></section>'
            )
        inner = "".join(subblocks)
        sections.append(
            f'<section class="glos-cat-section q-year-section" aria-labelledby="sess-{sid}">'
            f'<h2 id="sess-{sid}" class="glos-cat-heading glos-cat-heading--ja">{html.escape(heading)}</h2>'
            f"{inner}</section>"
        )
    return "\n".join(sections) if sections else "<p>過去問の静的ページがありません。</p>"


def public_url(base_url: str, site_prefix: str, rel_path: str) -> str:
    """相対パス rel_path（例 q/past/.../ または index.html）→ 絶対URL"""
    base = base_url.rstrip("/")
    pfx = (site_prefix or "").strip("/").strip()
    rel_path = rel_path.lstrip("/")
    if pfx:
        return f"{base}/{pfx}/{rel_path}"
    return f"{base}/{rel_path}"


def meta_description(text: str, limit: int = 155) -> str:
    one = re.sub(r"\s+", " ", text).strip()
    if len(one) <= limit:
        return one
    return one[: limit - 1] + "…"


def breadcrumb_label_past(era_raw: str, month_raw: str) -> str:
    e = (era_raw or "").strip()
    m = (month_raw or "").strip()
    if m:
        return f"{e}・{m}"
    return e


def build_question_html(page: dict, rel_path: Path) -> str:
    is_orig = page["is_orig"]
    field = page["field"]
    field_ja = FIELD_LABEL_JA[field]
    qwidth = page["qwidth"]
    num = page["num"]
    base_url = page["base_url"].rstrip("/")
    site_prefix = page["site_prefix"].strip("/").strip()

    if is_orig:
        qid = question_string_id_orig(page["session_or_pool"], field, qwidth)
        title_mid = f"オリジナル・{field_ja} 第{num}問"
    else:
        era_slug = page["era_slug"]
        sp = page["session_or_pool"]
        qid = question_string_id_past(era_slug, sp, field, qwidth)
        title_mid = f"{breadcrumb_label_past(page['era_raw'], page['month_raw'])}・{field_ja} 第{num}問"

    title = f"{title_mid}｜一衛マスター（第一種衛生管理者試験）"
    desc = meta_description(page["text"])
    canonical = page["canonical"]

    root_idx = rel_to_root_index(rel_path)
    q_hub_idx = href_q_index(rel_path)
    css_href = rel_to_site_css(rel_path)

    opts_html = "".join(
        f'<li class="q-opt"><span class="q-opt-num">（{i}）</span> {html.escape(o)}</li>'
        for i, o in enumerate(page["opts"], start=1)
    )

    def full_site_url(path_after_root: str) -> str:
        path_after_root = path_after_root.lstrip("/")
        if site_prefix:
            return f"{base_url}/{site_prefix}/{path_after_root}"
        return f"{base_url}/{path_after_root}"

    if is_orig:
        crumbs_nav = [("トップ", root_idx)]
        ld_items = [
            {"@type": "ListItem", "position": 1, "name": "トップ", "item": full_site_url("index.html")},
            {
                "@type": "ListItem",
                "position": 2,
                "name": title_mid,
                "item": canonical,
            },
        ]
    else:
        crumbs_nav = [
            ("トップ", root_idx),
            ("過去問一覧", q_hub_idx),
        ]
        hub_item_url = public_url(base_url, site_prefix, "q/index.html")
        ld_items = [
            {"@type": "ListItem", "position": 1, "name": "トップ", "item": full_site_url("index.html")},
            {"@type": "ListItem", "position": 2, "name": "過去問一覧", "item": hub_item_url},
            {
                "@type": "ListItem",
                "position": 3,
                "name": title_mid,
                "item": canonical,
            },
        ]

    nav_items = []
    for name, href in crumbs_nav:
        nav_items.append(f'<li><a href="{html.escape(href)}">{html.escape(name)}</a></li>')
    nav_items.append(f"<li aria-current='page'>{html.escape(title_mid)}</li>")

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
            {"@type": "BreadcrumbList", "itemListElement": ld_items},
        ],
    }

    canonical_tag = f'<link rel="canonical" href="{html.escape(canonical)}">'

    stem_html = html.escape(page["text"]).replace("\n", "<br>\n")
    exp_html = html.escape(page["exp"]).replace("\n", "<br>\n")
    app_hash = "#past" if not is_orig else "#orig"
    app_label = "アプリで過去問を開く" if not is_orig else "アプリで演習する"

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
{canonical_tag}
<meta name="robots" content="index, follow">
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
      {"".join(nav_items)}
    </ol>
  </nav>
</header>
<main class="q-static-main">
  <p class="q-meta"><span class="q-id">ID: <code>{html.escape(qid)}</code></span> · <span>{html.escape(field_ja)}</span></p>
  <h1 class="q-h1">{html.escape(title_mid)}</h1>
  <section class="q-block" aria-labelledby="q-stem-h">
    <h2 id="q-stem-h" class="q-h2">問題</h2>
    <div class="q-stem">{stem_html}</div>
  </section>
  <section class="q-block" aria-labelledby="q-opts-h">
    <h2 id="q-opts-h" class="q-h2">選択肢</h2>
    <ol class="q-opts">
      {opts_html}
    </ol>
  </section>
  <section class="q-block q-answer" aria-labelledby="q-ans-h">
    <h2 id="q-ans-h" class="q-h2">正答</h2>
    <p>正答は <strong>（{html.escape(page["ans_display"])}）</strong> です。</p>
  </section>
  <section class="q-block" aria-labelledby="q-exp-h">
    <h2 id="q-exp-h" class="q-h2">解説</h2>
    <div class="q-exp">{exp_html}</div>
  </section>
  <p class="q-app-link"><a href="{html.escape(root_idx)}{app_hash}">{html.escape(app_label)}</a></p>
</main>
{render_static_q_footer(rel_path)}
</body>
</html>
"""


def write_q_past_index(
    out_root: Path,
    parsed_rows: list[dict],
    n_past: int,
    n_orig: int,
    base_url: str,
    site_prefix: str,
) -> None:
    rel = Path("q/index.html")
    root_idx = href_repo_root(rel, "index.html")
    css_href = rel_to_site_css(rel)
    canonical = public_url(base_url, site_prefix, "q/index.html")
    body_sections = build_past_list_sections(parsed_rows)
    meta_robots = '<meta name="robots" content="index, follow">'
    sitemap_href = html.escape(href_repo_root(rel, "sitemap.xml"))

    body = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>過去問一覧｜一衛マスター（第一種衛生管理者試験）</title>
<meta name="description" content="第一種衛生管理者試験の過去問を開催回・科目別の静的ページで一覧しています。過去問 {n_past} 問収録。オリジナル問題 {n_orig} 問は学習アプリから利用できます。">
{meta_robots}
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
      <li aria-current="page">過去問一覧</li>
    </ol>
  </nav>
</header>
<main class="q-static-main">
  <h1 class="q-h1">過去問一覧</h1>
  <p class="q-meta">過去問 <strong>{n_past}</strong> 問（静的）・オリジナル <strong>{n_orig}</strong> 問（アプリ）</p>
  <p class="glos-static-intro q-index-intro">開催回・科目ごとの静的ページです。<strong><a href="{html.escape(root_idx)}#past">アプリで過去問</a></strong>では開催年・科目の絞り込みや学習記録が使えます。オリジナル問題は <strong><a href="{html.escape(root_idx)}#orig">アプリのオリジナル</a></strong>から。</p>
  <p class="q-meta"><a href="{sitemap_href}">サイトマップ（全ページ）</a></p>
  {body_sections}
  <p class="q-app-link"><a href="{html.escape(root_idx)}#past">アプリで過去問を開く</a></p>
</main>
{render_static_q_footer(rel, current_q_index=True)}
</body>
</html>
"""
    (out_root / "index.html").write_text(body, encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="CSV から静的問題ページ q/ を生成")
    ap.add_argument(
        "--base-url",
        default="https://eisei1shu-master.jp",
        help="canonical / sitemap 用の本番オリジン（末尾スラッシュ不要）",
    )
    ap.add_argument(
        "--site-prefix",
        default="",
        help="GitHub Pages のプロジェクトサイト時など（例: my-repo）。ユーザサイトなら空",
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="既定: リポジトリ直下の q/",
    )
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    out_root = args.out_dir or (repo_root / "q")
    data_dir = repo_root / "data"
    csv_paths = [
        data_dir / "eisei1_past_questions.csv",
        data_dir / "eisei1_original_questions.csv",
    ]
    paths = [p for p in csv_paths if p.exists()]
    if not paths:
        print("data/*.csv が見つかりません。", file=sys.stderr)
        sys.exit(1)

    rows_in: list[dict] = []
    for p in paths:
        rows_in.extend(load_rows(p))

    parsed: list[dict] = []
    for i, row in enumerate(rows_in):
        try:
            parsed.append(parse_row(row, i + 2))
        except Exception as e:
            print(f"{e}（{paths} 合算 行 {i + 2}）", file=sys.stderr)
            sys.exit(1)

    widths = compute_widths(parsed)
    for r in parsed:
        r["qwidth"] = format_qwidth(r["num"], widths[r["group_key"]])

    seen_paths: set[str] = set()
    base_url = args.base_url.rstrip("/")
    site_prefix = args.site_prefix.strip("/").strip()

    # 出力先を空にしてから生成
    if out_root.exists():
        shutil.rmtree(out_root)
    out_root.mkdir(parents=True)

    urls_for_sitemap: list[str] = []

    n_past = n_orig = 0
    for r in parsed:
        if r["is_orig"]:
            rel = Path(
                relative_url_path_orig(r["session_or_pool"], r["field"], r["qwidth"])
            )
            n_orig += 1
        else:
            rel = Path(
                relative_url_path_past(r["era_slug"], r["session_or_pool"], r["field"], r["qwidth"])
            )
            n_past += 1

        sp = str(rel).replace("/index.html", "").replace("\\", "/")
        web_dir = sp + "/"
        if site_prefix:
            canonical = f"{base_url}/{site_prefix}/{web_dir}"
        else:
            canonical = f"{base_url}/{web_dir}"
        canonical = canonical.replace("/./", "/")

        r["base_url"] = base_url
        r["site_prefix"] = site_prefix
        r["canonical"] = canonical

        key = str(rel).replace("\\", "/")
        if key in seen_paths:
            print(f"重複パス: {key}", file=sys.stderr)
            sys.exit(1)
        seen_paths.add(key)

        if rel.parts[0] != "q":
            print(f"内部エラー: 想定外のパス {rel}", file=sys.stderr)
            sys.exit(1)
        rel_under_q = Path(*rel.parts[1:])
        full_path = out_root / rel_under_q
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(build_question_html(r, rel), encoding="utf-8")
        urls_for_sitemap.append(canonical)

    hub_canonical = public_url(base_url, site_prefix, "q/index.html")
    static_urls = [
        public_url(base_url, site_prefix, ""),
        public_url(base_url, site_prefix, "about.html"),
        public_url(base_url, site_prefix, "privacy-terms.html"),
        hub_canonical,
    ]
    all_sitemap_urls = static_urls + urls_for_sitemap

    sitemap_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for u in sorted(set(all_sitemap_urls)):
        sitemap_lines.append("  <url>")
        sitemap_lines.append(f"    <loc>{xml_escape(u)}</loc>")
        sitemap_lines.append("    <changefreq>monthly</changefreq>")
        sitemap_lines.append("  </url>")
    sitemap_lines.append("</urlset>")
    root_sitemap_path = repo_root / "sitemap.xml"
    root_sitemap_path.write_text("\n".join(sitemap_lines) + "\n", encoding="utf-8")

    robots_body = (
        "User-agent: *\nAllow: /\n\n"
        f"Sitemap: {public_url(base_url, site_prefix, 'sitemap.xml')}\n"
    )
    (repo_root / "robots.txt").write_text(robots_body, encoding="utf-8")

    write_q_past_index(out_root, parsed, n_past, n_orig, base_url, site_prefix)

    print(
        f"生成完了: {len(seen_paths)} 問 + q/index.html（過去問一覧）+ {root_sitemap_path.name} + robots.txt → {out_root} ほか"
    )


if __name__ == "__main__":
    main()
