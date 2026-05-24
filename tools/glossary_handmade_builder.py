# -*- coding: utf-8 -*-
"""用語ごとに手作り品質の記事フィールドを組み立てる（全件リライト用）。"""
from __future__ import annotations

import re

from apply_glossary_from_term_facts import EXAM_BY_SLUG, TABLE_BY_SLUG
from generate_glossary_long_descriptions import strip_legacy_leading_prefix
from glossary_derive_content import (
    _NUM_VAL,
    _sentences,
    derive_exam_points,
    derive_lead,
    derive_memory_tip,
    derive_mistakes,
    derive_table_from_text,
    short_def_from,
)
from glossary_enrich_a_rank_content import _tbl
from glossary_fact_lookup import resolve_fact_key
from rewrite_with_numbers import TERM_FACTS

EXAM_LABEL = "第一種衛生管理者試験"

_THIN_MARKERS = (
    "説明において",
    "使う語です",
    "位置づけられます",
)


def strip_boilerplate(defn: str) -> str:
    t = strip_legacy_leading_prefix(defn or "")
    t = re.sub(
        r"「[^」]+」とは、[^。]+の説明において、",
        "",
        t,
        count=1,
    )
    t = re.sub(r"使う語です。まず、", "", t, count=1)
    t = re.sub(r"説明するときに使う語です。", "", t, count=1)
    return t.strip()


def is_thin_definition(defn: str) -> bool:
    d = (defn or "").strip()
    if len(d) < 140:
        return True
    return sum(1 for m in _THIN_MARKERS if m in d) >= 2


def best_source_text(row: dict[str, str]) -> tuple[str, str | None]:
    """(本文ソース, TERM_FACTSキー)"""
    term = (row.get("term") or "").strip()
    slug = (row.get("slug") or "").strip()
    fact_key = resolve_fact_key(term, slug)
    if fact_key:
        return TERM_FACTS[fact_key].strip(), fact_key
    defn = strip_boilerplate(row.get("definition") or "")
    if defn and not is_thin_definition(defn):
        return defn, None
    if defn:
        return defn, None
    return f"「{term}」は{(row.get('category') or '本試験').strip()}で押さえる用語です。", None


def _term_short(term: str) -> str:
    return term.split("（")[0].strip()


def _extract_laws(text: str) -> list[str]:
    found: list[str] = []
    for m in re.finditer(r"（([^）]*(?:法|令|則)[^）]{0,40})）", text):
        s = m.group(1).strip()
        if s and s not in found:
            found.append(s)
    return found


def _keyword_rows(text: str, term: str) -> list[list[str]]:
    """定義文から義務・手続キーワードを拾い表にする。"""
    rows: list[list[str]] = []
    checks = [
        ("選任・設置", r"選任|設置|指名"),
        ("頻度・期限", r"毎月|年\d+回|か月以内|日以内|14日"),
        ("記録・保存", r"保存|記録|議事録"),
        ("届出・報告", r"届出|報告|労基署"),
        ("測定・評価", r"測定|評価|管理区分"),
        ("保護・教育", r"保護具|教育|健診"),
    ]
    for label, pat in checks:
        if re.search(pat, text):
            m = re.search(
                rf".{{0,25}}(?:{pat}).{{0,35}}",
                text,
            )
            snippet = (m.group(0) if m else label)[:40].strip("、。")
            rows.append([label, snippet or "本文の定義を参照"])
    if rows:
        return rows[:6]
    short = _term_short(term)
    return [
        ["定義", f"{short}の意味と制度上の位置づけ"],
        ["試験", "数値・主体・期限の3点セット"],
        ["関連", "近い用語との違いを表で整理"],
    ]


def resolve_table(term: str, text: str, slug: str, category: str) -> str:
    if slug in TABLE_BY_SLUG:
        return TABLE_BY_SLUG[slug]
    tbl = derive_table_from_text(term, text)
    if tbl:
        return tbl
    rows = _keyword_rows(text, term)
    if "法令" in category:
        headers = ["観点", "内容"]
    elif category.startswith("労働衛生"):
        headers = ["観点", f"{_term_short(term)}で確認すること"]
    else:
        headers = ["観点", "整理のポイント"]
    return _tbl(headers, rows)


def _exam_focus_paragraph(term: str, category: str, text: str) -> str:
    short = _term_short(term)
    if "法令" in category:
        return (
            f"{EXAM_LABEL}の関係法令では、{short}について"
            "「誰が・いつ・どこへ届出し・何年保存するか」がセットで出題されます。"
            "条文番号だけでなく、人数・頻度・保存年限の数値が入れ替えられた選択肢に注意してください。"
        )
    if category.startswith("労働衛生"):
        return (
            f"{short}は、ばく露の評価から保護具・作業環境測定・健診までが連動します。"
            "単独の対策（測定だけ・マスクだけ）を正とする誤りがよく混ざるため、"
            "優先順位（除去→封じ込め→換気→保護具）もあわせて確認してください。"
        )
    if category == "労働生理":
        return (
            f"{short}は、からだのしくみや検査の指標として問われます。"
            "定義の暗記に加え、分母の取り方（誰を母数にするか）や"
            "急性／慢性、可逆／不可逆の対比が選択肢になりやすいです。"
        )
    return (
        f"{short}は{category}の重要語です。"
        "用語の意味に加え、関連する制度・数値・手続の違いを1枚のメモにまとめると定着しやすくなります。"
    )


def _intro_expand(sent: str, term: str, category: str) -> str:
    short = _term_short(term)
    if not sent:
        return f"「{term}」は{category}で頻出のキーワードです。定義をそのまま暗記するのではなく、制度の中での役割まで含めて押さえます。"
    return (
        f"{sent.rstrip('。')}。"
        f"ここでは{short}を、試験で問われる「定義＋数値＋手続」のセットとして整理します。"
    )


def _commentary_for_sentence(sent: str, term: str) -> str:
    short = _term_short(term)
    if "義務" in sent and "努力" not in sent:
        return f"※{short}では、努力義務ではなく法令上の義務かどうかが問われやすいポイントです。"
    if re.search(r"\d+\s*年", sent) and "保存" in sent:
        return "※保存年限は他制度（1年・3年・5年・30年）と取り違えられやすいので、条文ごとにメモしてください。"
    if "選任" in sent:
        return "※選任主体（事業者）と報告先（労基署）をセットで覚えると、主体の入れ替え問題に強くなります。"
    if "測定" in sent:
        return "※測定の頻度・対象・評価方法は、物質や作業場の種類で異なるため、一覧表にまとめるとよいです。"
    if "委員会" in sent and "毎月" in sent:
        return "※「年1回でよい」という誤りが定番です。毎月1回以上の記述と照合してください。"
    if "偽" in sent or "陽性" in sent or "陰性" in sent:
        return "※検査用語は分母（誰を母数にするか）が命です。2×2表で整理してください。"
    if len(sent) > 40:
        return f"※上記は{short}の理解を深めるための補足です。過去問では一文だけ切り取った誤り選択肢が作られます。"
    return ""


def _numeric_detail_paragraph(text: str, term: str) -> str:
    items: list[str] = []
    for m in _NUM_VAL.finditer(text):
        val = m.group(1) + m.group(2)
        ctx = text[max(0, m.start() - 18) : m.end() + 8].replace("\n", "")
        items.append(f"・{val}（{ctx.strip('、。')}）")
    if len(items) < 2:
        return ""
    short = _term_short(term)
    return (
        f"{short}で押さえる数値・期限は次のとおりです。\n"
        + "\n".join(items[:8])
        + "\n数値だけを単独で覚えると入れ替えに弱いため、意味（上限・頻度・保存・規模）と結びつけてください。"
    )


def _past_exam_paragraph(term: str, category: str, text: str) -> str:
    short = _term_short(term)
    if "法令" in category:
        return (
            f"過去問では、{short}について正しい説明に似せ、"
            "人数要件・開催頻度・保存年限・届出先のいずれか1点だけをずらした選択肢が多く見られます。"
            "「どちらが誤りか」を選ぶ設問では、ずれた1要素を言語化できると正答率が上がります。"
        )
    if category.startswith("労働衛生"):
        return (
            f"過去問では、{short}を単独の対策として正しく見せる誤り"
            "（測定のみ・保護具のみ・健診のみ）や、管理区分・濃度の数値入れ替えが頻出です。"
            "関連する法令・規則名の取り違えもセットで確認してください。"
        )
    if category == "労働生理":
        return (
            f"過去問では、{short}の定義文の一部だけを切り取り、"
            "分母・指標名（感度／特異度／予測値）を入れ替える問題が多いです。"
            "計算問題では2×2表を書いてから判断するとミスが減ります。"
        )
    return (
        f"過去問では、{short}の定義と、近い用語の違いを問ぶ形式が中心です。"
        "本文の表を見ながら、誤りの作られ方（数値・主体・期限）をメモしてください。"
    )


def _study_flow_paragraph(term: str, category: str) -> str:
    short = _term_short(term)
    return (
        f"学習の順序は、(1){short}の定義を一文で言える、(2)本文の表の数値・期限を言える、"
        f"(3)頻出ポイント5件のうち2件を自分の言葉で説明できる、の3段階が目安です。"
        f"関連用語と違いを1枚にまとめ、過去問で「なぜ誤りか」まで確認すると定着します。"
    )


def _workplace_paragraph(term: str, category: str, text: str) -> str:
    short = _term_short(term)
    if "健診" in text or "健康診断" in text:
        return (
            f"職場では、{short}の結果が就業上の措置（作業変更・二次健診）につながります。"
            "個人情報の取扱いと、衛生委員会・産業医への報告の流れも実務の要点です。"
        )
    if "測定" in text or "濃度" in text:
        return (
            f"現場では、{short}に関する測定記録と改善措置の記録がセットで管理されます。"
            "管理区分の悪化時は、工程見直し・局所排気・保護具の見直しを短いサイクルで行います。"
        )
    if "選任" in text or "委員会" in text:
        return (
            f"体制面では、{short}の選任・会議の開催・議事録保存が継続的に求められます。"
            "紙の記録だけでなく、実際の改善（再発防止）までつながっているかが監査の観点になります。"
        )
    if "中毒" in text or "ばく露" in text or "有害" in category:
        return (
            f"有害要因では、{short}の認識遅れが健康障害につながります。"
            "発生源の把握、測定、保護具、教育を組み合わせた管理が、事故・障害防止の基本です。"
        )
    return (
        f"現場の衛生管理では、{short}を単独で見ず、"
        "作業手順・記録・教育のどこに組み込むかを決めると運用がぶれにくくなります。"
    )


def compose_handmade_body(
    term: str,
    category: str,
    source: str,
    *,
    slug: str = "",
) -> str:
    src = strip_boilerplate(source)
    sents = _sentences(src)
    parts: list[str] = []

    parts.append(_intro_expand(sents[0] if sents else "", term, category))
    parts.append(_exam_focus_paragraph(term, category, src))

    tbl = resolve_table(term, src, slug, category)
    if tbl:
        parts.append(tbl)

    num_para = _numeric_detail_paragraph(src, term)
    if num_para:
        parts.append(num_para)

    for sent in sents[1:] if sents else []:
        parts.append(sent)
        note = _commentary_for_sentence(sent, term)
        if note:
            parts.append(note)

    parts.append(_past_exam_paragraph(term, category, src))
    parts.append(_workplace_paragraph(term, category, src))

    laws = _extract_laws(src)
    if laws:
        parts.append(
            f"根拠法令の例：{('、'.join(laws[:3]))}。"
            "試験では、類似条文・省令名・条番号の入れ替えに注意してください。"
        )

    parts.append(_study_flow_paragraph(term, category))

    body = "\n\n".join(p.strip() for p in parts if p.strip())
    plain_len = len(re.sub(r"<[^>]+>", "", body))
    if plain_len < 900:
        short = _term_short(term)
        parts.append(
            f"まとめると、{short}は{category}の文脈で、"
            "定義・数値・主体・手続・関連制度の5点をセットで問われる用語です。"
            "本記事の表と頻出ポイントを使い、過去問で「誤りの理由」まで言える状態を目指してください。"
        )
        body = "\n\n".join(p.strip() for p in parts if p.strip())
    return body


def article_title_for(term: str) -> str:
    short = _term_short(term)
    if len(short) > 28:
        short = short[:26] + "…"
    return f"{short}とは？意味・試験ポイント・注意点【{EXAM_LABEL}】"


def faq_pair(term: str) -> tuple[str, str, str, str]:
    q1 = f"{term}は{EXAM_LABEL}で重要ですか？"
    a1 = (
        "重要です。定義だけでなく、数値・対象・手続・関連制度との違いが"
        "選択肢で入れ替えられることがあります。本文の表と頻出ポイントを確認してください。"
    )
    q2 = "公式情報も確認した方がよいですか？"
    a2 = (
        "はい。本記事は学習用の要点整理です。法令改正や正式な運用は、"
        "e-Gov法令検索・厚生労働省・試験実施団体の公式情報で受験前に確認してください。"
    )
    return q1, a1, q2, a2


def legal_basis_from_text(text: str) -> str:
    return "; ".join(_extract_laws(text)[:4])


def exam_for_slug(slug: str, term: str, text: str, category: str) -> str:
    if slug in EXAM_BY_SLUG:
        return EXAM_BY_SLUG[slug]
    return derive_exam_points(term, text, category)


def build_handmade_patch(row: dict[str, str], *, use_manual_body: str | None = None) -> dict[str, str]:
    term = (row.get("term") or "").strip()
    slug = (row.get("slug") or "").strip()
    category = (row.get("category") or "").strip()
    source, fact_key = best_source_text(row)

    if use_manual_body:
        body = use_manual_body.strip()
        defn = strip_boilerplate(row.get("definition") or source)
    else:
        defn = source if source.startswith("「") else f"「{term}」{source.lstrip('「')}"
        body = compose_handmade_body(term, category, source, slug=slug)
        if "<table" not in body:
            tbl = resolve_table(term, source, slug, category)
            if tbl:
                body = body.rstrip() + "\n\n" + tbl

    exam = exam_for_slug(slug, term, source, category)
    q1, a1, q2, a2 = faq_pair(term)
    legal = legal_basis_from_text(source) or (row.get("legal_basis") or "").strip()

    patch: dict[str, str] = {
        "definition": defn,
        "short_def": short_def_from(defn, term),
        "article_title": article_title_for(term),
        "article_lead": derive_lead(term, source),
        "term_detail_body": body,
        "exam_points": exam,
        "explanation": exam,
        "common_mistakes": derive_mistakes(term, source, category),
        "memory_tip": derive_memory_tip(term, source),
        "faq_1_question": q1,
        "faq_1_answer": a1,
        "faq_2_question": q2,
        "faq_2_answer": a2,
    }
    if legal:
        patch["legal_basis"] = legal
    return patch
