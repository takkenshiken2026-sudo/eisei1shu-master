#!/usr/bin/env python3
from pathlib import Path

SRC = Path("/Users/otedaiki/Projects/eisei2shu-master/tools/write_eisei2shu_hub_premium_faqs.py")
DST = Path(__file__).resolve().parent / "write_eisei1shu_hub_premium_faqs.py"

text = SRC.read_text(encoding="utf-8")
text = text.replace("write_eisei2shu_hub_s30", "write_eisei1shu_hub_s30")
text = text.replace("第二種衛生管理者", "第一種衛生管理者")
text = text.replace("第二種の", "第一種の")
text = text.replace("第二種は", "第一種は")
text = text.replace("第二種に", "第一種に")
text = text.replace("第二種で", "第一種で")
text = text.replace("第二種筆記", "第一種筆記")
text = text.replace("第二種受験", "第一種受験")
text = text.replace("第二種範囲", "第一種範囲")
text = text.replace("第二種試験", "第一種試験")
text = text.replace("第二種でも", "第一種でも")
text = text.replace("第二種寄り", "第一種寄り")
text = text.replace("第二種か第一種", "第一種か第二種")
text = text.replace("shiken-30mon-300ten", "shiken-44mon-400ten")
text = text.replace("yugai-hani-kongou", "yugai-gaihan-kongou")
text = text.replace("30問", "44問")
text = text.replace("300点", "400点")
text = text.replace("180点", "240点")
text = text.replace("各10問", "5範囲")
text = text.replace("3科目", "5範囲")
text = text.replace("有害業務を除く", "有害業務を含む5範囲")
text = text.replace("有害業務を除き", "有害業務を含む5範囲")
text = text.replace("有害業務以外", "有害業務を含む5範囲")
text = text.replace("有害以外", "有害業務含む")
text = text.replace("非有害業務", "有害業務を行う事業場")
text = text.replace(
    "原則として有害業務を行う事業場に第二種衛生管理者を選任します。",
    "原則として有害業務を行う事業場等で第一種衛生管理者を選任します。",
)
text = text.replace(
    "特定化学物質・鉛・四アルキル鉛等の有害業務を行う事業場では、第一種衛生管理者の選任が必要となる場合があります。",
    "非有害業務のみの事業場では第二種衛生管理者の選任が典型です。選任要件は労働安全衛生法・施行令で確認してください。",
)
# restore 二種 comparison sentences
text = text.replace(
    "第一種は44問（各10問）・400点満点・総合240点以上かつ各科目40点以上が合格の目安です。"
    "第一種は44問・400点・240点等で異なります。",
    "第一種は44問（5範囲）・400点満点・総合240点以上かつ各科目40点以上が合格の目安です。"
    "第二種は30問・300点・180点等で異なります。",
)
text = text.replace(
    "筆記試験の出題は労働衛生（有害業務含む）・関係法令（有害業務含む）・労働生理の3科目です。"
    "有害業務は第一種との比較理解のために学習しますが、第一種で深掘りする必要はありません。",
    "筆記試験の出題は労働衛生・関係法令・労働生理等の5範囲（有害業務含む）です。"
    "第二種との比較（30問・有害以外）も整理しますが、第一種では有害業務・特定化学物質等を本番範囲で学習してください。",
)
text = text.replace(
    "第一種受験者向けの整理は？",
    "第一種受験者向けの整理は？",
)
text = text.replace(
    "非有害業務場での第二種選任が典型です。第一種との比較表に「専任・巡視」を追記し、",
    "有害業務を含む事業場での第一種選任が典型です。第二種との比較表に「専任・巡視」を追記し、",
)
text = text.replace(
    "第一種で覚える数値は？",
    "第一種で覚える数値は？",
)
text = text.replace(
    "44問・400点・240点（総合）・各科目40点・有害業務以外の出題です。44問・240点は第一種の数値です。",
    "44問・400点・240点（総合）・各科目40点・有害業務含む5範囲の出題です。30問・180点は第二種の数値です。",
)
text = text.replace(
    "「第一種に特定化学物質が本問で出る」",
    "「第一種に特定化学物質は出ない」",
)
text = text.replace(
    "第一種に有害業務は出る？",
    "第一種に有害業務は出る？",
)
text = text.replace(
    "筆記試験の出題範囲から有害業務は除かれます。第一種との比較・選任理解のために学習します。",
    "筆記試験では有害業務を含む5範囲が出題されます。第二種（30問・有害以外）との境界を比較で整理してください。",
)
text = text.replace(
    "第一種受験者が特定化学物質だけを深掘りするのは効率が悪いです。",
    "第一種受験者は特定化学物質・鉛・石綿・有機溶剤等を要項の範囲表に沿って学習してください。",
)
text = text.replace("44問・400点は第一種です。第一種は44問・300点です。", "44問・400点は第一種です。30問・300点は第二種です。")
text = text.replace(
    "総合240点以上かつ各科目40点以上（400点満点）です。240点は第一種のイメージです。",
    "総合240点以上かつ各科目40点以上（400点満点）です。180点は第二種のイメージです。",
)
text = text.replace(
    "満点が300点か400点かで合格点が変わります。",
    "満点が300点（二種）か400点（一種）かで合格点が変わります。",
)
text = text.replace(
    "第一種の基本手順・義務主体の正誤を中心に、有害業務の詳細は第一種比較の枠に留めてください。",
    "有害業務・特定化学物質の手順・義務主体を中心に、第二種との境界は比較表で整理してください。",
)

DST.write_text(text, encoding="utf-8")
print(f"wrote {DST}")
