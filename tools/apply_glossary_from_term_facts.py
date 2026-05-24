#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rewrite_with_numbers.TERM_FACTS からプレースホルダー用語をリッチ化する。

  python3 tools/apply_glossary_from_term_facts.py
  python3 tools/apply_glossary_from_term_facts.py --dry-run
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GLOSSARY_CSV = ROOT / "data" / "glossary_terms.csv"

sys.path.insert(0, str(ROOT / "tools"))
from glossary_body_pad import pad_term_detail_body  # noqa: E402
from glossary_derive_content import (  # noqa: E402
    derive_exam_points,
    derive_lead,
    derive_mistakes,
    derive_memory_tip,
)
from glossary_enrich_a_rank_content import _ep, _tbl  # noqa: E402
from rewrite_with_numbers import TERM_FACTS  # noqa: E402

from glossary_fact_lookup import SLUG_TO_FACT, resolve_fact_key  # noqa: E402

EXAM_BY_SLUG: dict[str, str] = {
    "sagyo-kankyo-sokutei": _ep(
        "「作業環境測定は任意」→ 指定作業場で義務",
        "「記録保存は1年」→ 原則3年（特別管理物質30年）",
        "「第3管理区分は良好」→ 速やかに改善が必要",
        "「測定頻度はすべて1年」→ 粉じん・有機溶剤等は6か月以内",
        "「評価は健診結果のみ」→ 測定濃度が基礎",
    ),
    "eisei-iinkai": _ep(
        "「50人未満でも設置義務」→ 常時50人以上",
        "「開催は年1回でよい」→ 毎月1回以上",
        "「議事録保存は1年」→ 3年",
        "「委員は事業者のみ」→ 労働者側推薦が半数",
        "「安全委員会と別物で不可」→ 合同の安全衛生委員会可",
    ),
    "rodo-anzen-eisei-ho": _ep(
        "「目的は労働条件改善のみ」→ 安全と健康の確保",
        "「事業者義務は努力規定のみ」→ 最低基準遵守＋快適職場",
        "「労働者に罰則なし」→ 協力義務等はある",
        "「安衛法は労基法に優先」→ 相まって適用",
        "「定義は省令のみ」→ 法1〜5条の総則",
    ),
    "anzen-eisei-kyoiku": _ep(
        "「特別教育は任意」→ 危険有害業務で義務",
        "「教育記録保存不要」→ 特別教育は3年",
        "「技能講習＝特別教育」→ 修了証で資格化する別制度",
        "「雇入時教育は不要」→ 雇入時・作業変更時に実施",
        "「職長教育は5年ごと再教育」→ 安衛法60条",
    ),
    "risk-assessment": _ep(
        "「RAは努力義務のみ」→ 化学物質は義務（記録3年）",
        "「優先順位は保護具が先」→ 本質安全→工学→管理→PPE",
        "「5ステップに記録はない」→ 結果の記録が最終ステップ",
        "「重篤度だけで評価」→ 重篤度×頻度",
        "「RA＝作業環境測定」→ 別の枠組み",
    ),
    "soonnsei-nacho": _ep(
        "「4000Hz落ち込みは伝音性難聴」→ 感音性",
        "「一側のみでも問題なし」→ 両側性・対称性",
        "「回復可能」→ 不可逆",
        "「85dB未満でも測定不要」→ 85dB以上が測定対象",
        "「耳栓は任意」→ 90dB超は保護具が必要な水準",
    ),
    "anzen-eisei-kanri-taisei": _ep(
        "「衛生管理者は100人未満不要」→ 50人以上",
        "「産業医は300人未満不要」→ 50人以上（規模で専任等）",
        "「委員会は任意」→ 50人以上で設置",
        "「総括は全業種必須」→ 業種・規模で選任",
        "「体制は厚労大臣が選任」→ 事業者が選任",
    ),
    "choujikan-rodo-mensetu": _ep(
        "「月45時間超で必ず実施」→ 月80時間超＋本人申出",
        "「事業者が全員に強制面接」→ 本人申出が前提",
        "「記録保存3年」→ 5年",
        "「医師でなくても可」→ 医師による面接指導",
        "「ストレスチェックと同一」→ 別制度",
    ),
    "rodosha-teigi": _ep(
        "「労働者＝正社員のみ」→ 派遣・パート・有期も含む",
        "「使用者＝労働者」→ 事業者が使用者",
        "「労働基準法の労働者と異なる」→ 9条の定義",
        "「請負は常に労働者に含まない」→ 実態で判断",
        "「安衛法の保護対象外」→ 保護対象",
    ),
    "denri-hoshasen": _ep(
        "「外部被ばくのみ」→ 内部被ばくも区別",
        "「線量限度は年1000mSv」→ 実効5年100・年50mSv等",
        "「α線は鉛板で遮蔽」→ 紙で遮蔽、飛程が短い",
        "「管理区域は1mSv超」→ 3か月1.3mSv超等の定義",
        "「妊婦に限度なし」→ 妊娠中は厳しい限度",
    ),
    "kyokuho-haikisochi": _ep(
        "「制御風速はすべて1.0m/s」→ 形式により0.4〜1.0",
        "「定期自主検査不要」→ 1年以内ごと",
        "「局所排気＝全体換気」→ 発散源近傍の捕集",
        "「レシーバー式は外付け」→ 別形式",
        "「点検記録不要」→ 記録整備が望ましい",
    ),
}

TABLE_BY_SLUG: dict[str, str] = {
    "sagyo-kankyo-sokutei": _tbl(
        ["対象例", "測定頻度の目安"],
        [
            ["粉じん・有機溶剤・特化物", "6か月以内ごと"],
            ["鉛", "1年以内ごと"],
            ["暑熱", "半月以内ごと"],
        ],
    ),
    "eisei-iinkai": _tbl(
        ["項目", "要点"],
        [
            ["設置", "常時50人以上"],
            ["開催", "毎月1回以上"],
            ["議事録", "3年保存"],
        ],
    ),
    "risk-assessment": _tbl(
        ["ステップ", "内容"],
        [
            ["1", "危険源の特定"],
            ["2", "リスクの見積り"],
            ["3", "優先度設定"],
            ["4", "低減措置（除去→工学→管理→PPE）"],
            ["5", "記録（3年）"],
        ],
    ),
}


def _body_from_fact(fact: str, table: str = "") -> str:
    text = fact.strip()
    parts = re.split(r"(?<=[。．])", text)
    buf: list[str] = []
    chunk = ""
    for p in parts:
        p = p.strip()
        if not p:
            continue
        chunk += p
        if len(chunk) >= 120 or p.endswith(("ます。", "です。", "した。")):
            buf.append(chunk.strip())
            chunk = ""
    if chunk.strip():
        buf.append(chunk.strip())
    body = "\n\n".join(buf)
    if table:
        body = body + "\n\n" + table
    return body


def _is_placeholder(row: dict) -> bool:
    term = (row.get("term") or "").strip()
    defn = (row.get("definition") or "").strip()
    body = (row.get("term_detail_body") or "").strip()
    if len(body) > 400:
        return False
    if defn == term or len(defn) < 30:
        return True
    if len(body) <= len(term) + 10:
        return True
    return False


def build_patch(row: dict, fact_key: str) -> dict[str, str]:
    fact = TERM_FACTS[fact_key]
    slug = (row.get("slug") or "").strip()
    term = (row.get("term") or "").strip()
    category = (row.get("category") or "").strip()
    table = TABLE_BY_SLUG.get(slug, "")
    body = _body_from_fact(fact, table)
    body = pad_term_detail_body(
        body, term=term, category=category, core=fact_key, definition=fact
    )
    lead = derive_lead(term, fact)
    category = (row.get("category") or "").strip()
    exam = EXAM_BY_SLUG.get(slug) or derive_exam_points(term, fact, category)
    return {
        "definition": fact,
        "article_lead": lead,
        "term_detail_body": body,
        "exam_points": exam,
        "common_mistakes": derive_mistakes(term, fact, category),
        "memory_tip": derive_memory_tip(term, fact),
        "explanation": exam,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    with GLOSSARY_CSV.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
        fieldnames = list(rows[0].keys()) if rows else []

    updated = 0
    for row in rows:
        slug = (row.get("slug") or "").strip()
        fact_key = resolve_fact_key((row.get("term") or "").strip(), slug) or ""
        if fact_key not in TERM_FACTS:
            continue
        if not _is_placeholder(row):
            continue
        patch = build_patch(row, fact_key)
        for k, v in patch.items():
            if k in fieldnames:
                row[k] = v
        if patch.get("definition"):
            d = patch["definition"].strip()
            if d.startswith("「"):
                row["short_def"] = d[:200] + ("…" if len(d) > 200 else "")
        updated += 1

    if args.dry_run:
        print(f"更新予定: {updated} 語")
        return 0

    with GLOSSARY_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    print(f"更新: {updated} 語（TERM_FACTS）-> {GLOSSARY_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
