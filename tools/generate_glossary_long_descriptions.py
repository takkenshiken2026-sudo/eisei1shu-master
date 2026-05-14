#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
glossary-terms-checklist.csv の「解説」を、用語の意味が伝わる短文（目安200字程度）に整形する。
マスターCSVと同期して eisei1-data-glossary.js を再生成する前提で使用する。

  python3 tools/generate_glossary_long_descriptions.py
  python3 tools/generate_glossary_long_descriptions.py --dry-run
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 以前の版で解説先頭に付いていた文（再生成時に剥がす）
LEGACY_LEADING_PREFIXES: tuple[str, ...] = (
    "有害業務に関する法令・命令の説明において",
    "衛生管理体制や共通手続きを定める法令の説明において",
    "有害因子のばく露と防止策に関する労働衛生の説明において",
    "作業環境・職場の健康課題に関する労働衛生の説明において",
    "人体の機能や有害因子の作用・病態に関する説明において",
)


def strip_legacy_leading_prefix(s: str) -> str:
    t = s.strip()
    for p in LEGACY_LEADING_PREFIXES:
        if t.startswith(p):
            t = t[len(p) :].lstrip("、")
            break
    return t


def looks_like_generated_definition(s: str) -> bool:
    """すでにこのスクリプトが出力した定義文っぽいときは真（短い手入力メモと区別）。"""
    s = s.strip()
    if len(s) < 100:
        return False
    if not s.startswith("「"):
        return False
    if "とは、" not in s:
        return False
    if "使う語です" in s or "用語であり" in s:
        return True
    if "説明において" in s and len(s) > 140:
        return True
    return False


def extract_seed_hint(description: str) -> str:
    """
    長文化以前の短い学習メモを取り出す。
    自動生成済みの定義全文はヒントとして使わない（誤った入れ子を防ぐ）。
    """
    s = (description or "").strip()
    if not s:
        return ""
    if looks_like_generated_definition(s):
        return ""
    m = re.search(r"ここでの整理メモは「([^」]+)」", s)
    if m:
        return m.group(1).strip()
    bullets = re.findall(r"・[^：\n]+：「([^」]+)」", s)
    if bullets:
        return "・".join(bullets)
    if "【試験の狙い】" not in s and len(s) < 120:
        return s
    return ""


def extract_core_from_flat_definition(desc: str, cat: str) -> str:
    """前置きなし／ありの定義文から核心句（〜を中心に／を手がかりに／に関してからだの直前）を取出す。"""
    t = strip_legacy_leading_prefix(desc)
    if not t:
        return ""
    if "法令" in cat:
        m = re.search(r"「[^」]+」とは、(.+?)を中心に、法令が", t)
        return m.group(1).strip() if m else ""
    if cat.startswith("労働衛生"):
        m = re.search(r"「[^」]+」とは、(.+?)を手がかりに、", t)
        return m.group(1).strip() if m else ""
    m = re.search(r"「[^」]+」とは、(.+?)に関してからだの", t)
    return m.group(1).strip() if m else ""


def recover_core_from_nested_duplicate(desc: str, cat: str) -> str:
    """
    誤って定義全文をヒントにしたときにできる入れ子の重複から、
    もともとの核心句（hint を hint_to_core_phrase した相当）だけを拾う。
    """
    if not desc:
        return ""
    if "法令" in cat:
        m = re.search(r"おもに(.+?)について定められた義務", desc)
        return m.group(1).strip() if m else ""
    if cat.startswith("労働衛生"):
        m = re.search(r"」とは、(.+?)を踏まえて説明される評価", desc)
        return m.group(1).strip() if m else ""
    m = re.search(r"」とは、(.+?)に関してからだの反応や疾患の説明に用いる語ですに関して", desc)
    return m.group(1).strip() if m else ""


def _enumerate_parts(parts: list[str]) -> str:
    p = [x.strip() for x in parts if x.strip()]
    if not p:
        return ""
    if len(p) == 1:
        return p[0]
    if len(p) == 2:
        return f"{p[0]}および{p[1]}"
    return "、".join(p[:-1]) + "および" + p[-1]


def hint_to_core_phrase(hint: str) -> str:
    """学習メモを、定義文に埋め込む短い核心句にする。"""
    h = hint.strip().rstrip("。")
    if not h:
        return ""

    m = re.match(r"^(.+?)と(.+?)のイメージ$", h)
    if m:
        a, b = m.group(1).strip(), m.group(2).strip()
        return f"{a}と{b}の関係"

    if h.endswith("のイメージ"):
        return re.sub(r"のイメージ$", "", h).strip()

    if h.endswith("の入口"):
        core = re.sub(r"の入口$", "", h).strip()
        return f"{core}に関する基本的な論点"

    if "・" in h:
        parts = [p.strip() for p in h.split("・")]
        return _enumerate_parts(parts)

    if "/" in h:
        parts = [p.strip() for p in h.split("/")]
        return _enumerate_parts(parts)

    return h


def clamp_chars(s: str, max_len: int = 200) -> str:
    """句読点の手前で切り、目安文字数に収める。"""
    s = s.strip()
    if len(s) <= max_len:
        return s
    cut = max_len - 1
    while cut > 50 and s[cut] not in "、。；":
        cut -= 1
    if cut <= 50:
        return s[: max_len - 1] + "…"
    return s[:cut] + "…"


def polish_core(core: str) -> str:
    """核心句を読みやすく整える。"""
    c = core.strip()
    if c.count("・") == 1 and "および" not in c:
        c = c.replace("・", "および", 1)
    return c


def build_definition(cat: str, term: str, hint: str, core_override: str | None = None) -> str:
    core = polish_core(core_override.strip()) if core_override else ""
    if not core and hint:
        core = polish_core(hint_to_core_phrase(hint))

    if not core:
        text = (
            f"「{term}」は労働衛生の学習で用いられる用語です。"
            f"細かな意味や要件は教材や法令の該当箇所で確認するとよいでしょう。"
        )
        return clamp_chars(text, 200)

    if "法令" in cat:
        text = (
            f"「{term}」とは、{core}を中心に、法令が使用者などに課す義務や届出・記録、"
            f"運用上の役割などを整理するときに使う語です。"
            f"具体的な要件や対象は、関係規則・告示で示されています。"
        )
    elif cat.startswith("労働衛生"):
        text = (
            f"「{term}」とは、{core}を手がかりに、ばく露評価・対策の優先順位・管理区分などを説明するときに使う語です。"
            f"有害環境と対策・管理の対応を語るときに位置づけられます。"
        )
    else:
        text = (
            f"「{term}」とは、{core}に関してからだのしくみや変化、疾患の成り立ちを説明するときに使う語です。"
            f"解剖・生理・病態のどこに焦点があるかで語の意味が決まります。"
        )

    text = re.sub(r"。+", "。", text.strip())
    return clamp_chars(text, 200)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="先頭5件だけ表示しファイルは書かない")
    args = ap.parse_args()

    src = ROOT / "docs/glossary-terms-checklist.csv"
    if not src.is_file():
        print(f"見つかりません: {src}", file=sys.stderr)
        sys.exit(1)

    raw = src.read_text(encoding="utf-8-sig")
    reader = csv.DictReader(raw.splitlines())
    rows: list[dict[str, str]] = []
    for row in reader:
        cat = (row.get("カテゴリ") or "").strip()
        term = (row.get("用語") or "").strip()
        raw_desc = (row.get("解説") or "").strip()
        hint = extract_seed_hint(raw_desc)
        if not hint and raw_desc and len(raw_desc) < 120 and "【試験の狙い】" not in raw_desc:
            hint = raw_desc.strip()

        recovered_core = ""
        if not hint and raw_desc:
            recovered_core = extract_core_from_flat_definition(raw_desc, cat)
            if not recovered_core:
                recovered_core = recover_core_from_nested_duplicate(raw_desc, cat)

        if not term:
            continue
        desc = build_definition(cat, term, hint, core_override=recovered_core or None)
        rows.append({"カテゴリ": cat, "用語": term, "解説": desc})

    if args.dry_run:
        for r in rows[:5]:
            print("---", r["用語"], "(", len(r["解説"]), "字) ---")
            print(r["解説"])
            print()
        return

    master = ROOT / "docs/dai1shu-glossary-terms-master.csv"
    for path in (src, master):
        with path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["カテゴリ", "用語", "解説"])
            w.writeheader()
            w.writerows(rows)

    lens = [len(r["解説"]) for r in rows]
    print(
        f"更新: {len(rows)} 件 -> glossary-terms-checklist.csv / dai1shu-glossary-terms-master.csv "
        f"(解説の文字数: 最小{min(lens)} / 最大{max(lens)} / 平均{sum(lens)//len(lens)})"
    )


if __name__ == "__main__":
    main()
