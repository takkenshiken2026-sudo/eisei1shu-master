#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Write affiliate book briefs + CSV rows for eisei1shu-master (Amazon tag ue083093-22)."""

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
    "affiliate-textbooks-recommend": {
        "slug": "affiliate-textbooks-recommend",
        "theme_key": "textbooks-recommend",
        "search_intent": "第一種衛生管理者の独学向けおすすめテキストを比較して選びたい",
        "title": "第一種衛生管理者のおすすめ参考書・テキスト3選【2026年度版・独学】",
        "layout": "product-comparison",
        "asp_primary": "amazon",
        "comparison_kind": "books",
        "comparison_title": "おすすめテキスト3選（比較）",
        "price_disclaimer": (
            "価格・在庫・版情報は執筆時点（2026-06-03）のAmazon税込参考です。"
            "購入前に必ず販売ページでご確認ください。"
        ),
        "products": [
            book(
                1,
                "2026年度版 スッキリわかる 第1種衛生管理者 テキスト&問題集",
                "TAC出版",
                "4300121265",
                price_yen=3080,
                pages=512,
                for_who="初学者で図解と演習を1冊にまとめたい人",
                highlights=[
                    "イラスト中心で5分野の全体像をつかみやすい",
                    "章末演習でテキストと問題の往復がしやすい",
                    "TACブランドで独学の定番として選ばれやすい",
                ],
            ),
            book(
                2,
                "第1種衛生管理者 合格教本&問題集",
                "技術評論社",
                "4297154978",
                price_yen=3520,
                pages=560,
                for_who="解説の厚みと演習量のバランスを重視する人",
                highlights=[
                    "教本パートで論点を丁寧に整理",
                    "問題集パートで演習量を確保しやすい",
                    "技術評論社シリーズで他資格教材との相性がよい",
                ],
            ),
            book(
                3,
                "改訂3版 この1冊で合格! 村中一英の第1種衛生管理者 テキスト&問題集",
                "KADOKAWA",
                "4046077948",
                edition="改訂3版",
                price_yen=2860,
                pages=480,
                for_who="著者の解説トーンで暗記→演習を進めたい人",
                highlights=[
                    "村中一英氏の語り口で条文・数値を整理しやすい",
                    "テキストと問題がセットで復習サイクルを組み立てやすい",
                    "改訂版で最新の出題傾向を反映",
                ],
            ),
        ],
        "related_links": [
            "benkyou-junban:勉強の順番",
            "dokugaku-guide:独学合格ガイド",
            "benkyou-jikan:勉強時間の目安",
            "affiliate-problem-books:おすすめ問題集",
            "affiliate-beginner-material-set:初学者向け教材セット",
        ],
        "operator_note": "Amazon tag=ue083093-22。2026-06-03確認。",
    },
    "affiliate-problem-books": {
        "slug": "affiliate-problem-books",
        "theme_key": "problem-books",
        "search_intent": "第一種衛生管理者の過去問・問題集を比較して選びたい",
        "title": "第一種衛生管理者のおすすめ問題集3選【過去問・予想模試2026】",
        "layout": "product-comparison",
        "asp_primary": "amazon",
        "comparison_kind": "books",
        "comparison_title": "おすすめ問題集3選（比較）",
        "price_disclaimer": (
            "価格・在庫は執筆時点（2026-06-03）のAmazon税込参考です。"
            "購入前に販売ページで最新版を確認してください。"
        ),
        "products": [
            book(
                1,
                "2026年版 ユーキャンの第1種衛生管理者 重要過去問&予想模試",
                "ユーキャン / 自由国民社",
                "4426616565",
                price_yen=1980,
                pages=320,
                for_who="予想模試付きで演習量を一気に確保したい人",
                highlights=[
                    "重要過去問と予想模試を1冊で回しやすい",
                    "ユーキャン系列で速習テキストとの併用がしやすい",
                    "直前期の総仕上げにも使える",
                ],
            ),
            book(
                2,
                "詳解 第1種衛生管理者過去6回問題集 '26年版",
                "成美堂出版",
                "4415240909",
                edition="'26年版",
                price_yen=1760,
                pages=288,
                for_who="直近の本試験形式で解きたい人",
                highlights=[
                    "過去6回分を解説付きで収録",
                    "本試験に近い形式で時間配分の練習に向く",
                    "成美堂の問題集ラインで他教材と組み合わせやすい",
                ],
            ),
            book(
                3,
                "第一種衛生管理者試験問題集 2026年度版",
                "全国労働基準関係団体連合会",
                "4867881007",
                price_yen=2200,
                pages=256,
                for_who="試験実施団体系の問題形式に慣れたい人",
                highlights=[
                    "労基団連発行で試験形式に近い演習ができる",
                    "足切り対策の演習量確保に向く",
                    "他社問題集との使い分けで弱点補強しやすい",
                ],
            ),
        ],
        "related_links": [
            "kakomon-kakaikata:過去問の回し方",
            "dokugaku-guide:独学合格ガイド",
            "goukaku-kijun:合格基準",
            "affiliate-textbooks-recommend:おすすめテキスト",
            "affiliate-beginner-material-set:初学者向け教材セット",
        ],
        "operator_note": "Amazon tag=ue083093-22。労基団連版は年度更新に注意。",
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
            "価格は執筆時点（2026-06-03）のAmazon税込参考です。"
            "購入前に必ず販売ページでご確認ください。"
        ),
        "products": [
            book(
                1,
                "2026年版 ユーキャンの第1種・第2種衛生管理者 速習レッスン",
                "ユーキャン / 自由国民社",
                "4426616557",
                price_yen=1650,
                pages=240,
                for_who="短期で全体像を先に掴みたい初学者",
                highlights=[
                    "コンパクトな速習構成で全体像を短期把握",
                    "一種・二種共通部分の整理にも使える",
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
                    "成美堂の問題集・攻略本へのステップアップがしやすい",
                    "仕事終わりの30分学習と相性がよい",
                ],
            ),
            book(
                3,
                "これだけ覚える 第1種・第2種衛生管理者 '26年版",
                "成美堂出版",
                "4415241204",
                edition="'26年版",
                price_yen=1320,
                pages=192,
                for_who="一問一答・暗記帳として持ち歩きたい人",
                highlights=[
                    "覚えるべき論点をコンパクトに整理",
                    "通勤時間の暗記・確認に向く",
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
        ],
        "operator_note": "Amazon tag=ue083093-22。速習系はテキスト本体の代替にならない点を本文で明記。",
    },
}


CSV_ROWS = {
    "affiliate-textbooks-recommend": {
        "title": "第一種衛生管理者のおすすめ参考書・テキスト3選【2026年度版・独学】",
        "meta_description": (
            "第一種衛生管理者試験の独学向けおすすめテキスト3選。"
            "TAC「スッキリわかる」・技術評論社「合格教本&問題集」・村中一英テキストを比較。"
            "選び方と一衛マスター過去問との併用も解説。"
        ),
        "lead": (
            "第一種衛生管理者試験は範囲が広く、最初の1冊選びで学習効率が大きく変わります。"
            "本記事では2026年度版の主要テキスト&問題集3冊を、初学者・社会人独学の視点で比較します。"
            "価格・版情報は購入前にAmazonの販売ページで必ずご確認ください。"
        ),
        "priority": "370",
        "original_note": "Amazon Associates tag=ue083093-22。比較: 4300121265 / 4297154978 / 4046077948。",
        "user_intent": "独学で使う第一種衛生管理者のテキストを、解説の厚み・演習量・初学者向きで比較して1冊に絞りたい。",
        "action_items": "比較表で3冊の違いを確認する;自分の学習スタイルに合う1冊を選ぶ;一衛マスター過去問で弱点分野を把握する",
        "revision_note": "2026-06-03: Amazonリンク付き書籍比較アフィリエイト記事として公開",
        "sections": [
            (
                "この記事でわかること",
                "第一種衛生管理者試験の独学では、公式テキスト相当の理解と演習量の確保が合格の前提です。"
                "本記事では2026年度版のテキスト&問題集3冊——"
                "2026年度版 スッキリわかる 第1種衛生管理者 テキスト&問題集、"
                "第1種衛生管理者 合格教本&問題集、"
                "改訂3版 この1冊で合格! 村中一英の第1種衛生管理者 テキスト&問題集——"
                "を初学者・再受験者それぞれの向き不向きで整理します。\n\n"
                "あわせて、一衛マスターの過去問演習と組み合わせる順番（テキスト→演習→弱点復習）も示します。",
            ),
            (
                "テキスト選びの基準（5分野・足切りを意識）",
                "選ぶ前に、安全衛生技術試験協会（公式）で出題範囲5分野と科目別合格基準（足切り）を確認してください。"
                "テキストは「解説で理解する時間」と「章末・別冊で演習する時間」のバランスで選ぶと挫折しにくくなります。\n\n"
                "社会人独学では、次の2点も判断材料になります。\n\n"
                "- 通勤中に読める分量か\n"
                "- 週末にまとめて演習できる問題量か\n\n"
                "1冊に絞れない場合は、テキスト1冊＋過去問専門1冊の2冊構成も有効です（おすすめ問題集の記事も参照）。",
            ),
            (
                "3冊の選び方（タイプ別）",
                "[[affiliate-hub-placeholder]]\n\n"
                "上記3冊はいずれもテキストと演習がセットのALL-in-one型です。"
                "初学者は図解の多い2026年度版 スッキリわかる 第1種衛生管理者 テキスト&問題集から入る選択が多く、"
                "解説を厚く読みたい人は第1種衛生管理者 合格教本&問題集、"
                "著者の語り口で進めたい人は改訂3版 この1冊で合格! 村中一英の第1種衛生管理者 テキスト&問題集が向きます。",
            ),
            (
                "1位：スッキリわかるの特徴",
                "2026年度版 スッキリわかる 第1種衛生管理者 テキスト&問題集（TAC出版）は、"
                "イラストと要点整理で5分野の全体像をつかみやすい定番です。"
                "初学者が最初の1冊に選びやすく、章末演習でテキストと問題の往復がしやすい構成です。\n\n"
                "向いている人：衛生管理者試験が初めてで、独学のロードマップと合わせて1冊で進めたい人。",
            ),
            (
                "2位・3位の特徴",
                "第1種衛生管理者 合格教本&問題集（技術評論社）は解説ボリュームと演習量のバランス型。"
                "条文・数値の整理を丁寧に読みたい人向けです。\n\n"
                "改訂3版 この1冊で合格! 村中一英の第1種衛生管理者 テキスト&問題集（KADOKAWA）は、"
                "著者の解説で暗記→演習のリズムを作りやすい1冊です。"
                "速習から入りたい場合は初学者向け教材の記事も参照してください。",
            ),
            (
                "テキストと一衛マスター過去問の併用",
                "テキストで論点を押さえたら、一衛マスターの過去問・一問一答で「本試験形式」の演習に移ります。"
                "分野別得点を記録し、足切りライン（科目40%）に届いていない分野をテキスト該当章に戻って復習するサイクルが効率的です。\n\n"
                "演習だけでは理解が浅い分野があれば、通信講座の併用も選択肢です（オンライン講座比較の記事）。",
            ),
            (
                "購入前チェックリスト",
                "購入前に以下を確認してください。\n"
                "・2026年度版（最新版）か\n"
                "・テキストのみ／問題集のみではなくセット版か\n"
                "・Amazon在庫・価格（執筆時点と異なる場合あり）\n"
                "・手元の学習計画（3か月／6か月）に対してページ数・演習量が見合うか",
            ),
        ],
        "faqs": [
            (
                "テキストは1冊だけで足りますか？",
                "ALL-in-one型テキスト1冊＋当サイトの過去問演習で独学は可能です。"
                "演習量が足りないと感じたら、おすすめ問題集の記事で紹介している過去問専門1冊を追加する構成がおすすめです。",
            ),
            (
                "二種合格者はどのテキストが向いていますか？",
                "既に論点の骨格がある場合は、第1種衛生管理者 合格教本&問題集や村中一英テキストで"
                "一種特有の論点（労働衛生・関係法令の深掘り）に時間を割く選び方が向きます。",
            ),
            (
                "スピード合格! パターン別攻略法は使わないのですか？",
                "成美堂「スピード合格! 第1種衛生管理者 パターン別攻略法 '26年版」は解法パターン整理向けです。"
                "テキスト1冊目としては本記事の3冊の方が初学者向き。パターン整理は問題集と併用する使い方が多いです。",
            ),
        ],
        "related_links": (
            "benkyou-junban:勉強の順番;"
            "dokugaku-guide:独学合格ガイド;"
            "benkyou-jikan:勉強時間の目安;"
            "kakomon-kakaikata:過去問の回し方;"
            "affiliate-problem-books:おすすめ問題集;"
            "affiliate-beginner-material-set:初学者向け教材セット;"
            "affiliate-online-course-compare:オンライン講座比較;"
            f"{amazon('4300121265')}:スッキリわかる（Amazon）;"
            f"{amazon('4297154978')}:合格教本&問題集（Amazon）;"
            f"{amazon('4046077948')}:村中一英テキスト（Amazon）"
        ),
        "key_points": "テキスト選びの基準;おすすめ3冊の比較;スッキリわかるの特徴;合格教本・村中テキストの違い;過去問との併用",
    },
    "affiliate-problem-books": {
        "title": "第一種衛生管理者のおすすめ問題集3選【過去問・予想模試2026】",
        "meta_description": (
            "第一種衛生管理者のおすすめ問題集3選。"
            "ユーキャン重要過去問&予想模試、成美堂過去6回、労基団連試験問題集を比較。"
            "過去問の回し方と足切り対策も解説。"
        ),
        "lead": (
            "第一種衛生管理者試験では、過去問・予想問題の演習量が得点安定の鍵です。"
            "本記事では2026年度版の問題集3冊を、収録形式・解説量・独学との相性で比較します。"
        ),
        "priority": "365",
        "original_note": "Amazon tag=ue083093-22。4426616565 / 4415240909 / 4867881007。",
        "user_intent": "第一種衛生管理者の過去問・予想模試付き問題集を比較し、演習のメイン1冊を決めたい。",
        "action_items": "3冊の収録形式を比較する;演習計画に組み込む1冊を選ぶ;足切り分野を過去問で確認する",
        "revision_note": "2026-06-03: Amazonリンク付き問題集比較アフィリエイト記事として公開",
        "sections": [
            (
                "この記事でわかること",
                "テキストで論点を学んだ後は、本試験形式の演習で時間配分と足切り対策を固めます。"
                "本記事では2026年版 ユーキャンの第1種衛生管理者 重要過去問&予想模試、"
                "詳解 第1種衛生管理者過去6回問題集 '26年版、"
                "第一種衛生管理者試験問題集 2026年度版の3冊を比較します。",
            ),
            (
                "問題集選びの基準",
                "問題集選びでは、(1)本試験に近い形式か (2)解説で復習できるか (3)演習量が計画に見合うかを確認します。"
                "足切り（科目40%）対策には、分野別に解ける問題集か、解説で弱点分野に戻れるかが重要です。",
            ),
            (
                "3冊の選び方（タイプ別）",
                "[[affiliate-hub-placeholder]]\n\n"
                "予想模試まで含めて演習量を確保したい人は2026年版 ユーキャンの第1種衛生管理者 重要過去問&予想模試、"
                "直近の本試験形式を解きたい人は詳解 第1種衛生管理者過去6回問題集 '26年版、"
                "試験実施団体系の形式に慣れたい人は第一種衛生管理者試験問題集 2026年度版が向きます。",
            ),
            (
                "1位：ユーキャン重要過去問&予想模試",
                "2026年版 ユーキャンの第1種衛生管理者 重要過去問&予想模試は、"
                "重要過去問に加え予想模試が付属し、直前期の総仕上げにも使えます。"
                "ユーキャン 速習レッスンで全体像を掴んだ後の演習メインにも向きます。",
            ),
            (
                "2位・3位：成美堂過去6回・労基団連",
                "詳解 第1種衛生管理者過去6回問題集 '26年版（成美堂出版）は過去6回分を解説付きで収録。"
                "本試験の時間感覚を養うのに適しています。\n\n"
                "第一種衛生管理者試験問題集 2026年度版（全国労働基準関係団体連合会）は、"
                "試験形式に近い演習が目的の1冊です。他社問題集との使い分けで弱点補強に使えます。",
            ),
            (
                "過去問の回し方（一衛マスターとの併用）",
                "当サイトの過去問で分野別得点を把握したうえで、問題集で「時間を計って解く」練習を行います。"
                "誤答は用語解説・比較表で類似論点まで整理し、1週間後に解き直してください。"
                "詳しい手順は kakomon-kakaikata を参照。",
            ),
            (
                "パターン別攻略法との使い分け",
                "スピード合格! 第1種衛生管理者 パターン別攻略法 '26年版（成美堂出版）は、"
                "解法パターンの整理向けです。問題集単体の代わりというより、"
                "演習後にパターン整理として併用する受験生も多いです。",
            ),
        ],
        "faqs": [
            (
                "過去問だけで合格できますか？",
                "演習量は確保できますが、初めての論点はテキストで理解してから問題集に入る方が効率的です。"
                "おすすめテキストの記事で紹介している1冊と組み合わせる構成を推奨します。",
            ),
            (
                "問題集は何冊必要ですか？",
                "メイン1冊＋当サイト過去問で足りる場合が多いです。"
                "予想模試と本試験形式の両方欲しい場合は2冊構成もあります。",
            ),
            (
                "最新年度版じゃないとダメですか？",
                "出題範囲・法改正の反映のため、購入時は2026年度版（最新版）を選んでください。"
                "中古は版の確認が必要です。",
            ),
        ],
        "related_links": (
            "kakomon-kakaikata:過去問の回し方;"
            "dokugaku-guide:独学合格ガイド;"
            "goukaku-kijun:合格基準;"
            "affiliate-textbooks-recommend:おすすめテキスト;"
            "affiliate-beginner-material-set:初学者向け教材;"
            f"{amazon('4426616565')}:ユーキャン過去問&予想模試（Amazon）;"
            f"{amazon('4415240909')}:成美堂過去6回（Amazon）;"
            f"{amazon('4867881007')}:労基団連問題集（Amazon）"
        ),
        "key_points": "問題集選びの基準;3冊の比較;ユーキャン過去問の特徴;成美堂・労基団連の違い;過去問の回し方",
    },
    "affiliate-beginner-material-set": {
        "title": "第一種衛生管理者の初学者向け教材セット3選【速習・要点整理2026】",
        "meta_description": (
            "第一種衛生管理者試験の初学者向け教材3選。"
            "ユーキャン速習レッスン、成美堂集中レッスン、これだけ覚えるを比較。"
            "本格的なテキスト選びへのステップも解説。"
        ),
        "lead": (
            "第一種衛生管理者試験をこれから始める方は、いきなり厚いテキストより"
            "速習・要点整理で全体像を掴んでから本格教材に移る方法も有効です。"
            "本記事では2026年度版のコンパクト教材3冊を比較します。"
        ),
        "priority": "360",
        "original_note": "Amazon tag=ue083093-22。4426616557 / 4415241050 / 4415241204。",
        "user_intent": "初学者が第一種衛生管理者の学習を始めるとき、速習・要点整理系の1冊を選びたい。",
        "action_items": "3冊の分量と用途を比較する;速習1冊で全体像を掴む;テキスト本冊への移行時期を決める",
        "revision_note": "2026-06-03: Amazonリンク付き初学者教材比較アフィリエイト記事として公開",
        "sections": [
            (
                "この記事でわかること",
                "初学者向け教材（速習・要点整理）は、5分野の地図を作る用途が中心です。"
                "2026年版 ユーキャンの第1種・第2種衛生管理者 速習レッスン、"
                "第1種衛生管理者 集中レッスン '26年版、"
                "これだけ覚える 第1種・第2種衛生管理者 '26年版の3冊を比較します。",
            ),
            (
                "速習・要点整理の位置づけ",
                "速習本は本試験対策のメイン教材の代わりにはなりません。"
                "全体像把握→テキスト1冊（おすすめテキストの記事）→問題集→過去問、"
                "という流れの「最初の1〜2週間」に使うイメージです。",
            ),
            (
                "3冊の選び方（タイプ別）",
                "[[affiliate-hub-placeholder]]\n\n"
                "短期で全体像を掴むなら2026年版 ユーキャンの第1種・第2種衛生管理者 速習レッスン、"
                "要点から演習へ移りたいなら第1種衛生管理者 集中レッスン '26年版、"
                "通勤暗記用ならこれだけ覚える 第1種・第2種衛生管理者 '26年版が向きます。",
            ),
            (
                "1位：ユーキャン速習レッスン",
                "2026年版 ユーキャンの第1種・第2種衛生管理者 速習レッスンは、"
                "コンパクトに5分野の輪郭を把握するのに向いています。"
                "本格的なテキスト購入前の予習や、学習再開時のウォームアップにも使えます。",
            ),
            (
                "2位・3位：集中レッスン・これだけ覚える",
                "第1種衛生管理者 集中レッスン '26年版はレッスン形式で論点を短時間復習。"
                "成美堂の問題集・攻略本系列への橋渡しに適しています。\n\n"
                "これだけ覚える 第1種・第2種衛生管理者 '26年版は一問一答・暗記帳として持ち運びやすく、"
                "直前期の最終確認にも向きます。",
            ),
            (
                "テキスト本冊への移行タイミング",
                "速習で5分野の全体像が掴めたら（目安1〜2週間）、"
                "おすすめテキストの記事で紹介している1冊に移行します。"
                "並行して一衛マスターの一問一答で弱点を洗い出すと効率的です。",
            ),
            (
                "初学者の2冊構成例",
                "例：速習レッスン→スッキリわかるテキスト→ユーキャン過去問&予想模試→当サイト過去問。"
                "教材は増やしすぎず、1フェーズ1冊を原則にすると計画が立てやすくなります。",
            ),
        ],
        "faqs": [
            (
                "速習本だけで受験できますか？",
                "演習量・解説の深さが不足するため非推奨です。"
                "速習後は必ずテキストまたは問題集の本冊に移行してください。",
            ),
            (
                "一種と二種共通の本は第一種だけの学習に使えますか？",
                "共通論点の整理には使えますが、一種特有の深い論点はテキスト本冊で補完が必要です。",
            ),
            (
                "どのくらいでテキストに移ればよいですか？",
                "5分野を一通り眺め、勉強の順番（benkyou-junban）がイメージできたら移行で十分です。"
                "目安は1〜3週間です。",
            ),
        ],
        "related_links": (
            "benkyou-junban:勉強の順番;"
            "study-plan-beginner:初学者向け学習計画;"
            "ichimon-ittou-guide:一問一答の使い方;"
            "affiliate-textbooks-recommend:おすすめテキスト;"
            "affiliate-problem-books:おすすめ問題集;"
            f"{amazon('4426616557')}:ユーキャン速習レッスン（Amazon）;"
            f"{amazon('4415241050')}:集中レッスン（Amazon）;"
            f"{amazon('4415241204')}:これだけ覚える（Amazon）"
        ),
        "key_points": "速習教材の位置づけ;3冊の比較;ユーキャン速習の特徴;集中レッスン・暗記帳;テキスト移行タイミング",
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
        row["title"] = cfg["title"]
        row["meta_description"] = cfg["meta_description"]
        row["lead"] = cfg["lead"]
        row["priority"] = cfg["priority"]
        row["original_note"] = cfg["original_note"]
        row["user_intent"] = cfg["user_intent"]
        row["action_items"] = cfg["action_items"]
        row["revision_note"] = cfg["revision_note"]
        row["content_status"] = "published"
        row["related_links"] = cfg["related_links"]
        row["key_points"] = cfg["key_points"]
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
        print(f"patched CSV row: {slug}")

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
