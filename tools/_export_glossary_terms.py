#!/usr/bin/env python3
import csv, io
from pathlib import Path
p = Path(__file__).resolve().parents[1] / "data/glossary_terms.csv"
rows = list(csv.DictReader(io.StringIO(p.read_text(encoding="utf-8-sig"))))
terms = sorted({(r.get("term") or "").strip() for r in rows if (r.get("term") or "").strip()})
out = Path(__file__).resolve().parents[1] / "glossary_terms_list.txt"
out.write_text("\n".join(terms[:800]), encoding="utf-8")
print(len(terms), "->", out)
