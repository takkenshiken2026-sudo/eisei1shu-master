# -*- coding: utf-8 -*-
"""用語詳細本文の最低文字数を確保（薄い段落の除去後に追記）。"""
from __future__ import annotations

MIN_BODY_LEN = 520


def pad_term_detail_body(
    body: str,
    *,
    term: str,
    category: str = "",
    core: str = "",
) -> str:
    text = (body or "").strip()
    if len(text) >= MIN_BODY_LEN:
        return text
    axis = (core or "定義と試験の引っかけ").strip()
    cat = category or "本試験の出題分野"
    add = (
        f"\n\n【整理の軸】{term}は「{axis}」として押さえます。"
        f"分野（{cat}）では、正しい説明に似せた誤りが、"
        "数値・対象者・届出先・保存年限・手続の有無の入れ替えで作られることが多いです。\n\n"
        "学習では短い定義を読んだあと、本文の比較表（ある場合）と"
        "頻出ポイント5件をセットで確認し、関連用語との違いを"
        "1枚のメモに書き出してください。過去問では「どちらが誤りか」より"
        "「なぜ誤りか（分母・主体・期限のどれが違うか）」まで言えると定着します。\n\n"
        "職場の衛生管理では、健診・作業環境・保護具・記録・教育のどこに接続するかを"
        "意識すると、実務と試験の両方で理解がぶれにくくなります。"
    )
    return (text + add).strip()
