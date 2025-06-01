
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import time
import argparse
import requests

"""
export GITHUB_TOKEN= 토큰 입력
실행 명령어 : python github_track.py <OWNER> <REPO_NAME>
"""

# GitHub API 및 Raw 콘텐츠 기본 URL
GITHUB_API = "https://api.github.com"
RAW_BASE = "https://raw.githubusercontent.com"

# 상태 및 출력 파일 경로
STATE_FILE = "converted/git-ai-sample-converted/last_event_state.json"
EVENTS_FILE = "converted/git-ai-sample-converted/repo_events.json"
FILE_SHAS_FILE = "file_shas.json"
FILES_CONTENT_FILE = "repo_files.json"

# 제외할 디렉터리(가상환경, 의존 모듈 등)
IGNORE_PREFIXES = (
    "venv/", ".venv/", "node_modules/",
    "backend/fastAPI/venv/", "frontend/node_modules/"
)


def create_session(token=None):
    """GitHub 인증 세션 생성"""
    session = requests.Session()
    if token:
        session.headers.update({"Authorization": f"token {token}"})
    return session


def load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def fetch_and_store_events(session, owner, repo):
    url = f"{GITHUB_API}/repos/{owner}/{repo}/events"
    try:
        resp = session.get(url, params={"per_page": 100})
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if resp.status_code == 403:
            reset = resp.headers.get('X-RateLimit-Reset')
            print(f"Rate limit exceeded; reset timestamp: {reset}. Ensure GITHUB_TOKEN is set.")
            return
        else:
            print(f"Error fetching events: {e}")
            return

    events = resp.json() or []
    state = load_json(STATE_FILE)
    last_id = state.get("last_id") if isinstance(state, dict) else state

    new = []
    for ev in events:
        if last_id and ev.get("id") == last_id:
            break
        new.append({
            "id":         ev.get("id"),
            "type":       ev.get("type"),
            "actor":      ev.get("actor",{}).get("login"),
            "repo":       ev.get("repo",{}).get("name"),
            "created_at": ev.get("created_at"),
            "payload":    ev.get("payload")
        })

    if new:
        new.reverse()
        all_events = load_json(EVENTS_FILE) or []
        all_events.extend(new)
        save_json(all_events, EVENTS_FILE)
        save_json({"last_id": new[-1]["id"]}, STATE_FILE)
        print(f"{len(new)} new events saved, last_id={new[-1]['id']}")
    else:
        print("No new events.")


def get_raw_content(owner, repo, branch, path, session):
    url = f"{RAW_BASE}/{owner}/{repo}/{branch}/{path}"
    resp = session.get(url)
    resp.raise_for_status()
    return resp.text




def main():
    parser = argparse.ArgumentParser(
        description="GitHub 이벤트 폴링 및 브랜치 파일 변경분까지 수집"
    )
    parser.add_argument("owner", help="저장소 소유자 (예: octocat)")
    parser.add_argument("repo",  help="저장소 이름   (예: Hello-World)")
    parser.add_argument(
        "--branch", default="main",
        help="감시할 브랜치명 (기본: main)"
    )
    parser.add_argument(
        "--interval", type=int, default=30,
        help="폴링 간격(초)"
    )
    args = parser.parse_args()

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN 환경 변수가 설정되지 않았습니다.\n  export GITHUB_TOKEN=your_token")
        sys.exit(1)
    session = create_session(token)

    print(f"▶ Polling {args.owner}/{args.repo}@{args.branch} every {args.interval}s …")
    while True:
        fetch_and_store_events(session, args.owner, args.repo)
        time.sleep(args.interval)

if __name__ == "__main__":
    main()

