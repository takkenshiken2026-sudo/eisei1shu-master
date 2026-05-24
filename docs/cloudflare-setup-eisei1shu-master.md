# Cloudflare セットアップ（eisei1shu-master.jp）

## 現状（2026-05 時点）

| 項目 | 状態 |
|------|------|
| DNS | **ムームードメイン**（`dns01/02.muumuu-domain.com`） |
| 向き先 | GitHub Pages（`185.199.108.x` など） |
| CDN | GitHub / Fastly（`via: varnish`, `server: GitHub.com`） |
| `Cache-Control` | **`max-age=600`（10分）** — PageSpeed のキャッシュ警告の原因 |
| Cloudflare | **未使用**（`cf-ray` ヘッダーなし） |

Cloudflare のキャッシュルールは、**ドメインの DNS を Cloudflare 経由（プロキシ ON）にしたあと**でないと効きません。

---

## 手順 1 — Cloudflare にゾーンを追加

1. [Cloudflare ダッシュボード](https://dash.cloudflare.com/) → **サイトを追加**
2. ドメイン: `eisei1shu-master.jp`
3. プラン: Free で可
4. 表示された **ネームサーバー（2つ）** を控える（例: `ada.ns.cloudflare.com` など）

---

## 手順 2 — ムームードメインで NS を切り替え

1. [ムームードメイン](https://muumuu-domain.com/) にログイン
2. `eisei1shu-master.jp` → **ネームサーバー設定**
3. 「ムームーDNS」→ **他社ネームサーバー** に変更
4. Cloudflare から案内された **2つの NS** を入力して保存

反映まで **数時間〜最大 48 時間** かかることがあります。  
[WhatsMyDNS](https://www.whatsmydns.net/#NS/eisei1shu-master.jp) で NS が Cloudflare になったか確認してください。

---

## 手順 3 — Cloudflare DNS レコード（GitHub Pages）

ゾーン → **DNS** → **レコード** で次を設定します（プロキシは **オレンジ雲＝プロキシ済み**）。

| タイプ | 名前 | 内容 | プロキシ |
|--------|------|------|----------|
| `A` | `@` | `185.199.108.153` | プロキシ ON |
| `A` | `@` | `185.199.109.153` | プロキシ ON |
| `A` | `@` | `185.199.110.153` | プロキシ ON |
| `A` | `@` | `185.199.111.153` | プロキシ ON |
| `CNAME` | `www` | `takkenshiken2026-sudo.github.io`（実際の GitHub Pages ホスト名） | プロキシ ON |

GitHub リポジトリ → **Settings → Pages → Custom domain** に `eisei1shu-master.jp` が登録済みであることを確認してください。

**SSL/TLS** → 概要: **フル（厳密）** を推奨。  
**SSL/TLS** → エッジ証明書: Universal SSL が **Active** になるまで待つ。

---

## 手順 4 — キャッシュルール（UI）

**ルール** → **キャッシュルール** → **ルールを作成**

### ルール A（優先・上に配置）— HTML は短く

- **カスタムフィルター式**:
  ```
  (http.host eq "eisei1shu-master.jp" and (http.request.uri.path eq "/" or http.request.uri.path.extension eq "html"))
  ```
- **キャッシュの資格** → キャッシュする
- **エッジ TTL** → ブラウザ TTL に従う、または 2 時間
- **ブラウザ TTL** → `override_origin` → **0** または **120** 秒（HTML を長期固定しない）

### ルール B — JS / CSS は長く

- **カスタムフィルター式**:
  ```
  (http.host eq "eisei1shu-master.jp" and http.request.uri.path.extension in {"js" "css"})
  ```
- **キャッシュの資格** → キャッシュする
- **エッジ TTL** → 1 か月
- **ブラウザ TTL** → `override_origin` → **31536000**（1 年）

デプロイ時に `?v=<Git SHA>` が付くため（`prepare_public_site.sh` 内の `inject_spa_asset_version.py`）、内容更新後は URL が変わり古い JS が残りにくくなります。

---

## 手順 5 — API でルールを一括適用（任意）

Cloudflare API トークン（権限: Zone → Cache Rules → Edit、Zone → Zone → Read）を用意し:

```bash
export CLOUDFLARE_API_TOKEN="（ダッシュボードで発行）"
export CLOUDFLARE_ZONE_NAME="eisei1shu-master.jp"
python3 tools/cloudflare_apply_cache_rules.py
```

---

## 手順 6 — 動作確認

```bash
bash tools/verify_cache_headers.sh
```

成功時の目安:

- 応答に **`cf-ray`** がある（Cloudflare 経由）
- `eisei1-data-bundle.js` など JS の `cache-control` に **長い `max-age`** または Cloudflare による上書き
- `index.html` は **短い TTL** または `must-revalidate`

PageSpeed Insights で「効率的なキャッシュ保存期間」を再計測してください。

---

## トラブルシュート

| 症状 | 対処 |
|------|------|
| 522 / SSL エラー | SSL を「フル（厳密）」に。GitHub Pages 側のカスタムドメイン設定を確認 |
| サイトが古いまま | Cloudflare **キャッシュのパージ** → すべてパージ |
| ルールが効かない | プロキシが **DNS only（灰色雲）** になっていないか確認 |
| `bundle.js` が 404 | GitHub Actions の Deploy が成功しているか確認 |

## 関連

- [performance-cloudflare-cache.md](./performance-cloudflare-cache.md) — キャッシュと SPA の関係
- リポジトリ `_headers` — **Cloudflare Pages にホストした場合のみ** 自動適用（現状は GitHub Pages）
