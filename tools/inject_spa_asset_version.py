#!/usr/bin/env python3
"""public_site/index.html の SPA 静的アセット URL にビルド版 ?v= を付与する。"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGET = ROOT / "public_site" / "index.html"

# バージョンクエリを付ける対象（同一オリジン・拡張子付きパスのみ）
ASSET_RE = re.compile(
    r"""(?P<attr>href|src)=(?P<q>["'])(?P<path>(?:/)?(?:eisei1-|site-(?:theme|analytics|pages|config|q-index|terms-index))[^"'?]+\.(?:js|css))(?P=q)""",
    re.IGNORECASE,
)
SPA_ASSET_V_RE = re.compile(
    r'window\.__SPA_ASSET_V__\s*=\s*""',
)


def version_from_env() -> str:
    sha = os.environ.get("GITHUB_SHA", "").strip()
    if len(sha) >= 7:
        return sha[:7]
    return "local"


def inject(text: str, version: str) -> str:
    def repl(m: re.Match[str]) -> str:
        path = m.group("path")
        if "?v=" in path:
            return m.group(0)
        return f'{m.group("attr")}={m.group("q")}{path}?v={version}{m.group("q")}'

    return ASSET_RE.sub(repl, text)


def inject_spa_asset_version_var(text: str, version: str) -> str:
    return SPA_ASSET_V_RE.sub(f'window.__SPA_ASSET_V__="{version}"', text, count=1)


def main() -> int:
    target = Path(os.environ.get("TARGET", str(DEFAULT_TARGET)))
    if not target.is_file():
        print(f"inject_spa_asset_version.py: 対象がありません: {target}", file=sys.stderr)
        return 1
    ver = version_from_env()
    original = target.read_text(encoding="utf-8")
    updated = inject_spa_asset_version_var(inject(original, ver), ver)
    if updated != original:
        target.write_text(updated, encoding="utf-8")
        print(f"inject_spa_asset_version.py: {target.name} に ?v={ver} を付与しました。")
    else:
        print(f"inject_spa_asset_version.py: 変更なし（{target.name}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
