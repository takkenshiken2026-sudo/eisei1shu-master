#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用語ページの定義品質を監査し、人手での書き直しが必要な候補を一覧出力する。

clean_glossary_quality.py は「明らかなゴミ」を機械的に除去するが、
ソースデータが元々「定義になっていない」用語（例：自己言及・テンプレ語salad）は
事実の捏造を避けるためそのまま残している。本スクリプトはそうした
「定義が弱い」ページを検出し、reports/glossary-quality-audit.csv に書き出す。

使い方:
    python3 tools/audit_glossary_quality.py
    # GSC表示のあるURLを優先表示したい場合は --gsc に「表示のあるパス」改行区切りファイルを渡す
"""
from __future__ import annotations

import csv
import io
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TERMS_DIR = ROOT / "terms"
OUT = ROOT / "reports" / "glossary-quality-audit.csv"

# 「定義として弱い／中身がない」ことを示すマーカー
WEAK_MARKERS = [
    "を手がかりに",
    "位置づけられます",
    "を語るときに",
    "を説明するときに",
    "整理するときに",
]


def extract(html: str, pat: str) -> str:
    m = re.search(pat, html, re.S)
    return m.group(1).strip() if m else ""


def faq_definition(html: str) -> str:
    """クリーンアップ後の定義はFAQ(Q1)の回答に入っている。そこを正とする。"""
    import json
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        for node in data.get("@graph", []):
            if node.get("@type") == "FAQPage":
                me = node.get("mainEntity") or []
                if me:
                    return me[0].get("acceptedAnswer", {}).get("text", "").strip()
    return ""


def main() -> int:
    gsc_paths: set[str] = set()
    args = sys.argv[1:]
    if len(args) >= 2 and args[0] == "--gsc":
        gsc_paths = {line.strip() for line in Path(args[1]).read_text().splitlines() if line.strip()}

    rows = []
    for f in sorted(TERMS_DIR.glob("*.html")):
        if f.name == "index.html":
            continue
        html = f.read_text(encoding="utf-8")
        term = extract(html, r'"@type": "DefinedTerm".*?"name": "([^"]+)"')
        defn = faq_definition(html)

        reasons = []
        for mk in WEAK_MARKERS:
            if mk in defn:
                reasons.append(mk)
        # 定義本体（「…とは/は、」以降）が極端に短い場合のみ「中身なし」とみなす
        body = re.sub(r"^「[^」]*」(?:とは|は)[、。]?", "", defn)
        if len(body) < 16:
            reasons.append("定義が短い/中身が薄い")
        if not reasons:
            continue
        rel = f"/terms/{f.name}"
        rows.append({
            "url": rel,
            "term": term,
            "weak_reason": " / ".join(sorted(set(reasons))),
            "has_gsc_impression": "Y" if rel in gsc_paths else "",
            "current_definition": defn[:120],
        })

    # GSC表示ありを上に、その中で用語名順
    rows.sort(key=lambda r: (r["has_gsc_impression"] != "Y", r["term"]))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=["url", "term", "weak_reason", "has_gsc_impression", "current_definition"])
    w.writeheader()
    for r in rows:
        w.writerow(r)
    OUT.write_text(buf.getvalue(), encoding="utf-8")

    print(f"要・定義書き直し候補: {len(rows)} ページ")
    print(f"  （GSC表示あり: {sum(1 for r in rows if r['has_gsc_impression'] == 'Y')} ページ）")
    print(f"レポート: {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
