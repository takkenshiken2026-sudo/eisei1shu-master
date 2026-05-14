#!/usr/bin/env python3
"""
public_site/index.html の const SUPABASE_URL / const SUPABASE_KEY を環境変数で上書きする。
GitHub Actions では Repository secrets の SUPABASE_URL / SUPABASE_KEY を渡す。

例:
  SUPABASE_URL=https://xxxx.supabase.co SUPABASE_KEY=sb_publishable_... \\
    TARGET=public_site/index.html python3 tools/inject_supabase_into_html.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path


def main() -> None:
    target = os.environ.get("TARGET", "public_site/index.html")
    path = Path(target)
    if not path.is_file():
        print(f"inject_supabase_into_html.py: ファイルがありません: {path}", file=sys.stderr)
        sys.exit(1)
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = (
        os.environ.get("SUPABASE_KEY", "").strip()
        or os.environ.get("SUPABASE_ANON_KEY", "").strip()
    )
    if not url or not key:
        print(
            "inject_supabase_into_html.py: SUPABASE_URL と SUPABASE_KEY（または SUPABASE_ANON_KEY）が必要です。",
            file=sys.stderr,
        )
        sys.exit(1)
    text = path.read_text(encoding="utf-8")
    pat_url = re.compile(r"^const SUPABASE_URL = .*?;$", re.MULTILINE)
    pat_key = re.compile(r"^const SUPABASE_KEY = .*?;$", re.MULTILINE)
    text, c1 = pat_url.subn("const SUPABASE_URL = " + json.dumps(url) + ";", text, count=1)
    text, c2 = pat_key.subn("const SUPABASE_KEY = " + json.dumps(key) + ";", text, count=1)
    if c1 != 1 or c2 != 1:
        print(
            f"inject_supabase_into_html.py: 置換に失敗しました（SUPABASE_URL {c1} 件, SUPABASE_KEY {c2} 件）。",
            file=sys.stderr,
        )
        sys.exit(1)
    path.write_text(text, encoding="utf-8")
    print(f"inject_supabase_into_html.py: OK ({path})")


if __name__ == "__main__":
    main()
