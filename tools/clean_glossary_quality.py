#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用語ページ（terms/*.html）と data/glossary_terms.csv の安全クリーンアップ。

自動生成時に混入した「明らかなゴミ」のみを除去する（事実の捏造はしない）:
  - プレースホルダ素通し  「補足N-N。」
  - 未処理テンプレ語       「compare で整理する」→「比較表で整理する」
  - 全ページ同一の定型句   「観点A/B/C：…。」
  - 文法破綻               「はとは」→「とは」
  - meta description 等の語尾「…」での途切れ
  - 全ページ重複のボイラープレートFAQ（Q2〜Q4）を削除し、定義(Q1)のみ残す

terms/*.html は本番にそのまま配信される静的ファイル（デプロイ時に再生成されない）。
CSV はソース・オブ・トゥルースなので将来の再生成に備えて同様に整える。
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TERMS_DIR = ROOT / "terms"
CSV_PATH = ROOT / "data" / "glossary_terms.csv"

# 重複ボイラープレートFAQ・テンプレ残骸の判定
BOILER = re.compile(r"【[2-4]】|補足\d+-\d+|(?<![A-Za-z])compare(?![A-Za-z])|観点[A-C]：")


def clean_tokens(s: str) -> str:
    if not isinstance(s, str) or not s:
        return s
    s = s.replace("はとは", "とは")
    s = re.sub(r"\s*補足\d+-\d+。?", "", s)
    s = re.sub(r"\s*観点[A-C]：[^。]*。", "", s)
    s = s.replace("compare で整理する", "比較表で整理する")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def trim_ellipsis(s: str) -> str:
    """語尾が「…」で途切れた不完全な末尾文を落として、完結文だけ残す。"""
    if not s or "…" not in s:
        return s
    s = re.sub(r"[^。]*…。?\s*$", "", s).rstrip()
    s = s.replace("…", "")
    if "。" in s and not s.endswith("。"):
        s = s[: s.rfind("。") + 1]
    return s.strip()


def clean_desc(s: str) -> str:
    return trim_ellipsis(clean_tokens(s))


def derive_definition(defined_term_desc: str, q1_answer: str, term: str) -> str:
    """「<用語>とは、…」の定義一文を、最もきれいなソースから取り出す。"""
    dtd = clean_desc(defined_term_desc or "")
    m = re.search(r"(「?" + re.escape(term) + r"」?とは.*)$", dtd)
    if m and len(m.group(1)) > 8:
        return m.group(1).strip()
    a = clean_tokens(q1_answer or "")
    a = re.sub(r"^【1】定義：", "", a)
    a = re.sub(r"。根拠は関連法令。.*$", "。", a)
    return trim_ellipsis(a).strip()


def clean_ldjson_graph(graph: list, term: str) -> tuple[list, str]:
    """@graph を整え、定義一文を返す。"""
    # DefinedTerm.description と Q1 から定義を取り出す
    dt_desc = ""
    q1_ans = ""
    for node in graph:
        if node.get("@type") == "DefinedTerm":
            dt_desc = node.get("description", "")
        if node.get("@type") == "FAQPage":
            me = node.get("mainEntity") or []
            if me:
                q1_ans = me[0].get("acceptedAnswer", {}).get("text", "")
    defn = derive_definition(dt_desc, q1_ans, term)

    for node in graph:
        t = node.get("@type")
        if t in ("DefinedTerm", "WebPage"):
            if "description" in node:
                node["description"] = clean_desc(node["description"])
        if t == "FAQPage":
            me = node.get("mainEntity") or []
            kept = [q for q in me if not BOILER.search(q.get("acceptedAnswer", {}).get("text", ""))]
            if not kept and me:
                kept = [me[0]]
            # 定義(Q1)の回答をきれいな定義一文に置き換える
            if kept and defn:
                kept[0].setdefault("acceptedAnswer", {})["text"] = defn
            for q in kept[1:]:
                ans = q.get("acceptedAnswer", {})
                ans["text"] = clean_desc(ans.get("text", ""))
            node["mainEntity"] = kept
    return graph, defn


def clean_visible_faq(html: str, defn: str) -> str:
    """可視FAQ <section> 内の重複<details>を削除し、定義の<details>のみ残す。"""
    det_re = re.compile(r"<details class=\"term-faq-item\"[^>]*>.*?</details>", re.S)

    def repl_section(m: re.Match) -> str:
        sec = m.group(0)
        details = det_re.findall(sec)
        if not details:
            return sec
        kept = [d for d in details if not BOILER.search(re.sub(r"<[^>]+>", "", d))]
        if not kept:
            kept = [details[0]]
        first = kept[0]
        if defn:
            first = re.sub(r"(<div>).*?(</div>)", lambda mm: mm.group(1) + defn + mm.group(2), first, count=1, flags=re.S)
        # section 内の details 群を、残す1件に差し替え
        all_details_block = re.search(r"(<details class=\"term-faq-item\".*</details>)", sec, re.S)
        if all_details_block:
            sec = sec[: all_details_block.start(1)] + first + sec[all_details_block.end(1):]
        return sec

    return re.sub(r"<section class=\"seo-article-section\"[^>]*aria-labelledby=\"term-sec-faq\"[^>]*>.*?</section>",
                  repl_section, html, flags=re.S)


def process_html(path: Path) -> bool:
    html = path.read_text(encoding="utf-8")
    orig = html
    term = ""
    mt = re.search(r'"@type": "DefinedTerm".*?"name": "([^"]+)"', html, re.S)
    if mt:
        term = mt.group(1)

    defn = ""

    def repl_ld(m: re.Match) -> str:
        nonlocal defn
        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError:
            return m.group(0)
        graph = data.get("@graph")
        if isinstance(graph, list):
            data["@graph"], defn = clean_ldjson_graph(graph, term)
        body = json.dumps(data, ensure_ascii=False, indent=2)
        return '<script type="application/ld+json">\n' + body + "\n</script>"

    html = re.sub(r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>',
                  repl_ld, html, flags=re.S)

    # meta description / og:description（ld+json と同一文字列）を掃除
    def repl_meta(m: re.Match) -> str:
        return m.group(1) + clean_desc(m.group(2)) + m.group(3)

    html = re.sub(r'(<meta name="description" content=")([^"]*)(")', repl_meta, html)
    html = re.sub(r'(<meta property="og:description" content=")([^"]*)(")', repl_meta, html)

    # 可視FAQ
    html = clean_visible_faq(html, defn)

    # 念のため本文の残存トークンも掃除（FAQ以外に紛れ込んだ場合）
    html = html.replace("compare で整理する", "比較表で整理する")

    if html != orig:
        path.write_text(html, encoding="utf-8")
        return True
    return False


def process_csv() -> int:
    if not CSV_PATH.is_file():
        return 0
    text = CSV_PATH.read_text(encoding="utf-8-sig")
    rows = list(csv.reader(text.splitlines()))
    if not rows:
        return 0
    header = rows[0]
    idx = {name: i for i, name in enumerate(header)}
    changed = 0
    for r in rows[1:]:
        if len(r) < len(header):
            r.extend([""] * (len(header) - len(r)))
        before = list(r)
        # 重複ボイラープレートFAQ(Q2〜Q4)を空に
        for key in ("faq_2_question", "faq_2_answer", "faq_3_question",
                    "faq_3_answer", "faq_4_question", "faq_4_answer"):
            if key in idx:
                r[idx[key]] = ""
        # 残りのテキスト列のトークンを掃除
        for col, i in idx.items():
            if col.startswith("faq_2") or col.startswith("faq_3") or col.startswith("faq_4"):
                continue
            r[i] = clean_tokens(r[i])
        if r != before:
            changed += 1
    out = []
    w = []
    import io
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(header)
    for r in rows[1:]:
        writer.writerow(r)
    CSV_PATH.write_text(buf.getvalue(), encoding="utf-8")
    return changed


def main() -> int:
    args = sys.argv[1:]
    targets = None
    if args and args[0] == "--files":
        targets = [Path(p) for p in args[1:]]
    files = targets if targets else sorted(TERMS_DIR.glob("*.html"))
    n = 0
    for f in files:
        if f.name == "index.html":
            continue
        if process_html(f):
            n += 1
    print(f"HTML 更新: {n} / {len(files)} ファイル")
    if not targets:
        c = process_csv()
        print(f"CSV 更新: {c} 行")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
