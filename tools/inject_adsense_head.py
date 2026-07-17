#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全公開 HTML の <head> に Google AdSense スクリプトを挿入する。

site-config.json の adsenseClientId が空なら、既存の AdSense タグを除去する。
ビルド後（生成 HTML を含む）に実行する想定。

例:
  python3 tools/inject_adsense_head.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.html_footer import inject_adsense_head  # noqa: E402
from tools.site_config import adsense_client_id  # noqa: E402

SKIP_DIR_NAMES = frozenset(
    {
        ".git",
        "public_site",
        "reports",
        "node_modules",
        "sites",
        "docs",
        "__pycache__",
        ".cursor",
    }
)


def iter_html_files(root: Path) -> list[Path]:
    out: list[Path] = []
    for path in sorted(root.rglob("*.html")):
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        out.append(path)
    return out


def main() -> int:
    client = adsense_client_id()
    changed = 0
    for path in iter_html_files(ROOT):
        old = path.read_text(encoding="utf-8")
        new = inject_adsense_head(old)
        if new != old:
            path.write_text(new, encoding="utf-8")
            changed += 1
    if client:
        print(f"inject_adsense_head: updated {changed} file(s) (client={client})")
    else:
        print(f"inject_adsense_head: adsenseClientId 未設定 — removed from {changed} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
