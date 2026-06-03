#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Write affiliate course briefs + CSV rows for eisei1shu-master (A8 SMART / オンスク)."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML が必要です") from exc

ROOT = Path(__file__).resolve().parents[1]
BRIEFS = ROOT / "data" / "affiliate-briefs"
CSV_PATH = ROOT / "data" / "guide_articles.csv"

A8_SMART = (
    "https://px.a8.net/svt/ejp?a8mat=4B3TF0+DUBVNM+4LOQ+BW0YB"
    "&a8ejpredirect=https%3A%2F%2Fwww.joho-gakushu.or.jp%2Feiseikanrisya%2F"
    "%3Futm_source%3DAffi%26utm_medium%3Dlist%26utm_campaign%3D01"
)
A8_ONSUKU = (
    "https://px.a8.net/svt/ejp?a8mat=4B3TF0+DUXB9E+408S+BW0YB"
    "&a8ejpredirect=https%3A%2F%2Fonsuku.jp%2Ftraining%2Feisei2"
)

PRICE_CHECKED = "2026-06-03"


def course(
    rank: int,
    name: str,
    provider: str,
    *,
    price_yen: int = 0,
    price_label: str = "",
    billing_type: str = "lump",
    duration: str = "",
    lecture_hours: str = "",
    support: str = "",
    a8_url: str = "",
    image_file: str = "",
    for_who: str = "",
    highlights: list[str],
) -> dict:
    product: dict = {
        "rank": rank,
        "offer_type": "course",
        "name": name,
        "provider": provider,
        "billing_type": billing_type,
        "a8_url": a8_url,
        "image_file": image_file,
        "for_who": for_who,
        "highlights": highlights,
    }
    if price_label:
        product["price_label"] = price_label
    elif price_yen:
        product["price_yen"] = price_yen
    if duration:
        product["duration"] = duration
    if lecture_hours:
        product["lecture_hours"] = lecture_hours
    if support:
        product["support"] = support
    return product


BRIEFS_DATA = {
    "affiliate-online-course-compare": {
        "slug": "affiliate-online-course-compare",
        "theme_key": "online-course-compare",
        "search_intent": "第一種衛生管理者向けオンライン講座をSMARTとオンスクで比較したい",
        "title": "第一種衛生管理者のオンライン講座比較【SMART合格講座 vs オンスク】独学との併用",
        "layout": "product-comparison",
        "asp_primary": "a8",
        "comparison_kind": "courses",
        "comparison_title": "オンライン講座2選（比較）",
        "price_disclaimer": (
            f"料金・受講条件は執筆時点（{PRICE_CHECKED}）の各公式ページ参考です。"
            "申込前に必ず最新の料金・キャンペーンを確認してください。"
        ),
        "products": [
            course(
                1,
                "SMART合格講座（第一種衛生管理者）",
                "情報学習支援協会",
                price_yen=29700,
                billing_type="lump",
                duration="視聴3年間",
                lecture_hours="約12時間40分",
                support="SMART答練・進捗管理",
                a8_url=A8_SMART,
                image_file="eisei1-smart-goukaku.jpg",
                for_who="有害業務まで含めて動画で一気に理解したい人",
                highlights=[
                    "宮川隆氏による第一種向け動画（有害業務約6時間含む）",
                    "買い切り29,700円（税込）で視聴3年",
                    "SMART答練で過去問・予想問題を動画解説",
                ],
            ),
            course(
                2,
                "オンスク.JP 衛生管理者オンライン通信講座",
                "オンスク.JP",
                price_label="月額1,078〜1,628円（税込・ウケホーダイ）",
                billing_type="monthly",
                duration="月額または一括パック",
                lecture_hours="講義50回・約4.5時間",
                support="練習536問・進捗管理・復習機能",
                a8_url=A8_ONSUKU,
                image_file="eisei1-onsuku-eisei2.jpg",
                for_who="短期間・低コストで弱点補強したい社会人",
                highlights=[
                    "講義50回＋練習536問で演習量を確保",
                    "ウケホーダイ月額1,078〜1,628円（税込）",
                    "スマホ視聴・倍速・ダウンロード教材対応",
                ],
            ),
        ],
        "operator_note": f"A8 SMART・オンスク。価格確認日 {PRICE_CHECKED}。",
    },
    "affiliate-dokugaku-goukaku-hokan": {
        "slug": "affiliate-dokugaku-goukaku-hokan",
        "theme_key": "dokugaku-goukaku-hokan",
        "search_intent": "第一種衛生管理者は独学で合格できるか、講座が必要なケースを知りたい",
        "asp_primary": "a8",
        "products": [
            {
                "name": "SMART合格講座（第一種衛生管理者）",
                "provider": "情報学習支援協会",
                "a8_url": A8_SMART,
            },
            {
                "name": "オンスク.JP 衛生管理者オンライン通信講座",
                "provider": "オンスク.JP",
                "a8_url": A8_ONSUKU,
            },
        ],
        "operator_note": f"ASPリンク判定用brief（比較UIなし）。確認日 {PRICE_CHECKED}。",
    },
}


CSV_ROWS = {
    "affiliate-online-course-compare": {
        "meta_description": (
            "第一種衛生管理者向けにSMART合格講座（買い切り29,700円）と"
            "オンスク（月額1,078〜1,628円）を料金・講義量・演習で比較。"
            "独学・一衛マスター過去問との併用プランも解説。"
        ),
        "lead": (
            "第一種衛生管理者試験の独学で、法令の条文整理や有害業務の理解に時間がかかる場合、"
            "オンライン講座で動画と演習を補強する選択肢があります。"
            "本記事ではSMART合格講座（買い切り型）とオンスク.JP（月額型）を、"
            "料金・講義量・演習の観点から比較します。"
            "料金は執筆時点の公式ページ参考です。申込前に各サイトで最新条件を確認してください。"
        ),
        "user_intent": (
            "SMART合格講座とオンスクの違いを把握し、"
            "自分の学習スタイル（買い切りでじっくり／月額で短期集中）に合う講座を1つ選びたい。"
        ),
        "action_items": (
            "2講座の比較表で料金と演習量を確認する;"
            "独学の弱点分野に合う講座を選ぶ;"
            "一衛マスター過去問との週間学習例を試す"
        ),
        "revision_note": f"{PRICE_CHECKED}: 公式LPで料金再確認・本文全面リライト",
        "original_note": (
            f"A8 SMART・オンスク。SMART 29,700円・オンスク月額1,078〜1,628円（税込）。"
            f"確認日 {PRICE_CHECKED}。"
        ),
        "key_points": "2講座の比較ポイント;独学との併用;受講期間の目安",
        "sections": [
            (
                "オンライン講座選びの基準（第一種向け）",
                "第一種衛生管理者向け講座を選ぶときは、次の4点を押さえます。\n\n"
                "- 有害業務（労働衛生・関係法令）まで動画でカバーしているか\n"
                "- 演習量（一問一答・過去問解説）が足りるか\n"
                "- 料金体系（買い切りか月額か）が学習期間と合うか\n"
                "- 視聴期限・解約条件が仕事のペースに合うか\n\n"
                "講座はテキストや過去問の代わりではなく、"
                "独学でつまずいた分野を動画で補強する位置づけです。"
                "安全衛生技術試験協会（公式）の出題範囲と照合しながら選んでください。",
            ),
            (
                "2講座の比較の見方",
                "SMART合格講座は買い切り29,700円（税込）で視聴3年、"
                "動画約12時間40分＋SMART答練がセットです。"
                "オンスク.JPはウケホーダイ月額1,078〜1,628円（税込）で、"
                "講義50回・練習536問をスマホ中心に回せます。\n\n"
                "長期で何度も見返したい人はSMART、"
                "試験3〜4か月前から短期集中したい人はオンスク.JPが選ばれやすい傾向です。",
            ),
            (
                "SMART合格講座の特徴",
                "SMART合格講座（第一種衛生管理者）は、情報学習支援協会の買い切り型講座です。"
                "宮川隆氏による動画で、労働生理・労働衛生（有害業務含む）・関係法令を約12時間40分で学べます。"
                "第二種共通部分に加え、第一種で必要な有害業務の追加講義（約6時間）が含まれる点が強みです。\n\n"
                "SMART答練では過去問・予想問題を一問一答形式で解き、解説動画で復習できます。"
                "視聴期限は申込日から3年間。分割払いにも対応しています（公式ページ参照）。\n\n"
                "向いている人：動画で法令の流れを一度通したい人、"
                "有害業務の条文整理に時間をかけたい二種合格者。",
            ),
            (
                "オンスク.JP講座の特徴",
                "オンスク.JP 衛生管理者オンライン通信講座は、"
                "日本衛生管理者ネットワーク監修の月額型講座です。"
                "講義動画50回（約4.5時間）に加え、練習問題536問と進捗・復習機能が付いています。\n\n"
                "ウケホーダイプランは月額1,078〜1,628円（税込、2026-06-02時点）で、"
                "初期費用・入会金なし。3か月パック（税込4,884円〜）など一括プランもあります。"
                "スマホでの倍速視聴や講義スライドのダウンロードに対応しており、"
                "通勤時間の学習と相性がよい構成です。\n\n"
                "向いている人：試験直前数か月でコストを抑えつつ演習量を確保したい社会人。",
            ),
            (
                "一衛マスター過去問との併用プラン",
                "講座は「理解」、一衛マスターの過去問は「本試験形式の演習」に使い分けます。\n\n"
                "例（週5日・1日60分）：\n"
                "- 月〜水：講座動画1〜2本＋該当分野の一問一答\n"
                "- 木：過去問を分野別に10問（足切りライン確認）\n"
                "- 金：間違えた論点を用語解説・比較表で整理\n\n"
                "講座で学んだ条文が演習問題で活きるかを、"
                "毎週末に過去問の正答率で確認するサイクルが効果的です。",
            ),
            (
                "受講期間とコストの目安",
                "試験まで6か月ある場合、SMART合格講座（29,700円・3年視聴）は"
                "月あたり約4,950円相当。動画を何度も見返す計画ならコスパが出やすいです。\n\n"
                "試験まで3か月の短期集中なら、オンスク.JPの3か月パック（税込4,884円〜）や"
                "月額1,078円プランの方が総額を抑えやすいケースがあります。"
                "ただし演習の主戦場は過去問なので、講座料金＋テキスト・問題集の合計も見てください。",
            ),
            (
                "申込前のチェックリスト",
                "申込前に以下を各公式ページで確認してください。\n"
                "・最新の受講料（キャンペーン・分割払い条件）\n"
                "・視聴期限・解約・自動更新の有無\n"
                "・第一種の有害業務がカリキュラムに含まれるか\n"
                "・スマホ視聴・オフライン視聴の可否\n"
                "・自分の弱点分野（足切り40%ライン）と講座の章立てが合うか",
            ),
        ],
        "faqs": [
            (
                "第一種衛生管理者は独学だけで合格できますか？",
                "過去問演習と科目別の足切り対策ができれば独学でも可能です。"
                "詳しくは独学合格と講座の併用の記事も参照してください。",
            ),
            (
                "試験まで3か月ならSMARTとオンスクどちらが得ですか？",
                "短期ならオンスクの月額・3か月パックの方が総額を抑えやすいことが多いです。"
                "一方、有害業務を動画でじっくり整理したい場合はSMARTも検討余地があります。"
                "自分の弱点分野と比較表の演習量で判断してください。",
            ),
            (
                "二種合格者はどちらの講座が向いていますか？",
                "共通論点は既知でも、第一種の有害業務・関係法令の深掘りが課題になりやすいです。"
                "有害業務の動画ボリュームが多いSMARTが向く人もいれば、"
                "演習536問で速攻仕上げたい人にはオンスクが向きます。",
            ),
        ],
    },
    "affiliate-dokugaku-goukaku-hokan": {
        "meta_description": (
            "第一種衛生管理者は独学で合格できるか、必要な勉強時間の目安、"
            "通信講座を併用した方がよいケース、SMART・オンスクの選び方を解説。"
            "過去問との時間配分も整理します。"
        ),
        "lead": (
            "「第一種衛生管理者は独学で合格できる？」と検索する方へ。"
            "結論として、過去問演習と科目別の足切り対策ができれば独学でも合格は可能です。"
            "一方で、有害業務の条文整理や法令の理解に時間がかかる場合は、"
            "通信講座で動画・演習を補強する選択肢もあります。"
            "本記事では勉強時間の目安と、講座が効くケースを整理します。"
        ),
        "user_intent": (
            "独学で第一種衛生管理者に合格できる条件と勉強時間の目安を知り、"
            "必要ならSMART・オンスクのどちらを検討すべきか判断したい。"
        ),
        "action_items": (
            "独学で足りる条件を自分に当てはめる;"
            "勉強時間の目安を学習計画に反映する;"
            "弱点分野があれば講座比較記事で候補を絞る"
        ),
        "revision_note": f"{PRICE_CHECKED}: 本文全面リライト・PR表記削除",
        "original_note": (
            "検索意図: 独学 合格 できる / 勉強時間 / 通信講座。"
            f"A8 SMART・オンスク。確認日 {PRICE_CHECKED}。"
        ),
        "key_points": "独学で足りる条件;勉強時間の目安;講座が効くケース",
        "sections": [
            (
                "独学だけで合格できる条件",
                "第一種衛生管理者試験は、科目ごとに40%以上・全体60%以上の足切りがあります。"
                "独学で合格するには、次が揃っていることが重要です。\n\n"
                "- 公式テキストまたはALL-in-one教材で5分野の全体像を把握できている\n"
                "- 過去問・問題集で演習量を確保し、分野別得点を記録している\n"
                "- 足切りラインに届いていない科目を特定し、該当章に戻れる\n"
                "- 安全衛生技術試験協会（公式）の最新要項で出題範囲を確認している\n\n"
                "この4点が回せていれば、通信講座なしでも対策は可能です。",
            ),
            (
                "勉強時間の目安（初学者・社会人）",
                "初学者がゼロから独学する場合の目安は、おおむね次のとおりです。\n\n"
                "- 3か月コース：1日90〜120分（週6日）＋週末に過去問まとめ\n"
                "- 6か月コース：1日45〜60分（週5日）でテキスト→問題集→過去問\n"
                "- 二種合格者：共通分野は圧縮でき、有害業務・一種特有論点に+1〜2か月\n\n"
                "数字はあくまで目安です。"
                "一衛マスターの過去問で分野別正答率を見ながら、"
                "自分のペースに合わせて調整してください。",
            ),
            (
                "独学だけでは苦戦しやすい論点",
                "独学で時間がかかりやすいのは、次の分野です。\n\n"
                "- 有害業務に関する労働衛生・関係法令（第一種特有の深い範囲）\n"
                "- 作業環境測定・局所排気装置など数値・手順が絡む論点\n"
                "- 複数法令が絡む事例問題（主体の取り違え）\n\n"
                "テキストを読んでも理解が浅い分野は、"
                "用語解説・比較表で整理したうえで、"
                "同分野の過去問を集中的に解くのが先決です。"
                "それでも進まない場合に講座を検討する、という順序がおすすめです。",
            ),
            (
                "通信講座が効くケース",
                "次のような状況では、SMART合格講座やオンスク.JPの併用が効果的です。\n\n"
                "- 有害業務の条文を動画で一度通したい（SMART向き）\n"
                "- 演習536問で短期間にアウトプットを増やしたい（オンスク向き）\n"
                "- 仕事が忙しく、テキストだけでは学習習慣が続かない\n"
                "- 二種合格後、一種特有論点だけを効率よく仕上げたい\n\n"
                "講座は必須ではありません。"
                "詳しい料金・機能比較はオンライン講座比較の記事を参照してください。",
            ),
            (
                "SMARTとオンスクの使い分け（概要）",
                "SMART合格講座は買い切り29,700円（税込）・視聴3年で、"
                "動画約12時間40分とSMART答練がセットです。"
                "長期で何度も見返す計画に向きます。\n\n"
                "オンスク.JPは月額1,078〜1,628円（税込・ウケホーダイ）で、"
                "講義50回・練習536問をスマホ中心に学べます。"
                "試験3〜4か月前からの短期集中に向きます。\n\n"
                "どちらも申込前に公式ページで最新料金を確認してください。",
            ),
            (
                "独学×過去問の3か月学習例",
                "独学メインで3か月仕上げる例です（1日60分・週6日）。\n\n"
                "1〜4週目：テキスト1冊で5分野を通読＋一問一答\n"
                "5〜8週目：問題集1冊＋一衛マスター過去問（分野別）\n"
                "9〜12週目：過去問通し演習＋足切り分野の該当章復習\n\n"
                "8週目時点で有害業務の正答率が40%を下回る場合、"
                "残り期間でSMARTまたはオンスクのどちらか1つに絞って併用する判断も有効です。",
            ),
            (
                "独学中心で進めるときの注意",
                "講座を検討する前に、教材を増やしすぎないことが大切です。"
                "テキスト1冊＋問題集1冊＋一衛マスター過去問の3点セットを回せていないうちに"
                "講座を追加すると、どれも中途半端になりがちです。\n\n"
                "まず過去問で現在地を把握し、"
                "足切り分野と理解不足分野をメモしてから講座を選ぶと、"
                "投資対効果が見えやすくなります。",
            ),
        ],
        "faqs": [
            (
                "第一種衛生管理者は独学だけで合格できますか？",
                "はい。過去問演習量と足切り対策ができていれば独学でも可能です。"
                "演習量が足りない・有害業務の理解が進まない場合は講座を検討してください。",
            ),
            (
                "通信講座はいつから始めるとよいですか？",
                "テキストで全体像を把握した後（目安1〜2か月）が目安です。"
                "最初から講座だけに頼るより、弱点が見えてから始める方が効率的です。",
            ),
            (
                "仕事しながらでも独学で間に合いますか？",
                "1日45〜60分を6か月確保できれば可能なケースが多いです。"
                "3か月に短縮する場合は演習量の確保が鍵で、"
                "問題集と過去問の時間配分を事前に決めておくとよいです。",
            ),
        ],
    },
}


def write_briefs() -> None:
    BRIEFS.mkdir(parents=True, exist_ok=True)
    for slug, data in BRIEFS_DATA.items():
        path = BRIEFS / f"{slug}.yaml"
        path.write_text(
            yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False),
            encoding="utf-8",
        )
        print(f"wrote brief → {path}")


def patch_csv() -> None:
    from write_eisei1_affiliate_book_articles import COURSE_AFFILIATE_KEY_POINTS, COURSE_AFFILIATE_RELATED

    with CSV_PATH.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    if not fieldnames:
        raise SystemExit("CSV header missing")

    for row in rows:
        slug = row.get("slug", "")
        if slug not in CSV_ROWS:
            continue
        cfg = CSV_ROWS[slug]
        for key in ("meta_description", "lead", "user_intent", "action_items", "revision_note", "original_note", "key_points"):
            if key in cfg:
                row[key] = cfg[key]
        row["fact_checked_at"] = PRICE_CHECKED
        row["content_status"] = "published"
        for i, (heading, body) in enumerate(cfg["sections"], start=1):
            row[f"section_{i}_heading"] = heading
            body_clean = body.replace("[[affiliate-hub-placeholder]]", "").strip()
            row[f"section_{i}_body"] = body_clean
        for i in range(len(cfg["sections"]) + 1, 8):
            row[f"section_{i}_heading"] = ""
            row[f"section_{i}_body"] = ""
        for i, (q, a) in enumerate(cfg["faqs"], start=1):
            row[f"faq_{i}_question"] = q
            row[f"faq_{i}_answer"] = a
        for i in range(len(cfg["faqs"]) + 1, 4):
            row[f"faq_{i}_question"] = ""
            row[f"faq_{i}_answer"] = ""
        print(f"patched CSV row: {slug}")

    for row in rows:
        slug = row.get("slug", "")
        if slug in COURSE_AFFILIATE_RELATED:
            row["related_links"] = COURSE_AFFILIATE_RELATED[slug]
            row["fact_checked_at"] = PRICE_CHECKED
            print(f"patched course related_links: {slug}")
        if slug in COURSE_AFFILIATE_KEY_POINTS and slug not in CSV_ROWS:
            row["key_points"] = COURSE_AFFILIATE_KEY_POINTS[slug]

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    write_briefs()
    patch_csv()
    return 0


if __name__ == "__main__":
    sys.exit(main())
