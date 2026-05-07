# Slack Alert 설정 가이드

## 개요
ElasticSearch에서 위험 키워드가 포함된 프롬프트를 탐지하여 슬랙으로 알림을 보내는 스크립트.

## 탐지 키워드
- password, api_key, secret, DROP TABLE
- rm -rf, kubectl delete, aws secret
- private_key, access_token

## 실행 방법

### 1회 실행
```powershell
python alert\slack_alert.py
```

### 자동 실행 (Windows 작업 스케줄러)
1. `Windows 검색` → **작업 스케줄러** 열기
2. **작업 만들기** 클릭
3. **트리거** → 새로 만들기 → **5분마다** 반복 설정
4. **동작** → 새로 만들기 → 프로그램: `python`
5. 인수: `C:\Users\HANILNETWORKS-IMG\claude-telemetry\alert\slack_alert.py`
6. 확인

## 설정 변경
`slack_alert.py` 상단 설정값 수정:
- `SLACK_WEBHOOK_URL`: 슬랙 Webhook URL
- `CHECK_INTERVAL_MINUTES`: 조회 간격 (분)
- `DANGEROUS_KEYWORDS`: 탐지 키워드 목록
