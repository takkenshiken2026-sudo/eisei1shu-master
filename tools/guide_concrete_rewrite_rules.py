#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""試験ガイド手書きリライト：具体性＋文中例示ルール。"""

from __future__ import annotations

import re

from tools.editorial_quality import norm
from tools.guide_tatoeba_limit import MAX_EXAMPLE_MARKERS_PER_ARTICLE, count_example_markers

# 文中の例示・場面描写（浅い例示検出用）
EXAMPLE_MARKERS_RE = re.compile(
    r"例えば|たとえば|たとえ|例として|イメージ(?:として|すると)|好比|想像すると|"
    r"具体(?:例|的)には|一例として|場面として|ケース(?:として|例)|"
    r"たとえば[、,]?[0-9０-９月火水木金土日曜]|"
    r"「[^」]{6,48}」(?:の|と|なら|では)"
)

# 5節中、具体アンカーが十分な節数（例えば/たとえばは不要）
MIN_SECTIONS_WITH_CONCRETE_ANCHORS = 3

MIN_ANCHORS_PER_CONCRETE_SECTION = 2

# 例示がない節は表外 prose に必要な具体アンカー数
MIN_ANCHORS_WITHOUT_EXAMPLE = 3

# FAQ 回答のうち具体性を満たす必要がある数
MIN_FAQ_WITH_CONCRETE = 2

# 例示文（マーカー含む文）の最低文字数
MIN_EXAMPLE_SENTENCE_LEN = 24

# 資格非依存の具体アンカー（表の行は _body_without_table で除外）
CONCRETE_ANCHOR_RE = re.compile(
    r"\d+[％%]|"
    r"\d+[問時間分週日]|"
    r"\d+:\d+|"
    r"\d+/\d+|"
    r"[0-9０-９]+月[0-9０-９]+日|"
    r"令和[0-9０-９]+年度|"
    r"第[0-9０-９]+章|"
    r"P\.[0-9０-９]+|"
    r"Q[0-9０-９]+|"
    r"正答率|"
    r"[月火水木金土日]曜|"
    r"残り\d+|"
    r"\d+か月|\d+週|"
    r"[0-9,，]+円|"
    r"演習[0-9０-９]+|"
    r"ミス[0-9０-９]+|"
    r"模試|要項|受験票|申込"
)

# マーカー直後が抽象助言だけの浅い例示
SHALLOW_AFTER_MARKER_RE = re.compile(
    r"(?:例えば|たとえば|具体例として|一例として)[、,]?"
    r"[^。！？\n]{0,40}(?:してください|しましょう|が大切|を心がけ|が重要|必要です|おすすめです)"
)

SENTENCE_SPLIT_RE = re.compile(r"[。！？\n]+")

PIPE_TABLE_ROW_RE = re.compile(r"^\|", re.M)

READER_PROSE_KEYS = (
    "lead",
    "user_intent",
    *(f"section_{n}_body" for n in range(1, 6)),
    *(f"faq_{n}_answer" for n in range(1, 4)),
)


def skip_concrete_rules(patch: dict[str, str]) -> bool:
    """編集合格お手本（exam-schedule 等・具体例なし）のみ具体性チェック対象外。"""
    note = norm(patch.get("revision_note", ""))
    return "お手本" in note and "具体例" not in note


def _body_without_table(body: str) -> str:
    lines = [ln for ln in body.split("\n") if ln.strip() and not PIPE_TABLE_ROW_RE.match(ln.strip())]
    return "\n".join(lines)


def _sentences(text: str) -> list[str]:
    parts = SENTENCE_SPLIT_RE.split(norm(text))
    return [p.strip() for p in parts if p.strip()]


def substantive_example_sentences(prose: str) -> list[str]:
    """例示マーカー＋具体アンカー＋最低長を満たす文。"""
    found: list[str] = []
    for sent in _sentences(prose):
        if not EXAMPLE_MARKERS_RE.search(sent):
            continue
        if len(sent) < MIN_EXAMPLE_SENTENCE_LEN:
            continue
        if SHALLOW_AFTER_MARKER_RE.search(sent):
            continue
        if CONCRETE_ANCHOR_RE.search(sent):
            found.append(sent)
    return found


def section_has_example(body: str) -> bool:
    prose = _body_without_table(norm(body))
    return bool(prose and EXAMPLE_MARKERS_RE.search(prose))


def section_concrete_anchor_count(body: str) -> int:
    prose = _body_without_table(norm(body))
    if not prose:
        return 0
    return len(CONCRETE_ANCHOR_RE.findall(prose))


def section_concrete_status(body: str) -> tuple[bool, str]:
    """(合格, 理由コード: substantive|anchors|shallow|missing)"""
    prose = _body_without_table(norm(body))
    if not prose:
        return False, "missing"
    if substantive_example_sentences(prose):
        return True, "substantive"
    if section_has_example(prose) and not substantive_example_sentences(prose):
        return False, "shallow"
    if section_concrete_anchor_count(body) >= MIN_ANCHORS_WITHOUT_EXAMPLE:
        return True, "anchors"
    return False, "missing"


def faq_answer_is_concrete(answer: str) -> bool:
    text = norm(answer)
    if not text:
        return False
    if substantive_example_sentences(text):
        return True
    return section_concrete_anchor_count(text) >= 2


def article_example_marker_count(patch: dict[str, str]) -> int:
    total = 0
    for key in READER_PROSE_KEYS:
        total += count_example_markers(norm(patch.get(key, "")))
    return total


def _lead_errors(prefix: str, lead: str) -> list[str]:
    errors: list[str] = []
    if not lead:
        return errors
    if EXAMPLE_MARKERS_RE.search(lead) and not substantive_example_sentences(lead):
        if SHALLOW_AFTER_MARKER_RE.search(lead):
            errors.append(
                f"{prefix} lead example is too abstract (add numbers, field, or weekday)"
            )
        elif section_concrete_anchor_count(lead) < 2:
            errors.append(
                f"{prefix} lead has 例えば/たとえば but lacks concrete anchors"
            )
    return errors


def _user_intent_errors(prefix: str, patch: dict[str, str]) -> list[str]:
    errors: list[str] = []
    ui = norm(patch.get("user_intent"))
    if not ui:
        return errors
    if not substantive_example_sentences(ui) and section_concrete_anchor_count(ui) < 1:
        errors.append(
            f"{prefix} user_intent needs a concrete anchor (not title repeat)"
        )
    lead = norm(patch.get("lead"))
    if lead and ui:
        # 先頭80字がほぼ同一ならリードの写しとみなす
        a, b = lead[:80], ui[:80]
        if a == b or (len(a) > 40 and a[:40] == b[:40] and len(set(a.split()) & set(b.split())) > 12):
            errors.append(f"{prefix} user_intent must differ from lead opening (reader benefit)")
    return errors


def validate_concrete_rewrite(slug: str, patch: dict[str, str]) -> list[str]:
    """REWRITES 1件分の具体性＋例示チェック。ERROR 文言の list を返す。"""
    if skip_concrete_rules(patch):
        return []

    errors: list[str] = []
    prefix = f"{slug}:"

    marker_count = article_example_marker_count(patch)
    if marker_count > MAX_EXAMPLE_MARKERS_PER_ARTICLE:
        errors.append(
            f"{prefix} use 例えば/たとえば at most {MAX_EXAMPLE_MARKERS_PER_ARTICLE} times "
            f"(got {marker_count})"
        )

    lead = norm(patch.get("lead"))
    errors.extend(_lead_errors(prefix, lead))
    errors.extend(_user_intent_errors(prefix, patch))

    concrete_sections = 0
    for n in range(1, 6):
        bcol = f"section_{n}_body"
        body = norm(patch.get(bcol))
        if not body:
            continue
        anchor_count = section_concrete_anchor_count(body)
        if anchor_count >= MIN_ANCHORS_PER_CONCRETE_SECTION:
            concrete_sections += 1
            continue
        ok, reason = section_concrete_status(body)
        if not ok:
            if reason == "shallow":
                errors.append(
                    f"{prefix} {bcol} has 例えば/たとえば but example lacks "
                    f"numbers/field/weekday (shallow)"
                )
            else:
                errors.append(
                    f"{prefix} {bcol} needs concrete anchors "
                    f"({MIN_ANCHORS_WITHOUT_EXAMPLE}+ outside the table)"
                )

    if concrete_sections < MIN_SECTIONS_WITH_CONCRETE_ANCHORS:
        errors.append(
            f"{prefix} need {MIN_SECTIONS_WITH_CONCRETE_ANCHORS}+ sections with "
            f"{MIN_ANCHORS_PER_CONCRETE_SECTION}+ concrete anchors "
            f"(got {concrete_sections})"
        )

    faq_answers = [norm(patch.get(f"faq_{n}_answer")) for n in range(1, 4)]
    faq_answers = [a for a in faq_answers if a]
    concrete_faq = sum(1 for a in faq_answers if faq_answer_is_concrete(a))
    if concrete_faq < MIN_FAQ_WITH_CONCRETE:
        errors.append(
            f"{prefix} need {MIN_FAQ_WITH_CONCRETE}+ FAQ answers with concrete anchors "
            f"(got {concrete_faq})"
        )

    return errors
