#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docs/glossary-terms-checklist.csv から eisei1-data-glossary.js（埋め込み用）を生成する。
HTTPでCSVを取れない環境（file:// 等）でも用語一覧が表示されるようにする。

  python3 tools/glossary_csv_to_embed_js.py
  python3 tools/glossary_csv_to_embed_js.py -o eisei1-data-glossary.js
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

# 第一種試験の科目区分（用語一覧）。問題データの law/rights/limit とは別系統。
CAT_JA_TO_CODE = {
    "関係法令（有害業務）": "lawH",
    "労働衛生（有害業務）": "rightsH",
    "関係法令（有害以外）": "lawN",
    "労働衛生（有害以外）": "rightsN",
    "労働生理": "limit",
}


def summary_from_desc(desc: str) -> str:
    t = re.sub(r"\s+", " ", (desc or "").strip())
    if not t:
        return "概要"
    m = re.match(r"^[^。．!?？]+[。．]?", t)
    s = m.group(0) if m else t
    if len(s) > 72:
        s = s[:69] + "…"
    return s


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "-i",
        "--input",
        type=Path,
        default=Path("docs/glossary-terms-checklist.csv"),
    )
    ap.add_argument(
        "-o", "--output", type=Path, default=Path("eisei1-data-glossary.js")
    )
    args = ap.parse_args()
    root = Path(__file__).resolve().parent.parent
    csv_path = args.input if args.input.is_absolute() else root / args.input
    out_path = args.output if args.output.is_absolute() else root / args.output
    if not csv_path.is_file():
        print(f"入力がありません: {csv_path}", file=sys.stderr)
        sys.exit(1)

    text = csv_path.read_text(encoding="utf-8-sig")
    reader = csv.DictReader(text.splitlines())
    if not reader.fieldnames or "カテゴリ" not in reader.fieldnames:
        print("CSV ヘッダーに カテゴリ,用語,解説 が必要です", file=sys.stderr)
        sys.exit(1)

    items: list[dict] = []
    for i, row in enumerate(reader):
        term = (row.get("用語") or "").strip()
        if not term:
            continue
        cat_ja = (row.get("カテゴリ") or "").strip()
        cat = CAT_JA_TO_CODE.get(cat_ja) or "lawN"
        desc = (row.get("解説") or "").strip()
        items.append(
            {
                "id": f"csv-{i}",
                "cat": cat,
                "term": term,
                "reading": "",
                "summary": summary_from_desc(desc),
                "desc": desc,
            }
        )

    lines = [
        "/* eisei1-data-glossary.js — 第一種衛生管理者試験 用語（埋め込み）",
        " * 再生成: python3 tools/glossary_csv_to_embed_js.py",
        " */",
        "let GLOSSARY_DATA = " + json.dumps(items, ensure_ascii=False, indent=2) + ";",
        "",
    ]
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"{len(items)} 件 -> {out_path}")


if __name__ == "__main__":
    main()
