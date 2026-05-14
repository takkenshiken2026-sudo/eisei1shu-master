#!/usr/bin/env python3
"""Check root-relative href in static HTML against the repo filesystem.

SPA routes (/quiz/*, /dashboard, /review) are allowed without a matching file.
Run from repo root: python3 tools/verify_static_internal_links.py
"""
from __future__ import annotations

import pathlib
import re
import sys
import urllib.parse
from typing import Optional

SPA_PREFIXES = (
    "/quiz/past",
    "/quiz/orig",
    "/quiz/ichimondou",
    "/dashboard",
    "/review",
)

HREF_RE = re.compile(r'href\s*=\s*"(/[^"#?]*)')


def is_spa(path: str) -> bool:
    for pre in SPA_PREFIXES:
        if path == pre or path.startswith(pre + "/"):
            return True
    return False


def resolve(root: pathlib.Path, path: str) -> Optional[pathlib.Path]:
    articles = root / "articles"
    terms = root / "terms"
    p = path.rstrip("/") or "/"
    if p == "/":
        return root / "index.html"
    if p.startswith("/articles/"):
        rel = p[len("/articles/") :]
        if not rel or rel.endswith("/"):
            return articles / "index.html"
        if not rel.endswith(".html"):
            rel = rel + ".html"
        return articles / rel
    if p == "/articles":
        return articles / "index.html"
    if p.startswith("/terms/"):
        rel = p[len("/terms/") :]
        if not rel or rel.endswith("/"):
            return terms / "index.html"
        if not rel.endswith(".html"):
            rel = rel + ".html"
        return terms / rel
    if p == "/terms":
        return terms / "index.html"
    if p.startswith("/q/"):
        return root / path.lstrip("/")
    if p.startswith("/"):
        return root / p.lstrip("/")
    return None


def exists_target(fs: pathlib.Path) -> bool:
    if fs.is_file():
        return True
    if fs.is_dir() and (fs / "index.html").is_file():
        return True
    return False


def scan_file(root: pathlib.Path, html: pathlib.Path) -> list[tuple[str, str, str]]:
    broken: list[tuple[str, str, str]] = []
    text = html.read_text(encoding="utf-8")
    for m in HREF_RE.finditer(text):
        raw = m.group(1)
        path = urllib.parse.unquote(raw.split("#")[0].split("?")[0])
        if not path or path.startswith("//"):
            continue
        if is_spa(path):
            continue
        fs = resolve(root, path)
        if fs is None:
            broken.append((str(html.relative_to(root)), raw, "unresolved path"))
            continue
        if not exists_target(fs):
            broken.append(
                (str(html.relative_to(root)), raw, f"missing: {fs.relative_to(root)}")
            )
    return broken


def main() -> int:
    root = pathlib.Path(__file__).resolve().parent.parent
    targets: list[pathlib.Path] = [root / "index.html"]
    targets.extend(sorted((root / "articles").glob("*.html")))
    targets.extend(sorted((root / "terms").glob("*.html")))
    all_broken: list[tuple[str, str, str]] = []
    total = 0
    for html in targets:
        if not html.is_file():
            continue
        hits = len(HREF_RE.findall(html.read_text(encoding="utf-8")))
        total += hits
        all_broken.extend(scan_file(root, html))
    print(f"Checked {total} root-relative href in {len(targets)} HTML files.")
    if all_broken:
        print(f"BROKEN ({len(all_broken)}):")
        for src, href, reason in all_broken:
            print(f"  {src}: {href} -> {reason}")
        return 1
    print("OK: no broken internal links.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
