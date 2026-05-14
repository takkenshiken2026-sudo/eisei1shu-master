#!/usr/bin/env bash
# public_site/index.html などに、過去に ERR_NAME_NOT_RESOLVED を起こした誤綴りが残っていないか検査する。
set -euo pipefail
HTML="${1:?使い方: $0 <index.htmlのパス>}"
if [[ ! -f "$HTML" ]]; then
  echo "verify_supabase_url_in_html.sh: ファイルがありません: $HTML" >&2
  exit 1
fi
if grep -qE 'ujysjdaboqqlkijjjtn|ujysjdaboqgslkijjjtn' "$HTML"; then
  echo "verify_supabase_url_in_html.sh: SUPABASE_URL に無効な Project ref が含まれています（qql または qgs）。" >&2
  echo "Supabase ダッシュボード → Settings → API の URL を Copy で貼り付けてください。" >&2
  exit 1
fi
if ! grep -qE "const SUPABASE_URL = [\"']https://[a-z0-9-]+\\.supabase\\.co[\"']" "$HTML"; then
  echo "verify_supabase_url_in_html.sh: const SUPABASE_URL の形式が想定と異なります。" >&2
  exit 1
fi
echo "verify_supabase_url_in_html.sh: OK ($HTML)"
