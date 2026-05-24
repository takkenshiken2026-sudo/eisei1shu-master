# -*- coding: utf-8 -*-
"""用語詳細記事：やさしい文体・要点の具体例・覚え方・FAQ（3〜4件）を生成。"""
from __future__ import annotations

import re

from glossary_derive_content import (
    _NUM_VAL,
    _sentences,
    derive_exam_points,
    short_def_from,
)
from glossary_fact_lookup import resolve_fact_key
from rewrite_with_numbers import TERM_FACTS

EXAM_LABEL = "第一種衛生管理者試験"


def _term_short(term: str) -> str:
    return term.split("（")[0].strip()


def simplify_prose(text: str) -> str:
    """難しい接続をやわらかくし、文を読みやすくする。"""
    if not text.strip():
        return text
    t = text.strip()
    reps = (
        ("において", "では"),
        ("に関して", "について"),
        ("という語です", "です"),
        ("用いられる", "使われる"),
        ("位置づけられます", "位置づけられます"),
        ("整理するときに使う語です", "整理するときの言葉です"),
        ("課す義務", "義務"),
        ("負うものです", "必要です"),
        ("となります", "になります"),
        ("であり、", "で、"),
        ("すなわち、", "つまり、"),
        ("なお、", "また、"),
    )
    for a, b in reps:
        t = t.replace(a, b)
    t = re.sub(r"（([^）]{25,})）", r"（\1）", t)
    parts = _sentences(t)
    out: list[str] = []
    for s in parts:
        s = s.strip()
        if len(s) > 95:
            mid = s.find("、", 50, 80)
            if mid > 0:
                out.append(s[: mid + 1])
                out.append(s[mid + 1 :].lstrip())
                continue
        out.append(s if s.endswith("。") else s + "。")
    return "\n\n".join(out)


def _example_paragraph(term: str, category: str, source: str) -> str:
    short = _term_short(term)
    nums = [m.group(1) + m.group(2) for m in _NUM_VAL.finditer(source)][:3]
    if "法令" in category or "関係法令" in category:
        if nums:
            return (
                f"【具体例】従業員が{nums[0]}の事業場で、{short}の要件を満たすかどうかが問われます。"
                f"たとえば「{nums[0]}だから不要」と言い換えた選択肢は、人数の数値をずらした典型的な誤りです。"
            )
        return (
            f"【具体例】50人の事業場で{short}が必要かどうか、100人の事業場では人数が変わるか、"
            "といった形で数値が入れ替えられます。条文番号だけ暗記せず、「誰が・いつ・何年保存」までセットで覚えてください。"
        )
    if category.startswith("労働衛生"):
        if "測定" in source or "管理区分" in source:
            return (
                "【具体例】作業環境測定の結果が第2管理区分になった職場では、改善計画と再測定の期限が問題になります。"
                f"「第3区分は良好」と書き換える誤りは、{short}の理解が浅いときに選ばれやすいパターンです。"
            )
        if nums:
            return (
                f"【具体例】濃度や期限が{nums[0]}と示されているとき、選択肢では{nums[1] if len(nums) > 1 else '別の数値'}に"
                f"すり替えることがあります。{short}は数値と対策（測定・保護具・健診）をセットで押さえてください。"
            )
        return (
            f"【具体例】粉じん作業では{short}に関する測定・保護具・教育が同時に問われます。"
            "「測定だけで十分」とする誤りは、ばく露管理を一つに絞ったときに出やすいです。"
        )
    if category == "労働生理":
        if "感度" in term or "特異度" in term or "検査" in term:
            return (
                "【具体例】100人に病気がある10人の集団で、検査が8人を陽性と判定したとき、"
                "感度は8÷10＝80%です。「陽性だった人の割合」と混同すると答えが逆になります。"
            )
        return (
            f"【具体例】{short}は、からだの反応や検査の数値として説明されます。"
            "急性と慢性、可逆と不可逆のどちらか一方だけを強調した選択肢に注意してください。"
        )
    return (
        f"【具体例】{short}を説明するとき、定義の一部だけを切り取った選択肢が正しく見えることがあります。"
        "本文全体と照合し、数値・主体・期限のどれが違うかを言えるようにしてください。"
    )


def build_summary_body(term: str, category: str, source: str) -> str:
    """まず押さえる要点（具体例つき）。"""
    src = simplify_prose(source)
    sents = _sentences(src)
    short = _term_short(term)
    parts: list[str] = []

    if sents:
        parts.append(
            f"この記事で最初に押さえたいのは、次の一文です。\n{sents[0]}"
        )
    else:
        parts.append(f"「{term}」は、{category}でよく出るキーワードです。")

    parts.append(
        f"一言で言うと、{short}は「誰が・何を・いつまで」がセットになった用語です。"
        "試験では、定義文の丸暗記より、この3点を別の言葉に置き換えた誤り選択肢が出ます。"
    )
    parts.append(_example_paragraph(term, category, source))

    if len(sents) > 1:
        parts.append("あわせて、次も覚えておいてください。\n" + "\n".join(sents[1:3]))

    return "\n\n".join(parts)


def build_memory_tip(term: str, category: str, source: str) -> str:
    """覚え方・整理のコツ（詳しめ）。"""
    short = _term_short(term)
    nums = [m.group(1) + m.group(2) for m in _NUM_VAL.finditer(source)][:4]
    num_line = f"・数値メモ：{'／'.join(nums)}" if nums else "・数値メモ：本文の表から拾う"
    law = re.findall(r"（([^）]*(?:法|令|則)[^）]{0,30})）", source)
    law_line = f"・根拠：{law[0]}" if law else "・根拠：記事の法令・根拠欄を確認"

    if "法令" in category:
        hook = f"{short}＝義務の主体＋期限＋保存年限"
        memo = (
            "1枚の紙に「50人・毎月・3年」のように、数字だけを先に書き、"
            "その横に「衛生委員会」「選任」などの語を対応づけます。"
        )
    elif category.startswith("労働衛生"):
        hook = f"{short}＝ばく露→対策の順で整理"
        memo = (
            "発生源の把握、測定、保護具、健診の4段階を矢印でつなぐと、"
            "「対策は一つだけでよい」という誤りに気づきやすくなります。"
        )
    elif category == "労働生理":
        hook = f"{short}＝分母（誰を母数にするか）"
        memo = "2×2表を必ず書き、縦軸を「実際の病気の有無」、横軸を「検査結果」に固定します。"
    else:
        hook = f"{short}＝定義＋数値＋関連語"
        memo = "関連用語との違いを左右2列の表に書き、試験前に声に出して確認します。"

    return (
        f"■キーワード\n{hook}\n\n"
        f"■1枚メモの作り方\n{memo}\n\n"
        f"■書き出す項目\n"
        f"{num_line}\n"
        f"{law_line}\n"
        f"・関連語：記事下のリンクから2語だけ選び、違いを1行で書く\n\n"
        f"■直前の見直し\n"
        f"頻出ポイント5件を「誤りの型」（数値違い／主体違い／期限違い）に分類すると、"
        f"本番で迷ったときに戻る場所がはっきりします。"
    )


def build_faqs(term: str, category: str, source: str, exam_points: str) -> list[tuple[str, str]]:
    """FAQ 4件（質問・回答）。"""
    short = _term_short(term)
    sd = short_def_from(source, term)
    ep = exam_points or derive_exam_points(term, source, category)
    first_ep = ep.split(";")[0].strip() if ep else ""

    return [
        (
            f"{term}とは何ですか？",
            simplify_prose(
                f"{term}とは、{sd.rstrip('。')}。"
                f"現場では制度の一部として使われ、{EXAM_LABEL}では定義と数値・手続がセットで問われます。"
            ),
        ),
        (
            f"{EXAM_LABEL}で{short}はどう出題されますか？",
            simplify_prose(
                f"正しい説明に似せて、数値・主体・期限のどれかを入れ替えた選択肢が多いです。"
                f"代表例：{first_ep if first_ep else '本文の頻出ポイントを確認してください'}。"
                "過去問では「どちらが誤りか」を選ぶ形式も多いので、誤りの理由まで言えると安心です。"
            ),
        ),
        (
            f"{short}でよくある誤解は何ですか？",
            simplify_prose(
                f"単語の意味だけ覚えて、人数・頻度・保存年限を後回しにすることです。"
                f"また、似た用語（関連用語）と役割の違いが曖昧なまま本番に入ると、取り違えが起きやすくなります。"
                "本文の表と「よくある誤解」の節を、セットで読み返してください。"
            ),
        ),
        (
            "公式の制度内容はどこで確認すればよいですか？",
            (
                f"{EXAM_LABEL}の学習用に要点をまとめた記事です。"
                "受験前には、e-Gov法令検索、厚生労働省の労働安全衛生ページ、"
                "安全衛生技術試験協会の試験要項など、公式情報で最新の数値・要件を必ず確認してください。"
            ),
        ),
    ]


def best_source_for_row(row: dict[str, str]) -> str:
    term = (row.get("term") or "").strip()
    slug = (row.get("slug") or "").strip()
    key = resolve_fact_key(term, slug)
    if key:
        return TERM_FACTS[key]
    return (row.get("definition") or row.get("short_def") or "").strip()


def build_reader_patch(row: dict[str, str]) -> dict[str, str]:
    term = (row.get("term") or "").strip()
    category = (row.get("category") or "").strip()
    source = best_source_for_row(row)
    source = simplify_prose(source)

    exam = (row.get("exam_points") or "").strip() or derive_exam_points(term, source, category)
    faqs = build_faqs(term, category, source, exam)

    patch: dict[str, str] = {
        "summary_body": build_summary_body(term, category, source),
        "memory_tip": build_memory_tip(term, category, source),
        "article_lead": simplify_prose(
            (row.get("article_lead") or "").strip()
            or short_def_from(source, term)
        ),
        "exam_points": exam,
        "explanation": exam,
    }

    body = (row.get("term_detail_body") or "").strip()
    if body:
        patch["term_detail_body"] = simplify_prose(body)

    for i, (q, a) in enumerate(faqs, start=1):
        patch[f"faq_{i}_question"] = q
        patch[f"faq_{i}_answer"] = simplify_prose(a)

    if not (row.get("common_mistakes") or "").strip():
        patch["common_mistakes"] = (
            f"「{term}」は、定義と数値・手続をバラバラに覚えると取り違えやすいです。"
            "具体例つきの要点と表を見ながら、関連用語との違いを1枚にまとめてください。"
        )

    return patch
