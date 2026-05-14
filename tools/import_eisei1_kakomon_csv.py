#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
デスクトップ等の過去問CSV（開催年数,開催月,問番号,科目,問,(1)〜(5),正答番号,解説）
を tools が期待する列順・科目名に整形し data/eisei1_past_questions.csv に書き出す。

例:
  python3 tools/import_eisei1_kakomon_csv.py ~/Desktop/eisei1_kakomon.csv
  python3 tools/csv_to_eisei1_master.py -o eisei1-master-data.js
  python3 tools/build_question_pages.py
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TOOLS_DIR.parent


def normalize_subject(s: str) -> str:
    s = (s or "").strip()
    m = re.match(r"^(関係法令|労働衛生|労働生理)", s)
    if not m:
        raise ValueError(f"科目を正規化できません: {s!r}")
    return m.group(1)


def normalize_era_year(y: str) -> str:
    y = (y or "").strip()
    for a, b in (
        ("令和元年", "令和1年"),
        ("平成元年", "平成1年"),
        ("昭和元年", "昭和1年"),
    ):
        y = y.replace(a, b)
    return y


OUT_FIELDS = [
    "開催年数",
    "開催月",
    "科目",
    "問番号",
    "(1)",
    "(2)",
    "(3)",
    "(4)",
    "(5)",
    "正答番号",
    "問",
    "解説",
]


def main() -> None:
    ap = argparse.ArgumentParser(description="過去問CSVを data/eisei1_past_questions.csv に取り込む")
    ap.add_argument("src", type=Path, help="入力CSV（例: ~/Desktop/eisei1_kakomon.csv）")
    ap.add_argument(
        "-o",
        "--output",
        type=Path,
        default=_REPO_ROOT / "data" / "eisei1_past_questions.csv",
        help="出力先（既定: data/eisei1_past_questions.csv）",
    )
    args = ap.parse_args()

    text = args.src.expanduser().read_text(encoding="utf-8-sig")
    rows = list(csv.DictReader(text.splitlines()))
    if not rows:
        print("入力にデータ行がありません。", file=sys.stderr)
        sys.exit(1)

    out_rows: list[dict[str, str]] = []
    for i, row in enumerate(rows, start=2):
        try:
            subj = normalize_subject(row.get("科目", ""))
        except ValueError as e:
            print(f"行{i}: {e}", file=sys.stderr)
            sys.exit(1)
        opts = [(row.get(f"({j})") or "").strip() for j in range(1, 6)]
        if not all(opts):
            opts = [f"（図表）出題時の模式図・選択肢（{j}）を参照してください" for j in range(1, 6)]
        out_rows.append(
            {
                "開催年数": normalize_era_year(row.get("開催年数") or ""),
                "開催月": (row.get("開催月") or "").strip(),
                "科目": subj,
                "問番号": str(row.get("問番号", "")).strip(),
                "問": (row.get("問") or "").strip(),
                "(1)": opts[0],
                "(2)": opts[1],
                "(3)": opts[2],
                "(4)": opts[3],
                "(5)": opts[4],
                "正答番号": str(row.get("正答番号", "")).strip(),
                "解説": (row.get("解説") or "").strip(),
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=OUT_FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(out_rows)

    print(f"{len(out_rows)} 行 -> {args.output}")


if __name__ == "__main__":
    main()
