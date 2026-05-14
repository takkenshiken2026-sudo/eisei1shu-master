#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
問題ID・URLスラッグ（docs/question-id-url-slug-spec.md）の共通実装。
csv_to_eisei1_master.py と build_question_pages.py から利用する。
"""

from __future__ import annotations

import re
import unicodedata

FIELD_MAP = {"関係法令": "law", "労働衛生": "rights", "労働生理": "limit"}
FIELD_NUM = {"law": 1, "rights": 2, "limit": 3}

# month_bucket のタグ出現順（csv_to_eisei1_master と同一）
_MONTH_TAGS = ("カテゴリ別90", "前期", "後期", "10月", "4月")

_BUCKET_TO_SLUG = {
    "カテゴリ別90": "cat90",
    "前期": "zenki",
    "後期": "koki",
    "10月": "oct",
    "4月": "apr",
}


def normalize_era(s: str) -> str:
    return re.sub(r"\s+", "", (s or "").strip())


def strip_era_parenthetical(開催年数: str) -> str:
    """令和7年（2025）→ 令和7年"""
    s = normalize_era(開催年数)
    return re.sub(r"（[^）]*）", "", s)


def month_bucket(s: str) -> str:
    """開催月からバケット文字列（従来ロジックと同一）。空は unknown-month。"""
    m = (s or "").strip()
    if not m:
        return "unknown-month"
    for tag in _MONTH_TAGS:
        if tag in m:
            return tag
    return m


def month_key_for_pool(row: dict) -> str:
    """
    pool_year の辞書キー用。オリジナルで開催月が空のときは default（規約）。
    """
    era = normalize_era(row.get("開催年数") or "")
    raw = (row.get("開催月") or "").strip()
    if era == "オリジナル" and not raw:
        return "default"
    return month_bucket(row.get("開催月") or "")


def slugify_nfkc(text: str) -> str:
    """NFKC 後、小文字 a-z0-9 以外を - に。"""
    s = unicodedata.normalize("NFKC", (text or "").strip()).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    if not s:
        raise ValueError(f"スラッグ化結果が空: {text!r}")
    return s


def era_slug_past(開催年数: str) -> str:
    """過去問の元号スラッグ r07 / h31 / s63"""
    era = strip_era_parenthetical(開催年数)
    m = re.match(r"^令和(\d+)年", era)
    if m:
        return f"r{int(m.group(1)):02d}"
    m = re.match(r"^平成(\d+)年", era)
    if m:
        return f"h{int(m.group(1)):02d}"
    m = re.match(r"^昭和(\d+)年", era)
    if m:
        return f"s{int(m.group(1)):02d}"
    raise ValueError(f"開催年数から era スラッグを作れません: {開催年数!r}")


def session_or_pool_slug(開催年数: str, 開催月: str) -> str:
    """
    過去問: session スラッグ、オリジナル: pool スラッグ。
    オリジナルで開催月が空のときは default。
    """
    era = normalize_era(開催年数)
    raw = (開催月 or "").strip()
    if era == "オリジナル" and not raw:
        return "default"
    bucket = month_bucket(開催月 or "")
    if bucket in _BUCKET_TO_SLUG:
        return _BUCKET_TO_SLUG[bucket]
    return slugify_nfkc(bucket)


def question_string_id_past(era_slug: str, session: str, field: str, num_str: str) -> str:
    return f"past.{era_slug}.{session}.{field}.{num_str}"


def question_string_id_orig(pool: str, field: str, num_str: str) -> str:
    return f"orig.{pool}.{field}.{num_str}"


def relative_url_path_past(era_slug: str, session: str, field: str, qwidth: str) -> str:
    return f"q/past/{era_slug}/{session}/{field}/{qwidth}/index.html"


def relative_url_path_orig(pool: str, field: str, qwidth: str) -> str:
    return f"q/orig/{pool}/{field}/{qwidth}/index.html"
