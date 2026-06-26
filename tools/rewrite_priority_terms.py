#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GSC表示のある重要用語ページの「定義になっていない」定型salad文を、
正確な内容へ書き換える（reports/glossary-quality-audit.csv の最優先4件）。

方針:
  1) 重要フィールド（meta/og description、ld+json の DefinedTerm/WebPage.description、
     FAQ Q1 回答）は決定論的に正しい定義へ置き換える。
  2) 可視本文に残る定型salad（リード・要点・定義節・compare表・連携文）は、
     全形「FragA。FragB」と前回クリーンアップで切れた「FragA。」の両方に対応して
     正しい定義/要点へ置換する。
HTML と data/glossary_terms.csv の両方へ適用する。
"""
from __future__ import annotations

import csv
import io
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TERMS = ROOT / "terms"
CSV_PATH = ROOT / "data" / "glossary_terms.csv"

FRAGB = "ばく露評価・対策の優先順位・管理区分などを説明するときに有害環境と対策・管理の対応を語るときに位置づけられます"
DESC_TMPL = "{term}の意味、法令・根拠、試験で押さえるポイントを第一種衛生管理者試験向けに整理。「{label}」とは、{defn}。"


class Plan:
    def __init__(self, slug, term, label, frag_a, frag_renkei, defn, point, renkei):
        self.slug = slug
        self.term = term            # DefinedTerm 表示名
        self.label = label          # 「…」とは、で使う見出し
        self.defn = defn            # 「…」とは、{defn}。
        self.point = point
        # 本文salad置換（長い順に適用）。全形と切れ形の両方を網羅。
        core_p = f"{frag_a}。{FRAGB}"
        core_c = f"{frag_a}、{FRAGB}"
        self.body_subs = [
            (core_p, defn),                 # 全形（定義文）
            (core_c, point),                # 読点形（要点）
            (frag_renkei, renkei),          # 連携文
            (f"{frag_a}。", f"{defn}。"),    # 切れ形（定義文）
            (f"{frag_a}、", f"{point}、"),  # 切れ形（要点）
        ]

    @property
    def description(self):
        return DESC_TMPL.format(term=self.term, label=self.label, defn=self.defn)

    @property
    def faq_answer(self):
        return f"「{self.label}」とは、{self.defn}。"


PLANS = [
    Plan(
        "metal-fume-concept", "金属ヒューム（概念）", "金属ヒューム（概念）",
        "溶接および溶断のばく露を手がかりに",
        "金属ヒュームは、ばく露の評価から保護具・作業環境測定・健診までが連動します",
        defn="金属を高温で溶融・加熱したときに発生した金属蒸気が、空気中で冷却・凝縮・酸化してできる固体の微粒子（粒径おおむね0.1〜1μm程度）です。粒子が非常に細かく、肺の奥（肺胞）まで達しやすいのが特徴です",
        point="ヒュームは金属蒸気が凝縮してできた固体の微粒子で、ミスト（液体）やガス・蒸気とは区別される",
        renkei="亜鉛・銅などの吸入で金属熱、マンガンなどで神経障害を生じ、溶接ヒュームは令和3年から特定化学物質として規制される",
    ),
    Plan(
        "halogenated-hydrocarbons", "ハロゲン化炭化水素（トリクロロエチレン等）", "ハロゲン化炭化水素（トリクロロエチレン等）",
        "代替および規制動向とリスクを手がかりに",
        "ハロゲン化炭化水素は、ばく露の評価から保護具・作業環境測定・健診までが連動します",
        defn="炭化水素の水素原子の一部を塩素・フッ素・臭素などのハロゲンで置き換えた有機化合物の総称で、トリクロロエチレン・テトラクロロエチレン・ジクロロメタンなどが含まれます。揮発性が高く、蒸気の吸入により中枢神経抑制（頭痛・めまい・麻酔作用）や肝・腎障害を起こします",
        point="揮発性が高く蒸気の吸入ばく露が中心で、急性影響は中枢神経抑制、慢性影響は肝・腎障害",
        renkei="トリクロロエチレン等の発がん性物質は有機溶剤から特定化学物質（特別管理物質）へ規制が移行し、作業環境測定・特殊健康診断・呼吸用保護具が連動する",
    ),
    Plan(
        "oxidizable-substances-spontaneous-combustion", "易酸化物質・自然発火（概念）", "易酸化物質・自然発火",
        "危険物取扱いに関する基本的な論点を手がかりに",
        "易酸化物質・自然発火は、ばく露の評価から保護具・作業環境測定・健診までが連動します",
        defn="酸素と結びつきやすいため常温でも酸化熱が内部に蓄積し、外部の火源がなくても発火点に達して燃え出す（自然発火する）性質をもつ物質です。乾性油のしみた布・ぼろ、黄りん、金属粉などが代表例です",
        point="外部の火源なしに酸化熱の蓄積で発火する点が、着火源を要する引火・発火との違い",
        renkei="対策は分散・少量保管と換気・放熱で蓄熱を防ぐことが基本で、乾性油を含むウエスの放置などが危険",
    ),
]

# 特殊健康診断: 本文は実コンテンツあり。定義フィールドのみ正す。
TOKUSHU = Plan(
    "tokushu-kenshin-kokiatsu", "特殊健康診断", "特殊健康診断（鉛）",
    "＜＜なし＞＞", "＜＜なし＞＞",
    defn="鉛中毒予防規則53条により、鉛業務に常時従事する労働者に対して雇入れ時・配置替え時、およびその後6か月以内ごとに1回（はんだ付け・有機鉛等の軽度業務は1年以内ごと）実施する健康診断です。血液中の鉛量や尿中デルタアミノレブリン酸量などを検査し、個人票は5年保存します",
    point="", renkei="",
)
TOKUSHU.body_subs = [
    ("特殊健康診断は（鉛）」とは。", TOKUSHU.faq_answer),
    ("「特殊健康診断（鉛）」とは。", "「特殊健康診断（鉛）」とは、"),
]
ALL = PLANS + [TOKUSHU]


def set_descriptions(html: str, plan: Plan) -> str:
    desc = plan.description
    html = re.sub(r'(<meta name="description" content=")[^"]*(")', lambda m: m.group(1) + desc + m.group(2), html)
    html = re.sub(r'(<meta property="og:description" content=")[^"]*(")', lambda m: m.group(1) + desc + m.group(2), html)

    def repl_ld(m: re.Match) -> str:
        data = json.loads(m.group(1))
        for node in data.get("@graph", []):
            t = node.get("@type")
            if t in ("DefinedTerm", "WebPage") and "description" in node:
                node["description"] = desc
            if t == "FAQPage":
                me = node.get("mainEntity") or []
                if me:
                    me[0].setdefault("acceptedAnswer", {})["text"] = plan.faq_answer
        return '<script type="application/ld+json">\n' + json.dumps(data, ensure_ascii=False, indent=2) + "\n</script>"

    return re.sub(r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>', repl_ld, html, flags=re.S)


def apply_subs(text: str, subs: list[tuple[str, str]]) -> str:
    for old, new in sorted(subs, key=lambda p: -len(p[0])):
        text = text.replace(old, new)
    return text


def process_html(plan: Plan) -> bool:
    path = TERMS / f"{plan.slug}.html"
    html = path.read_text(encoding="utf-8")
    new = html
    if plan.slug != "tokushu-kenshin-kokiatsu":
        new = set_descriptions(new, plan)
    else:
        # 可視FAQの壊れた定義も実定義へ
        new = new.replace("特殊健康診断は（鉛）」とは。", plan.faq_answer)
        new = set_descriptions(new, plan)
    new = apply_subs(new, plan.body_subs)
    # ld+json 妥当性確認
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', new, re.S):
        json.loads(m.group(1))
    if new != html:
        path.write_text(new, encoding="utf-8")
        return True
    return False


def process_csv() -> int:
    by_slug = {p.slug: p for p in ALL}
    text = CSV_PATH.read_text(encoding="utf-8-sig")
    rows = list(csv.reader(text.splitlines()))
    header = rows[0]
    sidx = header.index("slug")
    changed = 0
    for r in rows[1:]:
        if len(r) <= sidx or r[sidx] not in by_slug:
            continue
        plan = by_slug[r[sidx]]
        before = list(r)
        for i in range(len(r)):
            r[i] = apply_subs(r[i], plan.body_subs)
        if r != before:
            changed += 1
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(header)
    for r in rows[1:]:
        w.writerow(r)
    CSV_PATH.write_text(buf.getvalue(), encoding="utf-8")
    return changed


def main() -> int:
    n = sum(1 for p in ALL if process_html(p))
    c = process_csv()
    print(f"HTML 更新 {n} ページ / CSV 更新 {c} 行")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
