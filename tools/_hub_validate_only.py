#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_glossary_pages import make_term_lookup
from tools.knowledge_hub_rules import check_compare_row, check_mistakes_row, check_numbers_row
import csv

DATA = ROOT / "data"
_, gloss = [], []
import io

text = (DATA / "glossary_terms.csv").read_text(encoding="utf-8-sig")
rows = list(csv.DictReader(io.StringIO(text)))
for row in rows:
    t = (row.get("term") or "").strip()
    if t:
        gloss.append({"term": t, "slug_file": "x.html"})
lookup = make_term_lookup(gloss)

errors = []
for kind, path, fn in (
    ("compare", DATA / "comparisons.csv", check_compare_row),
    ("numbers", DATA / "numbers.csv", check_numbers_row),
    ("mistakes", DATA / "mistakes.csv", check_mistakes_row),
):
    rrows = list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8-sig"))))
    for i, row in enumerate(rrows, start=2):
        if not (row.get("title") or "").strip():
            continue
        for issue in fn(row, term_lookup=lookup, line=i):
            if issue.level == "ERROR":
                errors.append(f"{path.name}:{i} [{issue.column}] {issue.message}")

out = ROOT / "_hub_errors.txt"
out.write_text(f"count={len(errors)}\n" + "\n".join(errors), encoding="utf-8")
print(len(errors))
