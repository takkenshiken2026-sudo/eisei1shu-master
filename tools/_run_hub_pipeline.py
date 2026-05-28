#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=ROOT, check=True)


def main() -> None:
    run([sys.executable, "tools/_fix_glossary_terms.py"])
    run([sys.executable, "tools/write_eisei1shu_hub_data.py"])
    run([sys.executable, "tools/_hub_validate_only.py"])
    err = ROOT / "_hub_errors.txt"
    print(err.read_text(encoding="utf-8")[:2000])


if __name__ == "__main__":
    main()
