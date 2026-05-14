#!/usr/bin/env python3
"""
用語一覧 terms/index.html を生成する（SEO用）。
- 全用語: docs/glossary-terms-checklist.csv の「カテゴリ」「用語」（科目別に列挙）
- 個別記事リンク: glossary-article-slugs.json のスラッグかつ terms-dir に同名 .html がある場合のみ
- CSV に無いが記事 HTML だけある用語は「その他」に追記
"""
from __future__ import annotations

import argparse
import csv
import html
import json
from collections import defaultdict
from pathlib import Path


CAT_ORDER = (
    "関係法令（有害業務）",
    "関係法令（有害以外）",
    "労働衛生（有害業務）",
    "労働衛生（有害以外）",
    "労働生理",
)

# チップ表示ラベル（data-cat は正式な区分名のまま）
CHIP_LABEL: dict[str, str] = {
    "関係法令（有害業務）": "法令（有害業務）",
    "関係法令（有害以外）": "法令（有害以外）",
    "労働衛生（有害業務）": "衛生（有害業務）",
    "労働衛生（有害以外）": "衛生（有害以外）",
    "労働生理": "労働生理",
}


def load_csv_rows_ordered(csv_path: Path) -> list[tuple[str, str]]:
    """CSV の行順で (カテゴリ, 用語) のリストを返す。"""
    out: list[tuple[str, str]] = []
    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cat = (row.get("カテゴリ") or "").strip()
            term = (row.get("用語") or "").strip()
            if term:
                out.append((cat or "その他", term))
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--slug-json", type=Path, required=True)
    p.add_argument("--csv", type=Path, help="glossary-terms-checklist.csv（必須推奨）")
    p.add_argument("--terms-dir", type=Path, required=True, help="公開用 terms（*.html が並ぶディレクトリ）")
    p.add_argument("--out", type=Path, required=True, help="例: public_site/terms/index.html")
    p.add_argument("--base", default="https://eisei1shu-master.jp", help="canonical / JSON-LD 用（末尾スラッシュなし）")
    args = p.parse_args()

    base = str(args.base).rstrip("/")
    terms_dir: Path = args.terms_dir
    if not terms_dir.is_dir():
        raise SystemExit(f"terms-dir が存在しません: {terms_dir}")

    slug_map: dict[str, str] = json.loads(args.slug_json.read_text(encoding="utf-8"))
    if not isinstance(slug_map, dict):
        raise SystemExit("slug-json はオブジェクト形式の JSON である必要があります")

    # 用語名 → 公開用スラッグ（実ファイルがあるもののみ）
    article_slug: dict[str, str] = {}
    for term, slug in slug_map.items():
        slug = str(slug).strip()
        term = str(term).strip()
        if not slug or not term:
            continue
        if (terms_dir / f"{slug}.html").is_file():
            article_slug[term] = slug

    if not args.csv or not args.csv.is_file():
        raise SystemExit("glossary-terms-checklist.csv を --csv で指定してください（全用語一覧のソース）")

    csv_rows = load_csv_rows_ordered(args.csv)
    if not csv_rows:
        raise SystemExit("CSV に用語がありません")

    csv_term_set = {t for _, t in csv_rows}

    display_rows: list[tuple[str, str, str | None]] = []
    for cat, term in csv_rows:
        display_rows.append((cat, term, article_slug.get(term)))

    # CSV に無いが記事 HTML だけある用語（プレースホルダー等）
    for term, slug in sorted(article_slug.items()):
        if term not in csv_term_set:
            display_rows.append(("その他", term, slug))

    n_all = len(display_rows)
    n_link = sum(1 for *_, s in display_rows if s)

    def sort_key_display(row: tuple[str, str, str | None]) -> tuple[int, str]:
        cat, term, _ = row
        try:
            ci = CAT_ORDER.index(cat)
        except ValueError:
            ci = len(CAT_ORDER)
        return (ci, term)

    display_rows.sort(key=sort_key_display)

    by_cat: dict[str, list[tuple[str, str | None]]] = defaultdict(list)
    for cat, term, slug in display_rows:
        by_cat[cat].append((term, slug))

    # JSON-LD: 記事 URL がある項目のみ（ItemList の item に URL を付ける）
    list_items_ld: list[dict] = []
    pos = 1
    for cat, term, slug in display_rows:
        if not slug:
            continue
        list_items_ld.append(
            {
                "@type": "ListItem",
                "position": pos,
                "name": term,
                "item": f"{base}/terms/{slug}.html",
            }
        )
        pos += 1

    ld_desc = (
        f"第一種衛生管理者試験の用語を{n_all}語、試験区分別に掲載しています。"
        f"個別の解説ページがある用語は{n_link}件です。"
    )
    ld = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "第一種衛生管理者試験 用語解説一覧",
        "description": ld_desc,
        "numberOfItems": len(list_items_ld),
        "itemListElement": list_items_ld,
    }

    cat_keys = [c for c in CAT_ORDER if c in by_cat]
    for c in by_cat:
        if c not in cat_keys and c != "その他":
            cat_keys.append(c)
    if "その他" in by_cat and "その他" not in cat_keys:
        cat_keys.append("その他")

    body_sections: list[str] = []

    def term_only_key(tup: tuple[str, str | None]) -> str:
        return tup[0]

    for cat in cat_keys:
        items = by_cat.get(cat)
        if not items:
            continue
        safe_cat = html.escape(cat, quote=True)
        body_sections.append(f'<section class="terms-idx-cat" aria-labelledby="cat-{safe_cat}">')
        body_sections.append(f'  <h2 id="cat-{safe_cat}">{html.escape(cat)}</h2>')
        body_sections.append('  <ul class="terms-idx-list">')
        for term, slug in sorted(items, key=term_only_key):
            et = html.escape(term)
            if slug:
                es = html.escape(slug, quote=True)
                body_sections.append(f'    <li><a href="/terms/{es}.html">{et}</a></li>')
            else:
                body_sections.append(f'    <li><span class="terms-idx-plain">{et}</span></li>')
        body_sections.append("  </ul>")
        body_sections.append("</section>")

    body_html = "\n".join(body_sections)

    chip_lines = [
        '<button type="button" class="chip on" data-cat="all">すべて</button>',
    ]
    for c in CAT_ORDER:
        if c not in by_cat:
            continue
        lab = CHIP_LABEL.get(c, c)
        chip_lines.append(
            f'<button type="button" class="chip" data-cat="{html.escape(c, quote=True)}">'
            f"{html.escape(lab)}</button>"
        )
    if "その他" in by_cat:
        chip_lines.append('<button type="button" class="chip" data-cat="その他">その他</button>')
    chips_html = "\n    ".join(chip_lines)

    ld_json = json.dumps(ld, ensure_ascii=False, indent=2)
    meta_desc = (
        f"第一種衛生管理者試験の重要用語{n_all}語を試験区分別に一覧。"
        f"解説記事ページへのリンクが付いている用語は{n_link}件です。"
        "関係法令・労働衛生・労働生理の語句を整理しています。"
    )

    page = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>用語解説一覧（全{n_all}語）｜一衛マスター（第一種衛生管理者試験）</title>
<meta name="description" content="{html.escape(meta_desc, quote=True)}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{html.escape(base + "/terms/", quote=True)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{html.escape(base + "/terms/", quote=True)}">
<meta property="og:title" content="用語解説一覧（全{n_all}語）｜一衛マスター">
<meta property="og:description" content="{html.escape(ld_desc, quote=True)}">
<meta property="og:locale" content="ja_JP">
<script type="application/ld+json">
{ld_json}
</script>
<script defer src="/site-analytics.js"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {{
  --bg: #ffffff;
  --bg2: #f4f4f5;
  --bg3: #e4e4e7;
  --text: #111111;
  --text2: #555555;
  --text3: #888888;
  --ink: #333333;
  --border: rgba(0,0,0,0.10);
  --border2: rgba(0,0,0,0.18);
  --font: 'Noto Sans JP', sans-serif;
  --r: 6px;
  --r2: 10px;
  --sh: 0 1px 3px rgba(0,0,0,0.07);
  --max-w: 1160px;
}}
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: var(--font);
  font-size: 16px;
  line-height: 1.8;
  background: #f0f0f1;
  color: var(--text);
  -webkit-font-smoothing: antialiased;
}}
a {{ color: var(--ink); text-decoration: underline; text-underline-offset: 3px; }}
a:hover {{ opacity: 0.9; }}

.site-header {{
  background: var(--bg);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 50;
}}
.site-header-inner {{
  max-width: var(--max-w);
  margin: 0 auto;
  padding: 0 20px;
  height: 52px;
  display: flex;
  align-items: center;
  gap: 12px;
}}
.header-back {{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text3);
  text-decoration: none;
  padding: 6px 10px;
  border-radius: var(--r);
  border: 1px solid var(--border2);
  background: var(--bg);
  transition: all .15s;
}}
.header-back:hover {{ background: var(--bg2); color: var(--text); opacity: 1; }}
.header-back svg {{ width: 14px; height: 14px; stroke: currentColor; fill: none; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }}
.header-logo {{
  font-size: 15px;
  font-weight: 700;
  color: var(--text);
  text-decoration: none;
}}
.header-sep {{ color: var(--text3); font-size: 13px; }}

.container {{
  max-width: var(--max-w);
  margin: 0 auto;
  padding: 20px 20px 56px;
}}
.breadcrumb {{
  font-size: 12px;
  color: var(--text3);
  margin-top: 6px;
}}
.breadcrumb a {{
  color: var(--text3);
  text-decoration: none;
}}
.breadcrumb a:hover {{
  text-decoration: underline;
}}
.breadcrumb-sep {{
  margin: 0 6px;
  color: var(--bg3);
}}
.page-title {{
  font-size: 1.55rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  margin: 12px 0 10px;
}}
.lead {{
  font-size: 15px;
  color: var(--text2);
  margin-bottom: 16px;
  line-height: 1.7;
}}
.meta-row {{
  display: flex;
  flex-wrap: wrap;
  gap: 10px 12px;
  align-items: center;
  margin: 16px 0 18px;
}}
.pill {{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 700;
  color: var(--text2);
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 6px 10px;
}}
.search {{
  flex: 1;
  min-width: min(420px, 100%);
  display: flex;
  gap: 10px;
  align-items: center;
}}
.search input {{
  width: 100%;
  padding: 10px 12px;
  border-radius: var(--r2);
  border: 1.5px solid var(--border2);
  background: var(--bg);
  color: var(--text);
  outline: none;
  font-size: 15px;
}}
.search input:focus {{ border-color: rgba(0,0,0,0.35); }}
.chips {{
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}}
.chip {{
  cursor: pointer;
  user-select: none;
  border: 1px solid var(--border2);
  background: var(--bg);
  color: var(--text2);
  padding: 7px 10px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 700;
  transition: all .15s;
}}
.chip:hover {{ background: var(--bg2); color: var(--text); }}
.chip.on {{
  background: var(--ink);
  color: #fff;
  border-color: var(--ink);
}}
.section {{
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--r2);
  box-shadow: var(--sh);
  padding: 18px 18px 6px;
  margin-top: 14px;
}}
.terms-idx-cat {{
  margin-top: 16px;
}}
.terms-idx-cat:first-child {{
  margin-top: 4px;
}}
.terms-idx-cat h2 {{
  font-size: 14px;
  font-weight: 800;
  color: var(--ink);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  border-bottom: 1px solid var(--border);
  padding-bottom: 8px;
  margin-bottom: 10px;
}}
.terms-idx-list {{
  list-style: none;
  columns: 2;
  column-gap: 22px;
  margin-bottom: 10px;
}}
@media (max-width: 760px) {{
  .terms-idx-list {{ columns: 1; }}
  .search {{ min-width: 100%; }}
}}
.terms-idx-list li {{
  break-inside: avoid;
  margin: 0 0 8px;
}}
.terms-idx-list a {{
  display: inline-flex;
  align-items: baseline;
  gap: 8px;
  text-decoration: none;
  color: var(--ink);
  font-weight: 400;
  font-size: 14px;
}}
.terms-idx-list a:hover {{ text-decoration: underline; }}
.terms-idx-plain {{
  font-size: 14px;
  color: var(--text2);
  font-weight: 400;
}}
.badge {{
  font-size: 11px;
  font-weight: 800;
  color: var(--text3);
  border: 1px solid var(--border);
  background: var(--bg2);
  border-radius: 999px;
  padding: 1px 7px;
}}
.hide {{ display: none !important; }}
.footer {{
  margin-top: 18px;
  font-size: 13px;
  color: var(--text3);
  text-align: center;
}}
</style>
</head>
<body>
<header class="site-header">
  <div class="site-header-inner">
    <a class="header-back" href="/">
      <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M9.5 3.5L5 8l4.5 4.5"/></svg>
      トップへ
    </a>
    <a class="header-logo" href="/">一衛マスター</a>
    <span class="header-sep">/</span>
    <span style="font-size:13px;color:var(--text3);font-weight:700">用語解説一覧</span>
  </div>
</header>

<main class="container">
  <nav class="breadcrumb" aria-label="パンくずリスト">
    <a href="/">トップ</a><span class="breadcrumb-sep">/</span><span>用語解説</span>
  </nav>
  <h1 class="page-title">用語解説一覧（全{n_all}語）</h1>
  <p class="lead">第一種衛生管理者試験の用語を試験区分ごとに一覧しています。個別の解説ページ（静的HTML）が用意されている用語はリンクから開けます。その他用語の説明文はトップの「用語解説」タブ（アプリ内一覧）で参照できます。</p>

  <div class="meta-row">
    <span class="pill">全 <span id="terms-total">{n_all}</span> 語（記事リンク <span id="terms-linked">{n_link}</span> 件）</span>
    <div class="search" role="search" aria-label="用語検索">
      <input id="q" type="search" inputmode="search" placeholder="例：WBGT、局所排気装置、衛生委員会…" autocomplete="off">
    </div>
  </div>

  <div class="chips" aria-label="科目フィルタ">
    {chips_html}
  </div>

  <section class="section" aria-label="用語一覧">
{body_html}
    <div class="footer">
      <span id="terms-hit"></span>
      <div style="margin-top:10px">学習アプリ本体は <a href="/">トップ</a> から利用できます。</div>
    </div>
  </section>
</main>

<script>
(() => {{
  try {{
    if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
  }} catch(_e) {{}}
  window.scrollTo(0, 0);

  const q = document.getElementById('q');
  const chips = Array.from(document.querySelectorAll('.chip[data-cat]'));
  const cats = Array.from(document.querySelectorAll('.terms-idx-cat'));
  const totalEl = document.getElementById('terms-total');
  const hitEl = document.getElementById('terms-hit');
  let activeCat = 'all';

  function norm(s) {{
    return (s || '').toString().trim().toLowerCase();
  }}

  function apply() {{
    const query = norm(q.value);
    let shown = 0;

    cats.forEach(sec => {{
      const cat = sec.querySelector('h2')?.textContent || '';
      const catOk = (activeCat === 'all') || (cat === activeCat);
      const items = Array.from(sec.querySelectorAll('li'));
      let anyInCat = 0;
      items.forEach(li => {{
        const el = li.querySelector('a, .terms-idx-plain');
        const t = norm(el?.textContent || '');
        const ok = catOk && (!query || t.includes(query));
        li.classList.toggle('hide', !ok);
        if (ok) {{ anyInCat++; shown++; }}
      }});
      sec.classList.toggle('hide', anyInCat === 0);
    }});

    if (hitEl) {{
      hitEl.textContent = query || activeCat !== 'all'
        ? `表示：${{shown}}件`
        : '';
    }}
  }}

  q.addEventListener('input', apply);
  chips.forEach(btn => {{
    btn.addEventListener('click', () => {{
      chips.forEach(b => b.classList.remove('on'));
      btn.classList.add('on');
      activeCat = btn.dataset.cat || 'all';
      apply();
    }});
  }});
  apply();
}})();
</script>
</body>
</html>
"""

    out: Path = args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(f"generate_terms_index_html.py: {n_all} 語（記事リンク {n_link} 件） -> {out}")


if __name__ == "__main__":
    main()
