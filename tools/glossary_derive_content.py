# -*- coding: utf-8 -*-
"""定義文から用語固有の試験ポイント・注意点・追記段落を導出（汎用テンプレは使わない）。"""
from __future__ import annotations

import re

from glossary_enrich_a_rank_content import _ep, _tbl

_SENT_SPLIT = re.compile(r"(?<=[。．])")

_NUM_VAL = re.compile(
    r"(\d+(?:\.\d+)?)\s*(人|時間|か月|月|年|日|回|週|mSv|mg/m³|mg|dB|ppm|%|時間以内|年間|回まで|回以上|人以上|時間超)"
)

# 試験でよく入れ替えられる数値ペア（正→誤の候補）
_NUM_SWAP: dict[str, list[str]] = {
    "3年": ["1年", "5年"],
    "5年": ["3年", "1年"],
    "30年": ["10年", "3年"],
    "1年": ["3年"],
    "50人": ["30人", "100人"],
    "100人": ["50人", "300人"],
    "300人": ["100人", "500人"],
    "500人": ["300人", "1000人"],
    "45時間": ["36時間", "60時間"],
    "80時間": ["100時間", "60時間"],
    "6か月": ["1年", "3か月"],
    "14日": ["7日", "30日"],
    "85dB": ["80dB", "90dB"],
    "90dB": ["85dB", "100dB"],
}

_SUBJECT_SWAPS = (
    ("事業者", "労働者"),
    ("労働者", "事業者"),
    ("使用者", "労働者"),
    ("厚生労働大臣", "事業者"),
    ("所轄労働基準監督署長", "事業者"),
    ("衛生管理者", "産業医"),
    ("産業医", "衛生管理者"),
    ("安全管理者", "衛生管理者"),
)

_OPPOSITE_PAIRS = (
    ("義務", "任意"),
    ("必要", "不要"),
    ("禁止", "許可"),
    ("専任", "兼務"),
    ("常勤", "非常勤"),
    ("感音性", "伝音性"),
    ("急性", "慢性"),
    ("内部被ばく", "外部被ばく"),
    ("偽陽性", "偽陰性"),
    ("感度", "特異度"),
)


def _sentences(text: str) -> list[str]:
    parts: list[str] = []
    for chunk in _SENT_SPLIT.split(text.strip()):
        s = chunk.strip()
        if s:
            parts.append(s if s.endswith("。") else s + "。")
    return parts


def _wrong_number(val: str) -> str | None:
    for key, alts in _NUM_SWAP.items():
        if key in val:
            return val.replace(key, alts[0], 1)
    m = re.match(r"(\d+)(.+)", val)
    if m:
        n = int(m.group(1))
        unit = m.group(2)
        if n > 1:
            return f"{max(1, n // 2)}{unit}"
        return f"{n + 1}{unit}"
    return None


def derive_exam_points(term: str, text: str, category: str = "") -> str:
    """定義文の事実から誤り選択肢パターンを最大5件生成。"""
    pts: list[str] = []
    seen: set[str] = set()

    def add(p: str) -> None:
        p = p.strip()
        if not p or p in seen:
            return
        seen.add(p)
        pts.append(p)

    short = term.split("（")[0].strip()[:24]

    # 数値の書き換え
    for m in _NUM_VAL.finditer(text):
        val = m.group(1) + m.group(2)
        wrong = _wrong_number(val)
        if wrong and wrong != val:
            add(f"「{short}の要件は{wrong}」→ 誤り（本文は{val}）")

    # 文単位の反転・主体入れ替え
    for sent in _sentences(text):
        s = sent.replace(f"「{term}」", "").replace(f"「{short}」", "")
        if len(s) < 12:
            continue
        for a, b in _OPPOSITE_PAIRS:
            if a in sent and b not in sent:
                add(f"「{short}は{b}である」→ 誤り（{a}が要点）")
                break
        for sub_a, sub_b in _SUBJECT_SWAPS:
            if sub_a in sent:
                add(f"「{sub_b}が{short}の主体・実施者」→ 誤り（{sub_a}）")
                break
        if "保存" in sent and re.search(r"\d+\s*年", sent):
            add(f"「{short}の記録保存は1年でよい」→ 本文の保存年限と照合")
        if "毎月" in sent and "1回" in sent:
            add(f"「{short}は年1回開催でよい」→ 毎月1回以上の記述と矛盾")
        if "選任" in sent and "14日" in sent:
            add(f"「{short}の選任報告は30日以内」→ 14日以内の記述と矛盾")
        if len(pts) >= 5:
            break

    # 法令条番の取り違え
    laws = re.findall(r"（([^）]*(?:法|令|則)[^）]{0,35})）", text)
    if laws and len(pts) < 5:
        law = laws[0]
        add(f"「根拠は{law[:8]}…以外の法令」→ 条文番号・法令名の入れ替えに注意")

    # カテゴリ横断の固有論点（汎用5件の羅列はしない）
    if category == "労働生理" and "検査" in term and len(pts) < 3:
        if "感度" in text or "特異度" in text:
            add("「感度＝陽性の人の割合」→ 分母は実際に病気がある人")
    if "作業環境測定" in text and len(pts) < 4:
        add("「第3管理区分は良好」→ 速やかに改善が必要な区分")

    if not pts:
        add(f"「{short}は試験範囲外」→ 定義・数値・手続のいずれかが出題される")

    # 不足分は定義文から「〜ではない」「〜のみ」型の誤りを作る（同一文型の羅列は避ける）
    for sent in _sentences(text):
        if len(pts) >= 5:
            break
        if "ではない" in sent or "ではなく" in sent:
            add(f"「{short}」の説明で否定表現を肯定に読み替えた選択肢 → 誤り")
        elif re.search(r"\d+", sent) and "未満" in sent:
            add(f"「{short}」の基準値を『超』と『未満』で逆にした選択肢 → 誤り")
        elif "のみ" in sent or "だけ" in sent:
            add(f"「{short}」を単独要件として完結させた選択肢 → 関連制度とのセットで確認")

    return _ep(*pts[:5])


def derive_mistakes(term: str, text: str, category: str = "") -> str:
    sents = _sentences(text)
    if not sents:
        return f"「{term}」は類似用語とセットで整理すると取り違えにくくなります。"
    focus = sents[0]
    if len(sents) > 1 and any(k in sents[1] for k in ("義務", "選任", "保存", "測定", "届出")):
        focus = sents[1]
    hint = ""
    for a, b in _OPPOSITE_PAIRS:
        if a in text:
            hint = f"{a}と{b}、"
            break
    nums = [m.group(1) + m.group(2) for m in _NUM_VAL.finditer(text)][:2]
    num_part = f"数値（{'・'.join(nums)}）と" if nums else ""
    return (
        f"{focus.rstrip('。')}。"
        f"試験では{hint}{num_part}主体・期限のいずれかが入れ替えられた選択肢が出やすいです。"
        f"関連用語と違いを表にまとめてください（{category or '本試験'}）。"
    )


def derive_memory_tip(term: str, text: str) -> str:
    short = term.split("（")[0].strip()
    if "＝" in text or "とは、" in text:
        m = re.search(r"とは、([^。]{4,50})", text)
        if m:
            return f"{short}＝{m.group(1).strip()}"
    nums = [m.group(1) + m.group(2) for m in _NUM_VAL.finditer(text)][:2]
    if nums:
        return f"{short}：{'・'.join(nums)}をセットで暗記"
    return f"{short}：定義＋数値・主体を1行メモ"


def short_def_from(defn: str, term: str) -> str:
    d = defn.strip()
    if not d:
        return f"「{term}」の要点を整理した用語です。"
    if d.startswith("「"):
        end = d.find("。", 0, 240)
        if end > 0:
            return d[: end + 1]
    return d[:200] + ("…" if len(d) > 200 else "")


def derive_lead(term: str, text: str) -> str:
    sents = _sentences(text)
    if not sents:
        return f"「{term}」の意味と、試験で問われる数値・手続の違いを整理します。"
    if len(sents) == 1:
        return sents[0]
    return sents[0] + sents[1]


def derive_extra_paragraphs(definition: str, body: str) -> str:
    """本文に未収載の定義文のみ追記（テンプレ文は付けない）。"""
    extra: list[str] = []
    body_norm = re.sub(r"\s+", "", body)
    for sent in _sentences(definition):
        key = re.sub(r"\s+", "", sent)[:40]
        if key and key not in body_norm:
            extra.append(sent)
    return "\n\n".join(extra[:2])


def derive_table_from_text(term: str, text: str) -> str:
    """数値・略語が取れるときだけ表を作る。取れなければ空文字。"""
    rows: list[list[str]] = []
    seen: set[str] = set()
    patterns = [
        (re.compile(r"月\s*(\d+)\s*時間"), "月間上限", "{0}時間"),
        (re.compile(r"年\s*(\d+)\s*時間"), "年間上限", "{0}時間"),
        (re.compile(r"(\d+)\s*年(?:間)?保存"), "記録保存", "{0}年"),
        (re.compile(r"常時\s*(\d+)\s*人以上"), "規模要件", "常時{0}人以上"),
        (re.compile(r"(\d+)\s*か月以内"), "頻度", "{0}か月以内"),
        (re.compile(r"(\d+)\s*日以内"), "期限", "{0}日以内"),
    ]
    for pat, label, fmt in patterns:
        for m in pat.finditer(text):
            val = fmt.format(m.group(1))
            if val not in seen:
                seen.add(val)
                rows.append([label, val])
    if len(rows) >= 2:
        return _tbl(["項目", "数値・要件"], rows[:8])
    m = re.search(r"（([^）]{3,80})）", term)
    if m and "・" in m.group(1):
        parts = [p.strip() for p in m.group(1).split("・") if p.strip()]
        if len(parts) >= 3:
            return _tbl(
                ["要素", "ポイント"],
                [[p, f"{p}の意味を定義と照合"] for p in parts[:6]],
            )
    return ""


def is_generic_body(body: str) -> bool:
    if "入れ替えた誤り選択肢がよく作られます" in body:
        return True
    if "試験で確認すること】" in body and "関連制度" in body:
        return True
    return False
