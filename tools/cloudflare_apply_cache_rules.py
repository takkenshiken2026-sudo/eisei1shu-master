#!/usr/bin/env python3
"""eisei1shu-master.jp 向け Cloudflare キャッシュルールを API で適用する。"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

API = "https://api.cloudflare.com/client/v4"
HOST = os.environ.get("CLOUDFLARE_ZONE_NAME", "eisei1shu-master.jp").strip()
PHASE = "http_request_cache_settings"

RULE_HTML = {
    "description": "eisei1shu: HTML short browser cache",
    "expression": (
        f'(http.host eq "{HOST}" and '
        '(http.request.uri.path eq "/" or http.request.uri.path.extension eq "html"))'
    ),
    "action": "set_cache_settings",
    "enabled": True,
    "action_parameters": {
        "cache": True,
        "browser_ttl": {"mode": "override_origin", "default": 120},
        "edge_ttl": {"mode": "override_origin", "default": 7200},
    },
}

RULE_STATIC = {
    "description": "eisei1shu: JS/CSS long browser cache",
    "expression": (
        f'(http.host eq "{HOST}" and http.request.uri.path.extension in {{"js" "css"}})'
    ),
    "action": "set_cache_settings",
    "enabled": True,
    "action_parameters": {
        "cache": True,
        "browser_ttl": {"mode": "override_origin", "default": 31536000},
        "edge_ttl": {"mode": "override_origin", "default": 2678400},
    },
}

OUR_DESCRIPTIONS = {RULE_HTML["description"], RULE_STATIC["description"]}


def api(method: str, path: str, body: dict | None = None) -> dict:
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
    if not token:
        print("CLOUDFLARE_API_TOKEN が未設定です。", file=sys.stderr)
        sys.exit(1)
    url = f"{API}{path}"
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        print(f"API error {e.code} {path}:\n{err_body}", file=sys.stderr)
        sys.exit(1)
    if not payload.get("success", False):
        print(f"API failed {path}: {payload.get('errors')}", file=sys.stderr)
        sys.exit(1)
    return payload


def zone_id() -> str:
    zid = os.environ.get("CLOUDFLARE_ZONE_ID", "").strip()
    if zid:
        return zid
    res = api("GET", f"/zones?name={HOST}")
    zones = res.get("result") or []
    if not zones:
        print(f"ゾーンが見つかりません: {HOST}", file=sys.stderr)
        sys.exit(1)
    return zones[0]["id"]


def entrypoint_ruleset(zid: str) -> dict | None:
    res = api("GET", f"/zones/{zid}/rulesets/phases/{PHASE}/entrypoint")
    return res.get("result")


def merge_rules(existing: list[dict]) -> list[dict]:
    kept = [r for r in existing if r.get("description") not in OUR_DESCRIPTIONS]
    return [RULE_HTML, RULE_STATIC] + kept


def main() -> int:
    zid = zone_id()
    print(f"zone: {HOST} ({zid})")

    ep = entrypoint_ruleset(zid)
    if ep and ep.get("id"):
        ruleset_id = ep["id"]
        rules = merge_rules(ep.get("rules") or [])
        api("PUT", f"/zones/{zid}/rulesets/{ruleset_id}", {"rules": rules})
        print(f"更新しました: ruleset {ruleset_id}（ルール {len(rules)} 件）")
    else:
        api(
            "POST",
            f"/zones/{zid}/rulesets",
            {
                "name": f"{HOST} cache rules",
                "kind": "zone",
                "phase": PHASE,
                "rules": [RULE_HTML, RULE_STATIC],
            },
        )
        print("新規 ruleset を作成しました。")

    print("完了。bash tools/verify_cache_headers.sh で確認してください。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
