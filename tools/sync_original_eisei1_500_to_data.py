#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docs/original_eisei1_500.csv（5択・長い科目名）を
data/eisei1_original_questions.csv（csv_to_eisei1_master / build_question_pages 用の列形式）
に変換する。

同一分野（law / rights / limit）に200問ずつ等、問番号が重複するため、
分野ごとに通し番号の問番号を振り直す。

例:
  python3 tools/sync_original_eisei1_500_to_data.py
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

# build_ichimon_pages の SUBJECT_TO_FIELD と同じくらいの対応
LONG_SUBJECT_TO_FIELD: dict[str, str] = {
    "関係法令(有害業務に係るもの)": "law",
    "関係法令(有害業務に係るもの以外のもの)": "law",
    "労働衛生(有害業務に係るもの)": "rights",
    "労働衛生(有害業務に係るもの以外のもの)": "rights",
    "労働生理": "limit",
}

FIELD_TO_SHORT_SUBJECT = {"law": "関係法令", "rights": "労働衛生", "limit": "労働生理"}

OUT_COLUMNS = [
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


def load_rows(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8-sig")
    return list(csv.DictReader(text.splitlines()))


def main() -> None:
    ap = argparse.ArgumentParser(description="オリジナル500 CSV を data 用に同期")
    ap.add_argument(
        "--src",
        type=Path,
        default=None,
        help="既定: docs/original_eisei1_500.csv",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="既定: data/eisei1_original_questions.csv",
    )
    args = ap.parse_args()

    repo = Path(__file__).resolve().parent.parent
    src = args.src or (repo / "docs" / "original_eisei1_500.csv")
    out = args.out or (repo / "data" / "eisei1_original_questions.csv")

    if not src.exists():
        print(f"入力がありません: {src}", file=sys.stderr)
        sys.exit(1)

    rows = load_rows(src)
    per_field_num: dict[str, int] = defaultdict(int)
    out_rows: list[dict[str, str]] = []

    for line_no, row in enumerate(rows, start=2):
        subj_long = (row.get("科目") or "").strip()
        field = LONG_SUBJECT_TO_FIELD.get(subj_long)
        if not field:
            print(f"不明な科目 {subj_long!r}（{src} 行 {line_no}）", file=sys.stderr)
            sys.exit(1)

        stem = (row.get("問") or "").strip()
        if not stem:
            print(f"問 欠落（{src} 行 {line_no}）", file=sys.stderr)
            sys.exit(1)

        raw_ans = str(row.get("正答番号") or "").strip()
        if not raw_ans.isdigit():
            print(f"正答番号が不正 {raw_ans!r}（{src} 行 {line_no}）", file=sys.stderr)
            sys.exit(1)
        ans = int(raw_ans)
        if not (1 <= ans <= 5):
            print(f"正答番号が1〜5以外（{src} 行 {line_no}）", file=sys.stderr)
            sys.exit(1)

        opts = [(row.get(f"({i})") or "").strip() for i in range(1, 6)]
        if not all(opts):
            print(f"選択肢欠け（{src} 行 {line_no}）", file=sys.stderr)
            sys.exit(1)

        exp = (row.get("解説") or "").strip()
        era = (row.get("開催年数") or "").strip() or "オリジナル"

        per_field_num[field] += 1
        new_num = per_field_num[field]

        out_rows.append(
            {
                "開催年数": era,
                "開催月": "",
                "科目": FIELD_TO_SHORT_SUBJECT[field],
                "問番号": str(new_num),
                "(1)": opts[0],
                "(2)": opts[1],
                "(3)": opts[2],
                "(4)": opts[3],
                "(5)": opts[4],
                "正答番号": str(ans),
                "問": stem,
                "解説": exp,
            }
        )

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=OUT_COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(out_rows)

    print(f"sync_original: {len(out_rows)} 行 -> {out}")


if __name__ == "__main__":
    main()
