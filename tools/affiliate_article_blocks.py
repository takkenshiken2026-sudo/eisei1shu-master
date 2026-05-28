#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HTML blocks for affiliate guide articles (product cards, inline links)."""

from __future__ import annotations

import html
import re

from tools.site_config import brand_name, exam_name

# A8.net（第一種衛生管理者）
A8_SMART = (
    "https://px.a8.net/svt/ejp?a8mat=4B3TF0+DUBVNM+4LOQ+BW0YB"
    "&a8ejpredirect=https%3A%2F%2Fwww.joho-gakushu.or.jp%2Feiseikanrisya%2F"
    "%3Futm_source%3DAffi%26utm_medium%3Dlist%26utm_campaign%3D01"
)
A8_ONSUKU = (
    "https://px.a8.net/svt/ejp?a8mat=4B3TF0+DUXB9E+408S+BW0YB"
    "&a8ejpredirect=https%3A%2F%2Fonsuku.jp%2Ftraining%2Feisei2"
)

INLINE_LINK_RE = re.compile(r"\[\[link:([^\]|]+)\|([^\]]+)\]\]")
AFFILIATE_COURSE_CARDS = "[[affiliate-course-cards]]"

EXTERNAL_REL = "nofollow sponsored noopener noreferrer"


def apply_vars(value: str) -> str:
    text = (value or "").strip()
    return (
        text.replace("Sampleマスター", brand_name())
        .replace("◯◯試験（プレースホルダー）", exam_name())
        .replace("◯◯試験", exam_name())
    )


def split_semicolon(value: str) -> list[str]:
    return [x.strip() for x in (value or "").split(";") if x.strip()]


def _affiliate_anchor(href: str, label: str, class_name: str = "") -> str:
    cls = f' class="{class_name}"' if class_name else ""
    return (
        f'<a href="{html.escape(href, quote=True)}" target="_blank" rel="{EXTERNAL_REL}"{cls}>'
        f"{html.escape(label)}</a>"
    )


def affiliate_course_cards_html(article_slug: str) -> str:
    if article_slug != "affiliate-online-course-compare":
        return ""
    img_base = "../../images/affiliate"
    cards = [
        {
            "name": "SMART合格講座（第一種）",
            "vendor": "情報学習支援協会",
            "image": f"{img_base}/eisei1-smart-goukaku.jpg",
            "image_alt": "SMART合格講座 衛生管理者のイメージ",
            "price": "29,700円（税込・買い切り）",
            "meta": "視聴3年・講義約12時間40分・SMART答練",
            "points": (
                "宮川隆氏による動画講義で法令・衛生の流れを追いやすい",
                "有害業務の追加講義あり。長期で見直しやすい",
            ),
            "href": A8_SMART,
            "cta": "SMART合格講座の詳細を見る",
        },
        {
            "name": "衛生管理者オンライン通信講座",
            "vendor": "オンスク.JP",
            "image": f"{img_base}/eisei1-onsuku-eisei2.jpg",
            "image_alt": "オンスク 衛生管理者オンライン通信講座",
            "price": "月額1,078〜1,628円（税込・ウケホーダイ）",
            "meta": "講義50回・約4.5時間・練習536問",
            "points": (
                "日本衛生管理者ネットワーク監修。進捗・復習機能が充実",
                "短期でコストを抑えたい社会人向け。解約しやすい月額制",
            ),
            "href": A8_ONSUKU,
            "cta": "オンスク講座の詳細を見る",
        },
    ]
    items = []
    for card in cards:
        points_html = "".join(f"<li>{html.escape(p)}</li>" for p in card["points"])
        items.append(
            '<article class="affiliate-course-card">'
            f'<a class="affiliate-course-card-media" href="{html.escape(card["href"], quote=True)}" '
            f'target="_blank" rel="{EXTERNAL_REL}">'
            f'<img src="{html.escape(card["image"])}" alt="{html.escape(card["image_alt"])}" '
            'width="400" height="225" loading="lazy" decoding="async">'
            "</a>"
            '<div class="affiliate-course-card-body">'
            f'<h3 class="affiliate-course-card-title">{html.escape(card["name"])}</h3>'
            f'<p class="affiliate-course-card-vendor">{html.escape(card["vendor"])}</p>'
            f'<p class="affiliate-course-card-price">{html.escape(card["price"])}</p>'
            f'<p class="affiliate-course-card-meta">{html.escape(card["meta"])}</p>'
            f'<ul class="affiliate-course-card-points">{points_html}</ul>'
            f'{_affiliate_anchor(card["href"], card["cta"], "affiliate-course-card-cta")}'
            "</div></article>"
        )
    return (
        '<div class="affiliate-course-cards" role="list" aria-label="オンライン講座の比較">'
        + "".join(items)
        + "</div>"
    )


def format_inline_markup(text: str, article_slug: str) -> str:
    """Escape text but preserve [[link:url|label]] and affiliate card placeholders."""
    if AFFILIATE_COURSE_CARDS in text:
        text = text.replace(AFFILIATE_COURSE_CARDS, affiliate_course_cards_html(article_slug))
    chunks: list[str] = []
    pos = 0
    for match in INLINE_LINK_RE.finditer(text):
        if match.start() > pos:
            raw = text[pos : match.start()]
            chunks.append(html.escape(raw).replace("\n", "<br>"))
        href = match.group(1).strip()
        label = match.group(2).strip()
        rel = EXTERNAL_REL if href.startswith(("http://", "https://")) else "noopener noreferrer"
        chunks.append(
            f'<a href="{html.escape(href, quote=True)}" target="_blank" rel="{rel}">'
            f"{html.escape(label)}</a>"
        )
        pos = match.end()
    if pos < len(text):
        raw = text[pos:]
        if raw.lstrip().startswith("<div class=\"affiliate-course-cards"):
            chunks.append(raw)
        else:
            chunks.append(html.escape(raw).replace("\n", "<br>"))
    return "".join(chunks)


def article_body_html(text: str, article_slug: str) -> str:
    """Paragraphs / lists with inline links and affiliate blocks."""
    body = apply_vars(text)
    if not body:
        return ""
    if body.strip() == AFFILIATE_COURSE_CARDS:
        return affiliate_course_cards_html(article_slug)

    parts = [p.strip() for p in re.split(r"\n{2,}", body) if p.strip()] or [body]
    blocks: list[str] = []
    for part in parts:
        if part.strip() == AFFILIATE_COURSE_CARDS:
            blocks.append(affiliate_course_cards_html(article_slug))
            continue
        if part.lstrip().startswith("<div class=\"affiliate-course-cards"):
            blocks.append(part)
            continue
        items = split_semicolon(part)
        if len(items) >= 2 and "[[" not in part:
            blocks.append("<ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in items) + "</ul>")
        else:
            blocks.append(f"<p>{format_inline_markup(part, article_slug)}</p>")
    return "\n".join(blocks)
