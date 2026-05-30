#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SEO 記事本文向けの軽量マークアップ → HTML 変換。"""

from __future__ import annotations

import html
import re
from collections.abc import Callable

# 段落内の「A、B、C」列挙を箇条書きに起こすトリガー（保守的に限定）
_ENUM_TRIGGER = re.compile(
    r"(特に見落としやすいのは、|"
    r"(?:押さえる|確認(?:すべき)?)(?:項目|点)(?:は、)|"
    r"チェック(?:したい|すべき)?(?:項目|点)(?:は、)|"
    r"(?:手順|流れ|ポイント|ステップ)(?:は、))"
    r"([^。]{4,160}?)"
    r"(?:です|。|であり)",
)

_GENERIC_ENUM = re.compile(
    r"(?:[^。]{0,100}?(?:は、|として、))"
    r"((?:[^、。]{2,42}、){2,}[^、。]{2,42})"
    r"(?:です|。|であり|と)",
)

# CSV 本文に混入した <table class="seo-info-table">…</table>（エスケープされて露出する）
INLINE_SEO_TABLE_RE = re.compile(
    r'<table\s+class=["\']seo-info-table(?:\s+term-compare-table)?["\'][^>]*>.*?</table>',
    re.IGNORECASE | re.DOTALL,
)
_DANGEROUS_TAG_RE = re.compile(r"<(script|iframe|object|embed|style|link)\b", re.IGNORECASE)
_CELL_RE = re.compile(r"<t([hd])[^>]*>(.*?)</t\1>", re.IGNORECASE | re.DOTALL)


def split_semicolon(value: str) -> list[str]:
    return [x.strip() for x in (value or "").split(";") if x.strip()]


def _comma_list_items(chunk: str) -> list[str]:
    items = [x.strip() for x in re.split(r"[、,]", chunk) if x.strip()]
    if len(items) < 2:
        return []
    if any(len(item) > 52 for item in items):
        return []
    return items


def _try_trigger_list(block: str) -> str | None:
    match = _ENUM_TRIGGER.search(block)
    if match:
        items = _comma_list_items(match.group(2))
    else:
        match = _GENERIC_ENUM.search(block)
        if not match:
            return None
        items = _comma_list_items(match.group(1))
    if not items:
        return None
    before = block[: match.start()].rstrip()
    after = block[match.end() :].strip().lstrip("。．. ")
    parts: list[str] = []
    if before:
        parts.append(before)
    parts.append("\n".join(f"- {item}" for item in items))
    if after:
        parts.append(after)
    return "\n\n".join(parts)


def inject_comma_sentence_list(text: str) -> str:
    """列挙トリガーが無い段落でも、読点の多い文から箇条書きを起こす（控えめ）。"""
    if not text.strip() or "\n-" in text or ";" in text:
        return text

    blocks = re.split(r"\n{2,}", text.strip())
    out: list[str] = []
    for block in blocks:
        if block.lstrip().startswith("- "):
            out.append(block)
            continue
        triggered = _try_trigger_list(block)
        if triggered:
            out.append(triggered)
            continue

        sentences = [s for s in re.split(r"(?<=[。！？])", block) if s.strip()]
        best_items: list[str] = []
        best_idx = -1
        best_prefix = ""
        for idx, sent in enumerate(sentences):
            if sent.count("、") < 2:
                continue
            pos = sent.rfind("は、")
            chunk = sent[pos + 2 :] if pos >= 0 else sent
            chunk = re.sub(r"(?:です|ます|でした|である|であり)[。]?$", "", chunk.strip())
            chunk = chunk.rstrip("。")
            items = _comma_list_items(chunk)
            if len(items) >= 2 and len(items) > len(best_items):
                best_items = items
                best_idx = idx
                best_prefix = sent[:pos].strip() if pos >= 0 else ""
        if best_idx < 0:
            out.append(block)
            continue
        rebuilt: list[str] = []
        if best_idx > 0:
            rebuilt.append("".join(sentences[:best_idx]).strip())
        if best_prefix:
            rebuilt.append(best_prefix + "。")
        rebuilt.append("\n".join(f"- {item}" for item in best_items))
        tail = "".join(sentences[best_idx + 1 :]).strip()
        if tail:
            rebuilt.append(tail)
        out.append("\n\n".join(p for p in rebuilt if p))
    return "\n\n".join(out)


def strip_inline_seo_tables(text: str) -> str:
    """本文中の seo-info-table ブロックを除去（重複テンプレ表・エスケープ露出防止）。"""
    if not text or "<table" not in text.lower():
        return text
    out = INLINE_SEO_TABLE_RE.sub("", text)
    return re.sub(r"\n{3,}", "\n\n", out).strip()


def _cell_plain(html_fragment: str) -> str:
    plain = re.sub(r"<[^>]+>", "", html_fragment)
    return html.unescape(plain).strip()


def inline_seo_table_to_html(fragment: str) -> str:
    """許可タグのみで表を再構築（CSV 由来の属性・不正タグを落とす）。"""
    if _DANGEROUS_TAG_RE.search(fragment):
        return ""
    rows: list[list[tuple[str, str]]] = []
    for tr in re.finditer(r"<tr[^>]*>(.*?)</tr>", fragment, re.IGNORECASE | re.DOTALL):
        cells: list[tuple[str, str]] = []
        for m in _CELL_RE.finditer(tr.group(1)):
            tag = m.group(1).lower()
            text = _cell_plain(m.group(2))
            if text:
                cells.append((tag, text))
        if cells:
            rows.append(cells)
    if not rows:
        return ""
    thead = ""
    tbody_rows: list[str] = []
    first = rows[0]
    if first and all(tag == "th" for tag, _ in first):
        thead = (
            "<thead><tr>"
            + "".join(f"<th>{html.escape(label)}</th>" for _, label in first)
            + "</tr></thead>"
        )
        data_rows = rows[1:]
    else:
        data_rows = rows
    for cells in data_rows:
        tbody_rows.append(
            "<tr>"
            + "".join(
                (
                    f"<th>{html.escape(text)}</th>"
                    if tag == "th"
                    else f"<td>{html.escape(text)}</td>"
                )
                for tag, text in cells
            )
            + "</tr>"
        )
    if not thead and not tbody_rows:
        return ""
    body = "".join(tbody_rows)
    return (
        '<table class="seo-info-table">'
        f"{thead}<tbody>{body}</tbody></table>"
    )


def _split_text_and_tables(text: str) -> list[tuple[str, str]]:
    """('text'|'table', chunk) の順序付き分割。"""
    if not text:
        return []
    parts: list[tuple[str, str]] = []
    last = 0
    for match in INLINE_SEO_TABLE_RE.finditer(text):
        if match.start() > last:
            parts.append(("text", text[last : match.start()]))
        parts.append(("table", match.group(0)))
        last = match.end()
    if last < len(text):
        parts.append(("text", text[last:]))
    return parts or [("text", text)]


def inject_enumeration_lists(text: str) -> str:
    """既存 CSV 本文から列挙句を検出し `- ` 行のブロックを挿入する。"""
    if not text.strip() or "\n-" in text:
        return text

    blocks = re.split(r"\n{2,}", text.strip())
    out_blocks: list[str] = []
    for block in blocks:
        if block.lstrip().startswith("- "):
            out_blocks.append(block)
            continue
        triggered = _try_trigger_list(block)
        if triggered:
            out_blocks.append(triggered)
        else:
            out_blocks.append(block)
    merged = "\n\n".join(out_blocks)
    return inject_comma_sentence_list(merged)


def _render_paragraph(text: str, *, term_hrefs: dict[str, str] | None = None, linked_terms: set[str] | None = None) -> str:
    if term_hrefs and linked_terms is not None:
        from tools.internal_links import link_terms_in_plaintext

        return f"<p>{link_terms_in_plaintext(text, term_hrefs, linked_terms)}</p>"
    return f"<p>{html.escape(text).replace(chr(10), '<br>')}</p>"


def _render_block(
    block: str,
    *,
    term_hrefs: dict[str, str] | None = None,
    linked_terms: set[str] | None = None,
) -> str:
    lines = block.split("\n")
    non_empty = [ln for ln in lines if ln.strip()]
    if non_empty and all(ln.lstrip().startswith("- ") for ln in non_empty):
        items = [ln.lstrip()[2:].strip() for ln in non_empty]
        return "<ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in items) + "</ul>"

    if ";" in block and "\n" not in block:
        items = split_semicolon(block)
        if len(items) >= 2:
            return "<ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in items) + "</ul>"

    if block.startswith("### "):
        heading = block[4:].split("\n", 1)[0].strip()
        rest = block[4:].split("\n", 1)[1] if "\n" in block[4:] else ""
        html_parts = [f'<h3 class="term-subheading">{html.escape(heading)}</h3>']
        if rest.strip():
            html_parts.append(
                _render_block(rest.strip(), term_hrefs=term_hrefs, linked_terms=linked_terms)
            )
        return "".join(html_parts)

    paras = [p.strip() for p in re.split(r"\n{2,}", block) if p.strip()] or [block.strip()]
    return "".join(
        _render_paragraph(p, term_hrefs=term_hrefs, linked_terms=linked_terms)
        for p in paras
        if p.strip()
    )


def _seo_plain_body_html(
    text: str,
    *,
    term_hrefs: dict[str, str] | None = None,
    linked_terms: set[str] | None = None,
) -> str:
    body = inject_enumeration_lists(text.strip())
    if not body:
        return ""
    blocks = [b.strip() for b in re.split(r"\n{2,}", body) if b.strip()] or [body]
    return "".join(
        _render_block(block, term_hrefs=term_hrefs, linked_terms=linked_terms) for block in blocks
    )


def seo_section_body_html(
    text: str,
    *,
    transform: Callable[[str], str] | None = None,
    term_hrefs: dict[str, str] | None = None,
    linked_terms: set[str] | None = None,
) -> str:
    """セクション本文 HTML。`- ` 行・`;` 区切り・`###` 小見出し・埋め込み seo-info-table に対応。"""
    body = (transform(text) if transform else text).strip()
    if not body:
        return ""
    segments = _split_text_and_tables(body)
    out: list[str] = []
    for kind, chunk in segments:
        if kind == "table":
            table_html = inline_seo_table_to_html(chunk)
            if table_html:
                out.append(table_html)
            continue
        rendered = _seo_plain_body_html(
            chunk, term_hrefs=term_hrefs, linked_terms=linked_terms
        )
        if rendered:
            out.append(rendered)
    return "".join(out)
