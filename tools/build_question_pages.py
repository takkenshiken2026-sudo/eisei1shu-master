#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV から SEO 用の静的問題ページ（docs/question-id-url-slug-spec.md）を生成する。

使用例:
  python3 tools/build_question_pages.py
  python3 tools/build_question_pages.py --base-url https://example.github.io/repo --site-prefix repo

出力:
  - q/past/.../index.html, q/orig/.../index.html
  - q/past/{era}/index.html（年度ハブ）、q/past/{era}/{session}/index.html（会期ハブ）、
    q/past/{era}/{session}/{field}/index.html（科目ハブ）
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
SESSION_LABEL_JA = {
    "cat90": "カテゴリ別90",
    "zenki": "前期",
    "koki": "後期",
    "apr": "4月",
    "oct": "10月",
}
FIELD_INTRO_JA = {
    "law": "労働安全衛生法を中心とした関係法令の出題です。数値・選任要件・届出区分などを確認できます。",
    "rights": "化学物質・粉じん・騒音・健康診断など、労働衛生分野の過去問です。",
    "limit": "人体の生理・代謝・疲労・温熱など、労働生理分野の過去問です。",
}
FIELD_ORDER = ("law", "rights", "limit")


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


def era_slug_to_label(era_slug: str, era_raw_fallback: str = "") -> str:
    if era_raw_fallback:
        return strip_era_parenthetical_display(era_raw_fallback)
    kind, num_s = era_slug[0], era_slug[1:]
    try:
        num = int(num_s)
    except ValueError:
        return era_slug
    if kind == "r":
        return f"令和{num}年"
    if kind == "h":
        return f"平成{num}年"
    if kind == "s":
        return f"昭和{num}年"
    return era_slug


def strip_era_parenthetical_display(開催年数: str) -> str:
    return re.sub(r"（[^）]*）", "", (開催年数 or "").strip())


def session_label_ja(session: str, month_raw: str = "") -> str:
    return SESSION_LABEL_JA.get(session) or (month_raw or "").strip() or session


def href_q_past_hub(rel_file: Path, era_slug: str, session: str | None = None, field: str | None = None) -> str:
    """q/past/{era}[/{session}[/{field}]]/index.html への相対パス。"""
    target_parts = ["q", "past", era_slug]
    if session:
        target_parts.append(session)
    if field:
        target_parts.append(field)
    current_parts = rel_file.parent.parts
    common = 0
    for a, b in zip(current_parts, target_parts):
        if a == b:
            common += 1
        else:
            break
    ups = len(current_parts) - common
    down = target_parts[common:]
    if not down:
        if ups == 0:
            return "index.html"
        return "/".join([".."] * ups + ["index.html"])
    return "/".join([".."] * ups + list(down) + ["index.html"])


def href_past_question(rel_file: Path, r: dict) -> str:
    rel = Path(
        relative_url_path_past(r["era_slug"], r["session_or_pool"], r["field"], r["qwidth"])
    )
    target_parts = rel.parent.parts
    current_parts = rel_file.parent.parts
    common = 0
    for a, b in zip(current_parts, target_parts):
        if a == b:
            common += 1
        else:
            break
    ups = len(current_parts) - common
    down = list(target_parts[common:])
    return "/".join([".."] * ups + down + ["index.html"])


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


def hub_canonical_url(base_url: str, site_prefix: str, rel_under_q: str) -> str:
    rel_under_q = rel_under_q.strip("/")
    web_dir = f"q/{rel_under_q}/" if rel_under_q else "q/"
    return public_url(base_url, site_prefix, web_dir)


def collect_past_groups(parsed_rows: list[dict]) -> tuple[
    dict[str, str],
    dict[tuple[str, str], list[dict]],
    dict[tuple[str, str, str], list[dict]],
]:
    past = [r for r in parsed_rows if not r["is_orig"]]
    era_labels: dict[str, str] = {}
    by_session: dict[tuple[str, str], list[dict]] = defaultdict(list)
    by_field: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for r in past:
        es = r["era_slug"]
        sp = r["session_or_pool"]
        if es not in era_labels:
            era_labels[es] = strip_era_parenthetical_display(r["era_raw"])
        by_session[(es, sp)].append(r)
        by_field[(es, sp, r["field"])].append(r)
    return era_labels, by_session, by_field


def build_hub_list_html(
    rel_file: Path,
    items: list[tuple[str, str]],
    *,
    list_class: str = "q-year-list",
    ordered: bool = False,
) -> str:
    tag = "ol" if ordered else "ul"
    lis = "".join(
        f'<li><a href="{html.escape(href)}">{html.escape(label)}</a></li>'
        for label, href in items
    )
    return f'<{tag} class="{list_class}">{lis}</{tag}>'


def build_era_hub_sections(
    rel_file: Path,
    era_slug: str,
    era_label: str,
    by_session: dict[tuple[str, str], list[dict]],
) -> str:
    keys = sorted(
        [k for k in by_session if k[0] == era_slug],
        key=lambda k: session_sort_tuple(k[1]),
    )
    sections: list[str] = []
    for _, session in keys:
        rows = by_session[(era_slug, session)]
        sample = rows[0]
        sess_label = session_label_ja(session, sample["month_raw"])
        heading = f"{era_label}・{sess_label}"
        sid = f"{html.escape(era_slug)}-{html.escape(session)}"
        sess_hub = href_q_past_hub(rel_file, era_slug, session)
        subblocks: list[str] = []
        for fk in FIELD_ORDER:
            sub = [r for r in rows if r["field"] == fk]
            if not sub:
                continue
            sub.sort(key=lambda x: x["num"])
            field_hub = href_q_past_hub(rel_file, era_slug, session, fk)
            label_ja = FIELD_LABEL_JA[fk]
            lis = "".join(
                f'<li><a href="{html.escape(href_past_question(rel_file, r))}">第{r["num"]}問</a></li>'
                for r in sub
            )
            subblocks.append(
                f'<section class="q-session-field" aria-labelledby="hf-{sid}-{fk}">'
                f'<h3 id="hf-{sid}-{fk}" class="q-field-subhead">'
                f'<a href="{html.escape(field_hub)}">{html.escape(label_ja)}</a>'
                f"（{len(sub)}問）</h3>"
                f'<ol class="q-year-list">{lis}</ol></section>'
            )
        inner = "".join(subblocks)
        sections.append(
            f'<section class="glos-cat-section q-year-section" aria-labelledby="sess-{sid}">'
            f'<h2 id="sess-{sid}" class="glos-cat-heading glos-cat-heading--ja">'
            f'<a href="{html.escape(sess_hub)}">{html.escape(heading)}</a></h2>'
            f"{inner}</section>"
        )
    return "\n".join(sections)


def build_session_hub_sections(
    rel_file: Path,
    era_slug: str,
    session: str,
    rows: list[dict],
) -> str:
    sample = rows[0]
    era_label = era_slug_to_label(era_slug, sample["era_raw"])
    sess_label = session_label_ja(session, sample["month_raw"])
    sections: list[str] = []
    for fk in FIELD_ORDER:
        sub = [r for r in rows if r["field"] == fk]
        if not sub:
            continue
        sub.sort(key=lambda x: x["num"])
        field_hub = href_q_past_hub(rel_file, era_slug, session, fk)
        label_ja = FIELD_LABEL_JA[fk]
        intro = FIELD_INTRO_JA.get(fk, "")
        lis = "".join(
            f'<li><a href="{html.escape(href_past_question(rel_file, r))}">第{r["num"]}問</a></li>'
            for r in sub
        )
        sections.append(
            f'<section class="q-session-field" aria-labelledby="sf-{fk}">'
            f'<h2 id="sf-{fk}" class="glos-cat-heading glos-cat-heading--ja">'
            f'<a href="{html.escape(field_hub)}">{html.escape(label_ja)}</a>'
            f"（{len(sub)}問）</h2>"
            f'<p class="q-hub-field-intro">{html.escape(intro)}</p>'
            f'<ol class="q-year-list">{lis}</ol></section>'
        )
    return (
        f'<p class="glos-static-intro q-index-intro">'
        f"{html.escape(era_label)}・{html.escape(sess_label)}開催の過去問を科目別に掲載しています。"
        f"合計 <strong>{len(rows)}</strong> 問です。</p>\n" + "\n".join(sections)
    )


def build_field_hub_body(rel_file: Path, rows: list[dict]) -> str:
    rows = sorted(rows, key=lambda x: x["num"])
    sample = rows[0]
    era_label = era_slug_to_label(sample["era_slug"], sample["era_raw"])
    sess_label = session_label_ja(sample["session_or_pool"], sample["month_raw"])
    field_ja = FIELD_LABEL_JA[sample["field"]]
    intro = FIELD_INTRO_JA.get(sample["field"], "")
    items = [
        (f"第{r['num']}問", href_past_question(rel_file, r))
        for r in rows
    ]
    list_html = build_hub_list_html(rel_file, items, ordered=True)
    return (
        f'<p class="glos-static-intro q-index-intro">'
        f"{html.escape(era_label)}・{html.escape(sess_label)}・{html.escape(field_ja)}の過去問 "
        f"<strong>{len(rows)}</strong> 問です。{html.escape(intro)}</p>\n"
        f'<section aria-label="問題一覧">{list_html}</section>'
    )


def build_past_hub_html(
    *,
    rel_path: Path,
    title: str,
    description: str,
    canonical: str,
    h1: str,
    intro_html: str,
    body_sections: str,
    breadcrumbs: list[tuple[str, str, str]],
    base_url: str,
    site_prefix: str,
) -> str:
    """breadcrumbs: (表示名, ナビ用相対href, JSON-LD用絶対URL)"""
    root_idx = rel_to_root_index(rel_path)
    css_href = rel_to_site_css(rel_path)

    ld_items: list[dict] = []
    for pos, (name, _nav_href, abs_url) in enumerate(breadcrumbs, start=1):
        ld_items.append({"@type": "ListItem", "position": pos, "name": name, "item": abs_url})
    ld_items.append(
        {
            "@type": "ListItem",
            "position": len(breadcrumbs) + 1,
            "name": h1,
            "item": canonical,
        }
    )

    nav_items: list[str] = []
    for name, nav_href, _abs in breadcrumbs:
        nav_items.append(f'<li><a href="{html.escape(nav_href)}">{html.escape(name)}</a></li>')
    nav_items.append(f"<li aria-current='page'>{html.escape(h1)}</li>")

    json_ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "CollectionPage",
                "@id": canonical + "#webpage",
                "url": canonical,
                "name": title,
                "description": description,
                "inLanguage": "ja-JP",
            },
            {"@type": "BreadcrumbList", "itemListElement": ld_items},
        ],
    }

    current_q_index = rel_path == Path("q/index.html")
    footer = render_static_q_footer(rel_path, current_q_index=current_q_index)

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<link rel="canonical" href="{html.escape(canonical)}">
<meta name="robots" content="index, follow">
<meta property="og:type" content="website">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(description)}">
<meta property="og:url" content="{html.escape(canonical)}">
<meta name="twitter:card" content="summary">
<script defer src="/site-analytics.js"></script>
<link rel="stylesheet" href="{html.escape(css_href)}">
<script type="application/ld+json">
{json.dumps(json_ld, ensure_ascii=False, indent=2)}
</script>
</head>
<body class="q-static-page">
<header class="q-static-header">
  <p class="q-static-brand"><a href="{html.escape(root_idx)}">一衛マスター</a>（第一種衛生管理者試験）</p>
  <nav aria-label="パンくず">
    <ol class="q-breadcrumb">
      {"".join(nav_items)}
    </ol>
  </nav>
</header>
<main class="q-static-main">
  <h1 class="q-h1">{html.escape(h1)}</h1>
  {intro_html}
  {body_sections}
  <p class="q-app-link"><a href="{html.escape(root_idx)}#past">アプリで過去問を開く</a></p>
</main>
{footer}
</body>
</html>
"""


def write_past_hubs(
    out_root: Path,
    parsed_rows: list[dict],
    base_url: str,
    site_prefix: str,
) -> list[str]:
    era_labels, by_session, by_field = collect_past_groups(parsed_rows)
    hub_urls: list[str] = []

    era_slugs = sorted(era_labels.keys(), key=era_sort_tuple)
    for era_slug in era_slugs:
        era_label = era_slug_to_label(era_slug, era_labels[era_slug])
        era_rows = [r for k, rows in by_session.items() if k[0] == era_slug for r in rows]
        n_era = len(era_rows)
        rel_path = Path(f"q/past/{era_slug}/index.html")
        rel_under_q = f"past/{era_slug}"
        canonical = hub_canonical_url(base_url, site_prefix, rel_under_q)
        title = f"{era_label} 過去問一覧｜第一種衛生管理者試験｜一衛マスター"
        desc = (
            f"第一種衛生管理者試験・{era_label}の過去問を開催回・科目別にまとめています。"
            f"全{n_era}問。関係法令・労働衛生・労働生理ごとに静的ページで確認できます。"
        )
        intro = (
            f'<p class="glos-static-intro q-index-intro">'
            f"{html.escape(era_label)}の第一種衛生管理者試験 過去問を、開催回・科目別に整理しています。"
            f"合計 <strong>{n_era}</strong> 問です。"
            f"年度をまたいだ傾向は"
            f'<a href="{html.escape(href_repo_root(rel_path, "articles/kakomon-theme-frequency.html"))}">過去問の出題傾向記事</a>'
            f"も参照してください。</p>"
        )
        body = build_era_hub_sections(rel_path, era_slug, era_label, by_session)
        html_body = build_past_hub_html(
            rel_path=rel_path,
            title=title,
            description=desc,
            canonical=canonical,
            h1=f"{era_label} 過去問",
            intro_html=intro,
            body_sections=body,
            breadcrumbs=[
                (
                    "トップ",
                    href_repo_root(rel_path, "index.html"),
                    public_url(base_url, site_prefix, "index.html"),
                ),
                (
                    "過去問一覧",
                    href_q_index(rel_path),
                    public_url(base_url, site_prefix, "q/index.html"),
                ),
            ],
            base_url=base_url,
            site_prefix=site_prefix,
        )
        out_file = out_root / "past" / era_slug / "index.html"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(html_body, encoding="utf-8")
        hub_urls.append(canonical)

    for (era_slug, session), rows in sorted(
        by_session.items(),
        key=lambda kv: (era_sort_tuple(kv[0][0]), session_sort_tuple(kv[0][1])),
    ):
        sample = rows[0]
        era_label = era_slug_to_label(era_slug, sample["era_raw"])
        sess_label = session_label_ja(session, sample["month_raw"])
        heading = f"{era_label}・{sess_label}"
        n_sess = len(rows)
        rel_path = Path(f"q/past/{era_slug}/{session}/index.html")
        rel_under_q = f"past/{era_slug}/{session}"
        canonical = hub_canonical_url(base_url, site_prefix, rel_under_q)
        title = f"{heading} 過去問一覧｜第一種衛生管理者試験｜一衛マスター"
        desc = (
            f"第一種衛生管理者試験・{heading}の過去問{n_sess}問を科目別に掲載。"
            f"関係法令・労働衛生・労働生理の各問へリンクしています。"
        )
        body = build_session_hub_sections(rel_path, era_slug, session, rows)
        era_hub_canonical = hub_canonical_url(base_url, site_prefix, f"past/{era_slug}")
        html_body = build_past_hub_html(
            rel_path=rel_path,
            title=title,
            description=desc,
            canonical=canonical,
            h1=f"{heading} 過去問",
            intro_html="",
            body_sections=body,
            breadcrumbs=[
                (
                    "トップ",
                    href_repo_root(rel_path, "index.html"),
                    public_url(base_url, site_prefix, "index.html"),
                ),
                (
                    "過去問一覧",
                    href_q_index(rel_path),
                    public_url(base_url, site_prefix, "q/index.html"),
                ),
                (era_label, href_q_past_hub(rel_path, era_slug), era_hub_canonical),
            ],
            base_url=base_url,
            site_prefix=site_prefix,
        )
        out_file = out_root / "past" / era_slug / session / "index.html"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(html_body, encoding="utf-8")
        hub_urls.append(canonical)

    for (era_slug, session, field), rows in sorted(
        by_field.items(),
        key=lambda kv: (
            era_sort_tuple(kv[0][0]),
            session_sort_tuple(kv[0][1]),
            FIELD_ORDER.index(kv[0][2]) if kv[0][2] in FIELD_ORDER else 99,
        ),
    ):
        sample = rows[0]
        era_label = era_slug_to_label(era_slug, sample["era_raw"])
        sess_label = session_label_ja(session, sample["month_raw"])
        field_ja = FIELD_LABEL_JA[field]
        heading = f"{era_label}・{sess_label}・{field_ja}"
        n_field = len(rows)
        rel_path = Path(f"q/past/{era_slug}/{session}/{field}/index.html")
        rel_under_q = f"past/{era_slug}/{session}/{field}"
        canonical = hub_canonical_url(base_url, site_prefix, rel_under_q)
        title = f"{heading} 過去問｜第一種衛生管理者試験｜一衛マスター"
        desc = (
            f"第一種衛生管理者試験・{heading}の過去問{n_field}問。"
            f"問題文・選択肢・解説の静的ページへリンクしています。"
        )
        body = build_field_hub_body(rel_path, rows)
        era_hub_canonical = hub_canonical_url(base_url, site_prefix, f"past/{era_slug}")
        sess_hub_canonical = hub_canonical_url(base_url, site_prefix, f"past/{era_slug}/{session}")
        html_body = build_past_hub_html(
            rel_path=rel_path,
            title=title,
            description=desc,
            canonical=canonical,
            h1=f"{heading} 過去問",
            intro_html="",
            body_sections=body,
            breadcrumbs=[
                (
                    "トップ",
                    href_repo_root(rel_path, "index.html"),
                    public_url(base_url, site_prefix, "index.html"),
                ),
                (
                    "過去問一覧",
                    href_q_index(rel_path),
                    public_url(base_url, site_prefix, "q/index.html"),
                ),
                (era_label, href_q_past_hub(rel_path, era_slug), era_hub_canonical),
                (sess_label, href_q_past_hub(rel_path, era_slug, session), sess_hub_canonical),
            ],
            base_url=base_url,
            site_prefix=site_prefix,
        )
        out_file = out_root / "past" / era_slug / session / field / "index.html"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(html_body, encoding="utf-8")
        hub_urls.append(canonical)

    return hub_urls


def build_era_hub_nav_for_q_index(parsed_rows: list[dict]) -> str:
    era_labels, _, _ = collect_past_groups(parsed_rows)
    if not era_labels:
        return ""
    items = []
    for era_slug in sorted(era_labels.keys(), key=era_sort_tuple, reverse=True):
        label = era_slug_to_label(era_slug, era_labels[era_slug])
        href = f"past/{era_slug}/"
        items.append(f'<li><a href="{html.escape(href)}">{html.escape(label)}の過去問</a></li>')
    return (
        '<nav class="q-era-hub-nav" aria-label="年度別過去問">'
        '<h2 class="glos-cat-heading glos-cat-heading--ja">年度別一覧</h2>'
        f'<ul class="q-year-list">{"".join(items)}</ul></nav>'
    )


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
    for era_slug, session in sorted_keys:
        rows = groups[(era_slug, session)]
        sample = rows[0]
        heading = breadcrumb_label_past(sample["era_raw"], sample["month_raw"])
        era_label = era_slug_to_label(era_slug, sample["era_raw"])
        sid = f"{html.escape(era_slug)}-{html.escape(session)}"
        era_hub = f"past/{era_slug}/"
        sess_hub = f"past/{era_slug}/{session}/"
        subblocks: list[str] = []
        for fk in FIELD_ORDER:
            sub = [r for r in rows if r["field"] == fk]
            if not sub:
                continue
            sub.sort(key=lambda x: x["num"])
            label_ja = FIELD_LABEL_JA[fk]
            field_hub = f"past/{era_slug}/{session}/{fk}/"
            lis = "".join(
                f'<li><a href="{html.escape(href_past_question_from_q_index(r))}">第{r["num"]}問</a></li>'
                for r in sub
            )
            subblocks.append(
                f'<section class="q-session-field" aria-labelledby="sf-{sid}-{fk}">'
                f'<h3 id="sf-{sid}-{fk}" class="q-field-subhead">'
                f'<a href="{html.escape(field_hub)}">{html.escape(label_ja)}</a></h3>'
                f'<ol class="q-year-list">{lis}</ol></section>'
            )
        inner = "".join(subblocks)
        hub_links = (
            f'<p class="q-hub-links">'
            f'<a href="{html.escape(era_hub)}">{html.escape(era_label)}の一覧</a>'
            f' · <a href="{html.escape(sess_hub)}">この開催回の一覧</a></p>'
        )
        sections.append(
            f'<section class="glos-cat-section q-year-section" aria-labelledby="sess-{sid}">'
            f'<h2 id="sess-{sid}" class="glos-cat-heading glos-cat-heading--ja">{html.escape(heading)}</h2>'
            f"{hub_links}{inner}</section>"
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
        era_slug = page["era_slug"]
        session = page["session_or_pool"]
        era_label = era_slug_to_label(era_slug, page["era_raw"])
        sess_label = session_label_ja(session, page["month_raw"])
        era_hub_href = href_q_past_hub(rel_path, era_slug)
        sess_hub_href = href_q_past_hub(rel_path, era_slug, session)
        field_hub_href = href_q_past_hub(rel_path, era_slug, session, field)
        crumbs_nav = [
            ("トップ", root_idx),
            ("過去問一覧", q_hub_idx),
            (era_label, era_hub_href),
            (sess_label, sess_hub_href),
            (field_ja, field_hub_href),
        ]
        hub_item_url = public_url(base_url, site_prefix, "q/index.html")
        era_hub_url = hub_canonical_url(base_url, site_prefix, f"past/{era_slug}")
        sess_hub_url = hub_canonical_url(base_url, site_prefix, f"past/{era_slug}/{session}")
        field_hub_url = hub_canonical_url(
            base_url, site_prefix, f"past/{era_slug}/{session}/{field}"
        )
        ld_items = [
            {"@type": "ListItem", "position": 1, "name": "トップ", "item": full_site_url("index.html")},
            {"@type": "ListItem", "position": 2, "name": "過去問一覧", "item": hub_item_url},
            {"@type": "ListItem", "position": 3, "name": era_label, "item": era_hub_url},
            {"@type": "ListItem", "position": 4, "name": sess_label, "item": sess_hub_url},
            {"@type": "ListItem", "position": 5, "name": field_ja, "item": field_hub_url},
            {
                "@type": "ListItem",
                "position": 6,
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
<body class="q-static-page">
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
    era_nav = build_era_hub_nav_for_q_index(parsed_rows)
    body_sections = build_past_list_sections(parsed_rows)
    meta_robots = '<meta name="robots" content="index, follow">'
    sitemap_href = html.escape(href_repo_root(rel, "sitemap.xml"))

    body = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>過去問一覧｜一衛マスター（第一種衛生管理者試験）</title>
<meta name="description" content="第一種衛生管理者試験の過去問を開催回・科目別の静的ページで一覧しています。過去問 {n_past} 問収録。実践演習 {n_orig} 問は学習アプリから利用できます。">
{meta_robots}
<link rel="canonical" href="{html.escape(canonical)}">
<script defer src="/site-analytics.js"></script>
<link rel="stylesheet" href="{html.escape(css_href)}">
</head>
<body class="q-static-page">
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
  <p class="q-meta">過去問 <strong>{n_past}</strong> 問（静的）・実践演習 <strong>{n_orig}</strong> 問（アプリ）</p>
  <p class="glos-static-intro q-index-intro">開催回・科目ごとの静的ページです。<strong><a href="{html.escape(root_idx)}#past">アプリで過去問</a></strong>では開催年・科目の絞り込みや学習記録が使えます。実践演習は <strong><a href="{html.escape(root_idx)}#orig">アプリの実践演習</a></strong>から。</p>
  <p class="q-meta"><a href="{sitemap_href}">サイトマップ（全ページ）</a></p>
  {era_nav}
  {body_sections}
  <p class="q-app-link"><a href="{html.escape(root_idx)}#past">アプリで過去問を開く</a></p>
</main>
{render_static_q_footer(rel, current_q_index=True)}
</body>
</html>
"""
    (out_root / "index.html").write_text(body, encoding="utf-8")


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    past_csv = repo_root / "data" / "past_questions.csv"
    if past_csv.is_file():
        import subprocess

        for script in (
            "import_eisei1_original_to_practice_csv.py",
            "apply_site_config.py",
            "csv_to_exam_site_past_js.py",
            "csv_to_exam_site_ichimondou_js.py",
            "build_past_question_pages.py",
            "build_practice_ichimon_pages.py",
            "build_sitemap.py",
        ):
            subprocess.run(
                [sys.executable, f"tools/{script}"],
                cwd=repo_root,
                check=True,
            )
        return

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

    robots_body = (
        "User-agent: *\nAllow: /\n\n"
        f"Sitemap: {public_url(base_url, site_prefix, 'sitemap.xml')}\n"
    )
    (repo_root / "robots.txt").write_text(robots_body, encoding="utf-8")

    write_q_past_index(out_root, parsed, n_past, n_orig, base_url, site_prefix)
    hub_urls = write_past_hubs(out_root, parsed, base_url, site_prefix)
    root_sitemap_path = repo_root / "sitemap.xml"
    all_sitemap_urls = static_urls + urls_for_sitemap + hub_urls
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
    root_sitemap_path.write_text("\n".join(sitemap_lines) + "\n", encoding="utf-8")

    print(
        f"生成完了: {len(seen_paths)} 問 + {len(hub_urls)} ハブ + q/index.html（過去問一覧）"
        f" + {root_sitemap_path.name} + robots.txt → {out_root} ほか"
    )


if __name__ == "__main__":
    main()
