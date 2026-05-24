#!/usr/bin/env bash
# Cloudflare キャッシュ設定の簡易確認（eisei1shu-master.jp）
set -euo pipefail
BASE="${1:-https://eisei1shu-master.jp}"

check() {
  local path="$1"
  local label="$2"
  echo ""
  echo "=== ${label}: ${path} ==="
  curl -sSI "${BASE}${path}" | awk '
    BEGIN{IGNORECASE=1}
    /^HTTP\//{print}
    /^cache-control:/{print}
    /^cf-cache-status:/{print}
    /^cf-ray:/{print}
    /^server:/{print}
    /^expires:/{print}
    /^age:/{print}
  '
}

echo "対象: ${BASE}"

check "/" "HTML (top)"
check "/eisei1-data-bundle.js" "SPA data bundle"
check "/site-theme.css" "Theme CSS"

echo ""
if curl -sSI "${BASE}/" | grep -qi '^cf-ray:'; then
  echo "OK: Cloudflare 経由（cf-ray あり）"
else
  echo "注意: Cloudflare 未経由の可能性（cf-ray なし）。"
  echo "  → docs/cloudflare-setup-eisei1shu-master.md の手順 1〜3（NS 切替）を実施してください。"
fi

if curl -sSI "${BASE}/eisei1-data-bundle.js" | grep -qi 'max-age=600'; then
  echo "注意: JS がまだ max-age=600（10分）です。キャッシュルール適用後に再確認してください。"
fi
