#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data/eisei1_original_questions.csv（500問・5択）→ data/practice_questions.csv

一衛マスター専用。SPA 用 eisei1-master-data.js とは別に、静的 q/practice/ 用 CSV を生成する。

  python3 tools/import_eisei1_original_to_practice_csv.py
  python3 tools/import_eisei1_original_to_practice_csv.py --dry-run
"""

from __future__ import annotations

import argparse
import csv
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.site_config import field_labels  # noqa: E402

SOURCE = ROOT / "data" / "eisei1_original_questions.csv"
OUTPUT = ROOT / "data" / "practice_questions.csv"

# sync_original_eisei1_500_to_data.py の短縮科目 → site-config fields[].name
SUBJECT_TO_CATEGORY = {
    "関係法令": "関係法令（有害業務）",
    "労働衛生": "労働衛生（有害業務）",
    "労働生理": "労働生理",
}

CSV_COLUMNS = [
    "question_no",
    "type",
    "category",
    "tags",
    "stem",
    "preamble",
    "statement_a",
    "statement_b",
    "statement_c",
    "statement_d",
    "choice_1",
    "choice_2",
    "choice_3",
    "choice_4",
    "choice_5",
    "correct",
    "explanation",
    "explanation_summary",
    "explanation_correct",
    "explanation_choices",
    "explanation_point",
]


def norm(s: str | None) -> str:
    return (s or "").strip()


def category_for_subject(subject: str) -> str:
    subj = norm(subject)
    if subj in SUBJECT_TO_CATEGORY:
        return SUBJECT_TO_CATEGORY[subj]
    # site-config の canonical 名そのもの
    if subj in field_labels().values():
        return subj
    raise ValueError(f"未対応の科目: {subject!r}")


def row_to_practice(qno: int, row: dict, line_no: int) -> dict[str, str]:
    stem = norm(row.get("問"))
    if not stem:
        raise ValueError(f"行 {line_no}: 問（stem）が空")
    opts = [norm(row.get(f"({i})")) for i in range(1, 6)]
    if not all(opts):
        raise ValueError(f"行 {line_no}: 選択肢 (1)〜(5) が欠けています")
    raw_ans = norm(row.get("正答番号"))
    if not raw_ans.isdigit() or not (1 <= int(raw_ans) <= 5):
        raise ValueError(f"行 {line_no}: 正答番号が不正: {raw_ans!r}")
    ans = int(raw_ans)
    exp = norm(row.get("解説")) or "（解説は未入力です。）"
    subject = norm(row.get("科目"))
    category = category_for_subject(subject)
    return {
        "question_no": str(qno),
        "type": "single",
        "category": category,
        "tags": f"演習;{subject}",
        "stem": stem,
        "preamble": "",
        "statement_a": "",
        "statement_b": "",
        "statement_c": "",
        "statement_d": "",
        "choice_1": opts[0],
        "choice_2": opts[1],
        "choice_3": opts[2],
        "choice_4": opts[3],
        "choice_5": opts[4],
        "correct": str(ans),
        "explanation": exp,
        "explanation_summary": "",
        "explanation_correct": "",
        "explanation_choices": "",
        "explanation_point": "",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="eisei1_original_questions.csv → practice_questions.csv")
    ap.add_argument("--source", type=Path, default=SOURCE)
    ap.add_argument("--output", type=Path, default=OUTPUT)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-backup", action="store_true")
    args = ap.parse_args()

    source = args.source.resolve()
    output = args.output.resolve()
    if not source.is_file():
        print(f"入力がありません: {source}", file=sys.stderr)
        return 1

    rows_in = list(csv.DictReader(source.read_text(encoding="utf-8-sig").splitlines()))
    if not rows_in:
        print("入力 CSV が空です。", file=sys.stderr)
        return 1

    out_rows: list[dict[str, str]] = []
    for i, row in enumerate(rows_in, start=2):
        out_rows.append(row_to_practice(len(out_rows) + 1, row, i))

    by_cat: dict[str, int] = {}
    for r in out_rows:
        by_cat[r["category"]] = by_cat.get(r["category"], 0) + 1

    print(f"eisei1 original → practice CSV: {len(out_rows)} 問")
    for cat, n in sorted(by_cat.items()):
        print(f"  {cat}: {n}")
    print(f"  ソース: {source}")
    print(f"  出力:   {output}")

    if args.dry_run:
        return 0

    if output.is_file() and not args.no_backup:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = output.with_suffix(f".csv.bak-{stamp}")
        shutil.copy2(output, backup)
        print(f"  バックアップ: {backup.name}")

    with output.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        w.writerows(out_rows)

    print("書き出し完了。続けて python3 tools/build_question_pages.py を実行してください。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
