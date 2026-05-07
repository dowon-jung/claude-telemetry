#!/usr/bin/env python3
"""
Claude Code 위험 키워드 탐지 → 슬랙 알림 스크립트
실행: python slack_alert.py
주기 실행: Windows 작업 스케줄러에 등록 권장 (5분마다)
"""

import json
import os
import urllib.request
from datetime import datetime, timezone, timedelta

# =====================
# 설정값
# =====================
ES_URL = "http://localhost:9201"
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")
CHECK_INTERVAL_MINUTES = 5

DANGEROUS_KEYWORDS = [
    "password", "api_key", "secret", "DROP TABLE",
    "rm -rf", "kubectl delete", "aws secret",
    "private_key", "access_token",
]

# =====================
# ES 조회
# =====================
def search_dangerous_prompts():
    now = datetime.now(timezone.utc)
    from_time = now - timedelta(minutes=CHECK_INTERVAL_MINUTES)
    from_str = from_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    should_clauses = [
        {"wildcard": {"Attributes.prompt.value": f"*{kw}*"}}
        for kw in DANGEROUS_KEYWORDS
    ]

    query = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"Attributes.event.name": "user_prompt"}},
                    {"range": {"@timestamp": {"gte": from_str}}}
                ],
                "should": should_clauses,
                "minimum_should_match": 1
            }
        },
        "size": 10,
        "_source": ["Attributes.user.email", "Attributes.prompt.value", "@timestamp"]
    }

    url = f"{ES_URL}/logs-generic-default/_search"
    data = json.dumps(query).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as res:
            result = json.loads(res.read().decode("utf-8"))
            return result.get("hits", {}).get("hits", [])
    except Exception as e:
        print(f"ES 조회 오류: {e}")
        return []

# =====================
# 슬랙 알림 전송
# =====================
def send_slack_alert(hits):
    if not hits:
        return

    if not SLACK_WEBHOOK_URL:
        print("오류: SLACK_WEBHOOK_URL 환경변수가 설정되지 않았습니다.")
        return

    messages = []
    for hit in hits:
        src = hit.get("_source", {})
        email = src.get("Attributes.user.email", "unknown")
        prompt = src.get("Attributes.prompt.value", "")
        timestamp = src.get("@timestamp", "")
        matched = [kw for kw in DANGEROUS_KEYWORDS if kw.lower() in prompt.lower()]

        messages.append(
            f"• *{email}*\n"
            f"  시각: {timestamp}\n"
            f"  키워드: `{'`, `'.join(matched)}`\n"
            f"  프롬프트: {prompt[:100]}{'...' if len(prompt) > 100 else ''}"
        )

    text = (
        f"🚨 *Claude Code 위험 키워드 탐지*\n"
        f"최근 {CHECK_INTERVAL_MINUTES}분 내 {len(hits)}건 발생\n\n"
        + "\n\n".join(messages)
    )

    payload = json.dumps({"text": text}).encode("utf-8")
    req = urllib.request.Request(
        SLACK_WEBHOOK_URL, data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as res:
            print(f"슬랙 알림 전송 완료 ({len(hits)}건)")
    except Exception as e:
        print(f"슬랙 전송 오류: {e}")

# =====================
# 메인
# =====================
if __name__ == "__main__":
    print(f"[{datetime.now()}] 위험 키워드 탐지 시작...")
    hits = search_dangerous_prompts()
    if hits:
        print(f"탐지된 건수: {len(hits)}")
        send_slack_alert(hits)
    else:
        print("탐지된 위험 키워드 없음")
