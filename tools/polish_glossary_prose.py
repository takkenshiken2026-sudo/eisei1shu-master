#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docs/dai1shu-glossary-terms-master.csv の解説を、読点の羅列ではなく
「定義 → 数値要件の展開 → 実務上の含意」の流れが分かる日本語に整形する。

  python3 tools/polish_glossary_prose.py

※数値・条文番号・保存年限などの事実は極力維持し、接続・主述の補完のみ行う。
"""
from __future__ import annotations

import csv
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MASTER = ROOT / "docs" / "dai1shu-glossary-terms-master.csv"
MIRRORS = [
    ROOT / "docs" / "glossary-terms-checklist.csv",
    ROOT / "public_site" / "docs" / "dai1shu-glossary-terms-master.csv",
    ROOT / "public_site" / "docs" / "glossary-terms-checklist.csv",
]

CONNECTORS = (
    "まず",
    "次に",
    "さらに",
    "また",
    "なお",
    "そのうえ",
    "以上のとおり",
)

# 用語ごとの特別補正（全体置換）
SPECIAL: dict[str, str] = {
    "血液・酸素運搬（ヘモグロビン・COHb）": (
        "「血液・酸素運搬（ヘモグロビン・COHb）」は、肺で酸素を受け取り組織へ届ける過程を説明するときの語です。"
        "ヘモグロビンはヘム鉄の部位で酸素と可逆的に結合し、安静時の心拍出量に応じて酸素を運びます。"
        "一方で一酸化炭素は同じ結合部位に入り込み、酸素よりもはるかに強く結合するため、一般に酸素に対する親和性はおよそ200〜250倍と説明されます（いわゆるハルデーン係数のイメージ）。"
        "その結果、カルボキシヘモグロビン（COHb）が増えると酸素運搬能が落ちるだけでなく、残った酸素の解離も妨げられ、組織レベルでの酸素供給が悪化しやすくなります。"
        "臨床的にはCOHbが高いほど中枢症状が出やすく、職場では換気・発生源の遮断とともに、中毒疑いの評価指標として扱います。"
    ),
    "一酸化炭素（障害と機序）": (
        "「一酸化炭素（障害と機序）」は、一酸化炭素が酸素の運搬と組織での利用をどう乱すかを扱う論点です。"
        "一酸化炭素はヘモグロビンの酸素結合部位に結合し、酸素よりもはるかに強く結合するため、一般に酸素に対する親和性はおよそ200〜250倍と説明されます（ハルデーン係数の整理）。"
        "その結果、カルボキシヘモグロビン（COHb）が増えると酸素運搬能が低下し、残存する酸素の解離も妨げられやすく、組織レベルでは細胞性窒息に近い状態が生じます。"
        "急性高濃度曝露では頭痛や嘔吐から意識障害へ進行しやすく、急性中毒後に遅れて神経精神症状が出る遅発性脳症も鑑別の要点です。"
        "職場対策では、発生源の遮断、換気、測定、救助体制の確保が中心になります。"
    ),
}


def _strip_trailing_polite(s: str) -> str:
    s = s.rstrip("。")
    for suf in ("です", "ます", "せん", "ない", "ある", "いる", "れる", "られる", "した", "いい"):
        if s.endswith(suf):
            return s
    return s


def _ensure_sentence(s: str) -> str:
    s = s.strip().rstrip("。")
    if not s:
        return ""
    if re.search(
        r"(です|ます|せん|ない|ある|いる|れる|られる|なります|ました|でした|されます|されました|ください|いい|した)$",
        s,
    ):
        return s + "。"
    if re.search(r"(です|ます|せん|ない)(（[^）]+）)$", s):
        return s + "。"
    if re.search(r"\d", s) or re.search(
        r"(ppm|mSv|mg|dL|mEq|mmHg|Hz|dB|℃|lx|%|時間|分|秒|か月|週|日|人|種|回)",
        s,
    ):
        return s + "。"
    return s + "です。"


def split_sentences(text: str) -> list[str]:
    t = text.strip()
    parts: list[str] = []
    buf = []
    i = 0
    while i < len(t):
        ch = t[i]
        buf.append(ch)
        if ch == "。":
            seg = "".join(buf).strip()
            if seg:
                parts.append(seg.rstrip("。"))
            buf = []
        i += 1
    tail = "".join(buf).strip()
    if tail:
        parts.append(tail.rstrip("。"))
    return [p for p in parts if p]


def polish_description(term: str, desc: str) -> str:
    if term in SPECIAL:
        return SPECIAL[term]

    desc = desc.strip()
    if not desc:
        return desc

    sents = split_sentences(desc)
    if not sents:
        return desc

    out: list[str] = []

    first = sents[0].strip()
    if not first.startswith("「"):
        first = f"「{term}」とは、{first}"
    first = _strip_trailing_polite(first)
    out.append(_ensure_sentence(first))

    for idx, s in enumerate(sents[1:], start=1):
        s = s.strip()
        if not s:
            continue
        s = _strip_trailing_polite(s)
        conn = CONNECTORS[(idx - 1) % len(CONNECTORS)]
        if s.startswith(conn):
            merged = _ensure_sentence(s)
        else:
            merged = _ensure_sentence(f"{conn}、{s}")
        out.append(merged)

    text = "".join(out)
    text = re.sub(r"(です|ます|せん|ない|ある|いる|れる|られる)です。", r"\1。", text)
    text = re.sub(r"。{2,}", "。", text)
    return text


def main() -> None:
    if not MASTER.is_file():
        print(f"見つかりません: {MASTER}", file=sys.stderr)
        sys.exit(1)

    with MASTER.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    if not rows or rows[0] != ["カテゴリ", "用語", "解説"]:
        print("CSVヘッダー異常", file=sys.stderr)
        sys.exit(1)

    changed = 0
    for row in rows[1:]:
        if len(row) < 3:
            continue
        term = row[1].strip()
        old = row[2].strip()
        new = polish_description(term, old)
        if new != old:
            row[2] = new
            changed += 1

    with MASTER.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerows(rows)

    for mirror in MIRRORS:
        mirror.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(MASTER, mirror)

    print(f"整形 {changed} / {len(rows)-1} 件 -> {MASTER}")


if __name__ == "__main__":
    main()
