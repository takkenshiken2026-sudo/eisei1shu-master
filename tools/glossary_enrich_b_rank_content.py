# -*- coding: utf-8 -*-
"""重要度B用語（追加50件の29語）のリライト本文。"""
from __future__ import annotations

import json
from pathlib import Path

from glossary_enrich_a_rank_content import _ep, _tbl
from glossary_enrich_b_rank_bodies import BODY_APPEND, EXTRA_BODIES
from glossary_body_pad import pad_term_detail_body

_ROOT = Path(__file__).resolve().parent.parent
_BATCH = json.loads(
    (_ROOT / "data" / "glossary_add50_batch.json").read_text(encoding="utf-8")
)

_SKIP_PREFIX = (
    "第一種衛生管理者試験では、",
    "学習の進め方としては、",
)


def _strip_boilerplate(text: str) -> str:
    parts = []
    for para in (text or "").split("\n\n"):
        p = para.strip()
        if not p or any(p.startswith(s) for s in _SKIP_PREFIX):
            continue
        parts.append(p)
    return "\n\n".join(parts)


def _lead(item: dict) -> str:
    core = (item.get("core") or "").strip()
    if core:
        return core + "。試験では定義のほか、関連制度・数値・手続の違いがセットで問われます。"
    return (item.get("definition") or "")[:120]


# slug -> 追記・上書き（exam_points は5件に置換、related_terms は登録名）
_PATCHES: dict[str, dict] = {
    "yudoritsu": {
        "term_detail_body": (
            "尤度比（LR+）＝感度÷（1−特異度）。陽性のとき病気がある確率が何倍になるかを示し、"
            "有病率に依存しない検査性能の指標として使われます。\n\n"
            + _tbl(
                ["指標", "式・意味"],
                [
                    ["尤度比", "感度÷（1−特異度）"],
                    ["陽性予測値", "有病率にも依存"],
                    ["感度・特異度", "カットオフでトレードオフ"],
                ],
            )
        ),
        "exam_points": _ep(
            "「尤度比＝特異度÷感度」→ 誤り。分子は感度",
            "「尤度比は有病率に依存しない」→ 検査性能としては依存しないが陽性予測値は依存",
            "「尤度比1未満でも陽性は病気を強く支持」→ 1超が支持",
            "「感度だけ上げれば尤度比は必ず上がる」→ 特異度低下で分母が変わる",
            "「尤度比＝陽性予測値」→ 別概念",
        ),
        "related_terms": "感度（検査）; 特異度（検査）; ROC曲線",
    },
    "roc-curve": {
        "term_detail_body": (
            "ROC曲線はカットオフ変更時の感度（縦）と1−特異度＝偽陽性率（横）の軌跡です。"
            "AUCが大きいほど性能が高く、左上に近いほど良いとされます。\n\n"
            + _tbl(
                ["軸", "内容", "よくある誤り"],
                [
                    ["縦軸", "感度", "陽性率と混同"],
                    ["横軸", "1−特異度（偽陽性率）", "特異度そのものと混同"],
                    ["評価", "AUC・左上への近さ", "右下が良いと誤る"],
                ],
            )
        ),
        "exam_points": _ep(
            "「ROCの横軸は特異度」→ 誤り。1−特異度",
            "「カットオフを変えてもROCは変わらない」→ 誤り",
            "「感度と横軸は同じ」→ 横軸は偽陽性率",
            "「AUCが小さいほど性能が高い」→ 誤り",
            "「ROCは有病率で形が決まる」→ カットオフと検査性能の関係",
        ),
        "related_terms": "感度（検査）; 特異度（検査）; 尤度比",
    },
    "kesshoku-baisyo": {
        "term_detail_body": (
            "血液の三成分は役割が明確に分かれ、健診所見の読み取りの基礎になります。\n\n"
            + _tbl(
                ["成分", "主機能", "異常時の例"],
                [
                    ["赤血球", "酸素運搬", "貧血"],
                    ["白血球", "免疫", "感染・炎症"],
                    ["血小板", "止血", "出血傾向"],
                ],
            )
        ),
        "exam_points": _ep(
            "「血小板は酸素運搬」→ 誤り",
            "「白血球減少は必ず感染」→ 原因は多様",
            "「赤血球増加＝必ず良好」→ 多血症のことも",
            "「三成分は独立せず影響し合う」→ 正しい",
            "「血液検査はスクリーニングに使える」→ 正しい",
        ),
        "related_terms": "血液; ヘモグロビン; 貧血（鉄欠乏性）",
    },
    "shindenzu-kihon": {
        "exam_points": _ep(
            "「心電図は心音を記録」→ 誤り",
            "「正常心電図で心筋梗塞は除外」→ 発症直後は正常のことも",
            "「P波は心室の脱分極」→ 心房",
            "「ST上昇は必ず梗塞」→ 原因は多い",
            "「心電図は虚血のスクリーニングに使う」→ 正しい",
        ),
        "related_terms": "心臓; 心筋梗塞; 狭心症",
    },
    "kouketsuatsu": {
        "exam_points": _ep(
            "「高血圧＝必ず症状がある」→ 無症状が多い",
            "「1回の測定で診断」→ 複回測定が原則",
            "「高血圧は脳卒中リスクと無関係」→ 誤り",
            "「職場健診では生活習慣指導が重要」→ 正しい",
            "「拡張期だけが問題」→ 収縮期・拡張期とも評価",
        ),
        "related_terms": "虚血性心疾患; 脳卒中; 高血圧",
    },
    "kidou-kanki": {
        "exam_points": _ep(
            "「換気＝空気清浄のみ」→ 排出・導入の両方",
            "「気道障害は必ず感染」→ 化学性・物理性も",
            "「局所排気は全体換気と同義」→ 誤り",
            "「粉じん対策に換気は無関係」→ 関係あり",
            "「気道は鼻腔から細気管支まで」→ 正しい",
        ),
        "related_terms": "肺; 換気; 肺胞とガス交換",
    },
    "kiso-taisha": {
        "exam_points": _ep(
            "「基礎代謝＝運動時の消費」→ 安静時",
            "「年齢と無関係」→ 一般に加齢で低下",
            "「基礎代謝＝エネルギー代謝率」→ 別概念",
            "「体温維持にエネルギーを使う」→ 正しい",
            "「基礎代謝は作業強度評価の基準」→ 正しい",
        ),
        "related_terms": "エネルギー代謝率; 体温; ATP",
    },
    "energy-metabolism-rate": {
        "exam_points": _ep(
            "「代謝率が高いほど軽作業」→ 誤り。高いほど重い",
            "「基礎代謝と同義」→ 倍率で表す作業代謝",
            "「暑熱作業では代謝率が下がる」→ 一般に上昇",
            "「休憩設計と無関係」→ 関連あり",
            "「RMRは作業の重さの目安」→ 正しい",
        ),
        "related_terms": "基礎代謝; WBGT・熱中症・暑熱順化",
    },
    "atp": {
        "exam_points": _ep(
            "「ATPはタンパク質」→ ヌクレオチド系",
            "「ATPは貯蔵のみ」→ 合成と分解が連続",
            "「筋収縮にATP不要」→ 誤り",
            "「嫌気性のみでATP生成」→ 好気性も",
            "「ATP＝細胞のエネルギー通貨」→ 正しい",
        ),
        "related_terms": "基礎代謝; 筋収縮の仕組み",
    },
    "insulin-ketto": {
        "exam_points": _ep(
            "「インスリンは血糖を上げる」→ 下げる",
            "「低血糖は必ず糖尿病以外」→ 複数原因",
            "「健診の血糖・HbA1cと無関係」→ 関連",
            "「グルココルチコイドは血糖を下げる」→ 上げる方向",
            "「メタボは職場保健の論点」→ 正しい",
        ),
        "related_terms": "肝臓の機能; 代謝",
    },
    "kanzo-kinou": {
        "exam_points": _ep(
            "「肝臓は尿素合成のみ」→ 多機能",
            "「ALT上昇は必ず肝硬変」→ 原因多様",
            "「有機溶剤は肝に無関係」→ 肝機能検査が重要",
            "「解毒・胆汁分泌も肝の機能」→ 正しい",
            "「γ-GTPはアルコール負荷の目安」→ 正しい",
        ),
        "related_terms": "有機溶剤中毒予防規則（区分・局所排気・評価）; ベンゼン（毒性・規制）",
    },
    "jin-shikyugyo": {
        "exam_points": _ep(
            "「尿は糸球体のみで形成」→ 細管過程も必須",
            "「腎障害は必ず尿量増加」→ 乏尿のことも",
            "「重金属は腎排泄と関連」→ 正しい",
            "「電解質調節は腎の役割」→ 正しい",
            "「尿検査は健診で用いる」→ 正しい",
        ),
        "related_terms": "電解質と浸透圧; 肝臓の機能",
    },
    "denkaibun-shintou": {
        "exam_points": _ep(
            "「浸透圧＝温度」→ 溶質濃度",
            "「脱水は必ず高Na血症」→ 低張・等張・高張あり",
            "「暑熱では水分・電解質補給」→ 正しい",
            "「Na⁺・K⁺の濃度差が重要」→ 正しい",
            "「下痢嘔吐で電解質異常」→ 正しい",
        ),
        "related_terms": "腎・糸球体・尿形成; 熱中症の応急手当",
    },
    "shinkei-chuou-shinkei": {
        "exam_points": _ep(
            "「末梢神経は脳のみ」→ 誤り",
            "「神経伝導はすべて電気のみ」→ シナプスは化学",
            "「有機溶剤は神経障害を起こす」→ 正しい",
            "「中枢＝統合、末梢＝伝達」→ 正しい",
            "「VDT・精神負荷も神経系と関連」→ 正しい",
        ),
        "related_terms": "心理的要因（ストレス反応・メンタルヘルス）; トルエン（有機溶剤）",
    },
    "kin-shushuku": {
        "exam_points": _ep(
            "「収縮にATP不要」→ 誤り",
            "「ミオシンのみで収縮」→ アクチン・ミオシン",
            "「神経筋接合部は無関係」→ 興奮伝達",
            "「重作業・振動と筋疲労が関連」→ 正しい",
            "「滑りモデル＋ATP水解」→ 正しい",
        ),
        "related_terms": "ATP; 振動障害（手指）",
    },
    "shikaku-kussetsu": {
        "exam_points": _ep(
            "「屈折は耳の機能」→ 眼",
            "「老眼は近視」→ 調節力低下",
            "「VDT・照明と眼精疲労が関連」→ 正しい",
            "「近視・遠視・乱視は屈折異常」→ 正しい",
            "「有害光線は網膜・角膜に損傷」→ 正しい",
        ),
        "related_terms": "VDT作業（情報機器）; レーザー有害光線",
    },
    "dai1shu-atsuryoku-youki": {
        "exam_points": _ep(
            "「ボイラーと同一」→ 区分が異なる",
            "「検査不要」→ 定期自主検査あり",
            "「0.2MPa超等が要件の一つ」→ 正しい",
            "「設置・移転・廃止の届出」→ 正しい",
            "「機械等の安全衛生管理対象」→ 正しい",
        ),
        "related_terms": "ボイラー; 定期自主検査",
    },
    "yoka-souchi": {
        "exam_points": _ep(
            "「揚貨装置は作業環境測定対象」→ 機械安全",
            "「主任者不要」→ 荷重・区分で必要",
            "「つり上げ荷重で区分」→ 正しい",
            "「技能講習・特別教育の対象」→ 正しい",
            "「定期自主検査の対象」→ 正しい",
        ),
        "related_terms": "クレーン等運転業務（特別教育・技能講習）; 定期自主検査",
    },
    "denki-fan-kokyu-hogo": {
        "exam_points": _ep(
            "「規格適合は任意」→ 原則適合品",
            "「すべての粉じんに送気マスク」→ 区分・濃度で選定",
            "「ファンで呼吸負荷を下げる」→ 正しい",
            "「防毒マスク・送気マスクと区分が異なる」→ 正しい",
            "「譲渡制限がある保護具もある」→ 正しい",
        ),
        "related_terms": "呼吸用保護具（区分・選定・フィットテスト）; 対策の優先順位（労働衛生）",
    },
    "keikaku-todokede-28": {
        "exam_points": _ep(
            "「事後届でよい」→ 原則28日前（対象により30日・14日も）",
            "「全機械が対象」→ 法令で限定",
            "「届出先は厚生労働大臣」→ 所轄労基署長",
            "「OSHMS認定で一部免除」→ 正しい",
            "「ボイラー・圧力容器が例」→ 正しい",
        ),
        "related_terms": "OSHMS認定; 計画の届出（28日前・労基署）",
    },
    "oshms-nintei": {
        "exam_points": _ep(
            "「認定で全義務免除」→ 一部優遇",
            "「OSHMS＝ISO9001」→ 目的が異なる",
            "「計画届出の免除等」→ 正しい",
            "「リスクアセスメント・PDCA」→ 正しい",
            "「自主管理の枠組み」→ 正しい",
        ),
        "related_terms": "計画届の免除認定（OSHMS等）; リスクアセスメント（5ステップ）",
    },
    "kantokushocho": {
        "exam_points": _ep(
            "「監督署長＝厚生労働大臣」→ 労基署長",
            "「都道府県知事へ計画届」→ 原則労基署",
            "「36協定の認可権限」→ 関連",
            "「立入検査の権限」→ 正しい",
            "「届出・協定の受理先として頻出」→ 正しい",
        ),
        "related_terms": "36協定（時間外労働の上限）; 労使協定",
    },
    "pawahara-boshi": {
        "exam_points": _ep(
            "「パワハラは刑法のみ」→ 労働施策法で事業主義務",
            "「防止措置は任意」→ 義務",
            "「方針明示・相談体制が要点」→ 正しい",
            "「セクハラ・マタハラは均等法」→ 法令が異なる",
            "「迅速な事実確認」→ 正しい",
        ),
        "related_terms": "セクハラ・マタハラ防止措置（均等法）; メンタルヘルス",
    },
    "jiniki-shojo": {
        "term_detail_body": (
            "じん息は喉頭・気管支の痙攣による急性呼吸困難で、"
            "塩素・光気・ニトロジェンオキシド等の刺激性ガスで起こります。\n\n"
            + _tbl(
                ["用語", "病態", "時間経過"],
                [
                    ["じん息", "急性痙攣", "急性"],
                    ["じん肺", "粉じん線維化", "慢性"],
                    ["化学事故", "避難・換気・洗眼が先", "応急手当"],
                ],
            )
        ),
        "exam_points": _ep(
            "「じん息＝じん肺」→ 全く別",
            "「水で洗眼のみで十分」→ 避難・換気が先",
            "「刺激性ガス吸入で起こる」→ 正しい",
            "「じん肺は慢性線維化」→ 対比で覚える",
            "「化学物質漏えいと関連」→ 正しい",
        ),
        "related_terms": "じん肺; 化学物質の漏えい応急",
    },
    "toluene-yuki-yozai": {
        "term_detail_body": (
            "トルエンは中枢神経抑制作用が中心で、高濃度ばく露で酩酊様症状・肝障害等が問題になります。"
            "ベンゼン（造血・発がん）とは毒性プロファイルが異なります。\n\n"
            + _tbl(
                ["溶剤", "主な毒性", "試験のポイント"],
                [
                    ["トルエン", "神経系", "ベンゼンと区別"],
                    ["ベンゼン", "造血・発がん", "管理が厳しい"],
                ],
            )
        ),
        "exam_points": _ep(
            "「トルエンは発がん性が主」→ 神経系が中心",
            "「すべて有機溶剤が同濃度」→ 物質ごと",
            "「局所排気・測定・健診がセット」→ 正しい",
            "「ベンゼンと同一管理」→ 誤り",
            "「有機溶剤中毒予防規則の対象」→ 正しい",
        ),
        "related_terms": "ベンゼン（毒性・規制）; 有機溶剤中毒予防規則（区分・局所排気・評価）",
    },
    "laser-yugai-kosen": {
        "exam_points": _ep(
            "「可視光のみ危険」→ 不可視も有害",
            "「サングラスで十分」→ 専用保護具",
            "「クラス区分で管理」→ 正しい",
            "「網膜・角膜に局所損傷」→ 正しい",
            "「管理区域・保護眼鏡」→ 正しい",
        ),
        "related_terms": "紫外線・赤外線（職場）; 視覚と屈折",
    },
    "shigaisen-shokuba": {
        "exam_points": _ep(
            "「赤外線は目に無害」→ 白内障等あり",
            "「紫外線は冬は無害」→ 反射・積雪でも",
            "「溶接・アークで問題」→ 正しい",
            "「遮光保護具が対策」→ 正しい",
            "「紫外＝皮膚炎・水晶体」→ 正しい",
        ),
        "related_terms": "レーザー有害光線; 白内障（紫外・赤外・電離放射線）",
    },
    "ritsui-sagyo-kashi": {
        "exam_points": _ep(
            "「立位＝必ず下肢静脈瘤」→ リスク上昇",
            "「座位不要」→ 休憩・ローテーション有効",
            "「マット・ローテーションが対策」→ 正しい",
            "「人間工学の論点」→ 正しい",
            "「介護・重量物作業と関連」→ 正しい",
        ),
        "related_terms": "人間工学; 作業姿勢と疲労",
    },
    "hinkeketsu-tetsu": {
        "exam_points": _ep(
            "「貧血＝必ず白血病」→ 原因は多様",
            "「男性では貧血なし」→ 誤り",
            "「Hb低下＝酸素運搬↓」→ 正しい",
            "「鉛・慢性出血と関連」→ 正しい",
            "「健診所見として頻出」→ 正しい",
        ),
        "related_terms": "血液; 赤血球・白血球・血小板",
    },
}


def _build() -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for item in _BATCH:
        if item.get("importance") != "B":
            continue
        slug = item["slug"]
        patch = _PATCHES.get(slug, {})
        body = (
            patch.get("term_detail_body")
            or EXTRA_BODIES.get(slug)
            or _strip_boilerplate(item.get("detail") or "")
        )
        if slug in BODY_APPEND and BODY_APPEND[slug].strip() not in body:
            body = (body.rstrip() + BODY_APPEND[slug]).strip()
        body = pad_term_detail_body(
            body,
            term=item["term"],
            category=item.get("category") or "",
            core=item.get("core") or "",
        )
        mistakes = patch.get("common_mistakes") or (item.get("mistakes") or "").strip()
        if mistakes.startswith("「") and mistakes.endswith("」は、定義だけでなく"):
            mistakes = (
                f"「{item['term']}」は定義だけでなく、数値・対象・手続・関連制度との違いが"
                "セットで出題されます。関連用語と対比表で復習してください。"
            )
        related = patch.get("related_terms") or "; ".join(item.get("related") or [])
        exam = patch.get("exam_points") or _ep(*(item.get("exam_points") or []))
        entry: dict[str, str] = {
            "definition": item["definition"],
            "article_lead": patch.get("article_lead") or _lead(item),
            "term_detail_body": body,
            "exam_points": exam,
            "common_mistakes": mistakes,
            "memory_tip": item.get("memory") or "",
            "related_terms": related,
        }
        legal = "; ".join(item.get("legal_basis") or [])
        if legal:
            entry["legal_basis"] = legal
        out[slug] = entry
    return out


ENRICHMENTS: dict[str, dict[str, str]] = _build()
