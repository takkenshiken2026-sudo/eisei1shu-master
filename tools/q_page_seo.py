# -*- coding: utf-8 -*-
"""過去問・実践演習・一問一答の一覧／各問ページ向け SEO 文言（site-config.json の seoCopy）。"""

from __future__ import annotations

import html
import re

from tools.build_past_question_pages import meta_description
from tools.site_config import CONFIG, brand_name, exam_name

MODE_LABEL: dict[str, str] = {
    "past": "過去問",
    "practice": "実践演習",
    "ichimon": "一問一答",
}


def seo_copy() -> dict[str, str]:
    raw = CONFIG.get("seoCopy") if isinstance(CONFIG.get("seoCopy"), dict) else {}
    return {
        "mockExam": str(raw.get("mockExam") or "模試・模擬試験"),
        "studyModes": str(raw.get("studyModes") or "過去問・実践演習・一問一答"),
    }


def study_modes_note_html() -> str:
    """一覧・各問ページ本文に置く短い学習導線（表示＋検索キーワードの自然な含有）。"""
    c = seo_copy()
    text = (
        f"{exam_name()}の{c['studyModes']}と{c['mockExam']}対策を、このサイトでまとめて学習できます。"
        "タブから他の演習モードへ移動できます。"
    )
    return f'<p class="q-study-modes-note">{html.escape(text)}</p>'


def index_lead(mode: str) -> str:
    ex = exam_name()
    c = seo_copy()
    if mode == "past":
        return (
            f"{ex}の過去問を年度別・分野別にまとめています。"
            f"{c['mockExam']}前の出題傾向の確認や、{c['studyModes']}の中心コンテンツとして使えます。"
            "検索と絞り込みで目的の問題を探し、解説ページで正誤と解説を確認できます。"
        )
    if mode == "practice":
        from tools.site_config import ichimon_enabled, practice_formats

        if not ichimon_enabled() and practice_formats():
            return (
                f"{ex}の実践演習を分野別にまとめています。"
                "〇×方式と五肢選択方式を選んで、二種外務員の本番形式に近い演習ができます。"
                "各問題の解説ページで正誤を確認し、アプリで演習できます。"
            )
        return (
            f"{ex}の実践演習を分野別にまとめています。"
            f"{c['mockExam']}に近い形式で力を測る演習として、{c['studyModes']}と組み合わせて学習できます。"
            "各問題の解説ページで正誤を確認し、アプリで演習できます。"
        )
    return (
        f"{ex}の一問一答を年度・分野別にまとめています。"
        f"{c['mockExam']}前の知識確認や、{c['studyModes']}の隙間学習に使えます。"
        "検索と絞り込みのあと、解説ページからアプリ演習へ進めます。"
    )


def index_meta_description(mode: str, *, count: int) -> str:
    ex = exam_name()
    c = seo_copy()
    if mode == "past":
        base = (
            f"{ex}の過去問{count}問を年度・分野別に掲載。"
            f"{c['mockExam']}対策・{c['studyModes']}の学習に対応。"
            "検索・絞り込みのあと解説ページへ。"
        )
    elif mode == "practice":
        base = (
            f"{ex}の実践演習{count}問を分野別に掲載。"
            f"{c['mockExam']}前の演習として{c['studyModes']}と併用可能。"
            "検索・絞り込みと解説ページに対応。"
        )
    else:
        base = (
            f"{ex}の一問一答{count}問を年度・分野別に掲載。"
            f"{c['mockExam']}・本番前の{c['studyModes']}学習に対応。"
            "検索・絞り込みと解説に対応。"
        )
    return meta_description(base, 155)


_ICHIMON_META_SUFFIX_RE = re.compile(
    r"(は正しい|は誤り|は誤っている|は正しくない|は間違い)[。．]?\s*$"
)


def ichimon_meta_snippet(statement: str, *, answer: str = "") -> str:
    """一問一答 meta 用。設問末尾の「は正しい」等を除去（正答記号は answer_tail で付与）。"""
    s = (statement or "").strip()
    return _ICHIMON_META_SUFFIX_RE.sub("", s).rstrip("。． ")


def question_meta_description(
    mode: str,
    *,
    headline: str,
    category: str,
    body: str = "",
    answer_tail: str = "",
) -> str:
    """各問ページの meta description。

    検索スニペットで最初に見える語を検索クエリへ近づけるため、問題文（body）を先頭へ置き、
    識別子（第N問・分野）や定型の学習導線は後段へ回す（＝主題語のフロントロード）。
    """
    c = seo_copy()
    meta_tag = f"{headline}・{category}。"
    if mode == "past":
        tail = f"{c['mockExam']}対策や{c['studyModes']}と併用して学習できます。"
    elif mode == "practice":
        tail = (
            f"{c['mockExam']}前の演習として{c['studyModes']}と併用できます。"
            "選択肢と解説を掲載。"
        )
    else:
        tail = f"{c['mockExam']}前の確認に。{c['studyModes']}と併用できます。正誤と解説を掲載。"
    ans = (answer_tail or "").strip()
    ans_part = f" 正答: {ans}。" if ans else ""
    body = body.strip()
    if not body:
        return meta_description(meta_tag + ans_part + tail, 155)
    lead = f"{body}{ans_part}"
    combo = f"{lead} {meta_tag}"
    if len(combo) + len(tail) <= 150:
        return meta_description(f"{combo}{tail}", 155)
    if len(combo) <= 152:
        return meta_description(combo, 155)
    # 問題文が長い場合も、先頭は問題文のまま末尾（識別子）を圧縮する。
    budget = max(40, 150 - len(ans_part) - len(meta_tag))
    trimmed = body[:budget].rstrip("、。・ 　")
    return meta_description(f"{trimmed}…{ans_part} {meta_tag}", 155)


def index_search_placeholder(mode: str) -> str:
    if mode == "ichimon":
        return "例：2026-01-1、分野、問題文…"
    return "例：第1問、分野、問題文…"


def index_search_index_suffix() -> str:
    """一覧 JSON の search 列に足す共通キーワード。"""
    c = seo_copy()
    return f"{c['mockExam']} {c['studyModes']}"


def index_h1(mode: str) -> str:
    """一覧ページの H1（試験名＋モード名を先頭に）。"""
    return f"{exam_name()} {MODE_LABEL[mode]}"


def index_page_title(mode: str) -> str:
    """一覧ページの <title>（試験名・モード・模試キーワード・ブランド）。"""
    c = seo_copy()
    label = MODE_LABEL[mode]
    if mode == "past":
        sub = f"{c['mockExam']}対策"
    elif mode == "practice":
        sub = f"{c['mockExam']}前の演習"
    else:
        sub = f"{c['mockExam']}前の確認"
    return f"{exam_name()} {label}一覧｜{sub}｜{brand_name()}"


def past_year_display(year: int, wareki: str = "") -> str:
    """過去問の年度表示。exam_wareki があれば優先（20202 等の内部 ID を避ける）。"""
    w = (wareki or "").strip()
    if w:
        return w
    return f"{year}年"


def question_h1(
    mode: str,
    *,
    year: int = 0,
    qno: int = 0,
    question_id: str = "",
    category: str = "",
    year_label: str = "",
) -> str:
    """各問ページの H1（試験名＋モード＋識別子＋分野）。"""
    ex = exam_name()
    label = MODE_LABEL[mode]
    if mode == "past":
        yl = (year_label or "").strip() or past_year_display(year)
        return f"{ex} {label} {yl} 第{qno}問（{category}）"
    if mode == "practice":
        return f"{ex} {label} 第{qno}問（{category}）"
    return f"{ex} {label} {question_id}（{category}）"


def question_page_title(
    mode: str,
    *,
    year: int = 0,
    qno: int = 0,
    question_id: str = "",
    category: str = "",
    year_label: str = "",
    stem: str = "",
) -> str:
    """各問ページの <title>。stem があれば主題語を冒頭に前置して検索一致度を高める。"""
    base = (
        f"{question_h1(mode, year=year, qno=qno, question_id=question_id, category=category, year_label=year_label)}"
        f"｜{brand_name()}"
    )
    topic = stem_topic(stem) if stem else ""
    if topic:
        return f"{topic}｜{base}"
    return base


# 設問文（stem）から、検索クエリと一致しやすい「主題（トピック）」を取り出す境界。
# 「◯◯に関する次の記述のうち…」の ◯◯ 部分を主題として拾う。
_STEM_TOPIC_BOUNDARIES: tuple[str, ...] = (
    "に関する",
    "に定める",
    "に基づく",
    "に基づき",
    "について",
)
_STEM_TOPIC_LEAD_RE = re.compile(r"^(?:次の|以下の|下記の|上記の)")
_STEM_TOPIC_TRAIL = "、,。．・のがはを　 "


def stem_topic(stem: str, *, maxlen: int = 26) -> str:
    """設問文の先頭から主題語（検索意図に一致するキーワード）を抽出する。

    各問ページの <title> 冒頭に置くことで、同一プレフィックスで始まる
    量産型タイトルを避け、検索クエリとの一致度（＝CTR）を高める狙い。
    """
    s = re.sub(r"\s+", "", stem or "").strip()
    if not s:
        return ""
    s = _STEM_TOPIC_LEAD_RE.sub("", s)
    cut = len(s)
    for boundary in _STEM_TOPIC_BOUNDARIES:
        idx = s.find(boundary)
        if 0 < idx < cut:
            cut = idx
    topic = s[:cut]
    # 「◯◯における△△」型（分野名などの前置き）は、後段の主題語△△を優先する。
    # ただし括弧の内側で切ると壊れるため、前置き部分の括弧が閉じている場合のみ適用。
    idx = topic.find("における")
    if 2 <= idx <= 30:
        prefix, tail = topic[:idx], topic[idx + len("における"):]
        balanced = all(
            prefix.count(o) == prefix.count(c)
            for o, c in (("「", "」"), ("（", "）"), ("(", ")"))
        )
        if balanced and len(tail) >= 2:
            topic = tail

    def _strip_dangling_brackets(text: str) -> str:
        # 開き括弧だけが残る中途半端な切れ方を避ける。
        for open_br, close_br in (("「", "」"), ("（", "）"), ("(", ")")):
            if open_br in text and close_br not in text:
                text = text[: text.index(open_br)]
        return text

    topic = _strip_dangling_brackets(topic).rstrip(_STEM_TOPIC_TRAIL)
    # 主題が拾えなかった場合は、最初の読点／句点までを主題とみなす。
    if len(topic) < 2:
        topic = re.split(r"[、。]", s, maxsplit=1)[0]
    if len(topic) > maxlen:
        truncated = _strip_dangling_brackets(topic[:maxlen])
        topic = truncated.rstrip(_STEM_TOPIC_TRAIL) + "…"
    return topic


def past_question_page_title(
    *,
    year: int = 0,
    qno: int = 0,
    category: str = "",
    year_label: str = "",
    stem: str = "",
) -> str:
    """過去問各問ページの <title>。主題語を冒頭に置いて検索一致度を高める。"""
    yl = (year_label or "").strip() or past_year_display(year)
    base = f"{exam_name()} 過去問 {yl} 第{qno}問"
    topic = stem_topic(stem)
    if topic:
        return f"{topic}｜{base}｜{brand_name()}"
    label = f"（{category}）" if category else ""
    return f"{base}{label}｜{brand_name()}"


def question_meta_headline(
    mode: str,
    *,
    year: int = 0,
    qno: int = 0,
    question_id: str = "",
    year_label: str = "",
) -> str:
    """各問 meta description の headline 用。"""
    ex = exam_name()
    label = MODE_LABEL[mode]
    if mode == "past":
        yl = (year_label or "").strip() or past_year_display(year)
        return f"{ex}の{label} {yl} 第{qno}問"
    if mode == "practice":
        return f"{ex}の{label} 第{qno}問"
    return f"{ex}の{label} {question_id}"
