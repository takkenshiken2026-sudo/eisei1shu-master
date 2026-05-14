#!/usr/bin/env python3
"""
public_site/index.html に、GitHub Actions の Secrets から
  - GA4 測定ID（window.__GA4_MEASUREMENT_ID__）
  - Google サーチコンソールの所有権確認 meta（GOOGLE_SITE_VERIFICATION）
を反映する。

環境変数（いずれも任意）:
  GA4_MEASUREMENT_ID        例: G-XXXXXXXXXX
  GOOGLE_SITE_VERIFICATION  例: （サーチコンソールが発行するトークン文字列）

例:
  TARGET=public_site/index.html GA4_MEASUREMENT_ID=G-XXX GOOGLE_SITE_VERIFICATION=abc... \\
    python3 tools/inject_site_analytics_secrets.py
"""
from __future__ import annotations

import html
import json
import os
import re
import sys
from pathlib import Path

MARKER = "<!--SITE_VERIFICATION_META_INJECT-->"
GA_LINE_RE = re.compile(
    r'^(\s*)<script>window\.__GA4_MEASUREMENT_ID__\s*=\s*"";\s*</script>\s*$',
    re.MULTILINE,
)


def main() -> None:
    target = os.environ.get("TARGET", "public_site/index.html")
    path = Path(target)
    if not path.is_file():
        print(f"inject_site_analytics_secrets.py: ファイルがありません: {path}", file=sys.stderr)
        sys.exit(1)

    text = path.read_text(encoding="utf-8")
    gsc = os.environ.get("GOOGLE_SITE_VERIFICATION", "").strip()
    if gsc:
        esc = html.escape(gsc, quote=True)
        if MARKER not in text:
            print("inject_site_analytics_secrets.py: マーカーが見つかりません", file=sys.stderr)
            sys.exit(1)
        text = text.replace(
            MARKER,
            f'<meta name="google-site-verification" content="{esc}" />',
            1,
        )
    else:
        text = text.replace(MARKER, "")

    ga = os.environ.get("GA4_MEASUREMENT_ID", "").strip()
    if ga:
        if not re.match(r"^G-[A-Z0-9]+$", ga):
            print(
                f"inject_site_analytics_secrets.py: GA4_MEASUREMENT_ID の形式が不正です: {ga!r}",
                file=sys.stderr,
            )
            sys.exit(1)
        repl = f'<script>window.__GA4_MEASUREMENT_ID__ = {json.dumps(ga)};</script>'
        text, n = GA_LINE_RE.subn(repl, text, count=1)
        if n != 1:
            print(
                "inject_site_analytics_secrets.py: GA4 の window 行の置換に失敗しました。",
                file=sys.stderr,
            )
            sys.exit(1)

    path.write_text(text, encoding="utf-8")
    print(f"inject_site_analytics_secrets.py: OK ({path})")


if __name__ == "__main__":
    main()
