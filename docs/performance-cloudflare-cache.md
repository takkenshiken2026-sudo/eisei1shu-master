# PageSpeed：キャッシュ TTL（GitHub Pages + 独自ドメイン）

GitHub Pages の静的ファイルは **Cache-Control: max-age=600（10分）** が既定で、リポジトリからヘッダーを変更できません。PageSpeed の「効率的なキャッシュ保存期間を使用する」は、主にこの制限が原因です。

## 推奨：Cloudflare プロキシ（オレンジ雲）でエッジキャッシュ

`eisei1shu-master.jp` を Cloudflare 経由で GitHub Pages に向けている場合、**キャッシュルール**で JS/CSS のブラウザ TTL を延ばします。

1. Cloudflare ダッシュボード → 対象ゾーン → **ルール** → **キャッシュルール** → 作成
2. 例（カスタムルール）:
   - **フィールド**: ホスト名 ＝ `eisei1shu-master.jp`
   - **かつ** ファイル拡張子 が次のいずれかに該当: `js`, `css`
3. **設定**:
   - キャッシュの対象: **キャッシュする**
   - エッジ TTL: **1か月**（または「ブラウザ TTL に従う」＋下記ブラウザ TTL）
   - ブラウザ TTL: **1年**（31536000 秒）— デプロイ時に `?v=` が付く前提（下記）

`index.html` は **キャッシュしない** または **max-age=0** にし、JS/CSS だけ長期キャッシュにします。

## デプロイ時の `?v=`（キャッシュ更新）

`.github/workflows/deploy-pages.yml` の `inject_spa_asset_version.py` が、ビルドの Git SHA 短縮版を `eisei1-*.js` / `site-theme.css` 等の URL に付与します。Cloudflare で長期キャッシュしても、デプロイごとに URL が変わるため古いバンドルが残りにくくなります。

## Cloudflare Pages に移行する場合

リポジトリ直下の `_headers` がそのまま効きます（`prepare_public_site.sh` で `public_site/` にコピーされます）。

## レンダリングブロック（SPA）

`index.html` では次を実施済みです。

- 大容量データ JS・Supabase を **`defer`**（`</body>` 直前）
- アプリ本体は **`DOMContentLoaded`** 後に起動
- `site-theme.css` は **preload + onload** で非ブロッキング読み込み
