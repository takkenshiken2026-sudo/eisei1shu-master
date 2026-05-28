#!/usr/bin/env python3
"""Map related_terms semicolon tokens to exact glossary term strings."""
from __future__ import annotations

from pathlib import Path

TERM_MAP = {
    "第一種衛生管理者": "衛生工学衛生管理者（有害業務での選任）",
    "第二種衛生管理者": "衛生管理者（選任・常勤・専任・資格区分）",
    "有害業務": "衛生工学衛生管理者（有害業務での選任）",
    "定期健康診断": "定期健康診断／雇入時／特殊健康診断",
    "雇入時健康診断": "雇入時健康診断（直前3月以内省略可）",
    "二次健康診断": "健康診断事後措置",
    "個人別の健康診断結果等の記録": "健康診断個人票の保存（5年）",
    "作業環境測定記録": "作業環境測定（義務・頻度・評価・記録）",
    "作業環境管理区分（第1〜第3管理区分）": "作業環境評価基準・管理区分（第1～第3）",
    "A測定・B測定・C測定": "A測定・B測定・C測定の意味と使い分け",
    "全面換気・希釈換気": "プッシュプル型換気",
    "ストレスチェック制度": "ストレスチェック（年1回以上・50人以上）",
    "面接指導": "産業医面接指導と就業上の措置",
    "長時間労働者面接指導": "産業医面接指導と就業上の措置",
    "化学物質": "化学物質管理者（選任・職務）",
    "化学物質等による危険性等の調査等": "リスクアセスメント（化学・作業環境）",
    "安全衛生委員会": "衛生委員会／安全衛生委員会",
    "第一種衛生管理者試験 総まとめ：数値・頻度・保存期間一覧": "記録の作成・保存（測定・健康診断・教育等）",
    "第二種衛生管理者試験 総まとめ：数値・頻度・保存期間一覧": "記録の作成・保存（測定・健康診断・教育等）",
    "専任の衛生管理者": "専任の衛生管理者（有害業務30人超）",
    "特定化学物質": "特定化学物質障害予防規則（区分・技術的措置）",
    "鉛": "特殊健康診断（鉛）",
    "四アルキル鉛": "特殊健康診断（四アルキル鉛）",
    "石綿": "石綿（健康影響）",
    "有機溶剤": "有機溶剤中毒予防規則（区分・局所排気・評価）",
    "母性健康管理": "女性労働者・妊産婦・産後パートナーシップ（関連規定）",
    "一般の健康管理": "健康保持増進措置",
    "深夜業": "夜勤・交代勤務の健康影響",
    "熱中症": "WBGT・熱中症・暑熱順化",
    "A特性騒音レベル": "耳せつ・耳あての減衰値と保守",
    "産業医": "産業医（選任・職務・記録・巡視・面接指導）",
    "安全管理者": "統括安全衛生責任者・元方安全衛生管理者",
    "安全管理者（選任・職務）": "統括安全衛生責任者・元方安全衛生管理者",
    "衛生管理者の職務・専任・巡視": "衛生管理者（選任・常勤・専任・資格区分）",
    "衛生管理者の職務（総括・作業環境・健康保持増進）": "衛生管理者（選任・常勤・専任・資格区分）",
    "局所排気装置": "局所排気装置",
    "局所排気装置（密閉・囲い込み・吸引）": "局所排気装置",
    "労働安全衛生法": "労働安全衛生法",
    "作業主任者": "労働安全衛生法",
    "A測定": "A測定・B測定の概念",
    "B測定": "A測定・B測定の概念",
    "C測定": "A測定・B測定の概念",
    "振動障害": "振動障害（手指末梢振動）",
    "ろ過式防毒マスク": "防毒マスク（吸収缶・使用限界）",
    "エアラインマスク": "呼吸用保護具（区分・選定・フィットテスト）",
    "送気マスク・エアライン": "呼吸用保護具（区分・選定・フィットテスト）",
    "安全衛生教育": "安全衛生教育",
    "安全衛生教育（雇入れ時・職種変更時等）": "雇入れ時の安全衛生教育（安衛則35条）",
    "危険物": "危険物（指定数量・貯蔵）",
    "リスクアセスメント": "リスクアセスメント（化学・作業環境）",
    "作業環境測定": "作業環境測定（義務・頻度・評価・記録）",
    "衛生委員会": "衛生委員会",
}


def _map_related_line(line: str) -> str:
    if not line.startswith('        "') or not line.rstrip().endswith('",'):
        return line
    inner = line.strip()[1:-2]
    if ";" not in inner and inner not in TERM_MAP:
        return line
    parts = [p.strip() for p in inner.split(";")]
    out = [TERM_MAP.get(p, p) for p in parts]
    return '        "' + ";".join(out) + '",\n'


def fix_file(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    new_lines: list[str] = []
    for i, line in enumerate(lines):
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        if nxt.lstrip().startswith("[") or nxt.lstrip().startswith("("):
            line = _map_related_line(line)
        new_lines.append(line)
    path.write_text("".join(new_lines), encoding="utf-8")
    print("fixed", path.name)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    for name in (
        "write_eisei1shu_hub_s30_content.py",
        "write_eisei1shu_hub_s31_content.py",
        "write_eisei1shu_hub_s32_content.py",
        "write_eisei1shu_hub_s33_content.py",
        "write_eisei1shu_hub_s34_content.py",
        "write_eisei1shu_hub_s35_content.py",
        "write_eisei1shu_hub_s36_content.py",
        "write_eisei1shu_hub_s37_content.py",
        "write_eisei1shu_hub_s38_content.py",
        "write_eisei1shu_hub_s39_content.py",
        "write_eisei1shu_hub_s44_content.py",
        "write_eisei1shu_hub_s43_content.py",
        "write_eisei1shu_hub_s42_content.py",
        "write_eisei1shu_hub_s41_content.py",
        "write_eisei1shu_hub_s40_content.py",
        "write_eisei1shu_hub_premium_faqs.py",
    ):
        fix_file(root / "tools" / name)


if __name__ == "__main__":
    main()
