#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
試験ガイド記事（articles/*.html）と一覧・サイトマップ用URLリストを生成する。

  python3 tools/generate_guide_articles.py
"""
from __future__ import annotations

import json
import re
import xml.sax.saxutils as xml_escape
from pathlib import Path

BASE = "https://eisei1shu-master.jp"
DATE_MODIFIED = "2026-05-19"

ROOT = Path(__file__).resolve().parent.parent
ARTICLES_DIR = ROOT / "articles"
TEMPLATE_CSS = (ARTICLES_DIR / "dokugaku-guide.html").read_text(encoding="utf-8")
CSS_BLOCK = re.search(r"<style>(.*?)</style>", TEMPLATE_CSS, re.DOTALL)
if not CSS_BLOCK:
    raise SystemExit("CSS ブロックを dokugaku-guide.html から取得できません")
ARTICLE_CSS = CSS_BLOCK.group(1)

# 一覧に載せる全記事（表示順）。slug → 一覧用タイトル
INDEX_ENTRIES: list[tuple[str, str]] = [
    ("kakomon-theme-frequency", "第一種衛生管理者「過去問616問」から見る科目・テーマ別の出題傾向【14回分】"),
    ("shiken-guide", "第一種衛生管理者 試験ガイド【試験概要・受験資格・勉強法まで全体像を整理】"),
    ("shiken-kamoku", "第一種衛生管理者の試験科目・出題範囲【5区分44問・配点・頻出テーマ一覧】"),
    ("goukaku-kijun", "第一種衛生管理者の合格点・合格基準【44問中何問で合格？科目別の足切りを解説】"),
    ("juken-shikaku", "第一種衛生管理者の受験資格【学歴別・実務経験年数一覧】自分が受験できるか確認"),
    ("moushikomi-nagare", "第一種衛生管理者試験の申込み・受験の流れ【日程・必要書類・会場まで】"),
    ("goukakuritsu", "第一種衛生管理者の合格率・難易度【合格率だけで判断しない試験の実態】"),
    ("benkyou-jikan", "第一種衛生管理者の勉強時間はどれくらい？1ヶ月・2ヶ月・3ヶ月の学習計画"),
    ("dokugaku-guide", "第一種衛生管理者の独学合格ガイド【過去問・一問一答・直前対策の進め方】"),
    ("textbook-senmon", "第一種衛生管理者のテキスト・通信講座の選び方【独学との併用】"),
    ("nishu-kara-ichishu", "第二種衛生管理者から第一種へ【差分・勉強の進め方】"),
    ("kankei-hourei-benkyou", "第一種衛生管理者・関係法令の勉強法【数値暗記と過去問の使い方】"),
    ("rodoeisei-benkyou", "第一種衛生管理者・労働衛生の勉強法【有害業務・化学物質の重点】"),
    ("rodoseiri-benkyou", "第一種衛生管理者・労働生理の勉強法【計算と生理のつながり】"),
    ("kakomon-kakaikata", "第一種衛生管理者・過去問の効果的な回し方【1周目・2周目・3周目】"),
    ("chokuzen-1kagetsu", "第一種衛生管理者・試験直前1ヶ月の対策【やること優先順位】"),
    ("chokuzen-1shukan", "第一種衛生管理者・試験直前1週間の対策【最終確認リスト】"),
    ("saijuken-guide", "第一種衛生管理者・不合格後の再受験ガイド【切り替えと弱点克服】"),
    ("benkyou-junban", "第一種衛生管理者・勉強の順番【初学者向けロードマップ】"),
    ("shiken-mondai-keishiki", "第一種衛生管理者試験の問題形式・時間配分【44問・5区分の進め方】"),
    ("ichimon-ittou-guide", "第一種衛生管理者・一問一答の使い方【暗記・数値・組合せ問題】"),
    ("yuugai-gyoumu-matome", "第一種衛生管理者・有害業務・優遇措置の整理【法令と衛生のつながり】"),
    ("anzen-eisei-taisei", "第一種衛生管理者・安全衛生管理体制【選任・専任・委員会の整理】"),
    ("jisseki-shomeisho", "第一種衛生管理者・実務経験証明【事業者証明書のポイント】"),
    ("hoken-shi-juken", "保健師・看護師などから第一種衛生管理者を目指す【受験・勉強のコツ】"),
    ("machigai-chui-ten", "第一種衛生管理者・よく間違える論点【ひっかけ対策】"),
    ("goukaku-go-tetsuzuki", "第一種衛生管理者・合格後の手続きと業務【選任・届出の流れ】"),
    ("eisei-kanrisha-gyoumu", "衛生管理者の仕事内容とは【試験合格後に担う役割】"),
    ("kagaku-busshitsu-taisaku", "第一種衛生管理者・化学物質管理の試験対策【化管法・リスクアセスメント】"),
    ("funjin-sokutei-matome", "第一種衛生管理者・粉じんと作業環境測定【頻出論点の整理】"),
    ("kenko-shindan-guide", "第一種衛生管理者・健康診断の試験対策【定期・特定・保存期間】"),
    ("tokutei-gyomu-kenko", "特定業務従事者の健康診断とは【試験で問われる範囲】"),
    ("stress-check-taisaku", "第一種衛生管理者・ストレスチェックの試験対策【メンタルヘルス】"),
    ("netchu-wbgt-guide", "第一種衛生管理者・温熱・WBGT・暑熱順化【労働生理と法令】"),
    ("shukkin-dokugaku-jikan", "仕事しながら第一種衛生管理者を目指す【時間の作り方・学習習慣】"),
    ("orig-mondai-guide", "第一種衛生管理者・実践演習の使い方【本番前の実力チェック】"),
    ("sangyoui-senmon-eisei", "産業医と衛生管理者の違い【試験範囲と職場での役割】"),
    ("horei-kaisei-benkyou", "第一種衛生管理者・法令改正の追い方【最新版テキストの見方】"),
    ("shiken-tojitsu-mochimono", "第一種衛生管理者 試験当日の持ち物・注意事項・会場での過ごし方"),
]

# article_meta に定義があり、HTML を生成するスラッグ
GENERATED_SLUGS = {
    "moushikomi-nagare",
    "textbook-senmon",
    "nishu-kara-ichishu",
    "kankei-hourei-benkyou",
    "rodoeisei-benkyou",
    "rodoseiri-benkyou",
    "kakomon-kakaikata",
    "chokuzen-1kagetsu",
    "chokuzen-1shukan",
    "saijuken-guide",
    "benkyou-junban",
    "shiken-mondai-keishiki",
    "ichimon-ittou-guide",
    "yuugai-gyoumu-matome",
    "anzen-eisei-taisei",
    "jisseki-shomeisho",
    "hoken-shi-juken",
    "machigai-chui-ten",
    "goukaku-go-tetsuzuki",
    "eisei-kanrisha-gyoumu",
    "kagaku-busshitsu-taisaku",
    "funjin-sokutei-matome",
    "kenko-shindan-guide",
    "tokutei-gyomu-kenko",
    "stress-check-taisaku",
    "netchu-wbgt-guide",
    "shukkin-dokugaku-jikan",
    "orig-mondai-guide",
    "sangyoui-senmon-eisei",
    "horei-kaisei-benkyou",
}


def article_meta(slug: str) -> dict:
    """NEW_ARTICLES のメタ＋本文。slug は NEW_ARTICLE_SLUGS に含まれるもの。"""
    data: dict[str, dict] = {
        "moushikomi-nagare": {
            "title": "第一種衛生管理者試験の申込み・受験の流れ【日程・必要書類・会場まで】",
            "description": "第一種衛生管理者試験の申込みから当日までの流れ、必要書類、受験票・会場の確認ポイントを整理します。",
            "category": "受験案内",
            "body": """
<p>第一種衛生管理者試験は、毎年おおむね4月と10月に実施されます（年度により変更があるため、必ず最新の案内を確認してください）。申込みの段階で書類不備があると受験できないため、早めに準備するのが安全です。</p>
<h2>受験までの流れ（概要）</h2>
<ol>
<li>受験資格（学歴・労働衛生の実務経験）を確認する → <a href="/articles/juken-shikaku.html">受験資格の記事</a></li>
<li>試験協会の案内で申込期間・受験料・必要書類を確認する</li>
<li>インターネットまたは郵送で申込み、受験料を納付する</li>
<li>受験票・会場案内を受け取り、当日持ち物を準備する → <a href="/articles/shiken-tojitsu-mochimono.html">試験当日の記事</a></li>
<li>試験当日、指定会場で受験する</li>
</ol>
<h2>申込み時に確認したいこと</h2>
<ul>
<li>申込締切（当日消印有効など、年度ごとの表記に注意）</li>
<li>事業者証明書など、実務経験を証明する書類の形式</li>
<li>顔写真の規格、添付書類の有無</li>
<li>受験料の納付方法（クレジット・コンビニ等）</li>
</ul>
<h2>試験当日までにやること</h2>
<p>会場名・集合時間・交通手段を前日までに確認し、受験票と身分証明書、筆記用具を揃えます。試験内容の最終確認は<a href="/articles/chokuzen-1shukan.html">直前1週間の対策</a>を参照してください。</p>
<blockquote><p><strong>注意：</strong>申込要領・試験日程・会場は<a href="https://www.exam.or.jp/" target="_blank" rel="noopener noreferrer">安全衛生技術試験協会</a>の公式サイトで必ず確認してください。</p></blockquote>
""",
            "related": [
                ("juken-shikaku.html", "第一種衛生管理者の受験資格【学歴別・実務経験年数一覧】"),
                ("shiken-tojitsu-mochimono.html", "試験当日の持ち物・注意事項"),
                ("shiken-guide.html", "試験ガイド（全体像）"),
            ],
        },
        "textbook-senmon": {
            "title": "第一種衛生管理者のテキスト・通信講座の選び方【独学との併用】",
            "description": "第一種衛生管理者のテキスト・通信講座を選ぶ基準と、独学・一衛マスターとの併用の考え方を解説します。",
            "category": "勉強法",
            "body": """
<p>第一種衛生管理者は独学でも合格を狙えますが、初めての方はテキストや通信講座で全体像をつかむ選択も多いです。重要なのは「教材を増やしすぎない」ことです。</p>
<h2>テキスト選びのポイント</h2>
<ul>
<li>試験範囲（5区分・44問）を一通りカバーしているか</li>
<li>関係法令・労働衛生（有害／有害以外）・労働生理の配分が分かりやすいか</li>
<li>過去問解説または演習問題が付いているか</li>
<li>自分の実務経験（第二種保有、保健師など）に合った解説があるか</li>
</ul>
<h2>通信講座を検討する人</h2>
<p>平日の学習時間が短い、法令の読み解きに不安がある場合は、通信講座で学習計画と添削・質問対応を借りる方法もあります。一方、過去問演習量を確保できないまま動画視聴だけで終わらないよう注意が必要です。</p>
<h2>無料ツールとの併用</h2>
<p>テキストで論点を押さえたあと、<a href="/">一衛マスター</a>の過去問・一問一答で反復する流れが効率的です。出題傾向は<a href="/articles/kakomon-theme-frequency.html">過去問616問の傾向記事</a>も参考にしてください。</p>
<h2>まとめ</h2>
<ol>
<li>メイン教材は1〜2冊に絞る</li>
<li>過去問演習の時間を先に確保する</li>
<li>苦手科目だけ追加資料を検討する</li>
</ol>
""",
            "related": [
                ("dokugaku-guide.html", "独学合格ガイド"),
                ("benkyou-jikan.html", "勉強時間・学習計画"),
                ("kakomon-kakaikata.html", "過去問の回し方"),
            ],
        },
        "nishu-kara-ichishu": {
            "title": "第二種衛生管理者から第一種へ【差分・勉強の進め方】",
            "description": "第二種衛生管理者合格者が第一種を目指すときの出題範囲の差、追加で学ぶべき分野、勉強時間の目安を解説します。",
            "category": "勉強法",
            "body": """
<p>第二種衛生管理者試験に合格している方は、第一種の基礎の一部をすでに学んでいます。ただし第一種では<strong>有害業務に関する出題</strong>が増え、試験全体のボリュームも大きくなります。</p>
<h2>第二種との主な違い</h2>
<table><thead><tr><th>観点</th><th>第二種</th><th>第一種</th></tr></thead><tbody>
<tr><td>出題区分</td><td>3区分</td><td>5区分（44問）</td></tr>
<tr><td>有害業務</td><td>範囲が限定的</td><td>法令・衛生ともに比重が大きい</td></tr>
<tr><td>労働生理</td><td>出題あり</td><td>計算・グラフ読み取りも含む</td></tr>
</tbody></table>
<h2>追加で重点を置く分野</h2>
<ul>
<li>関係法令（有害業務）：化学物質・粉じん・鉛・有機溶剤など</li>
<li>労働衛生（有害業務）：ばく露評価、健康診断、作業環境測定</li>
<li>労働生理：代謝・呼吸・循環・疲労・温熱環境</li>
</ul>
<p>科目別の進め方は<a href="/articles/kankei-hourei-benkyou.html">関係法令</a>・<a href="/articles/rodoeisei-benkyou.html">労働衛生</a>・<a href="/articles/rodoseiri-benkyou.html">労働生理</a>の各記事を参照してください。</p>
<h2>勉強時間の目安</h2>
<p>第二種合格者は、おおむね<strong>50〜80時間</strong>程度で第一種の追加分を学習するケースが多いです（個人差あり）。<a href="/articles/benkyou-jikan.html">勉強時間の記事</a>とあわせて計画を立ててください。</p>
""",
            "related": [
                ("shiken-kamoku.html", "試験科目・出題範囲"),
                ("benkyou-jikan.html", "勉強時間の目安"),
                ("dokugaku-guide.html", "独学合格ガイド"),
            ],
        },
        "kankei-hourei-benkyou": {
            "title": "第一種衛生管理者・関係法令の勉強法【数値暗記と過去問の使い方】",
            "description": "第一種衛生管理者試験の関係法令（労働安全衛生法ほか）の効率的な勉強法。数値・選任要件・過去問の活用法を整理します。",
            "category": "科目別",
            "body": """
<p>関係法令は第一種でも配点の大きい分野です。条文の丸暗記より、<strong>「誰が・いつ・何をしなければならないか」</strong>の型で整理すると記憶が定着しやすくなります。</p>
<h2>出題の特徴</h2>
<ul>
<li>労働安全衛生法の体制（安全衛生管理体制、選任・届出）</li>
<li>化学物質・粉じん・鉛・有機溶剤などの個別法令</li>
<li>数値（届出人数、測定頻度、保存年数など）の組合せ問題</li>
</ul>
<p>頻出テーマは<a href="/articles/kakomon-theme-frequency.html">出題傾向記事</a>の関係法令欄も参照してください。</p>
<h2>おすすめの学習順</h2>
<ol>
<li>労働安全衛生法の全体像（事業者義務・体制）をテキストで確認</li>
<li>過去問で「関係法令」だけ解き、間違えた論点をメモ → <a href="/q/index.html">過去問一覧</a></li>
<li>数値・期限は一問一答で反復（<a href="/">学習トップ</a>）</li>
<li>用語で迷ったら<a href="/terms/rodo-anzen-eisei-ho.html">労働安全衛生法</a>などの解説を読む</li>
</ol>
<h2>数値の覚え方</h2>
<p>単独暗記より、同じテーマの問題をまとめて解くと効率が上がります（例：健康診断の頻度、作業環境測定、特別教育の対象）。表にまとめたテキストを1冊、自分用の間違いノートを1冊に絞るとよいです。</p>
<blockquote><p><strong>ポイント：</strong>合格基準上、関係法令で極端に低い得点は避けたい分野です。<a href="/articles/goukaku-kijun.html">合格基準の記事</a>も確認してください。</p></blockquote>
""",
            "related": [
                ("shiken-kamoku.html", "試験科目・出題範囲"),
                ("kakomon-kakaikata.html", "過去問の回し方"),
                ("rodoeisei-benkyou.html", "労働衛生の勉強法"),
            ],
        },
        "rodoeisei-benkyou": {
            "title": "第一種衛生管理者・労働衛生の勉強法【有害業務・化学物質の重点】",
            "description": "第一種衛生管理者試験の労働衛生分野（有害業務・有害以外）の勉強の進め方、頻出テーマ、過去問の使い方を解説します。",
            "category": "科目別",
            "body": """
<p>労働衛生は、職場の有害因子と健康影響・対策を問う分野です。第一種では<strong>有害業務</strong>に関する問題が多く、第二種からのステップアップではここに最も時間を使う人が多いです。</p>
<h2>区分の整理</h2>
<ul>
<li><strong>労働衛生（有害業務）</strong>：化学物質、粉じん、鉛、有機溶剤、特定化学物質など</li>
<li><strong>労働衛生（有害以外）</strong>：騒音・振動、温熱、照明、心理的要因、人間工学など</li>
</ul>
<h2>頻出しやすい論点</h2>
<ul>
<li>ばく露経路と健康障害の対応（吸入・経皮・蓄積）</li>
<li>作業環境測定・健康診断・リスクアセスメント</li>
<li>管理区分・記録・MSDS・表示</li>
<li>防毒マスク・局所排気装置などの対策</li>
</ul>
<h2>学習の進め方</h2>
<ol>
<li>物質名と障害の組合せを過去問で反復</li>
<li>測定方法（濃度・強度）と管理基準値の違いを図で整理</li>
<li>用語集で不明語を潰す（例：<a href="/terms/risk-assessment.html">リスクアセスメント</a>、<a href="/terms/sds.html">SDS</a>）</li>
</ol>
<p>演習は<a href="/q/index.html">過去問の静的ページ</a>または<a href="/">アプリの過去問モード</a>から。</p>
""",
            "related": [
                ("nishu-kara-ichishu.html", "第二種から第一種へ"),
                ("kankei-hourei-benkyou.html", "関係法令の勉強法"),
                ("kakomon-theme-frequency.html", "出題傾向まとめ"),
            ],
        },
        "rodoseiri-benkyou": {
            "title": "第一種衛生管理者・労働生理の勉強法【計算と生理のつながり】",
            "description": "第一種衛生管理者試験の労働生理分野の勉強法。計算問題・グラフ・生理現象の理解のコツを解説します。",
            "category": "科目別",
            "body": """
<p>労働生理は、人体の機能と職場環境・作業負荷の関係を問う分野です。感覚的に覚えるより、<strong>生理の流れ（例：酸素運搬→エネルギー代謝）</strong>でつなげると理解が深まります。</p>
<h2>出題のタイプ</h2>
<ul>
<li>基礎生理（循環・呼吸・代謝・腎・神経など）</li>
<li>温熱環境（WBGT、代謝率、服装・作業強度）</li>
<li>疲労・夜勤・時差・睡眠</li>
<li>簡単な計算・グラフ・表の読み取り</li>
</ul>
<h2>勉強のコツ</h2>
<ol>
<li>テキストの図を見ながら「原因→結果」を言語化する</li>
<li>計算は公式を暗記する前に、過去問で「何を求めているか」を把握</li>
<li>間違えた問題を科目別にノート化し、直前に見返す</li>
</ol>
<p>関連用語は<a href="/terms/wbgt-necchu-jyunka.html">WBGTと熱中症</a>など、<a href="/terms/">用語解説一覧</a>から確認できます。</p>
<h2>他科目とのバランス</h2>
<p>労働生理は出題数は法令・衛生より少ないものの、足切りラインを下回らないよう最低限の得点は確保したい分野です。全体計画は<a href="/articles/benkyou-jikan.html">勉強時間の記事</a>を参照してください。</p>
""",
            "related": [
                ("shiken-kamoku.html", "試験科目・出題範囲"),
                ("dokugaku-guide.html", "独学合格ガイド"),
                ("chokuzen-1kagetsu.html", "直前1ヶ月の対策"),
            ],
        },
        "kakomon-kakaikata": {
            "title": "第一種衛生管理者・過去問の効果的な回し方【1周目・2周目・3周目】",
            "description": "第一種衛生管理者の過去問を何周・どの順番で解くか。1周目から直前期までの回し方と、間違いノートの作り方を解説します。",
            "category": "勉強法",
            "body": """
<p>過去問は「解いた回数」より<strong>間違いの潰し方</strong>で効果が変わります。第一種では44問×複数年度と範囲が広いため、周回の目的を分けて進めるのがおすすめです。</p>
<h2>1周目：全体像と弱点の洗い出し</h2>
<ul>
<li>科目を分けてでもよいので、まずは一通り解く</li>
<li>正解でも「他の選択肢がなぜ違うか」分からない問題は○扱いにしない</li>
<li>間違えた問題にタグ（法令／衛生有害／衛生その他／生理）を付ける</li>
</ul>
<p>静的ページは<a href="/q/index.html">過去問一覧</a>、演習は<a href="/">学習トップの過去問モード</a>が便利です。</p>
<h2>2周目：間違いと頻出の集中</h2>
<ul>
<li>1周目の×だけを再解（テキストは見ない）</li>
<li>再度×なら解説を読み、用語・数値をノートへ</li>
<li><a href="/articles/kakomon-theme-frequency.html">出題傾向</a>と照らし、優先テーマを決める</li>
</ul>
<h2>3周目以降：本番形式</h2>
<p>制限時間を意識し、5区分を連続で解く練習を増やします。直前期は<a href="/articles/chokuzen-1kagetsu.html">直前1ヶ月</a>・<a href="/articles/chokuzen-1shukan.html">直前1週間</a>の記事に沿って負荷を調整してください。</p>
<blockquote><p><strong>注意：</strong>掲載問題は過去問形式の演習です。本番の原文・合格発表は<a href="https://www.exam.or.jp/" target="_blank" rel="noopener noreferrer">試験協会</a>の公式情報を確認してください。</p></blockquote>
""",
            "related": [
                ("dokugaku-guide.html", "独学合格ガイド"),
                ("goukaku-kijun.html", "合格基準"),
                ("kakomon-theme-frequency.html", "出題傾向まとめ"),
            ],
        },
        "chokuzen-1kagetsu": {
            "title": "第一種衛生管理者・試験直前1ヶ月の対策【やること優先順位】",
            "description": "第一種衛生管理者試験の直前1ヶ月でやるべきこと。過去問・一問一答・足切り回避の優先順位を整理します。",
            "category": "直前対策",
            "body": """
<p>直前1ヶ月は新しい教材を増やすより、<strong>得点できる論点の定着</strong>に切り替える時期です。特に第一種は科目別の足切りがあるため、苦手科目を放置しないことが重要です。</p>
<h2>優先度A（毎日）</h2>
<ul>
<li>過去問の間違いノートの再確認</li>
<li>一問一答で数値・期限・選任要件（10〜20分でも可）</li>
<li>苦手科目を1区分だけテキストで補強</li>
</ul>
<h2>優先度B（週2〜3回）</h2>
<ul>
<li>本番形式の模擬（44問に近い配分で時間計測）</li>
<li>出題傾向の再確認 → <a href="/articles/kakomon-theme-frequency.html">傾向記事</a></li>
</ul>
<h2>優先度C（余力があれば）</h2>
<ul>
<li>労働生理の計算問題の式の再確認</li>
<li>新しい論点のインプット（量は控えめ）</li>
</ul>
<h2>やめた方がよいこと</h2>
<ul>
<li>未読テキストの最初から読破</li>
<li>コミュニティやSNSでの不安の増幅（自分のノートに集中）</li>
</ul>
<p>合格ラインの考え方は<a href="/articles/goukaku-kijun.html">合格基準の記事</a>、1週間前は<a href="/articles/chokuzen-1shukan.html">直前1週間の記事</a>へ。</p>
""",
            "related": [
                ("chokuzen-1shukan.html", "直前1週間の対策"),
                ("kakomon-kakaikata.html", "過去問の回し方"),
                ("shiken-tojitsu-mochimono.html", "試験当日の注意"),
            ],
        },
        "chokuzen-1shukan": {
            "title": "第一種衛生管理者・試験直前1週間の対策【最終確認リスト】",
            "description": "第一種衛生管理者試験の直前1週間で確認すべき項目リスト。持ち物・体調・最終復習のポイントをまとめます。",
            "category": "直前対策",
            "body": """
<p>直前1週間は学習量を絞り、<strong>記憶の定着と本番コンディション</strong>を整える期間です。新規の広い範囲のインプットは最小限にし、間違いノートと頻出数値に集中しましょう。</p>
<h2>7日前〜3日前</h2>
<ul>
<li>過去問の×問題だけをもう一度解く</li>
<li>各科目で「最低限これだけは取る」リストを1ページにまとめる</li>
<li>会場・交通・受験票・身分証を確認 → <a href="/articles/shiken-tojitsu-mochimono.html">当日の記事</a></li>
</ul>
<h2>2日前〜前日</h2>
<ul>
<li>一問一答で数値・組合せをさらっと確認</li>
<li>睡眠を優先（徹夜の詰め込みは避ける）</li>
<li>筆記用具・時計・飲み物などをカバンにセット</li>
</ul>
<h2>当日朝</h2>
<ul>
<li>短時間でノートを見る程度にとどめる</li>
<li>会場到着は余裕をもって</li>
</ul>
<blockquote><p><strong>ポイント：</strong>直前に「知らない知識」に当たっても動じないよう、既に解いた過去問の復習を中心に。</p></blockquote>
""",
            "related": [
                ("chokuzen-1kagetsu.html", "直前1ヶ月の対策"),
                ("moushikomi-nagare.html", "申込み・受験の流れ"),
                ("shiken-tojitsu-mochimono.html", "試験当日の持ち物"),
            ],
        },
        "saijuken-guide": {
            "title": "第一種衛生管理者・不合格後の再受験ガイド【切り替えと弱点克服】",
            "description": "第一種衛生管理者試験に不合格だった場合の再受験の進め方。得点分布の見方、弱点科目の立て直しを解説します。",
            "category": "受験案内",
            "body": """
<p>不合格は「実力不足の断定」ではなく、<strong>その回の得点分布と自分の弱点</strong>を分析する材料です。感情の切り替えのあと、データに基づいて次の受験計画を立てましょう。</p>
<h2>まず確認すること</h2>
<ul>
<li>科目別の得点（足切りに近い科目はないか）→ <a href="/articles/goukaku-kijun.html">合格基準</a></li>
<li>全体正答率と、苦手だったテーマ（間違いノートがあれば振り返り）</li>
<li>試験協会の合格発表・復習用資料の有無（年度による）</li>
</ul>
<h2>再受験までの学習方針</h2>
<ol>
<li>最も得点が低い区分に学習時間の4割を割く</li>
<li>過去問は「×だけ」の周回から再開 → <a href="/articles/kakomon-kakaikata.html">過去問の回し方</a></li>
<li>第二種のみ合格者は<a href="/articles/nishu-kara-ichishu.html">差分記事</a>で有害業務を重点補強</li>
<li>次回申込みは早めに準備 → <a href="/articles/moushikomi-nagare.html">申込みの流れ</a></li>
</ol>
<h2>メンタル面</h2>
<p>短期間で詰め込みすぎるより、週あたりの学習時間を一定に保つ方が再現性が高いです。<a href="/articles/benkyou-jikan.html">2〜3ヶ月プラン</a>をベースに調整してください。</p>
""",
            "related": [
                ("goukaku-kijun.html", "合格基準"),
                ("dokugaku-guide.html", "独学合格ガイド"),
                ("benkyou-jikan.html", "勉強時間・学習計画"),
            ],
        },
        "benkyou-junban": {
            "title": "第一種衛生管理者・勉強の順番【初学者向けロードマップ】",
            "description": "第一種衛生管理者試験を初めて学ぶ人向けに、テキスト・過去問・一問一答の進める順番と全体のロードマップを解説します。",
            "category": "勉強法",
            "body": """
<p>第一種衛生管理者は範囲が広く、いきなり過去問だけでは挫折しやすい試験です。まず全体像をつかみ、次に演習で弱点を潰す<strong>2段階</strong>で進めると効率が上がります。</p>
<h2>ステップ1：試験のルールを押さえる（1〜3日）</h2>
<ul>
<li><a href="/articles/shiken-kamoku.html">試験科目・5区分44問</a>を読む</li>
<li><a href="/articles/goukaku-kijun.html">合格基準・足切り</a>を確認</li>
<li><a href="/articles/juken-shikaku.html">自分が受験できるか</a>を確認</li>
</ul>
<h2>ステップ2：テキストで大枠（2〜4週間）</h2>
<p>関係法令→労働衛生（有害以外→有害）→労働生理の順が一般的です。完璧に暗記せず「見出しレベル」で構造をつかみます。</p>
<h2>ステップ3：過去問で型を知る（3〜6週間）</h2>
<p>1周目は解きっぱなしでよいので、<a href="/articles/kakomon-kakaikata.html">過去問の回し方</a>に沿って進めます。<a href="/q/index.html">過去問一覧</a>または<a href="/">学習トップ</a>を利用。</p>
<h2>ステップ4：一問一答と弱点補強（試験直前まで）</h2>
<p>数値・組合せは<a href="/articles/ichimon-ittou-guide.html">一問一答の記事</a>を参照。苦手科目は科目別記事（<a href="/articles/kankei-hourei-benkyou.html">法令</a>・<a href="/articles/rodoeisei-benkyou.html">衛生</a>・<a href="/articles/rodoseiri-benkyou.html">生理</a>）で深掘り。</p>
""",
            "related": [
                ("benkyou-jikan.html", "勉強時間の目安"),
                ("dokugaku-guide.html", "独学合格ガイド"),
                ("shiken-guide.html", "試験ガイド（全体像）"),
            ],
        },
        "shiken-mondai-keishiki": {
            "title": "第一種衛生管理者試験の問題形式・時間配分【44問・5区分の進め方】",
            "description": "第一種衛生管理者試験の出題形式、5区分の並び、44問の時間配分の目安を解説します。",
            "category": "試験概要",
            "body": """
<p>第一種衛生管理者試験は、おおむね<strong>5区分・合計44問</strong>のマークシート方式です（年度により細部は異なるため、最新の試験要項を確認してください）。</p>
<h2>区分のイメージ</h2>
<ol>
<li>関係法令（有害業務）</li>
<li>関係法令（有害以外）</li>
<li>労働衛生（有害業務）</li>
<li>労働衛生（有害以外）</li>
<li>労働生理</li>
</ol>
<p>詳細は<a href="/articles/shiken-kamoku.html">試験科目の記事</a>を参照。</p>
<h2>時間配分の目安</h2>
<p>全体で約100分前後とされることが多く、1問あたり2分強が目安です。長文の設問は先読みせず、選択肢から消去法も有効です。</p>
<h2>本番に近い練習</h2>
<p>直前期は区分をまたいで44問を一気に解く練習を増やします。<a href="/articles/chokuzen-1kagetsu.html">直前1ヶ月</a>・<a href="/">アプリの模擬形式</a>と組み合わせてください。</p>
<blockquote><p><strong>注意：</strong>問題数・時間・合格基準は試験回で変更されることがあります。<a href="https://www.exam.or.jp/" target="_blank" rel="noopener noreferrer">安全衛生技術試験協会</a>の案内を必ず確認してください。</p></blockquote>
""",
            "related": [
                ("shiken-kamoku.html", "試験科目・出題範囲"),
                ("shiken-tojitsu-mochimono.html", "試験当日の注意"),
                ("goukaku-kijun.html", "合格基準"),
            ],
        },
        "ichimon-ittou-guide": {
            "title": "第一種衛生管理者・一問一答の使い方【暗記・数値・組合せ問題】",
            "description": "第一種衛生管理者試験で一問一答演習が向いている論点と、過去問との使い分け、反復の進め方を解説します。",
            "category": "勉強法",
            "body": """
<p>一問一答は、第一種衛生管理者試験の<strong>数値・期限・選任要件・物質と障害の組合せ</strong>を定着させるのに向いています。過去問で「なぜ間違えたか」を理解したあとの反復に使うと効果的です。</p>
<h2>向いている論点</h2>
<ul>
<li>健康診断・作業環境測定の頻度</li>
<li>特別教育・安全衛生教育の対象</li>
<li>化学物質と健康障害の対応</li>
<li>労働生理の基礎用語</li>
</ul>
<h2>向いていない使い方</h2>
<p>長文の事例問題や、複数条文を横断する論理問題は、一問一答だけでは対応しきれません。必ず過去問で文脈を学習してください。</p>
<h2>おすすめのルーティン</h2>
<ol>
<li>朝10分：前日の×だけ一問一答</li>
<li>週1回：科目別に50問まとめて</li>
<li>直前：間違いノートとセットで反復</li>
</ol>
<p>演習は<a href="/">学習トップの一問一答</a>、過去問形式は<a href="/q/index.html">過去問一覧</a>から。</p>
""",
            "related": [
                ("kakomon-kakaikata.html", "過去問の回し方"),
                ("dokugaku-guide.html", "独学合格ガイド"),
                ("kankei-hourei-benkyou.html", "関係法令の勉強法"),
            ],
        },
        "yuugai-gyoumu-matome": {
            "title": "第一種衛生管理者・有害業務・優遇措置の整理【法令と衛生のつながり】",
            "description": "第一種衛生管理者試験で重要な有害業務と優遇措置の考え方を、法令・労働衛生の両面から整理します。",
            "category": "科目別",
            "body": """
<p>第一種では<strong>有害業務</strong>に関する法令・労働衛生の出題が、第二種より多くなります。「優遇措置」は試験用語として、一定の条件を満たす事業場等に対する規制の緩和・特例を指すことがあります（設問文脈で確認）。</p>
<h2>押さえるべき軸</h2>
<ul>
<li>どの物質・作業が対象か（粉じん、化学物質、鉛、有機溶剤など）</li>
<li>事業者・衛生管理者・作業者それぞれの義務</li>
<li>健康診断・作業環境測定・記録保存</li>
</ul>
<h2>法令と衛生のつなげ方</h2>
<p>同じテーマが「関係法令」と「労働衛生」の両方から出ることがあります。物質名・管理区分・測定・健診をセットで覚えると得点が安定します。</p>
<p>関連用語：<a href="/terms/tokutei-kagaku-busshitsu-shogai-yobo.html">特定化学物質</a>、<a href="/terms/funzin-shogai-boshi.html">粉じん障害防止</a>など。</p>
""",
            "related": [
                ("nishu-kara-ichishu.html", "第二種から第一種へ"),
                ("rodoeisei-benkyou.html", "労働衛生の勉強法"),
                ("kakomon-theme-frequency.html", "出題傾向"),
            ],
        },
        "anzen-eisei-taisei": {
            "title": "第一種衛生管理者・安全衛生管理体制【選任・専任・委員会の整理】",
            "description": "労働安全衛生法に基づく安全衛生管理体制、衛生管理者・安全管理者・委員会の整理を試験対策向けに解説します。",
            "category": "科目別",
            "body": """
<p>関係法令で頻出するのが<strong>安全衛生管理体制</strong>です。常時雇用者数・業種・有害業務の有無によって、選任義務・専任性・委員会設置が変わります。</p>
<h2>整理のしかた</h2>
<ol>
<li>対象となる事業場か（常時雇用者数など）</li>
<li>誰を選任するか（衛生管理者・安全管理者・産業医）</li>
<li>専任か兼務か、委員会は必要か</li>
<li>選任届・変更届の要否</li>
</ol>
<p>数値問題が多いため、テキストの表を1冊にまとめ、過去問で当てはめ練習をします。</p>
<p>用語：<a href="/terms/sokatsu-anzen-eisei-kanrisha.html">総括安全衛生管理者</a>、<a href="/terms/anzen-eisei-kanri-taisei.html">安全衛生管理体制</a>、<a href="/terms/eisei-iinkai.html">衛生委員会</a>。</p>
""",
            "related": [
                ("kankei-hourei-benkyou.html", "関係法令の勉強法"),
                ("jisseki-shomeisho.html", "実務経験証明"),
                ("shiken-kamoku.html", "試験科目"),
            ],
        },
        "jisseki-shomeisho": {
            "title": "第一種衛生管理者・実務経験証明【事業者証明書のポイント】",
            "description": "第一種衛生管理者試験の受験に必要な労働衛生の実務経験証明・事業者証明書の確認ポイントを解説します。",
            "category": "受験案内",
            "body": """
<p>受験資格の多くは、<strong>労働衛生に関する実務経験</strong>を事業者証明書等で証明することを求められます。申込み直前になって準備が間に合わないケースが多いため、早めに勤務先と調整しましょう。</p>
<h2>確認すること</h2>
<ul>
<li>学歴に応じた必要年数を満たしているか → <a href="/articles/juken-shikaku.html">受験資格</a></li>
<li>経験期間の起算・終了日が証明できるか</li>
<li>業務内容が労働衛生の実務に該当するか</li>
<li>証明書の様式・押印・提出先</li>
</ul>
<h2>勤務先への依頼のコツ</h2>
<p>人事・総務だけでなく、産業保健担当・衛生管理者に相談するとスムーズなことがあります。過去の申込み事例があればフォーマットを流用できます。</p>
<p>申込み全体の流れは<a href="/articles/moushikomi-nagare.html">申込み・受験の流れ</a>を参照。</p>
<blockquote><p><strong>注意：</strong>証明書の様式・記載事項は年度ごとの試験要項に従ってください。</p></blockquote>
""",
            "related": [
                ("juken-shikaku.html", "受験資格一覧"),
                ("moushikomi-nagare.html", "申込みの流れ"),
                ("shiken-guide.html", "試験ガイド"),
            ],
        },
        "hoken-shi-juken": {
            "title": "保健師・看護師などから第一種衛生管理者を目指す【受験・勉強のコツ】",
            "description": "保健師・看護師・作業療法士など医療系資格者が第一種衛生管理者試験を受けるときの強み・弱点と勉強の進め方を解説します。",
            "category": "勉強法",
            "body": """
<p>医療系の資格・実務経験を持つ方は、労働衛生の実務経験要件や、衛生分野の理解で有利な面があります。一方、労働安全衛生法の数値・体制・個別法令は初見のことも多いです。</p>
<h2>強みになりやすい分野</h2>
<ul>
<li>労働衛生（健康診断・保健指導・疾病の知識）</li>
<li>労働生理の基礎（解剖生理の背景知識）</li>
<li>職場でのコミュニケーション・衛生管理の実感</li>
</ul>
<h2>重点補強したい分野</h2>
<ul>
<li>関係法令の数値・選任・届出</li>
<li>化学物質・粉じん・測定・管理区分</li>
<li>安全側の規制（機械・危険物等）に弱い場合はテキストで補強</li>
</ul>
<p>勉強時間の目安は<a href="/articles/benkyou-jikan.html">勉強時間の記事</a>。実務経験の該当性は<a href="/articles/juken-shikaku.html">受験資格</a>で確認。</p>
""",
            "related": [
                ("benkyou-junban.html", "勉強の順番"),
                ("rodoeisei-benkyou.html", "労働衛生の勉強法"),
                ("dokugaku-guide.html", "独学合格ガイド"),
            ],
        },
        "machigai-chui-ten": {
            "title": "第一種衛生管理者・よく間違える論点【ひっかけ対策】",
            "description": "第一種衛生管理者試験で受験者がつまずきやすい論点・ひっかけのパターンと対策をまとめます。",
            "category": "勉強法",
            "body": """
<p>第一種では「知っているつもり」でも、選択肢の微妙な違いで誤答になりやすい問題があります。過去問で×になった問題を分類すると、対策が立てやすくなります。</p>
<h2>ひっかけの典型パターン</h2>
<ul>
<li><strong>数字の取り違え</strong>（人数・年数・濃度・頻度）</li>
<li><strong>主体の取り違え</strong>（事業者・衛生管理者・作業者・厚生労働大臣）</li>
<li><strong>「すべて正しい」系</strong>の1つだけの誤り</li>
<li><strong>有害／有害以外</strong>の区分ミス</li>
<li><strong>類似物質</strong>の障害の取り違え</li>
</ul>
<h2>対策</h2>
<ol>
<li>×問題に「なぜ他の選択肢は違うか」を1行メモ</li>
<li>同型の問題をまとめて3問以上連続で解く</li>
<li>直前は間違いノートだけを見る</li>
</ol>
<p><a href="/articles/kakomon-theme-frequency.html">出題傾向</a>で頻出テーマを優先し、<a href="/articles/ichimon-ittou-guide.html">一問一答</a>で数値を固めます。</p>
""",
            "related": [
                ("kakomon-kakaikata.html", "過去問の回し方"),
                ("goukaku-kijun.html", "合格基準"),
                ("chokuzen-1shukan.html", "直前1週間"),
            ],
        },
        "goukaku-go-tetsuzuki": {
            "title": "第一種衛生管理者・合格後の手続きと業務【選任・届出の流れ】",
            "description": "第一種衛生管理者試験合格後の手続き、衛生管理者選任・届出、職場での業務開始までの流れを解説します。",
            "category": "受験案内",
            "body": """
<p>試験合格はゴールではなく、<strong>衛生管理者として選任される</strong>ための資格取得です。合格証明の手続き、事業場での選任・届出は、試験協会・都道府県労働局・事業者の手続きに従います（詳細は公式情報で確認）。</p>
<h2>合格後にすること（一般的な流れ）</h2>
<ol>
<li>合格発表の確認・合格証明の取得手続き</li>
<li>選任予定の事業場での衛生管理者選任</li>
<li>選任届等の提出（所轄労働基準監督署など）</li>
<li>衛生管理者としての初任研修等（必要な場合）</li>
</ol>
<h2>業務のイメージ</h2>
<p>具体的な日常業務は<a href="/articles/eisei-kanrisha-gyoumu.html">衛生管理者の仕事内容</a>を参照。法令上の体制は<a href="/articles/anzen-eisei-taisei.html">安全衛生管理体制</a>の記事とあわせて学ぶと理解が深まります。</p>
<blockquote><p><strong>注意：</strong>手続き・研修は法改正や所轄により異なります。厚生労働省・労働局・試験協会の最新情報を確認してください。</p></blockquote>
""",
            "related": [
                ("eisei-kanrisha-gyoumu.html", "衛生管理者の仕事内容"),
                ("juken-shikaku.html", "受験資格（選任要件の理解）"),
                ("shiken-guide.html", "試験ガイド"),
            ],
        },
        "eisei-kanrisha-gyoumu": {
            "title": "衛生管理者の仕事内容とは【試験合格後に担う役割】",
            "description": "第一種衛生管理者として選任された後の主な業務、産業医・安全管理者との役割分担、試験で学ぶ内容との関係を解説します。",
            "category": "試験概要",
            "body": """
<p>衛生管理者は、職場の労働者の健康を守るため、<strong>労働衛生に関する管理・指導</strong>を行う役割です。試験で学ぶ法令・衛生・生理の知識は、こうした実務の土台になります。</p>
<h2>主な業務例</h2>
<ul>
<li>健康診断・健康診断結果の評価と措置</li>
<li>作業環境の管理（測定の実施・改善指導）</li>
<li>化学物質・有害因子のリスク管理</li>
<li>安全衛生教育・衛生委員会の運営支援</li>
<li>健康障害の防止・早期発見のための職場巡視</li>
</ul>
<h2>他職種との分担</h2>
<p>産業医は医学的管理、安全管理者は安全側、衛生管理者は衛生側と分担されることが多いです。小規模事業場では兼務もあります。</p>
<h2>試験学習との関係</h2>
<p>受験動機が「選任予定」なら、職場の実態に照らして優先テーマを決めるとモチベーションが維持しやすいです。合格後の手続きは<a href="/articles/goukaku-go-tetsuzuki.html">合格後の手続き</a>を参照。</p>
""",
            "related": [
                ("goukaku-go-tetsuzuki.html", "合格後の手続き"),
                ("anzen-eisei-taisei.html", "安全衛生管理体制"),
                ("shiken-guide.html", "試験ガイド"),
            ],
        },
        "kagaku-busshitsu-taisaku": {
            "title": "第一種衛生管理者・化学物質管理の試験対策【化管法・リスクアセスメント】",
            "description": "化学物質管理に関する法令・リスクアセスメント・SDS・管理区分など、第一種衛生管理者試験の頻出論点を整理します。",
            "category": "科目別",
            "body": """
<p>化学物質は、第一種の労働衛生・関係法令の両方から繰り返し出題されます。物質名・管理区分・健康障害・対策を<strong>セットで覚える</strong>と得点が安定します。</p>
<h2>押さえる法令・制度</h2>
<ul>
<li>化管法（確認・表示・リスクアセスメント・記録等）</li>
<li>特定化学物質・有機溶剤・鉛・四アルキル鉛など個別規則</li>
<li>製造許可物質・名称公表物質の区別</li>
</ul>
<h2>試験での出題パターン</h2>
<ul>
<li>物質と健康障害の組合せ</li>
<li>管理濃度・ばく露限界・測定方法</li>
<li>防毒マスク・局所排気・密閉化</li>
</ul>
<p>用語：<a href="/terms/sds.html">SDS</a>、<a href="/terms/risk-assessment.html">リスクアセスメント</a>、<a href="/articles/yuugai-gyoumu-matome.html">有害業務の整理</a>。</p>
""",
            "related": [
                ("rodoeisei-benkyou.html", "労働衛生の勉強法"),
                ("kankei-hourei-benkyou.html", "関係法令の勉強法"),
                ("kakomon-theme-frequency.html", "出題傾向"),
            ],
        },
        "funjin-sokutei-matome": {
            "title": "第一種衛生管理者・粉じんと作業環境測定【頻出論点の整理】",
            "description": "粉じん障害防止規則・作業環境測定・管理区分など、粉じん関連の試験対策をまとめます。",
            "category": "科目別",
            "body": """
<p>粉じんは第一種で特に重要なテーマの一つです。じん肺・管理区分・測定頻度・健康診断との関係を横断的に整理しましょう。</p>
<h2>頻出キーワード</h2>
<ul>
<li>粉じん障害防止規則・管理区分（A/B/C等、最新法令で確認）</li>
<li>作業環境測定の対象・頻度・評価</li>
<li>防じんマスク・湿式作業・局所排気</li>
<li>健康診断（胸部X線・じん肺健診）</li>
</ul>
<h2>学習の進め方</h2>
<ol>
<li>テキストの粉じん章を表で1枚にまとめる</li>
<li>過去問で粉じん・測定のタグ付き問題だけ解く</li>
<li>用語：<a href="/terms/funzin-shogai-boshi.html">粉じん障害防止規則</a>、<a href="/terms/sagyo-kankyo-sokutei.html">作業環境測定</a></li>
</ol>
""",
            "related": [
                ("yuugai-gyoumu-matome.html", "有害業務の整理"),
                ("kenko-shindan-guide.html", "健康診断の対策"),
                ("rodoeisei-benkyou.html", "労働衛生の勉強法"),
            ],
        },
        "kenko-shindan-guide": {
            "title": "第一種衛生管理者・健康診断の試験対策【定期・特定・保存期間】",
            "description": "定期健康診断・特定健康診断・保存期間・雇入時健診など、健康診断に関する試験頻出論点を解説します。",
            "category": "科目別",
            "body": """
<p>健康診断は関係法令・労働衛生の両方から数値・対象・頻度が問われます。「誰が・いつ・何を・どう保存するか」で整理すると暗記しやすくなります。</p>
<h2>種類の整理</h2>
<ul>
<li>定期健康診断（対象者・項目・頻度）</li>
<li>特定健康診断・特定業務従事者の健康診断</li>
<li>雇入時・退職時の健康診断</li>
<li>結果の保存・通知・措置</li>
</ul>
<h2>試験対策</h2>
<p>数値は<a href="/articles/ichimon-ittou-guide.html">一問一答</a>、事例は<a href="/q/index.html">過去問</a>で反復。<a href="/articles/tokutei-gyomu-kenko.html">特定業務健診</a>は別記事で深掘りします。</p>
""",
            "related": [
                ("tokutei-gyomu-kenko.html", "特定業務の健康診断"),
                ("kankei-hourei-benkyou.html", "関係法令"),
                ("machigai-chui-ten.html", "よく間違える論点"),
            ],
        },
        "tokutei-gyomu-kenko": {
            "title": "特定業務従事者の健康診断とは【試験で問われる範囲】",
            "description": "特定業務従事者の健康診断の対象業務・検査項目・頻度など、第一種衛生管理者試験で問われるポイントを解説します。",
            "category": "科目別",
            "body": """
<p>特定業務（有機溶剤・鉛・四アルキル鉛・特定化学物質・粉じん・石綿など）に従事する労働者には、<strong>特定業務従事者の健康診断</strong>が求められます。試験では業務と健診内容の組合せが頻出です。</p>
<h2>覚え方</h2>
<ul>
<li>業務の種類ごとに「対象者・項目・頻度」を表にする</li>
<li>定期健診との違い（追加項目・頻度）を意識</li>
<li>事業者の措置義務（就業制限・配置転換等）とセット</li>
</ul>
<p>用語：<a href="/terms/tokutei-gyo-mu-kenko-shindan.html">特定業務従事者の健康診断</a>、<a href="/articles/kenko-shindan-guide.html">健康診断全般</a>。</p>
""",
            "related": [
                ("kenko-shindan-guide.html", "健康診断の試験対策"),
                ("kagaku-busshitsu-taisaku.html", "化学物質管理"),
                ("rodoeisei-benkyou.html", "労働衛生の勉強法"),
            ],
        },
        "stress-check-taisaku": {
            "title": "第一種衛生管理者・ストレスチェックの試験対策【メンタルヘルス】",
            "description": "ストレスチェック制度・高ストレス者への対応など、メンタルヘルス関連の試験論点を整理します。",
            "category": "科目別",
            "body": """
<p>ストレスチェックは、比較的新しい論点ですが出題が増えています。実施義務・実施方法・結果の取扱い・高ストレス者への措置を整理しましょう。</p>
<h2>押さえるポイント</h2>
<ul>
<li>実施対象（常時雇用者数等の区分）</li>
<li>実施者・実施方法・面接指導</li>
<li>事業者・労働者の権利義務</li>
<li>個人情報・プライバシーの配慮</li>
</ul>
<p>関連：<a href="/terms/stress-check.html">ストレスチェック</a>、<a href="/terms/anzen-eisei-kyoiku.html">安全衛生教育</a>。</p>
""",
            "related": [
                ("rodoeisei-benkyou.html", "労働衛生（有害以外）"),
                ("kankei-hourei-benkyou.html", "関係法令"),
                ("kakomon-theme-frequency.html", "出題傾向"),
            ],
        },
        "netchu-wbgt-guide": {
            "title": "第一種衛生管理者・温熱・WBGT・暑熱順化【労働生理と法令】",
            "description": "WBGT・暑熱順化措置・熱中症予防など、温熱環境に関する試験対策を労働生理と法令の両面から解説します。",
            "category": "科目別",
            "body": """
<p>温熱・暑熱は、労働生理の計算問題と、関係法令の措置義務の両方から出題されます。夏季試験前は特に復習価値が高いテーマです。</p>
<h2>労働生理側</h2>
<ul>
<li>WBGTの構成（乾球・湿球・黒球）</li>
<li>代謝率・服装・作業強度</li>
<li>熱中症のメカニズム・予防</li>
</ul>
<h2>法令・実務側</h2>
<ul>
<li>暑熱順化措置・熱中症対策（最新の告示・ガイドラインを確認）</li>
<li>水分補給・休息・教育</li>
</ul>
<p><a href="/terms/wbgt-necchu-jyunka.html">WBGTと熱中症</a>、<a href="/articles/rodoseiri-benkyou.html">労働生理の勉強法</a>。</p>
""",
            "related": [
                ("rodoseiri-benkyou.html", "労働生理の勉強法"),
                ("machigai-chui-ten.html", "計算・ひっかけ対策"),
                ("chokuzen-1kagetsu.html", "直前1ヶ月"),
            ],
        },
        "shukkin-dokugaku-jikan": {
            "title": "仕事しながら第一種衛生管理者を目指す【時間の作り方・学習習慣】",
            "description": "社会人が仕事と両立しながら第一種衛生管理者試験に合格するための時間確保・学習習慣・モチベーション管理を解説します。",
            "category": "勉強法",
            "body": """
<p>衛生管理者試験の受験者は社会人が多く、毎日まとまった勉強時間が取れない人も少なくありません。<strong>短時間の反復</strong>と<strong>週末の過去問</strong>の組み合わせが現実的です。</p>
<h2>時間の作り方</h2>
<ul>
<li>通勤・昼休み：一問一答10〜15問</li>
<li>帰宅後30分：その日の×問題だけ復習</li>
<li>週末2〜3時間：過去問を区分単位で</li>
</ul>
<h2>計画の立て方</h2>
<p><a href="/articles/benkyou-jikan.html">勉強時間の目安</a>を読み、試験日から逆算。2〜3ヶ月プランなら<a href="/articles/benkyou-junban.html">勉強の順番</a>に沿って進めます。</p>
<h2>続けるコツ</h2>
<p>完璧主義をやめ、学習記録を可視化（アプリの連続学習日数など）。<a href="/">一衛マスター</a>で隙間時間学習が可能です。</p>
""",
            "related": [
                ("benkyou-jikan.html", "勉強時間・学習計画"),
                ("dokugaku-guide.html", "独学合格ガイド"),
                ("textbook-senmon.html", "テキスト・通信講座"),
            ],
        },
        "orig-mondai-guide": {
            "title": "第一種衛生管理者・実践演習の使い方【本番前の実力チェック】",
            "description": "一衛マスターの実践演習の活用法。過去問との違い、いつ解くべきかを解説します。",
            "category": "勉強法",
            "body": """
<p>過去問に加え、<strong>実践演習</strong>で「見たことのない切り口」を試すと、本番での応用力が身につきやすくなります。一衛マスターでは学習トップの実践演習から利用できます。</p>
<h2>過去問との使い分け</h2>
<table><thead><tr><th></th><th>過去問</th><th>実践演習</th></tr></thead><tbody>
<tr><td>目的</td><td>出題傾向・形式の把握</td><td>理解度の確認・応用</td></tr>
<tr><td>タイミング</td><td>学習の中心（複数周）</td><td>1周目後〜直前の弱点補強</td></tr>
</tbody></table>
<h2>おすすめの進め方</h2>
<ol>
<li>過去問1周後、苦手科目だけ実践演習を20〜30問</li>
<li>正答率が安定したら本番形式の模擬へ</li>
</ol>
<p><a href="/articles/kakomon-kakaikata.html">過去問の回し方</a>、静的ページは<a href="/q/index.html">過去問一覧</a>。</p>
""",
            "related": [
                ("dokugaku-guide.html", "独学合格ガイド"),
                ("kakomon-kakaikata.html", "過去問の回し方"),
                ("chokuzen-1kagetsu.html", "直前1ヶ月"),
            ],
        },
        "sangyoui-senmon-eisei": {
            "title": "産業医と衛生管理者の違い【試験範囲と職場での役割】",
            "description": "産業医と衛生管理者（第一種・第二種）の役割の違い、試験で学ぶ範囲の違いを整理します。",
            "category": "試験概要",
            "body": """
<p>職場の健康管理では<strong>産業医</strong>と<strong>衛生管理者</strong>が連携しますが、資格・選任要件・業務内容は異なります。試験学習でも混同しやすいので整理しておきましょう。</p>
<h2>主な違い（概要）</h2>
<table><thead><tr><th></th><th>産業医</th><th>衛生管理者</th></tr></thead><tbody>
<tr><td>資格</td><td>医師免許が前提</td><td>試験合格等</td></tr>
<tr><td>中心業務</td><td>医学的管理・意見</td><td>労働衛生上の管理・指導</td></tr>
<tr><td>試験</td><td>別資格（医師）</td><td>第一種・第二種衛生管理者試験</td></tr>
</tbody></table>
<h2>試験で問われること</h2>
<p>衛生管理者試験では、産業医の選任・委託・権限と衛生管理者の役割の<strong>分担</strong>が問われることがあります。<a href="/articles/anzen-eisei-taisei.html">安全衛生管理体制</a>とあわせて学習。</p>
""",
            "related": [
                ("eisei-kanrisha-gyoumu.html", "衛生管理者の仕事"),
                ("anzen-eisei-taisei.html", "管理体制"),
                ("juken-shikaku.html", "受験資格"),
            ],
        },
        "horei-kaisei-benkyou": {
            "title": "第一種衛生管理者・法令改正の追い方【最新版テキストの見方】",
            "description": "労働安全衛生関係法令の改正を試験対策に反映する方法、テキスト選び・過去問との関係を解説します。",
            "category": "勉強法",
            "body": """
<p>法令は改正されます。試験は<strong>受験する回の時点で有効な法令</strong>に基づいて出題されます。古いテキストや古い過去問解説だけに頼ると誤答の原因になります。</p>
<h2>改正情報の確認先</h2>
<ul>
<li>試験協会の試験要項・問題の範囲</li>
<li>厚生労働省の法令・告示・通達</li>
<li>テキストの改訂版（発行年・改訂履歴を確認）</li>
</ul>
<h2>学習への入れ方</h2>
<ol>
<li>テキストはできるだけ新しい版を使う</li>
<li>改正箇所は付箋で「試験で変わる数値」だけ抜き出す</li>
<li>過去問は「考え方」は有効、数値は最新法令で上書き</li>
</ol>
<p>数値の確認は<a href="/articles/ichimon-ittou-guide.html">一問一答</a>と<a href="https://www.mhlw.go.jp/" target="_blank" rel="noopener noreferrer">厚生労働省</a>の公式情報を併用。</p>
""",
            "related": [
                ("kankei-hourei-benkyou.html", "関係法令の勉強法"),
                ("textbook-senmon.html", "テキストの選び方"),
                ("shiken-guide.html", "試験ガイド"),
            ],
        },
    }
    if slug not in data:
        raise KeyError(slug)
    return data[slug]


def render_related_box(related: list[tuple[str, str]]) -> str:
    if not related:
        return ""
    links = "\n".join(
        f'    <a class="related-link" href="/articles/{h}">{label}</a>'
        for h, label in related
    )
    return f"""
<div class="related-box">
  <div class="related-box-title">関連記事</div>
  <div class="related-links">
{links}
  </div>
</div>"""




def build_article_html(slug: str, meta: dict) -> str:
    title = meta["title"]
    desc = meta["description"]
    category = meta["category"]
    body = meta["body"].strip()
    related = meta.get("related", [])
    url = f"{BASE}/articles/{slug}.html"
    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "@id": f"{BASE}/#website",
                "url": f"{BASE}/",
                "name": "一衛マスター",
                "description": "第一種衛生管理者試験 無料学習プラットフォーム",
                "inLanguage": "ja",
            },
            {
                "@type": "Article",
                "@id": f"{url}#article",
                "headline": title,
                "description": desc,
                "dateModified": DATE_MODIFIED,
                "inLanguage": "ja",
                "isPartOf": {"@id": f"{BASE}/#website"},
                "publisher": {
                    "@type": "Organization",
                    "name": "一衛マスター",
                    "url": BASE + "/",
                },
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": 1,
                        "name": "トップ",
                        "item": f"{BASE}/",
                    },
                    {
                        "@type": "ListItem",
                        "position": 2,
                        "name": "試験・学習ガイド",
                        "item": f"{BASE}/articles/",
                    },
                    {
                        "@type": "ListItem",
                        "position": 3,
                        "name": title,
                        "item": url,
                    },
                ],
            },
        ],
    }
    related_html = render_related_box(related)
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:locale" content="ja_JP">
<meta property="og:site_name" content="一衛マスター">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<script type="application/ld+json">
{json.dumps(ld, ensure_ascii=False, indent=2)}
</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
{ARTICLE_CSS}
</style>
</head>
<body>
<header class="site-header">
  <div class="site-header-inner">
    <a href="/" class="header-back"><svg viewBox="0 0 24 24"><polyline points="15 18 9 12 15 6"/></svg>学習トップ</a>
    <span class="header-sep">›</span>
    <a href="/" class="header-logo">一衛マスター</a>
  </div>
</header>
<div class="page-wrap">
  <nav class="breadcrumb" aria-label="パンくず">
    <a href="/">トップ</a><span class="breadcrumb-sep">›</span><a href="/articles/">試験・学習ガイド</a><span class="breadcrumb-sep">›</span><span>{title}</span>
  </nav>
  <div class="article-meta">
    <span class="meta-category">{category}</span>
    <span class="meta-updated">更新日：{DATE_MODIFIED}</span>
  </div>
  <h1 class="article-title">{title}</h1>
  <article class="article-body">
{body}
{related_html}
  </article>
</div>
<footer class="site-footer">
  <a href="/">トップ</a> ・ <a href="/q/index.html">過去問一覧</a> ・ <a href="/terms/">用語集</a> ・ <a href="/articles/">試験ガイド</a> ・ <a href="/about.html">このサイトについて</a> ・ <a href="/related-sites.html">関連サイト</a> ・ <a href="/privacy-terms.html">プライバシー</a>
  <div style="margin-top:10px">第一種衛生管理者試験 無料学習プラットフォーム</div>
</footer>
</body>
</html>
"""


def build_index_html() -> str:
    n = len(INDEX_ENTRIES)
    items = "\n".join(
        f'    <li><a href="/articles/{slug}.html">{title}</a></li>'
        for slug, title in INDEX_ENTRIES
    )
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>試験・学習ガイド一覧｜一衛マスター（第一種衛生管理者試験）</title>
<meta name="description" content="第一種衛生管理者試験の受験資格・試験科目・合格基準・勉強法・試験当日の注意点など、試験対策の解説記事一覧です。">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{BASE}/articles/">
<meta property="og:type" content="website">
<meta property="og:url" content="{BASE}/articles/">
<meta property="og:title" content="試験・学習ガイド一覧｜一衛マスター">
<meta property="og:description" content="第一種衛生管理者試験の受験資格・試験科目・合格基準・勉強法・試験当日の注意点など、試験対策の解説記事一覧です。">
<meta property="og:locale" content="ja_JP">
<meta property="og:site_name" content="一衛マスター">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
{ARTICLE_CSS}
</style>
</head>
<body>
<header class="site-header">
  <div class="site-header-inner">
    <a href="/" class="header-back"><svg viewBox="0 0 24 24"><polyline points="15 18 9 12 15 6"/></svg>学習トップ</a>
    <span class="header-sep">›</span>
    <a href="/" class="header-logo">一衛マスター</a>
  </div>
</header>
<div class="page-wrap">
  <nav class="breadcrumb" aria-label="パンくず">
    <a href="/">トップ</a><span class="breadcrumb-sep">›</span><span>試験・学習ガイド一覧</span>
  </nav>
  <h1 class="article-title">試験・学習ガイド一覧</h1>
  <p class="idx-intro">受験資格・試験科目・合格基準・勉強の進め方など、第一種衛生管理者試験の<strong>横断的な解説記事</strong>をまとめています。用語ごとの詳細は<a href="/terms/">用語解説一覧</a>、過去問の静的URL一覧は<a href="/q/index.html">過去問一覧</a>、問題演習は<a href="/">学習トップ</a>から利用できます。</p>
  <p class="idx-count">全 {n} 本（静的HTML）</p>
  <ul class="idx-list" id="article-index-list">
{items}
  </ul>
</div>
<footer class="site-footer">
  <a href="/">トップ</a> ・ <a href="/q/index.html">過去問一覧</a> ・ <a href="/terms/">用語集</a> ・ <a href="/articles/">試験ガイド</a> ・ <a href="/about.html">このサイトについて</a> ・ <a href="/related-sites.html">関連サイト</a> ・ <a href="/privacy-terms.html">プライバシー</a>
  <div style="margin-top:10px">第一種衛生管理者試験 無料学習プラットフォーム</div>
</footer>
</body>
</html>
"""


def write_articles_sitemap(out: Path) -> None:
    urls = [f"{BASE}/articles/"]
    for slug, _ in INDEX_ENTRIES:
        urls.append(f"{BASE}/articles/{slug}.html")
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for u in sorted(set(urls)):
        lines.append("  <url>")
        lines.append(f"    <loc>{xml_escape.escape(u)}</loc>")
        lines.append("    <changefreq>monthly</changefreq>")
        lines.append("  </url>")
    lines.append("</urlset>")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    for slug in sorted(GENERATED_SLUGS):
        meta = article_meta(slug)
        path = ARTICLES_DIR / f"{slug}.html"
        path.write_text(build_article_html(slug, meta), encoding="utf-8")
        print(f"  {path.name}")
    index_path = ARTICLES_DIR / "index.html"
    index_path.write_text(build_index_html(), encoding="utf-8")
    print(f"  {index_path.name}（{len(INDEX_ENTRIES)} 本）")
    sitemap_path = ROOT / "sitemap-articles.xml"
    write_articles_sitemap(sitemap_path)
    print(f"  {sitemap_path.name}（{len(INDEX_ENTRIES) + 1} URL）")


if __name__ == "__main__":
    main()
