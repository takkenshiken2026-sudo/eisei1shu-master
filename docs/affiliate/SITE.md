# アフィリエイト運用メモ — 一衛マスター（eisei1shu-master）

手順の正本: [exam-site-shell `multi-site-affiliate-workflow.md`](https://github.com/takkenshiken2026-sudo/exam-site-shell/blob/main/docs/affiliate/multi-site-affiliate-workflow.md)

## サイト情報

| 項目 | 値 |
|------|-----|
| site-id | `eisei1shu-master` |
| ドメイン | https://eisei1shu-master.jp |
| 棚卸し日 | 2026-06-14 |
| テンプレ drift | ok=130 / drift=28 / total=158（`guide_index_picks_ui.py` 等未同期） |

---

## フェーズA 棚卸し結果（2026-06-14）

### サマリー

| 指標 | 値 |
|------|-----|
| アフィリエイト行（CSV） | 11 |
| `content_status=published` | 3 |
| **ASPリンク済み（CSV判定）** | **4** |
| **比較記事 HTML 生成** | **4**（hub付き3 + 導線記事1） |
| brief YAML | 5 |
| `images/affiliate/` | 9 webp + 2 jpg |
| `guideIndexPicks` | **設定済み**（grid-3・3枚） |
| 通常ガイド published | 170 |
| 通常ガイド → 比較記事（related_links） | **59** |
| 通常ガイド → 比較記事（本文 slug） | **59** |

### 重要な発見（要修正）

`published` の3本は **brief に ASP URL があるが、CSV の `related_links` / 本文に `https://` が無い**。

ビルドは `affiliate_article_is_buildable()` で **CSV 内の ASP のみ** を見るため、**HTML が一切生成されていない**（`validate_csv.py` も WARN）。

→ フェーズB/C の最優先: 公開3本の `related_links` 末尾に ASP URL 行を追加し、`build_article_pages.py` で HTML を生成する。

---

## 公開済み比較記事（CSV上 published・要 ASP 行追加）

| slug | brief | 画像 | 備考 |
|------|-------|------|------|
| `affiliate-textbooks-recommend` | あり（Amazon×3） | webp×3 | 手書きリライト済み。CSV に ASP 行なし |
| `affiliate-online-course-compare` | あり（A8 SMART・オンスク） | jpg×2 | 手書きリライト済み。CSV に ASP 行なし |
| `affiliate-dokugaku-goukaku-hokan` | あり | — | サイト固有 slug（独学×講座）。CSV に ASP 行なし |

## draft（次に公開候補）

| slug | brief | 内容 | ブロッカー |
|------|-------|------|------------|
| `affiliate-problem-books` | あり | 本文かなり執筆済み | `related_links` に Amazon URL + `published` |
| `affiliate-beginner-material-set` | あり | 本文かなり執筆済み | 同上 |
| `affiliate-correspondence-course` | なし | テンプレ placeholder | 全面リライト + ASP |
| 他6 slug | なし/一部 | テンプレ placeholder | ASP 確定まで触らない |

---

## guideIndexPicks

- **現状:** `site-config.json` にキーなし
- **目標:** 公開比較記事が **最低2本**（テキスト+講座）になってから `grid-3` で3枚導入
- **想定 href:**
  - course → `affiliate-online-course-compare/`
  - textbook → `affiliate-textbooks-recommend/`
  - problem-book → `affiliate-problem-books/`（公開後）

---

## 通常ガイド導線

- **完了（2026-06-14）:** 59本（`apply_affiliate_funnel_expansion.py`）
- **優先接続候補（slug）:** `dokugaku-guide`, `benkyou-junban`, `kakomon-kakaikata`, `textbook-selection`, `problem-book-selection`, `correspondence-course-guide`, `benkyou-jikan`
- **除外:** `goukakuritsu`, `after-pass-procedure`, `career-after-qualification`, `exam-venue-and-region`, `compare-similar-qualifications`

---

## ASP メモ（非公開）

- Amazon Associates: `tag=ue083093-22`（`original_note` / brief に記載済み）
- A8: SMART合格講座・オンスク（`affiliate-online-course-compare.yaml`）

---

## ロールアウト進捗

| フェーズ | 状態 | 完了日 | 備考 |
|----------|------|--------|------|
| A 現状把握 | **完了** | 2026-06-14 | 本ファイル |
| B エンジン同期 | **完了** | 2026-06-14 | sync 27 + affiliate_links 補完 + build_all OK |
| C 比較記事公開（HTML生成） | **完了** | 2026-06-14 | 3本 HTML。textbooks/online-course に hub |
| D guideIndexPicks | **完了** | 2026-06-14 | grid-3・3ハブ・3枚 | |
| E 通常ガイド導線 | **完了** | 2026-06-14 | 59/170 |
| F 比較記事4本 | **完了** | 2026-06-14 | 4本公開・相互リンク | |
| G 本番確認 | **完了** | 2026-06-12 | build_all 完走・検証 OK |

### フェーズG 結果（2026-06-12）

- `affiliate-problem-books` に FAQ 3問を追加（`validate_generated_seo.py` ブロッカー解消）
- **`build_all.py` 完走** — 全 validate OK
- 公開比較記事 **4本**（ASP·HTML すべてあり）
- `guideIndexPicks` grid-3 — `articles/` `terms/` `q/` 確認済み
- 通常ガイド導線 59/170 — `dokugaku-guide` 等で比較記事へ接続確認
- フッターに比較記事一括リンクなし（設計どおり）
- **次:** `git push` → CI 5〜7分 → 本番目視（`/articles/affiliate-textbooks-recommend/` `/articles/` `dokugaku-guide`）

### フェーズB 結果（2026-06-14）

- `sync_from_template.py --build`: 27ファイル同期（初回は `is_affiliate_skip_section` 欠落で失敗）
- テンプレ `affiliate_links.py` を takken 版で補完 → 本番へ反映
- `build_guide_retire_redirects.py` を追加（`build_all` 必須）
- **`build_all.py` 完走**（validate すべて OK）
- 比較記事 HTML: 依然 **0**（ASP CSV 未設定のため skip 11 — 想定どおり）

### フェーズC 結果（2026-06-14）

`related_links` 末尾に ASP URL を追加:

| slug | ASP 行 |
|------|--------|
| `affiliate-textbooks-recommend` | Amazon（スッキリわかる dp/4300121265） |
| `affiliate-online-course-compare` | A8 SMART合格講座 |
| `affiliate-dokugaku-goukaku-hokan` | A8 SMART合格講座 |

ビルド結果:

| slug | HTML | 比較 hub | 画像 |
|------|------|----------|------|
| `affiliate-textbooks-recommend` | あり | あり | webp×3 |
| `affiliate-online-course-compare` | あり | あり | jpg×2 |
| `affiliate-dokugaku-goukaku-hokan` | あり | なし（product-comparison brief なし） | — |

- `validate_internal_links.py`: OK（3196 files）
- 試験ガイド一覧: 173本（+3）

### フェーズD 結果（2026-06-14）

`site-config.json` に `guideIndexPicks` を追加（layout: `grid-3`、3枚）。

| kind | href | image |
|------|------|-------|
| 講座 | `affiliate-online-course-compare/` | `eisei1-smart-goukaku.jpg` |
| テキスト | `affiliate-textbooks-recommend/` | `eisei1-book-4300121265.webp` |
| 問題集 | `affiliate-problem-books/` | `eisei1-book-4426616565.webp` |

**3枚目の前提:** `affiliate-problem-books` を ASP 追加 + `published` 化（比較記事4本目）。

3ハブ index に同一カードを確認:

- `/articles/index.html` — `hub-promo--grid-3` ✅
- `/terms/index.html` — ✅
- `/q/index.html` — ✅

`validate_site_integration.py`: OK

### フェーズE 結果（2026-06-14）

`tools/apply_affiliate_funnel_expansion.py` で学習系 **59本** に導線追加。

| 指標 | 値 |
|------|-----|
| `related_links` → 比較記事 | **59 / 170** |
| 本文 slug → 比較記事 | **59 / 170** |
| 比較記事相互リンク | 4本更新 |

**マッピング例**

| 意図 | 比較記事 |
|------|----------|
| テキスト・教材選び | `affiliate-textbooks-recommend` |
| 過去問・演習・分野攻略 | `affiliate-problem-books` |
| 通信・社会人・学習計画 | `affiliate-online-course-compare` |
| 独学可否・勉強時間 | `affiliate-dokugaku-goukaku-hokan` |

**意図的に未接続（11本程度）:** 合格率·合格後·会場·他資格比較·再受験専用など `EXCLUDE_SLUGS`

`validate_internal_links.py`: OK

### 次のアクション

1. `git push` → CI 完了後に本番目視（比較記事·3ハブ·通常ガイド導線）
2. 必要なら比較記事5本目以降を段階公開（通信講座比較 draft 等）
