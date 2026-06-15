#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Write affiliate mock-exam + beginner-set briefs + CSV rows for eisei1shu-master."""

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
TAG = "ue083093-22"
OFFICIAL = "安全衛生技術試験協会（公式）"


def amazon(asin: str) -> str:
    return f"https://www.amazon.co.jp/dp/{asin}/ref=nosim?tag={TAG}"


def img(asin: str) -> str:
    return f"eisei1-book-{asin.lower()}.webp"


def book(
    rank: int,
    name: str,
    publisher: str,
    asin: str,
    *,
    edition: str = "2026年度版",
    price_yen: int = 0,
    pages: int = 0,
    for_who: str = "",
    highlights: list[str],
) -> dict:
    return {
        "rank": rank,
        "offer_type": "book",
        "name": name,
        "publisher": publisher,
        "edition": edition,
        "price_yen": price_yen,
        "price_note": "Amazon税込参考・送料別",
        "pages": pages,
        "format": "B5判",
        "asin": asin,
        "image_file": img(asin),
        "amazon_url": amazon(asin),
        "for_who": for_who,
        "highlights": highlights,
    }


BRIEFS_DATA = {
    "affiliate-mock-exam-materials": {
        "slug": "affiliate-mock-exam-materials",
        "theme_key": "mock-exam-materials",
        "search_intent": "第一種衛生管理者試験の模試・予想問題を比較して選びたい",
        "title": "第一種衛生管理者試験の模試・予想問題3選【100問本番形式2026】",
        "layout": "product-comparison",
        "asp_primary": "amazon",
        "comparison_kind": "books",
        "comparison_title": "模試・予想問題3選（比較）",
        "price_disclaimer": (
            "価格は執筆時点（2026-06-15）のAmazon税込参考です。"
            "試験形式は要項で必ず確認してください。"
        ),
        "products": [
            book(
                1,
                "2026年版 ユーキャンの第1種衛生管理者 重要過去問&予想模試",
                "ユーキャン / 自由国民社",
                "4426616565",
                price_yen=1760,
                pages=320,
                for_who="予想模試付きで直前の総仕上げをしたい人",
                highlights=[
                    "重要過去問と予想模試を1冊で100問本番形式に慣れやすい",
                    "直前期の模試回数を確保しやすい",
                    "ユーキャン系列で速習教材との併用がしやすい",
                ],
            ),
            book(
                2,
                "詳解 第1種衛生管理者過去6回問題集 '26年版",
                "成美堂出版",
                "4415240909",
                edition="'26年版",
                price_yen=1540,
                pages=288,
                for_who="直近の本試験形式で模試を回したい人",
                highlights=[
                    "過去6回分を解説付きで収録",
                    "13:30開始·180分の本番形式演習に向く",
                    "成美堂集中レッスンからのステップアップがしやすい",
                ],
            ),
            book(
                3,
                "第一種衛生管理者試験問題集 2026年度版",
                "全国労働基準関係団体連合会",
                "4867881007",
                price_yen=2420,
                pages=256,
                for_who="試験実施団体系の形式で模試を受けたい人",
                highlights=[
                    "労基団連発行で本試験形式に近い演習ができる",
                    "5科目足切りの模試分析に向く",
                    "他社問題集との使い分けで弱点補強しやすい",
                ],
            ),
        ],
        "related_links": [
            "mock-exam-how-to:模試の活用法",
            "timed-practice:時間を計った演習",
            "kakomon-kakaikata:過去問の回し方",
            "affiliate-problem-books:おすすめ問題集",
            "affiliate-textbooks-recommend:おすすめテキスト",
            "goukaku-kijun:合格基準",
        ],
        "operator_note": f"Amazon tag={TAG}。4426616565 / 4415240909 / 4867881007。2026-06-15 価格確認。",
    },
    "affiliate-beginner-material-set": {
        "slug": "affiliate-beginner-material-set",
        "theme_key": "beginner-material-set",
        "search_intent": "第一種衛生管理者を初学者が独学で始める教材セットを知りたい",
        "title": "第一種衛生管理者の初学者向け教材セット3選【速習・要点整理2026】",
        "layout": "product-comparison",
        "asp_primary": "amazon",
        "comparison_kind": "books",
        "comparison_title": "初学者向け教材3選（比較）",
        "price_disclaimer": (
            "価格は執筆時点（2026-06-15）のAmazon税込参考です。"
            "購入前に必ず販売ページでご確認ください。"
        ),
        "products": [
            book(
                1,
                "2026年版 ユーキャンの第1種・第2種衛生管理者 速習レッスン",
                "ユーキャン / 自由国民社",
                "4426616557",
                price_yen=2420,
                pages=240,
                for_who="短期で五科目の輪郭を先に掴みたい初学者",
                highlights=[
                    "コンパクトな速習構成で全体像を短期把握",
                    "一種·二種共通部分の整理にも使える",
                    "本格的なテキスト購入前の予習に向く",
                ],
            ),
            book(
                2,
                "第1種衛生管理者 集中レッスン '26年版",
                "成美堂出版",
                "4415241050",
                edition="'26年版",
                price_yen=1540,
                pages=224,
                for_who="要点整理から演習に移りたい人",
                highlights=[
                    "レッスン形式で論点を短時間復習",
                    "成美堂の問題集·攻略本へのステップアップがしやすい",
                    "仕事終わりの30分学習と相性がよい",
                ],
            ),
            book(
                3,
                "これだけ覚える 第1種・第2種衛生管理者 '26年版",
                "成美堂出版",
                "4415241204",
                edition="'26年版",
                price_yen=1100,
                pages=192,
                for_who="一問一答·暗記帳として持ち歩きたい人",
                highlights=[
                    "覚えるべき論点をコンパクトに整理",
                    "通勤時間の暗記·確認に向く",
                    "本試験直前の最終確認にも使える",
                ],
            ),
        ],
        "related_links": [
            "benkyou-junban:勉強の順番",
            "study-plan-beginner:初学者向け学習計画",
            "ichimon-ittou-guide:一問一答の使い方",
            "affiliate-textbooks-recommend:おすすめテキスト",
            "affiliate-problem-books:おすすめ問題集",
            "affiliate-online-course-compare:オンライン講座比較",
        ],
        "operator_note": (
            f"Amazon tag={TAG}。速習系はテキスト本体の代替にならない点を本文で明記。"
            " 2026-06-15 価格確認。"
        ),
    },
}


CSV_ROWS = {
    "affiliate-mock-exam-materials": {
        "title": "第一種衛生管理者試験の模試・予想問題3選【100問本番形式2026】",
        "meta_description": (
            "第一種衛生管理者試験の模試·予想問題3選。"
            "ユーキャン予想模試·成美堂過去6回·労基団連問題集を比較。"
            "100問·180分本番形式の模試回数と使い分けを解説。"
        ),
        "lead": (
            "第一種衛生管理者試験は100問·180分（13:30〜16:30）·5科目×各20問で、"
            "総合60％かつ各科目40％以上（足切り）が合格基準です（要項で再確認）。"
            "本番形式の模試は、テキスト第1周と問題集演習のあとに入れるのが定番です。"
            "本記事では2026年度版の模試·予想問題付き教材3冊を比較します。"
            "価格は購入前にAmazonで必ずご確認ください。"
        ),
        "priority": "360",
        "original_note": f"Amazon tag={TAG}。4426616565 / 4415240909 / 4867881007。",
        "user_intent": "第一種の100問本番形式模試に使う市販教材を比較して1冊に絞りたい。",
        "action_items": (
            "模試はテキスト第1周後から入れる;"
            "3冊の模試用途差を比較表で確認する;"
            "13:30開始·180分で100問通しを月1〜2回入れる;"
            "5科目8/20未満は24時間以内に解き直す;"
            "affiliate-problem-booksで演習のメイン1冊を先に決める"
        ),
        "revision_note": "2026-06-15: Amazon比較記事として全面リライト·published",
        "sections": [
            (
                "模試・予想問題の位置づけ",
                "第一種の模試は、テキストで論点を押さえたあと、"
                "100問·180分·5科目の本番形式で得点を測る演習です。"
                f"試験形式·合格基準は{OFFICIAL}の要項で確認してください。"
                "第二種向け30問教材と混同しないよう、"
                "表紙に「第1種」「100問」相当の範囲が明記されているかを購入前に確認します。"
                "たとえば9月から日曜13:30·100問·180分を月2回入れ、"
                "10月から予想模試を追加する計画が定番です。",
            ),
            (
                "3冊の選び方（模試用途別）",
                "予想模試まで含めて直前期の総仕上げをしたい人は"
                "「ユーキャン 重要過去問&予想模試」、"
                "直近の本試験形式で模試を回したい人は「成美堂 過去6回問題集」、"
                "試験実施団体系の形式に慣れたい人は「労基団連 試験問題集」が向きます。"
                "いずれも第一種専用（100問·5科目）かを表紙で確認し、"
                "すでに使っているテキスト·問題集と出版社系列を揃えると復習効率が上がります。"
                "迷った場合は、おすすめ問題集の記事で決めた1冊を模試のメインに据えるのが失敗しにくい選び方です。",
            ),
            (
                "1位：ユーキャン予想模試付きの特徴",
                "2026年版 ユーキャンの第1種衛生管理者 重要過去問&予想模試"
                "（ユーキャン / 自由国民社·1,760円税込参考·320ページ·B5判）は、"
                "予想模試付きで直前期の模試回数を確保したい人向けです。"
                "重要過去問で本試験形式に慣れたあと、予想模試を13:30開始·180分で受ける流れが組みやすい1冊です。"
                "5科目別得点を記録し、40％未満科目はテキスト該当章に戻って復習するサイクルが定着しやすい構成です。\n\n"
                "向いている人：直前1〜2ヶ月で予想模試を2回以上入れたい人。",
            ),
            (
                "2位：成美堂過去6回の特徴",
                "詳解 第1種衛生管理者過去6回問題集 '26年版"
                "（成美堂出版·1,540円税込参考·288ページ·B5判）は、"
                "直近6回分を解説付きで収録し、本試験に近い形式で模試を回したい人向けです。"
                "成美堂集中レッスンからのステップアップとして、"
                "過去回を1回ずつ100問·180分で受ける計画が立てやすい1冊です。"
                "mock-exam-how-to記事の模試スケジュールと併用すると、"
                "8月·9月·10月の3回模試日程に割り当てやすくなります。\n\n"
                "向いている人：直近の本試験形式で模試を重ねたい人。",
            ),
            (
                "3位：労基団連問題集の特徴",
                "第一種衛生管理者試験問題集 2026年度版"
                "（全国労働基準関係団体連合会·2,420円税込参考·256ページ·B5判）は、"
                "試験実施団体系の形式に慣れたい人向けです。"
                "5科目足切りの模試分析に向き、他社問題集との使い分けで弱点補強しやすい構成です。"
                "ユーキャンや成美堂で演習を進めたあと、"
                "別形式の模試として1回入れると出題の偏りに気づきやすくなります。"
                "年度更新に注意し、購入前に版表記を販売ページで確認してください。\n\n"
                "向いている人：試験形式のバリエーションを確保したい人。",
            ),
            (
                "模試スケジュールの具体例（6月開始）",
                "例：6〜8月はテキスト第1周→9月から問題集で週50問→"
                "9/14（日）·10/6（日）·10/27（日）に13:30開始·100問·180分の模試を入れる。"
                "各模試後は5科目別得点と時間切れ有無を記録し、"
                "8/20未満科目の誤答を24時間以内に解き直します。"
                "時間計測はtimed-practice記事、配分はtime-limit-strategy記事で先に整理すると"
                "模試結果の読み取りがぶれにくくなります。"
                "一衛マスター616問演習で解き直し優先度を決める習慣も併用してください。",
            ),
            (
                "購入前チェックリスト",
                "購入前に以下を確認してください。\n"
                "・2026年度版（最新版）か\n"
                "・第一種衛生管理者試験専用か（第二種30問教材と混同しない）\n"
                "・100問·5科目の本番形式で使えるか\n"
                "・模試をテキスト第1周前に入れない計画か\n"
                "・Amazon在庫·価格（執筆時点と異なる場合あり）\n"
                "・購入直前にAmazon販売ページで版表記·在庫状況を再確認してください。"
                "演習のメイン1冊はaffiliate-problem-booksで先に決め、"
                "模試用途が重複しないよう比較表で役割を整理してから購入してください。",
            ),
        ],
        "faqs": [
            (
                "模試はいつから始めればよいですか？",
                "テキスト第1周完了後（目安8月末）から、科目別20問·60分を挟み、"
                "9月中旬から100問·180分の本番形式へ移行するのが定番です。"
                "いきなり模試から始めると論点不足で得点が読めず、"
                "5科目足切りの優先順位がつけにくくなります。",
            ),
            (
                "問題集記事と同じASINを買う必要がありますか？",
                "同じASINでも、本記事は模試·予想問題の使い方に特化して説明しています。"
                "問題集記事で1冊を決めたうえで、模試回数と日程を本記事で整理してください。"
                "重複購入を避けるため、手元の問題集がユーキャンなら成美堂過去6回を"
                "別形式模試として使う構成も有効です。",
            ),
            (
                "第二種向けの模試教材は使えますか？",
                "第一種は100問·5科目なので、第二種向け30問教材は演習に不足します。"
                "表紙に「第1種」「100問」相当の範囲が明記されているかを必ず確認し、"
                "二種合格済みでも100問形式の模試で5科目40％足切りを確認してください。",
            ),
        ],
        "related_links": (
            "mock-exam-how-to:模試の活用法;"
            "timed-practice:時間を計った演習;"
            "time-limit-strategy:時間配分の戦略;"
            "kakomon-kakaikata:過去問の回し方;"
            "affiliate-problem-books:おすすめ問題集;"
            "affiliate-textbooks-recommend:おすすめテキスト;"
            f"{amazon('4426616565')}:ユーキャン予想模試（Amazon）;"
            f"{amazon('4415240909')}:成美堂過去6回（Amazon）;"
            f"{amazon('4867881007')}:労基団連問題集（Amazon）"
        ),
        "key_points": (
            "ユーキャン 重要過去問&予想模試;"
            "成美堂 過去6回問題集;"
            "労基団連 試験問題集;"
            "模試・予想問題の位置づけ;"
            "模試スケジュールの具体例"
        ),
    },
    "affiliate-beginner-material-set": {
        "title": "第一種衛生管理者の初学者向け教材セット3選【速習・要点整理2026】",
        "meta_description": (
            "第一種衛生管理者の初学者向け教材3選。"
            "ユーキャン速習·成美堂集中レッスン·これだけ覚えるを比較。"
            "速習1冊から本格テキストへの移行順を解説。"
        ),
        "lead": (
            "第一種衛生管理者試験の初学者教材は、"
            "速習·要点整理で五科目の輪郭を掴んでから本格テキストに移る方法が扱いやすいです。"
            "本試験は100問·180分·5科目×各20問で、"
            "総合60％かつ各科目40％以上が合格基準です（要項で再確認）。"
            "本記事では2026年度版のコンパクト教材3冊を、初学者の学習フェーズ別に比較します。"
            "価格は購入前にAmazonで必ずご確認ください。"
        ),
        "priority": "355",
        "original_note": f"Amazon tag={TAG}。4426616557 / 4415241050 / 4415241204。",
        "user_intent": "第一種初学者が最初に手にする速習·要点整理1冊を比較して決めたい。",
        "action_items": (
            "要項で100問·180分·5科目40％足切りを1行メモする;"
            "3冊の学習フェーズを比較表で確認する;"
            "2週間で速習1冊を試し7月に本格テキストを決める;"
            "週8時間を速習3h+演習5hに固定する;"
            "study-plan-beginnerで月次計画をカレンダー固定する"
        ),
        "revision_note": "2026-06-15: 初学者セット比較として全面リライト·published",
        "sections": [
            (
                "速習·要点整理の位置づけ",
                "初学者は「要項確認→速習1冊→本格テキスト1冊→問題集→100問模試」の順で段階投入します。"
                f"出題範囲·合格基準は{OFFICIAL}の要項で先に1枚にまとめ、"
                "学習カレンダーと申込手続きカレンダーは分離してください。"
                "速習本は本試験対策のメイン教材の代わりにはなりません。"
                "3冊を同時購入せず、速習到着後2週間で使い心地を確認してから本格テキストを追加するのが定番です。",
            ),
            (
                "3冊の選び方（フェーズ別）",
                "短期で輪郭を掴むなら「ユーキャン 速習レッスン」、"
                "要点整理から演習比重を上げたい人は「集中レッスン」、"
                "通勤暗記·最終確認用なら「これだけ覚える」が向きます。"
                "集中レッスン·これだけ覚えるはテキスト本体の代替にはならない点に注意し、"
                "いずれも2026年度版表記を購入前に確認してください。"
                "比較表で学習フェーズと週次時間に合う1冊から始め、段階的に本格教材へ移行してください。",
            ),
            (
                "1位：ユーキャン速習レッスンの特徴",
                "2026年版 ユーキャンの第1種·第2種衛生管理者 速習レッスン"
                "（ユーキャン / 自由国民社·2,420円税込参考·240ページ·B5判）は、"
                "衛生管理未経験の初学者が最初の1〜2週間に手に取りやすい速習1冊です。"
                "コンパクトな構成で五科目の輪郭を把握しやすく、"
                "本格的なテキスト購入前の予習や学習再開時のウォームアップにも使えます。"
                "おすすめテキストの記事で本格1冊を決める前の橋渡しとして位置づけます。\n\n"
                "向いている人：いきなり厚いテキストに踏み込む前に輪郭を掴みたい人。",
            ),
            (
                "2位：成美堂集中レッスンの特徴",
                "第1種衛生管理者 集中レッスン '26年版"
                "（成美堂出版·1,540円税込参考·224ページ·B5判）は、"
                "要点整理から演習へ移りたい人向けです。"
                "レッスン形式で論点を短時間復習でき、"
                "成美堂の過去6回問題集へのステップアップがしやすい構成です。"
                "ただしテキスト本体の代替にはならないため、"
                "スッキリや合格教本で第1周を終えたあとの要点整理用として使うのが定番です。"
                "仕事終わりの30分学習と相性がよい1冊です。\n\n"
                "向いている人：速習後に要点を短時間で復習したい人。",
            ),
            (
                "3位：これだけ覚えるの特徴",
                "これだけ覚える 第1種·第2種衛生管理者 '26年版"
                "（成美堂出版·1,100円税込参考·192ページ·B5判）は、"
                "通勤時間の暗記·確認に向くコンパクト1冊です。"
                "覚えるべき論点を整理し、一問一答·暗記帳として持ち歩きやすいサイズです。"
                "本試験直前の最終確認にも使えますが、"
                "単体では演習量が不足するため、テキスト·問題集とセットで使う計画を立ててください。"
                "ichimon-ittou-guide記事の暗記ループと併用すると定着しやすくなります。\n\n"
                "向いている人：通勤30分の暗記枠を確保したい人。",
            ),
            (
                "購入順序の具体例（6月開始）",
                "例：6/14要項30分→6/21演習10問→7/5（土）速習1冊決定→"
                "8/2（土）本格テキスト1冊追加→9月から100問·180分模試を月1回。"
                "速習到着後2週間で第1章+演習10問を試し、"
                "読みにくければ別冊へ切り替えてください。"
                "申込締切と受験手数料8,800円は学習量と混同しないよう、"
                "手続きカレンダーに先に登録しておきましょう。"
                "study-plan-beginner記事で週次8時間を先に固定すると、"
                "速習だけ買って本格テキストに移れないリスクを減らせます。",
            ),
            (
                "購入前チェックリスト",
                "購入前に以下を確認してください。\n"
                "・2026年度版（最新版）か\n"
                "・第一種衛生管理者試験専用か（第二種30問教材と混同しない）\n"
                "・速習·要点整理をメインテキストにしない計画か\n"
                "・Amazon在庫·価格（執筆時点と異なる場合あり）\n"
                "・週8時間以上確保できるか（不足ならstudy-plan-6months記事を検討）\n"
                "・購入直前にAmazon販売ページで版表記·在庫状況を再確認してください。"
                "3冊同時購入は避け、速習到着後2週間の試用結果で本格テキストを追加する順序を守ってください。",
            ),
        ],
        "faqs": [
            (
                "初学者は何を最初に買うべきですか？",
                "要項確認のあと速習·要点整理1冊です。"
                "たとえば6/14要項30分→6/21演習10問→7/5に本記事の3冊から1冊、"
                "8/2に本格テキスト1冊、の順が定番です。"
                "3冊同時購入は避けて段階投入してください。"
                "速習到着後2週間で第1章を試し、本格テキスト移行のタイミングを早めに決めましょう。",
            ),
            (
                "速習だけで独学合格できますか？",
                "速習は輪郭把握·予習用であり、本試験対策のメイン教材の代わりにはなりません。"
                "スッキリや合格教本で第1周を終え、問題集と100問模試で演習量を確保してください。"
                "有害業務などで40％未満が2週続く場合は、オンライン講座比較記事で補強を検討する段階です。",
            ),
            (
                "テキスト記事と初学者記事の違いは何ですか？",
                "テキスト記事は本格3冊の比較、"
                "本記事は初学者の学習フェーズ（速習→要点→暗記）に沿った3冊の位置づけを説明しています。"
                "速習1冊を試したうえで、本格テキストへの移行時期を本記事で整理してください。"
                "比較表で3冊の用途差を先に確認すると購入の失敗が減ります。",
            ),
        ],
        "related_links": (
            "benkyou-junban:勉強の順番;"
            "study-plan-beginner:初学者向け学習計画;"
            "ichimon-ittou-guide:一問一答の使い方;"
            "affiliate-textbooks-recommend:おすすめテキスト;"
            "affiliate-problem-books:おすすめ問題集;"
            "affiliate-online-course-compare:オンライン講座比較;"
            f"{amazon('4426616557')}:ユーキャン速習（Amazon）;"
            f"{amazon('4415241050')}:成美堂集中レッスン（Amazon）;"
            f"{amazon('4415241204')}:これだけ覚える（Amazon）"
        ),
        "key_points": (
            "ユーキャン 速習レッスン;"
            "成美堂 集中レッスン;"
            "これだけ覚える;"
            "購入順序の具体例;"
            "速習·要点整理の位置づけ"
        ),
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
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
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
        row["title"] = cfg["title"]
        row["meta_description"] = cfg["meta_description"]
        row["lead"] = cfg["lead"]
        row["priority"] = cfg["priority"]
        row["original_note"] = cfg["original_note"]
        row["user_intent"] = cfg["user_intent"]
        row["action_items"] = cfg["action_items"]
        row["revision_note"] = cfg["revision_note"]
        row["fact_checked_at"] = "2026-06-15"
        row["content_status"] = "published"
        row["related_links"] = cfg["related_links"]
        row["key_points"] = cfg["key_points"]
        for i, (heading, body) in enumerate(cfg["sections"], start=1):
            row[f"section_{i}_heading"] = heading
            row[f"section_{i}_body"] = body.strip()
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

    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    write_briefs()
    patch_csv()
    return 0


if __name__ == "__main__":
    sys.exit(main())
