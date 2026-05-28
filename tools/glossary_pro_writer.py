# -*- coding: utf-8 -*-
"""用語詳細記事を専門家×プロライター水準に引き上げる本文・要点・FAQ生成。"""
from __future__ import annotations

import re

from glossary_derive_content import (
    _NUM_VAL,
    _sentences,
    derive_exam_points,
    derive_mistakes,
    short_def_from,
)
from glossary_fact_lookup import resolve_fact_key
from glossary_handmade_builder import (
    EXAM_LABEL,
    _extract_laws,
    _term_short,
    compose_handmade_body,
    exam_for_slug,
    resolve_table,
    strip_boilerplate,
)
from glossary_reader_content import (
    build_faqs,
    build_memory_tip,
    build_summary_body,
    simplify_prose,
)
from rewrite_with_numbers import TERM_FACTS

# 汎用パディング（品質の低い繰り返し）を本文から除去
_BOILERPLATE_PATTERNS = (
    r"【復習の補足\d+】[^。]+。",
    r"復習では、[^。]+分類すると覚えやすくなります。",
    r"受験直前は、[^。]+確認してください。",
    r"関連用語リンクから1つずつ違いを書き足し[^。]+。",
    r"学習の順序は、\(1\)[^。]+定着します。",
    r"本文と頻出ポイントを往復し、過去問では誤りの理由[^。]+。",
    r"本文では、[^。]+文脈で定義・数値・主体・手続がセットで問われます。",
)


def _strip_boilerplate_body(text: str) -> str:
    t = text.strip()
    for pat in _BOILERPLATE_PATTERNS:
        t = re.sub(pat, "", t)
    parts: list[str] = []
    seen: set[str] = set()
    for block in re.split(r"\n{2,}", t):
        b = block.strip()
        if not b:
            continue
        key = re.sub(r"\s+", "", b)[:56]
        if key in seen:
            continue
        seen.add(key)
        parts.append(b)
    return "\n\n".join(parts)


def _expert_perspective(term: str, category: str, source: str) -> str:
    """専門家視点の解説（カテゴリ別）。"""
    short = _term_short(term)
    if "法令" in category:
        return (
            f"【専門家の視点】{short}は、法令試験では「正しい条文の知識」より、"
            "数値・主体・期限のどれがずれているかを見抜く力が問われます。"
            "実務でも、選任届の提出期限や議事録保存と同じく、期限を過ぎると是正指導の対象になります。"
            "暗記カードには「数字・誰が・どこへ」を必ず3列で書いてください。"
        )
    if category.startswith("労働衛生"):
        return (
            f"【専門家の視点】{short}は、職場のリスク管理の連鎖の中に位置づけて理解するのが本質です。"
            "ばく露の把握（測定）→管理区分の判定→保護具・健診・教育という流れを頭に描き、"
            "単独対策を正とする選択肢を意識的に除外する癖をつけましょう。"
        )
    if category == "労働生理":
        return (
            f"【専門家の視点】{short}は、生理のしくみと検査・指標の両面から問われます。"
            "グラフや2×2表は、式を暗記する前に「縦軸・横軸が何か」を言語化すると、"
            "計算ミスと定義の取り違えの両方を防げます。"
        )
    return (
        f"【専門家の視点】{short}は、用語単体ではなく制度全体の中での役割まで押さえると、"
        "本番の「すべて正しい」系問題で迷いにくくなります。"
        "関連用語との違いを1行で書けるかが、合格ラインとの差になりやすい論点です。"
    )


def _exam_strategy(term: str, category: str, exam_points: str) -> str:
    """試験突破の着眼点。"""
    short = _term_short(term)
    eps = [e.strip() for e in (exam_points or "").split(";") if e.strip()][:2]
    examples = "／".join(eps) if eps else "数値・主体・期限の入れ替え"
    return (
        f"【試験で差がつく見方】{short}の設問では、正解に近い文を1語だけ変えた選択肢が並びます。"
        f"典型パターン：{examples}。"
        "解くときは、(1)定義の主語と分母を声に出す、(2)本文の表と照合する、(3)関連用語と混同していないか確認する、"
        "の3ステップを10秒以内で回すと安定します。"
    )


def _workplace_narrative(term: str, category: str, source: str) -> str:
    """現場での意味づけ（具体シーン）。"""
    short = _term_short(term)
    if "健診" in source or "健康診断" in term:
        return (
            f"【現場での意味】{short}は、健診結果の管理・就業上の措置・二次健診の判断に直結します。"
            "人事データと混同せず、産業医・衛生管理者・安全衛生委員会が情報共有する流れを"
            "イメージしておくと、主体の入れ替え問題に強くなります。"
        )
    if "測定" in source or "管理区分" in source:
        return (
            f"【現場での意味】{short}は、改善計画の優先順位と再測定の期限を決める根拠になります。"
            "記録が残っていても濃度が基準超過のまま放置されていると、労基署の立入検査で指摘されやすい領域です。"
        )
    if "委員会" in source or "選任" in source:
        return (
            f"【現場での意味】{short}は、紙の体制図だけでなく、会議の頻度・議事録・改善の実行まで含めた運用が求められます。"
            "試験は条文寄りですが、実務では「開催したが記録がない」ことが問題になるため、頻度と保存年限はセットで覚えてください。"
        )
    if "ストレス" in term or "メンタル" in source:
        return (
            f"【現場での意味】{short}は、高ストレス者への面接・措置と、個人情報の取扱いの両方が問われます。"
            "集団分析の結果を委員会で共有する流れまで含めて整理しておくとよいです。"
        )
    return (
        f"【現場での意味】{short}は、作業手順・記録・教育のどこに組み込むかを決めないと現場運用がぶれます。"
        "試験では定義と数値が中心ですが、合格後は「誰がいつ何をするか」まで落とし込むのが衛生管理者の仕事です。"
    )


def _closing_synthesis(term: str, category: str) -> str:
    short = _term_short(term)
    return (
        f"【まとめ】{short}は、{category}の文脈で「定義・数値・主体・手続・関連制度」の5点を"
        "一枚のメモにまとめ、過去問では誤りの理由まで言える状態を目指してください。"
        "本記事の表・要点・頻出ポイントを往復すれば、独学でも十分に実力がつきます。"
    )


def compose_pro_body(
    term: str,
    category: str,
    source: str,
    *,
    slug: str = "",
    exam_points: str = "",
) -> str:
    """手作り本文に専門家ブロックを加え、低品質パディングを除去。"""
    base = compose_handmade_body(term, category, source, slug=slug)
    base = _strip_boilerplate_body(base)

    extras = [
        _expert_perspective(term, category, source),
        _workplace_narrative(term, category, source),
        _exam_strategy(term, category, exam_points or derive_exam_points(term, source, category)),
    ]
    body = base + "\n\n" + "\n\n".join(extras)

    plain = len(re.sub(r"<[^>]+>", "", body))
    if plain < 1100:
        tbl = resolve_table(term, source, slug, category)
        if tbl and tbl not in body:
            body += "\n\n" + tbl
        body += "\n\n" + _closing_synthesis(term, category)

    return _strip_boilerplate_body(body)


def build_pro_lead(term: str, category: str, source: str) -> str:
    sd = short_def_from(source, term)
    short = _term_short(term)
    return simplify_prose(
        f"{sd.rstrip('。')}。"
        f"{short}は{category}で繰り返し出る論点です。"
        "この記事では、現場での意味・試験のひっかけ・覚え方まで、受験生の視点で整理します。"
    )


def build_pro_mistakes(term: str, category: str, source: str) -> str:
    base = derive_mistakes(term, source, category)
    short = _term_short(term)
    extra = (
        f"また、{short}だけを単語カードにして、人数・頻度・保存年限を別カードにしていると、"
        "本番でセット問題に弱くなります。必ず同じカードの裏面に数値を書いてください。"
    )
    return simplify_prose(base + " " + extra)


def build_pro_faqs(term: str, category: str, source: str, exam_points: str) -> list[tuple[str, str]]:
    """FAQ4件（プロライター調）。"""
    short = _term_short(term)
    faqs = build_faqs(term, category, source, exam_points)
    if len(faqs) >= 3:
        faqs[2] = (
            f"独学で{short}をマスターするコツは？",
            simplify_prose(
                f"テキストで{short}の定義を読んだ直後に、過去問で同テーマの問題を3問解き、"
                "誤り選択肢の「どの語がずれているか」をメモします。"
                "用語解説一覧から関連語を2つ選び、違いを1行で書くと定着が早まります。"
            ),
        )
    return faqs


def best_source_for_row(row: dict[str, str]) -> str:
    term = (row.get("term") or "").strip()
    slug = (row.get("slug") or "").strip()
    key = resolve_fact_key(term, slug)
    if key:
        return TERM_FACTS[key]
    return strip_boilerplate(
        (row.get("term_detail_body") or row.get("definition") or row.get("short_def") or "").strip()
    )


def build_pro_patch(row: dict[str, str]) -> dict[str, str]:
    term = (row.get("term") or "").strip()
    slug = (row.get("slug") or "").strip()
    category = (row.get("category") or "").strip()
    source = best_source_for_row(row)

    exam = exam_for_slug(slug, term, source, category)
    body = compose_pro_body(term, category, source, slug=slug, exam_points=exam)
    defn = source if source.startswith("「") else f"「{term}」{source.lstrip('「')}"
    if not defn.endswith("。"):
        sents = _sentences(defn)
        defn = sents[0] if sents else defn

    faqs = build_pro_faqs(term, category, source, exam)
    patch: dict[str, str] = {
        "definition": simplify_prose(defn),
        "short_def": short_def_from(defn, term),
        "article_lead": build_pro_lead(term, category, source),
        "term_detail_body": body,
        "exam_points": exam,
        "explanation": exam,
        "common_mistakes": build_pro_mistakes(term, category, source),
        "summary_body": build_summary_body(term, category, source),
        "memory_tip": build_memory_tip(term, category, source),
    }
    laws = _extract_laws(source)
    if laws:
        patch["legal_basis"] = "; ".join(laws[:4])

    for i, (q, a) in enumerate(faqs, start=1):
        patch[f"faq_{i}_question"] = q
        patch[f"faq_{i}_answer"] = simplify_prose(a)

    return patch


def ensure_pro_body_length(body: str, term: str, category: str, source: str, slug: str) -> str:
    """低品質パディングなしで最低文字数を確保。"""
    text = _strip_boilerplate_body(body)
    plain = len(re.sub(r"<[^>]+>", "", text))
    if plain >= 1000:
        return text
    extra = compose_pro_body(term, category, source, slug=slug)
    return _strip_boilerplate_body(text + "\n\n" + extra)
