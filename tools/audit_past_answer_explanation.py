#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""past_questions.csv の正答番号と解説本文の整合を検証する。"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.q_explanation import norm, parse_explanation_choices, question_ask_mode

DEFAULT_CSV = ROOT / "data" / "past_questions.csv"
CIRC = "①②③④⑤"


@dataclass
class Issue:
    level: str
    qid: str
    line: int
    kind: str
    message: str

    def format(self) -> str:
        return f"[{self.level}] past_questions.csv:{self.line} {self.qid} ({self.kind}) {self.message}"


def parse_correct(raw: str) -> int | None:
    raw = norm(raw)
    if not raw:
        return None
    if raw in CIRC:
        return CIRC.index(raw) + 1
    if raw.isdigit():
        n = int(raw)
        return n if 1 <= n <= 5 else None
    return None


def extract_stated_answers(text: str) -> list[int]:
    if not text:
        return []
    found: list[int] = []
    for m in re.finditer(r"正(?:答|解)(?:は|が)?\s*[（(]?([1-5])[）)]?", text):
        found.append(int(m.group(1)))
    for m in re.finditer(r"正(?:答|解)(?:は|が)?\s*([①②③④⑤])", text):
        found.append(CIRC.index(m.group(1)) + 1)
    for m in re.finditer(r"正しい(?:の)?(?:は|が)?\s*[（(]?([1-5])[）)]?", text):
        found.append(int(m.group(1)))
    for m in re.finditer(r"正しい(?:の)?(?:は|が)?\s*([①②③④⑤])", text):
        found.append(CIRC.index(m.group(1)) + 1)
    return found


def says_choice_is_wrong(text: str, n: int) -> bool:
    if not text:
        return False
    c = CIRC[n - 1]
    patterns = [
        rf"[（(]{n}[）)]\s*(?:は|が)?\s*(?:誤り|誤っている|正しくない|不適切である|間違)",
        rf"{c}\s*(?:は|が)?\s*(?:誤り|誤っている|正しくない|不適切である|間違)",
        rf"誤っている(?:の)?(?:は|が)\s*[（(]{n}[）)]",
        rf"誤り(?:である)?(?:の)?(?:は|が)\s*[（(]{n}[）)]",
    ]
    return any(re.search(p, text) for p in patterns)


def says_choice_is_correct_answer(text: str, n: int) -> bool:
    if not text:
        return False
    return n in extract_stated_answers(text)


def audit_row(row: dict, line_no: int) -> list[Issue]:
    issues: list[Issue] = []
    if norm(row.get("is_invalidated")).upper() == "TRUE":
        return issues

    correct = parse_correct(row.get("correct"))
    if correct is None:
        return issues

    year = row.get("exam_year", "")
    qno = row.get("question_no", "")
    qid = f"{year}-{qno}"
    stem = norm(row.get("stem"))
    mode = question_ask_mode(stem)

    fields = {
        "explanation": norm(row.get("explanation")),
        "explanation_summary": norm(row.get("explanation_summary")),
        "explanation_correct": norm(row.get("explanation_correct")),
    }

    # 正しいもの／適切なものを選ぶ設問で、解説が別番号を正答と記載
    if mode in ("most_correct", "unknown"):
        for field, text in fields.items():
            for stated in extract_stated_answers(text):
                if stated != correct:
                    issues.append(
                        Issue(
                            "ERROR",
                            qid,
                            line_no,
                            "stated_answer_mismatch",
                            f"{field} に正答{stated}と記載（CSV正答={correct}）",
                        )
                    )

        ec = fields["explanation_correct"]
        if ec:
            for n in range(1, 6):
                if n != correct and says_choice_is_correct_answer(ec, n):
                    if not says_choice_is_correct_answer(ec, correct):
                        issues.append(
                            Issue(
                                "ERROR",
                                qid,
                                line_no,
                                "wrong_choice_as_answer",
                                f"explanation_correct が誤肢{n}を正答と説明（CSV正答={correct}）",
                            )
                        )

    # 「誤っているもの」設問以外で、正答肢を誤りと説明
    if mode == "most_correct":
        ec = fields["explanation_correct"]
        if ec and says_choice_is_wrong(ec, correct):
            issues.append(
                Issue(
                    "ERROR",
                    qid,
                    line_no,
                    "correct_marked_wrong",
                    f"explanation_correct が正答({correct})を誤り扱い",
                )
            )

    # explanation_choices に正答肢が誤答として入っている
    parsed = parse_explanation_choices(norm(row.get("explanation_choices")))
    if correct in parsed:
        note = parsed[correct]
        if says_choice_is_wrong(note, correct):
            issues.append(
                Issue(
                    "ERROR",
                    qid,
                    line_no,
                    "choices_mark_correct_wrong",
                    f"explanation_choices が正答({correct})を誤肢扱い",
                )
            )

    return issues


def audit_csv(path: Path) -> list[Issue]:
    issues: list[Issue] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for line_no, row in enumerate(reader, start=2):
            issues.extend(audit_row(row, line_no))
    return issues


def main() -> int:
    ap = argparse.ArgumentParser(description="過去問 CSV の正答・解説整合監査")
    ap.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    args = ap.parse_args()

    if not args.csv.exists():
        print(f"CSV not found: {args.csv}", file=sys.stderr)
        return 1

    issues = audit_csv(args.csv)
    errors = [i for i in issues if i.level == "ERROR"]
    for issue in issues:
        print(issue.format())

    if errors:
        print(f"\n{len(errors)} error(s) in {args.csv.name}", file=sys.stderr)
        return 1

    print(f"OK: {args.csv.name} — no answer/explanation mismatches")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
