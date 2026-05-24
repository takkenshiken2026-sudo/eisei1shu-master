# -*- coding: utf-8 -*-
"""用語詳細本文：定義文からの追記のみ（汎用テンプレのパディングは行わない）。"""
from __future__ import annotations

from glossary_derive_content import derive_extra_paragraphs


def pad_term_detail_body(
    body: str,
    *,
    term: str,
    category: str = "",
    core: str = "",
    definition: str = "",
) -> str:
    text = (body or "").strip()
    if definition:
        extra = derive_extra_paragraphs(definition, text)
        if extra:
            text = (text + "\n\n" + extra).strip()
    return text
