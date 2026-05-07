# Slack Alert 설정 가이드

## 개요
ElasticSearch에서 위험 키워드가 포함된 프롬프트를 탐지하여 슬랙으로 알림을 보내는 스크립트.

Kibana Gold 라이선스 없이 무료로 슬랙 알림을 구현한 방식.

---

## 탐지 키워드 (기본 설정)

```
password, api_key, secret, DROP TABLE,
rm -rf, kubectl delete, aws secret,
private_key, access_token
```

`slack_alert.py` 상단 `DANGEROUS_KEYWORDS` 목록에서 수정 가능.

---

## 실행 방법

### 환경변수 설정

```powershell
$env:SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

### 1회 실행

```powershell
python alert\slack_alert.py
```

### 자동 실행 (Windows 작업 스케줄러)

1. `Windows 검색` → **작업 스케줄러** 열기
2. **작업 만들기** 클릭
3. **트리거** → 새로 만들기 → **5분마다** 반복 설정
4. **동작** → 새로 만들기
   - 프로그램: `python`
   - 인수: `C:\Users\HANILNETWORKS-IMG\claude-telemetry\alert\slack_alert.py`
   - 시작 위치: `C:\Users\HANILNETWORKS-IMG\claude-telemetry`
5. **환경변수** 탭에서 `SLACK_WEBHOOK_URL` 추가
6. 확인

---

## 알림 예시

```
🚨 Claude Code 위험 키워드 탐지
최근 5분 내 1건 발생

• ehdnjs0615@hanilnetworks.com
  시각: 2026-05-07T08:35:20.204Z
  키워드: `password`
  프롬프트: password 테스트입니다...
```

---

## 설정 파일

`.env.example` 참고하여 실제 `.env` 파일 생성:

```
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

`.env` 파일은 `.gitignore`에 등록되어 git에 올라가지 않습니다.
