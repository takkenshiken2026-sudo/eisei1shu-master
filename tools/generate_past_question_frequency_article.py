#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data/eisei1_past_questions.csv と docs/past_question_theme_keywords.json から
科目・テーマ別の出題傾向を集計し、articles/kakomon-theme-frequency.html を生成する。

分類ルール:
  - 各設問の「問」「解説」を連結したテキストに対し、当該科目の各テーマのキーワード一致数をスコアとして比較
  - 最大スコアのテーマに1問を割り当て（同点は JSON 記載順で先勝ち）
  - 全テーマでスコア0の場合は「その他」に分類
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_DEFAULT_CSV = _REPO / "data" / "eisei1_past_questions.csv"
_DEFAULT_KW = _REPO / "docs" / "past_question_theme_keywords.json"
_DEFAULT_OUT = _REPO / "articles" / "kakomon-theme-frequency.html"


def load_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def session_key(row: dict) -> str:
    return f"{(row.get('開催年数') or '').strip()}｜{(row.get('開催月') or '').strip()}"


def classify_row(
    text: str,
    themes: list[dict],
) -> tuple[str, str, int]:
    """(theme_id, theme_label, score) — スコア>0 のテーマのみ。全て0ならその他。"""
    best_id = "__unmatched__"
    best_label = "その他（分類に当てはまらなかった設問）"
    best = 0
    for t in themes:
        sid = t["id"]
        label = t["label"]
        score = 0
        for kw in t["keywords"]:
            if kw in text:
                score += text.count(kw)
        if score > best:
            best = score
            best_id = sid
            best_label = label
    if best <= 0:
        return "__unmatched__", best_label, 0
    return best_id, best_label, best


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def build_article(
    *,
    rows: list[dict],
    theme_defs: dict[str, list[dict]],
    out_path: Path,
    generated_on: str,
) -> None:
    sessions = sorted({session_key(r) for r in rows})
    n_sessions = len(sessions)
    n_rows = len(rows)

    by_subject: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        sub = (r.get("科目") or "").strip()
        by_subject[sub].append(r)

    # theme_id -> stats
    theme_q_count: dict[str, int] = defaultdict(int)
    theme_sessions: dict[str, set[str]] = defaultdict(set)
    theme_label: dict[str, str] = {"__unmatched__": "その他（分類に当てはまらなかった設問）"}
    for sub, defs in theme_defs.items():
        for t in defs:
            theme_label[t["id"]] = t["label"]
    row_assignment: list[tuple[dict, str, str, int]] = []

    for r in rows:
        sub = (r.get("科目") or "").strip()
        defs = theme_defs.get(sub)
        if not defs:
            raise SystemExit(f"科目 {sub!r} のテーマ定義がありません")
        text = ((r.get("問") or "") + "\n" + (r.get("解説") or "")).strip()
        tid, tlabel, sc = classify_row(text, defs)
        theme_q_count[tid] += 1
        theme_sessions[tid].add(session_key(r))
        row_assignment.append((r, tid, tlabel, sc))

    # --- HTML ---
    parts: list[str] = []
    parts.append("<!DOCTYPE html>\n<html lang=\"ja\">\n<head>\n")
    parts.append('<meta charset="UTF-8">\n')
    parts.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">\n')
    title = "第一種衛生管理者「過去問616問」から見る科目・テーマ別の出題傾向【14回分】"
    parts.append(f"<title>{esc(title)}</title>\n")
    desc = (
        "第一種衛生管理者の過去問616問（14回分）を、科目とテーマ別に整理し、"
        "出題数と試験回ごとの出現の傾向をまとめました。"
    )
    parts.append(f'<meta name="description" content="{esc(desc)}">\n')
    parts.append('<meta name="robots" content="index, follow">\n')
    parts.append('<link rel="canonical" href="https://eisei1shu-master.jp/articles/kakomon-theme-frequency.html">\n')
    parts.append(f'<meta property="og:title" content="{esc(title)}">\n')
    parts.append(f'<meta property="og:description" content="{esc(desc)}">\n')
    parts.append('<meta property="og:type" content="article">\n')
    parts.append('<meta property="og:url" content="https://eisei1shu-master.jp/articles/kakomon-theme-frequency.html">\n')
    parts.append('<meta property="og:locale" content="ja_JP">\n')
    parts.append('<meta property="og:site_name" content="一衛マスター">\n')
    parts.append('<meta name="twitter:card" content="summary">\n')
    parts.append(f'<meta name="twitter:title" content="{esc(title)}">\n')
    parts.append(f'<meta name="twitter:description" content="{esc(desc)}">\n')
    parts.append('<script type="application/ld+json">\n')
    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "@id": "https://eisei1shu-master.jp/#website",
                "url": "https://eisei1shu-master.jp/",
                "name": "一衛マスター",
                "inLanguage": "ja",
            },
            {
                "@type": "Article",
                "@id": "https://eisei1shu-master.jp/articles/kakomon-theme-frequency.html#article",
                "headline": title,
                "description": desc,
                "dateModified": generated_on,
                "inLanguage": "ja",
                "isPartOf": {"@id": "https://eisei1shu-master.jp/#website"},
                "publisher": {"@type": "Organization", "name": "一衛マスター", "url": "https://eisei1shu-master.jp/"},
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "トップ", "item": "https://eisei1shu-master.jp/"},
                    {"@type": "ListItem", "position": 2, "name": "試験・学習ガイド", "item": "https://eisei1shu-master.jp/articles/"},
                    {
                        "@type": "ListItem",
                        "position": 3,
                        "name": title,
                        "item": "https://eisei1shu-master.jp/articles/kakomon-theme-frequency.html",
                    },
                ],
            },
        ],
    }
    parts.append(json.dumps(ld, ensure_ascii=False, indent=2))
    parts.append("\n</script>\n")

    # Reuse article CSS pattern (minimal inline from sibling)
    css_path = _REPO / "articles" / "shiken-kamoku.html"
    css_block = ""
    if css_path.is_file():
        raw = css_path.read_text(encoding="utf-8")
        m = re.search(r"<style>([\s\S]*?)</style>", raw)
        if m:
            css_block = m.group(1)
    if not css_block:
        css_block = "body{font-family:system-ui,sans-serif;line-height:1.8;padding:24px;}"
    parts.append("<style>\n" + css_block + "\n</style>\n</head>\n<body>\n")
    parts.append('<header class="site-header">\n')
    parts.append('  <div class="site-header-inner">\n')
    parts.append(
        '    <a href="/" class="header-back"><svg viewBox="0 0 24 24"><polyline points="15 18 9 12 15 6"/></svg>学習トップ</a>\n'
    )
    parts.append('    <span class="header-sep">›</span>\n')
    parts.append('    <a href="/" class="header-logo">一衛マスター</a>\n')
    parts.append("  </div>\n</header>\n")
    parts.append('<div class="page-wrap">\n')
    parts.append('  <nav class="breadcrumb" aria-label="パンくず">\n')
    parts.append(
        '    <a href="/">トップ</a><span class="breadcrumb-sep">›</span>'
        '<a href="/articles/">試験・学習ガイド</a><span class="breadcrumb-sep">›</span>'
        f"<span>{esc(title)}</span>\n"
    )
    parts.append("  </nav>\n")
    parts.append('  <div class="article-meta">\n')
    parts.append('    <span class="meta-category">過去問分析</span>\n')
    parts.append(f'    <span class="meta-updated">更新日：{esc(generated_on)}</span>\n')
    parts.append("  </div>\n")
    parts.append(f'  <h1 class="article-title">{esc(title)}</h1>\n')
    parts.append('  <article class="article-body">\n')

    parts.append(
        "<p>本記事は、一衛マスターに掲載している<strong>第一種衛生管理者の過去問</strong>をもとに、"
        "問題文と解説から<strong>科目別・テーマ別の出題傾向</strong>を整理したものです。"
        "公式の出題範囲の宣言ではなく、<strong>掲載データに基づく傾向</strong>として参考にしてください。</p>\n"
    )
    parts.append(
        f"<h2>1. 対象データ</h2>\n<ul>\n"
        f"<li>設問数：<strong>{n_rows}問</strong>（各回44問×<strong>{n_sessions}回分</strong>）</li>\n"
        "<li>科目：関係法令・労働衛生・労働生理</li>\n"
        "<li>テーマ分類：問題文と解説に現れる用語から、科目ごとのテーマに振り分けています</li>\n"
        "</ul>\n"
    )

    parts.append("<h2>2. 集計の考え方</h2>\n")
    parts.append(
        "<p>各設問は、問題文と解説の中で<strong>どのテーマの語句が最も多く当てはまるか</strong>で1つのテーマに分類しています。"
        "複数テーマにまたがる問題は、当てはまりが最も大きい側にのみカウントしています。"
        "どのテーマにも当てはまらなかった設問は、表の<strong>その他</strong>にまとめています。</p>\n"
    )

    parts.append("<h2>3. 科目別の設問数</h2>\n")
    parts.append("<table><thead><tr><th>科目</th><th>設問数</th><th>対象</th></tr></thead><tbody>\n")
    for sub in ("関係法令", "労働衛生", "労働生理"):
        c = len(by_subject.get(sub, []))
        parts.append(
            f"<tr><td>{esc(sub)}</td><td>{c}</td>"
            f"<td>過去{n_sessions}回分</td></tr>\n"
        )
    parts.append("</tbody></table>\n")

    sec = 4
    for sub in ("関係法令", "労働衛生", "労働生理"):
        defs = theme_defs[sub]
        parts.append(f"<h2>{sec}. テーマ別（{esc(sub)}）</h2>\n")
        sec += 1
        parts.append(
            "<table><thead><tr><th>テーマ</th><th>設問数</th>"
            f"<th>試験回で出現（/{n_sessions}回）</th><th>出現率</th></tr></thead><tbody>\n"
        )
        tids_order = [t["id"] for t in defs]
        stats_sub: list[tuple[str, str, int, int]] = []
        for tid in tids_order:
            stats_sub.append(
                (tid, theme_label[tid], theme_q_count.get(tid, 0), len(theme_sessions.get(tid, set())))
            )
        # unmatched only for this subject
        um = sum(1 for r, tid, _, _ in row_assignment if (r.get("科目") or "").strip() == sub and tid == "__unmatched__")
        um_sess = set()
        for r, tid, _, _ in row_assignment:
            if (r.get("科目") or "").strip() == sub and tid == "__unmatched__":
                um_sess.add(session_key(r))
        stats_sub.append(("__unmatched__", "その他（分類に当てはまらなかった設問）", um, len(um_sess)))

        for tid, lab, qc, sc in sorted(stats_sub, key=lambda x: (-x[2], x[1])):
            rate = (100.0 * sc / n_sessions) if n_sessions else 0.0
            parts.append(
                f"<tr><td>{esc(lab)}</td><td>{qc}</td><td>{sc}</td><td>{rate:.0f}%</td></tr>\n"
            )
        parts.append("</tbody></table>\n")

    parts.append(f"<h2>{sec}. この表の読み方</h2>\n<ul>\n")
    parts.append("<li>「試験回で出現」が高いテーマは、掲載している過去問の範囲で<strong>繰り返し出題されているテーマ</strong>です。</li>\n")
    parts.append("<li>学習の優先度は、本記事に加えて<a href=\"/articles/shiken-kamoku.html\">試験科目・出題範囲</a>や、ご自身の苦手分野も合わせて決めるとよいです。</li>\n")
    parts.append("<li>実際の演習は<a href=\"/\">学習トップの過去問</a>から進められます。</li>\n")
    parts.append("</ul>\n")

    parts.append('<div class="related-box">\n')
    parts.append('  <div class="related-box-title">関連記事</div>\n')
    parts.append('  <div class="related-links">\n')
    parts.append(
        '    <a class="related-link" href="/articles/shiken-kamoku.html">第一種衛生管理者の試験科目・出題範囲【5区分44問・配点・頻出テーマ一覧】</a>\n'
    )
    parts.append(
        '    <a class="related-link" href="/articles/dokugaku-guide.html">第一種衛生管理者の独学合格ガイド【過去問・一問一答・直前対策の進め方】</a>\n'
    )
    parts.append("  </div>\n</div>\n")

    parts.append("  </article>\n</div>\n")
    parts.append(
        '<footer class="site-footer">\n'
        '  <a href="/">一衛マスター</a> ｜ 第一種衛生管理者試験 無料学習プラットフォーム\n'
        "</footer>\n</body>\n</html>\n"
    )

    out_path.write_text("".join(parts), encoding="utf-8")
    print(f"generate_past_question_frequency_article.py: wrote {out_path}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path, default=_DEFAULT_CSV)
    ap.add_argument("--keywords", type=Path, default=_DEFAULT_KW)
    ap.add_argument("--out", type=Path, default=_DEFAULT_OUT)
    ap.add_argument("--date", default="", help="YYYY-MM-DD（JSON-LD用。省略時は本日）")
    args = ap.parse_args()
    gen_date = args.date.strip() or date.today().isoformat()

    if not args.csv.is_file():
        print(f"CSV がありません: {args.csv}", file=sys.stderr)
        sys.exit(1)
    if not args.keywords.is_file():
        print(f"キーワード JSON がありません: {args.keywords}", file=sys.stderr)
        sys.exit(1)

    theme_defs: dict[str, list[dict]] = json.loads(args.keywords.read_text(encoding="utf-8"))
    rows = load_rows(args.csv)
    # 過去問のみ（オリジナル混在時は除外）
    past_only: list[dict] = []
    for r in rows:
        era = (r.get("開催年数") or "").strip()
        if "オリジナル" in era:
            continue
        past_only.append(r)

    if not past_only:
        print("過去問行がありません（全行オリジナル？）", file=sys.stderr)
        sys.exit(1)

    build_article(rows=past_only, theme_defs=theme_defs, out_path=args.out, generated_on=gen_date)


if __name__ == "__main__":
    main()
