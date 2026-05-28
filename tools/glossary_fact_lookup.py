# -*- coding: utf-8 -*-
"""用語名・slug から TERM_FACTS のキーを解決する。"""
from __future__ import annotations

import re
import unicodedata

from rewrite_with_numbers import TERM_FACTS

# slug -> TERM_FACTS キー（表記ゆれ）
SLUG_TO_FACT: dict[str, str] = {
    "sagyo-kankyo-sokutei": "作業環境測定（義務・頻度・評価・記録）",
    "eisei-iinkai": "衛生委員会／安全衛生委員会",
    "rodo-anzen-eisei-ho": "労働安全衛生法（総則・事業者の義務）",
    "anzen-eisei-kyoiku": "安全衛生教育／特別教育／職長教育／技能講習",
    "risk-assessment": "リスクアセスメント（5ステップ）",
    "soonnsei-nacho": "騒音性難聴（毛細胞・4000Hz）",
    "anzen-eisei-kanri-taisei": "安全衛生管理体制（総括／衛生管理者／産業医）",
    "choujikan-rodo-mensetu": "長時間労働者面接指導（月80時間・本人申出）",
    "rodosha-teigi": "労働者（定義）",
    "denri-hoshasen": "電離放射線（外部・内部被ばく・線量）",
    "kyokuho-haikisochi": "局所排気装置（形式・制御速度・性能）",
    "a-b-c-sokutei": "A測定・B測定の概念",
    "anzen-eisei-kyoiku-2": "安全衛生教育／特別教育／職長教育／技能講習",
}

# 用語名の別表記 -> TERM_FACTS キー
TERM_ALIASES: dict[str, str] = {
    "安全衛生管理体制": "安全衛生管理体制（総括／衛生管理者／産業医）",
    "A測定・B測定・C測定の意味と使い分け": "A測定・B測定の概念",
    "衛生委員会": "衛生委員会／安全衛生委員会",
    "安全衛生委員会": "衛生委員会／安全衛生委員会",
    "アスベスト線維濃度・PCM・SEM（概念）": "アスベスト関連疾患（胸膜肥厚・中皮腫・肺癌）",
    "ベンゼン・芳香族溶媒（概念）": "ベンゼンと造血器疾患・白血病（概念）",
    "ベンゼン・トルエン・キシレン・スチレン（芳香族溶媒）": "ベンゼンと造血器疾患・白血病（概念）",
    "ばく露限界・許容濃度・濃度基準の読み方": "管理濃度",
    "管理濃度": "管理濃度",
    "ホルムアルデヒド・アクリルアルデヒド（刺激性・感作）": "ホルムアルデヒド（特化則）",
    "アスベスト線維濃度・PCM・SEM（概念）": "アスベスト関連疾患（胸膜肥厚・中皮腫・肺癌）",
    "重金属・複合ばく露（鉛・水銀等）": "重金属蓄積（鉛・水銀・カドミウム）",
}


def _norm(s: str) -> str:
    t = unicodedata.normalize("NFKC", (s or "").strip())
    t = re.sub(r"\s+", "", t)
    t = re.sub(r"（[^）]*）", "", t)
    return t


def _tokens(s: str) -> set[str]:
    t = _norm(s)
    parts = re.split(r"[・／、,\s]+", t)
    return {p for p in parts if len(p) >= 2}


def resolve_fact_key(term: str, slug: str = "") -> str | None:
    slug = (slug or "").strip()
    term = (term or "").strip()
    if slug in SLUG_TO_FACT:
        k = SLUG_TO_FACT[slug]
        return k if k in TERM_FACTS else None
    if term in TERM_ALIASES:
        k = TERM_ALIASES[term]
        return k if k in TERM_FACTS else None
    if term in TERM_FACTS:
        return term

    term_n = _norm(term)
    best_key: str | None = None
    best_score = 0

    term_tok = _tokens(term)
    for key in TERM_FACTS:
        key_n = _norm(key)
        if key_n == term_n:
            return key
        if term_n in key_n or key_n in term_n:
            score = min(len(term_n), len(key_n)) + 10
            if score > best_score:
                best_score, best_key = score, key
        overlap = len(term_tok & _tokens(key))
        if overlap >= 2:
            score = overlap * 5 + len(key)
            if score > best_score:
                best_score, best_key = score, key
        elif overlap == 1 and len(term_tok) <= 2:
            score = 6 + len(key)
            if score > best_score:
                best_score, best_key = score, key

    if best_score >= 10:
        return best_key
    return None
