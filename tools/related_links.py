#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""related_links 列のトークン解析（https:// は最初の : で分割しない）."""

from __future__ import annotations

import re


def parse_related_link_token(item: str) -> tuple[str, str]:
    """1件分を (target, label) に分解する。"""
    text = (item or "").strip()
    if not text:
        return "", ""
    if re.match(r"https?://", text, re.I):
        # https://example/path:表示ラベル（URL 内の : は除く）
        for i in range(len(text) - 1, 8, -1):
            if text[i] == ":":
                url, label = text[:i].strip(), text[i + 1 :].strip()
                if url.startswith(("http://", "https://")) and label:
                    return url, label
        return text, text
    if ":" in text:
        target, label = text.split(":", 1)
        return target.strip(), label.strip()
    return text, ""


def resolve_related_link_label(target: str, label: str, title: str) -> str:
    """明示ラベルが無い、または slug そのものなら記事タイトルを表示する。"""
    target = (target or "").strip()
    label = (label or "").strip()
    title = (title or "").strip()
    if not label or label == target:
        return title or target
    if re.fullmatch(r"[a-z0-9][a-z0-9-]*", label, re.I) and label == target:
        return title or target
    return label

