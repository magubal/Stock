#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def _request(url: str, method: str, token: str, payload: dict):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url=url,
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "consistency-monitoring-guard",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8", errors="ignore")
        return resp.status, body


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply GitHub branch protection for consistency monitoring checks")
    parser.add_argument("--repo", required=True, help="owner/repo")
    parser.add_argument("--branch", default="master", help="target branch")
    parser.add_argument("--dry-run", action="store_true", help="print payload only")
    parser.add_argument("--strict", action="store_true", help="require branch up-to-date before merge")
    args = parser.parse_args()

    token = (os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or "").strip()
    if not token and not args.dry_run:
        print("[FAIL] missing token (GITHUB_TOKEN or GH_TOKEN)")
        return 2

    required_contexts = [
        "consistency-monitoring-gate / consistency-monitoring-gate",
    ]
    payload = {
        "required_status_checks": {
            "strict": bool(args.strict),
            "contexts": required_contexts,
        },
        "enforce_admins": True,
        "required_pull_request_reviews": {
            "dismiss_stale_reviews": True,
            "require_code_owner_reviews": False,
            "required_approving_review_count": 1,
        },
        "restrictions": None,
        "required_linear_history": False,
        "allow_force_pushes": False,
        "allow_deletions": False,
        "block_creations": False,
        "required_conversation_resolution": True,
        "lock_branch": False,
        "allow_fork_syncing": True,
    }

    url = f"https://api.github.com/repos/{args.repo}/branches/{args.branch}/protection"
    if args.dry_run:
        print("[DRY-RUN] target:", url)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    try:
        status, body = _request(url, "PUT", token, payload)
        if status not in (200, 201):
            print(f"[FAIL] status={status}")
            print(body)
            return 1
        print("[OK] branch protection applied")
        print(body)
        return 0
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="ignore")
        print(f"[FAIL] HTTP {e.code}")
        print(detail)
        return 1
    except Exception as e:
        print(f"[FAIL] {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
