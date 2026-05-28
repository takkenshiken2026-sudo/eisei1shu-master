#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for name in ("eisei1shu", "eisei2shu"):
    proj = Path(f"/Users/otedaiki/Projects/{name}-master")
    if name == "eisei1shu":
        proj = ROOT
    elif name == "eisei2shu":
        proj = Path("/Users/otedaiki/Projects/eisei2shu-master")
    if name == "eisei2shu":
        subprocess.run([sys.executable, str(proj / "tools/write_eisei2shu_hub_data.py")], cwd=proj, check=True)
    else:
        subprocess.run([sys.executable, str(proj / "tools/write_eisei1shu_hub_data.py")], cwd=proj, check=True)
    r = subprocess.run(
        [sys.executable, str(proj / "tools/validate_csv.py")],
        cwd=proj,
        capture_output=True,
        text=True,
    )
    err_lines = [ln for ln in (r.stderr + r.stdout).splitlines() if "[ERROR]" in ln]
    out = proj / f"_validate_{name}.txt"
    out.write_text(
        f"exit={r.returncode}\nerrors={len(err_lines)}\n" + "\n".join(err_lines[:50]),
        encoding="utf-8",
    )
    print(name, r.returncode, len(err_lines))
