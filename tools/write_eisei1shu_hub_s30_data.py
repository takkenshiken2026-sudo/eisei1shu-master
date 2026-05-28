#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate eisei1shu hub S30 rows and write all CSVs."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.write_eisei1shu_hub_s30 import DATA, HEADER_COMPARE, HEADER_MISTAKES, HEADER_NUMBERS  # noqa: E402
from tools.write_eisei1shu_hub_s30_content import COMPARISONS, MISTAKES, NUMBERS  # noqa: E402


def write_csv(path: Path, header: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    assert len(COMPARISONS) == 10, len(COMPARISONS)
    assert len(NUMBERS) == 10, len(NUMBERS)
    assert len(MISTAKES) == 10, len(MISTAKES)
    write_csv(DATA / "comparisons.csv", HEADER_COMPARE, COMPARISONS)
    write_csv(DATA / "numbers.csv", HEADER_NUMBERS, NUMBERS)
    write_csv(DATA / "mistakes.csv", HEADER_MISTAKES, MISTAKES)
    print(f"wrote compare={len(COMPARISONS)} numbers={len(NUMBERS)} mistakes={len(MISTAKES)}")


if __name__ == "__main__":
    main()
