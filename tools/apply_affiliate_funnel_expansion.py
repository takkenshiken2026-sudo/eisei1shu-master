#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""学習系ガイドへ比較記事導線を追加し、公開済み affiliate 4本の相互リンクを整える。"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "guide_articles.csv"

AFFILIATE_TITLES = {
    "affiliate-textbooks-recommend": "第一種衛生管理者のおすすめ参考書・テキスト3選【2026年度版・独学】",
    "affiliate-problem-books": "第一種衛生管理者のおすすめ問題集3選【過去問・予想模試2026】",
    "affiliate-online-course-compare": "第一種衛生管理者のオンライン講座比較【SMART合格講座 vs オンスク】独学との併用",
    "affiliate-dokugaku-goukaku-hokan": "第一種衛生管理者は独学で合格できる？勉強時間の目安と通信講座が効くケース",
    "affiliate-mock-exam-materials": "第一種衛生管理者試験の模試・予想問題3選【100問本番形式2026】",
    "affiliate-beginner-material-set": "第一種衛生管理者の初学者向け教材セット3選【速習・要点整理2026】",
}

BODY = {
    "affiliate-textbooks-recommend": (
        "テキスト1冊は、affiliate-textbooks-recommend で出版社別の解説量を比較してから固定すると途中で変えずに済みます。"
    ),
    "affiliate-problem-books": (
        "演習1冊は、affiliate-problem-books で収録形式と解説量を比較してから週次計画に組み込むと迷いが減ります。"
    ),
    "affiliate-online-course-compare": (
        "独学が続かない分野は、affiliate-online-course-compare でSMARTとオンスクの学習設計を比較し、過去問演習量は維持したまま1社に絞ると続きやすいです。"
    ),
    "affiliate-dokugaku-goukaku-hokan": (
        "独学で足りるか迷う場合は、affiliate-dokugaku-goukaku-hokan で勉強時間の目安と講座が効くケースを先に確認すると教材投資の判断がしやすいです。"
    ),
    "affiliate-mock-exam-materials": (
        "本番形式の模試1冊は、affiliate-mock-exam-materials でユーキャン予想模試·成美堂過去6回·"
        "労基団連問題集の3冊を比較してから固定すると、"
        "13:30開始·100問·180分の模試回数と使い分けが整理しやすくなります。"
    ),
    "affiliate-beginner-material-set": (
        "初学者の第1冊は、affiliate-beginner-material-set でユーキャン速習·集中レッスン·これだけ覚えるの3冊を"
        "学習フェーズ別に比較してから固定すると、"
        "速習→本格テキストへの段階投入がぶれにくくなります。"
    ),
}

# slug → (primary_affiliate, section_n)
GUIDE_AFFILIATE: dict[str, tuple[str, int]] = {
    # 独学対策
    "dokugaku-guide": ("affiliate-dokugaku-goukaku-hokan", 2),
    "benkyou-jikan": ("affiliate-dokugaku-goukaku-hokan", 2),
    "benkyou-junban": ("affiliate-beginner-material-set", 2),
    "textbook-selection": ("affiliate-textbooks-recommend", 2),
    "textbook-senmon": ("affiliate-textbooks-recommend", 2),
    "textbook-vs-past-questions": ("affiliate-textbooks-recommend", 2),
    "problem-book-selection": ("affiliate-problem-books", 2),
    "correspondence-course-guide": ("affiliate-online-course-compare", 2),
    "kakomon-kakaikata": ("affiliate-problem-books", 2),
    "ichimon-ittou-guide": ("affiliate-beginner-material-set", 2),
    "orig-mondai-guide": ("affiliate-problem-books", 2),
    "free-materials-online": ("affiliate-textbooks-recommend", 2),
    "material-update-cycle": ("affiliate-textbooks-recommend", 2),
    "self-study-start": ("affiliate-dokugaku-goukaku-hokan", 2),
    "self-study-schedule": ("affiliate-online-course-compare", 2),
    "self-study-environment": ("affiliate-dokugaku-goukaku-hokan", 2),
    "self-study-motivation": ("affiliate-dokugaku-goukaku-hokan", 2),
    "self-study-mistakes": ("affiliate-problem-books", 2),
    "self-study-without-school": ("affiliate-online-course-compare", 2),
    "shukkin-dokugaku-jikan": ("affiliate-online-course-compare", 2),
    "hoken-shi-juken": ("affiliate-online-course-compare", 2),
    "horei-kaisei-benkyou": ("affiliate-textbooks-recommend", 2),
    "nishu-kara-ichishu": ("affiliate-textbooks-recommend", 2),
    "machigai-chui-ten": ("affiliate-problem-books", 2),
    # 学習計画
    "study-plan-3months": ("affiliate-textbooks-recommend", 2),
    "study-plan-6months": ("affiliate-textbooks-recommend", 2),
    "study-plan-1year": ("affiliate-textbooks-recommend", 2),
    "study-plan-working": ("affiliate-online-course-compare", 2),
    "study-plan-beginner": ("affiliate-beginner-material-set", 2),
    "first-30-days-plan": ("affiliate-beginner-material-set", 2),
    "balance-work-study": ("affiliate-online-course-compare", 2),
    "time-management": ("affiliate-online-course-compare", 2),
    # 過去問活用
    "past-questions-by-year": ("affiliate-problem-books", 2),
    "past-questions-by-field": ("affiliate-problem-books", 2),
    "past-questions-review-cycle": ("affiliate-problem-books", 2),
    "past-questions-score-analysis": ("affiliate-problem-books", 2),
    "past-questions-first-attempt": ("affiliate-problem-books", 2),
    "past-questions-wrong-reasons": ("affiliate-problem-books", 2),
    "past-questions-latest-year": ("affiliate-problem-books", 2),
    "bookmark-review-method": ("affiliate-problem-books", 2),
    "mock-exam-how-to": ("affiliate-mock-exam-materials", 3),
    "ichimon-practice": ("affiliate-problem-books", 2),
    "drill-volume-guide": ("affiliate-problem-books", 2),
    "timed-practice": ("affiliate-mock-exam-materials", 3),
    "simulation-exam-schedule": ("affiliate-mock-exam-materials", 2),
    "time-limit-strategy": ("affiliate-mock-exam-materials", 2),
    # 分野別（過去問フォーカス）
    "field-eisei-harm-past-question-focus": ("affiliate-problem-books", 2),
    "field-eisei-other-past-question-focus": ("affiliate-problem-books", 2),
    "field-law-harm-past-question-focus": ("affiliate-problem-books", 2),
    "field-law-other-past-question-focus": ("affiliate-problem-books", 2),
    "field-physio-past-question-focus": ("affiliate-problem-books", 2),
    # 直前（模試・演習）
    "final-mock-last-run": ("affiliate-mock-exam-materials", 2),
    "chokuzen-1kagetsu": ("affiliate-problem-books", 2),
    "chokuzen-1shukan": ("affiliate-problem-books", 2),
    # 復習
    "review-cycle-spaced": ("affiliate-problem-books", 2),
    "mistake-notebook": ("affiliate-problem-books", 2),
    "plateau-breakthrough": ("affiliate-dokugaku-goukaku-hokan", 2),
    # 試験概要（学習導線あり）
    "first-time-exam-guide": ("affiliate-dokugaku-goukaku-hokan", 2),
    "shiken-guide": ("affiliate-textbooks-recommend", 2),
    "goukaku-kijun": ("affiliate-problem-books", 2),
}

# 意図的に繋がない
EXCLUDE_SLUGS = frozenset({
    "pass-rate",
    "pass-rate-how-to-read",
    "goukakuritsu",
    "pass-score",
    "exam-difficulty",
    "difficulty-for-beginners",
    "after-pass-procedure",
    "career-after-qualification",
    "registration-after-pass",
    "pass-announcement-guide",
    "goukaku-go-tetsuzuki",
    "exam-venue-and-region",
    "compare-similar-qualifications",
    "fail-retry-plan",
    "retake-strategy",
    "retake-schedule-adjustment",
    "saijuken-guide",
})

# 2本目 related（任意）
SECONDARY_AFFILIATE: dict[str, str] = {
    "dokugaku-guide": "affiliate-textbooks-recommend",
    "correspondence-course-guide": "affiliate-dokugaku-goukaku-hokan",
    "kakomon-kakaikata": "affiliate-textbooks-recommend",
    "study-plan-working": "affiliate-dokugaku-goukaku-hokan",
    "textbook-selection": "affiliate-problem-books",
    "problem-book-selection": "affiliate-textbooks-recommend",
    "study-plan-beginner": "affiliate-textbooks-recommend",
    "benkyou-junban": "affiliate-textbooks-recommend",
    "mock-exam-how-to": "affiliate-problem-books",
    "timed-practice": "affiliate-problem-books",
}

AFFILIATE_CROSS_LINKS: dict[str, list[str]] = {
    "affiliate-textbooks-recommend": [
        "dokugaku-guide:独学合格ガイド",
        "benkyou-junban:勉強の順番",
        "kakomon-kakaikata:過去問の回し方",
        "affiliate-problem-books:おすすめ問題集",
        "affiliate-beginner-material-set:初学者向け教材セット",
        "affiliate-online-course-compare:オンライン講座比較",
        "affiliate-dokugaku-goukaku-hokan:独学合格と講座の併用",
    ],
    "affiliate-problem-books": [
        "kakomon-kakaikata:過去問の回し方",
        "dokugaku-guide:独学合格ガイド",
        "goukaku-kijun:合格基準",
        "affiliate-textbooks-recommend:おすすめテキスト",
        "affiliate-mock-exam-materials:模試・予想問題",
        "affiliate-online-course-compare:オンライン講座比較",
        "affiliate-dokugaku-goukaku-hokan:独学合格と講座の併用",
    ],
    "affiliate-online-course-compare": [
        "dokugaku-guide:独学合格ガイド",
        "correspondence-course-guide:通信講座の選び方",
        "benkyou-jikan:勉強時間",
        "affiliate-textbooks-recommend:おすすめテキスト",
        "affiliate-problem-books:おすすめ問題集",
        "affiliate-beginner-material-set:初学者向け教材セット",
        "affiliate-dokugaku-goukaku-hokan:独学合格と講座の併用",
    ],
    "affiliate-dokugaku-goukaku-hokan": [
        "dokugaku-guide:独学合格ガイド",
        "benkyou-jikan:勉強時間",
        "kakomon-kakaikata:過去問の回し方",
        "affiliate-textbooks-recommend:おすすめテキスト",
        "affiliate-problem-books:おすすめ問題集",
        "affiliate-beginner-material-set:初学者向け教材セット",
        "affiliate-online-course-compare:オンライン講座比較",
    ],
    "affiliate-mock-exam-materials": [
        "mock-exam-how-to:模試の活用法",
        "timed-practice:時間を計った演習",
        "kakomon-kakaikata:過去問の回し方",
        "affiliate-problem-books:おすすめ問題集",
        "affiliate-textbooks-recommend:おすすめテキスト",
        "goukaku-kijun:合格基準",
    ],
    "affiliate-beginner-material-set": [
        "benkyou-junban:勉強の順番",
        "study-plan-beginner:初学者向け学習計画",
        "ichimon-ittou-guide:一問一答の使い方",
        "affiliate-textbooks-recommend:おすすめテキスト",
        "affiliate-problem-books:おすすめ問題集",
        "affiliate-online-course-compare:オンライン講座比較",
    ],
}


def _split_related(value: str) -> list[str]:
    return [x.strip() for x in (value or "").split(";") if x.strip()]


def _append_related(value: str, token: str) -> str:
    parts = _split_related(value)
    slug = token.split(":", 1)[0]
    if any(p.split(":", 1)[0] == slug for p in parts):
        return ";".join(parts)
    parts.append(token)
    return ";".join(parts)


def _merge_affiliate_related(existing: str, internal: list[str]) -> str:
    asp = [p for p in _split_related(existing) if p.startswith("http")]
    merged: list[str] = []
    seen: set[str] = set()
    for token in internal:
        slug = token.split(":", 1)[0]
        if slug in seen:
            continue
        seen.add(slug)
        merged.append(token)
    for token in asp:
        if token not in merged:
            merged.append(token)
    return ";".join(merged)


def _append_body(body: str, aff_slug: str) -> str:
    sentence = BODY[aff_slug]
    if aff_slug in (body or ""):
        return body
    text = (body or "").rstrip()
    if not text:
        return sentence
    if not text.endswith("。"):
        text += "。"
    return text + sentence


def apply_guide_updates(rows: list[dict[str, str]]) -> int:
    by_slug = {r["slug"]: r for r in rows}
    changed = 0
    for slug, (aff_slug, sec_n) in GUIDE_AFFILIATE.items():
        if slug in EXCLUDE_SLUGS:
            continue
        row = by_slug.get(slug)
        if not row or (row.get("content_status") or "").strip() != "published":
            continue
        body_key = f"section_{sec_n}_body"
        old_body = row.get(body_key, "")
        new_body = _append_body(old_body, aff_slug)
        if new_body != old_body:
            row[body_key] = new_body

        token = f"{aff_slug}:{AFFILIATE_TITLES[aff_slug]}"
        new_rl = _append_related(row.get("related_links", ""), token)
        sec = SECONDARY_AFFILIATE.get(slug)
        if sec:
            new_rl = _append_related(new_rl, f"{sec}:{AFFILIATE_TITLES[sec]}")
        if new_rl != row.get("related_links", "") or new_body != old_body:
            row["related_links"] = new_rl
            changed += 1
    return changed


def apply_affiliate_cross_links(rows: list[dict[str, str]]) -> int:
    by_slug = {r["slug"]: r for r in rows}
    changed = 0
    for slug, internal in AFFILIATE_CROSS_LINKS.items():
        row = by_slug.get(slug)
        if not row:
            continue
        new_rl = _merge_affiliate_related(row.get("related_links", ""), internal)
        if new_rl != row.get("related_links", ""):
            row["related_links"] = new_rl
            changed += 1
    return changed


def main() -> None:
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    if not fieldnames:
        raise SystemExit("guide_articles.csv: no header")

    g = apply_guide_updates(rows)
    a = apply_affiliate_cross_links(rows)

    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Guide funnel: {len(GUIDE_AFFILIATE)} targets, {g} row(s) updated")
    print(f"Affiliate cross-links: {a} row(s) updated")


if __name__ == "__main__":
    main()
