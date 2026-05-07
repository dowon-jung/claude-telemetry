# Claude Code Telemetry Monitoring

> **Claude Team 플랜 팀원들의 Claude Code 사용 내역을 실시간으로 수집·저장·조회하는 보안 감사 시스템**

---

## 📌 프로젝트 배경

한일네트웍스 웹서비스파트에서 Claude Team 플랜을 도입하면서 아래 문제가 생겼다.

- 팀원들이 Claude Code로 무슨 작업을 하는지 PM이 파악하기 어려움
- 소스코드, DB 접속정보, API KEY 등 민감정보가 AI에 입력될 가능성
- 토큰 비용이 얼마나 발생하는지 추적 불가
- 보안 감사 목적의 로그 체계 부재

이를 해결하기 위해 **OpenTelemetry 기반 Claude Code 사용 로그 수집 시스템**을 구축했다.

---

## 🏗 시스템 아키텍처

```
팀원 PC (Claude Code CLI)
    └── OTEL Exporter (환경변수 활성화)
            ↓ HTTP / 포트 4328
PM PC (192.168.50.170)
    └── Docker Compose
        ├── EDOT Collector (elastic-agent 8.16)  ← 수신 게이트웨이
        ├── ElasticSearch 8.16                   ← 저장소
        └── Kibana 8.16                          ← 조회 대시보드
```

---

## 📊 수집 데이터

| 항목 | 필드명 | 비고 |
|---|---|---|
| 사용자 이메일 | `Attributes.user.email` | 팀원 식별 |
| 프롬프트 전문 | `Attributes.prompt.value` | 기본 REDACTED, 환경변수로 활성화 |
| 사용 모델 | `Attributes.model` | sonnet / haiku 구분 |
| 비용 | `Attributes.cost_usd` | 요청별 비용 |
| 입력 토큰 | `Attributes.input_tokens` | |
| 출력 토큰 | `Attributes.output_tokens` | |
| 세션 ID | `Attributes.session.id` | 대화 세션 추적 |
| 이벤트 시각 | `@timestamp` | |

---

## 🔍 수집 이벤트 종류

| 이벤트 | 설명 |
|---|---|
| `user_prompt` | 팀원이 입력한 프롬프트 |
| `api_request` | Claude API 호출 결과 (모델, 토큰, 비용) |
| `tool_result` | 툴 실행 결과 |
| `tool_decision` | 툴 실행 승인 여부 |
| `api_error` | API 오류 발생 |

---

## ⚙️ 기술 스택

| 영역 | 기술 |
|---|---|
| Telemetry | OpenTelemetry (OTLP/HTTP) |
| Collector | Elastic Agent 8.16 (EDOT 모드) |
| Storage | ElasticSearch 8.16 |
| Dashboard | Kibana 8.16 |
| Container | Docker Compose |
| Alert | Python + Slack Incoming Webhook |

---

## 🚀 빠른 시작

### 1. 수집 서버 실행 (PM PC)

```powershell
git clone https://github.com/dowon-jung/claude-telemetry.git
cd claude-telemetry\docker
docker compose up -d
```

### 2. 팀원 환경변수 설정 (팀원 PC - 1회)

```powershell
[System.Environment]::SetEnvironmentVariable("CLAUDE_CODE_ENABLE_TELEMETRY", "1", "User")
[System.Environment]::SetEnvironmentVariable("OTEL_METRICS_EXPORTER", "otlp", "User")
[System.Environment]::SetEnvironmentVariable("OTEL_LOGS_EXPORTER", "otlp", "User")
[System.Environment]::SetEnvironmentVariable("OTEL_EXPORTER_OTLP_PROTOCOL", "http/protobuf", "User")
[System.Environment]::SetEnvironmentVariable("OTEL_EXPORTER_OTLP_ENDPOINT", "http://192.168.50.170:4328", "User")
[System.Environment]::SetEnvironmentVariable("OTEL_LOG_USER_PROMPTS", "1", "User")
```

### 3. 설정 확인

```powershell
echo $env:CLAUDE_CODE_ENABLE_TELEMETRY   # 1
echo $env:OTEL_LOGS_EXPORTER             # otlp
echo $env:OTEL_EXPORTER_OTLP_ENDPOINT   # http://192.168.50.170:4328
echo $env:OTEL_LOG_USER_PROMPTS         # 1
```

### 4. Kibana 접속

| 서비스 | URL |
|---|---|
| Kibana (PM PC) | http://localhost:5602 |
| Kibana (팀원 PC) | http://192.168.50.170:5602 |
| ElasticSearch | http://localhost:9201 |

### 5. 슬랙 Alert 실행

```powershell
$env:SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
python alert\slack_alert.py
```

---

## 🔔 수집 범위

| 클라이언트 | 수집 여부 | 이유 |
|---|---|---|
| 터미널 `claude` (CLI) | ✅ 수집 | 환경변수 적용됨 |
| Claude Code 데스크탑 앱 | ❌ 미수집 | 환경변수 미적용 |
| claude.ai 웹 | ❌ 미수집 | 브라우저 구간 개입 불가 |

---

## 🛠 구축 과정에서 어려웠던 점

### 1. OTEL Collector ↔ ElasticSearch 버전 호환 문제
OTEL Collector v0.151.0의 기본 매핑 모드가 `otel`로 변경되면서 ES 8.12+ 이상이 필요했다.  
ES 8.13으로 시작했으나 `index_not_found_exception` 오류가 반복되었고,  
**ES 8.16 + EDOT Collector(elastic-agent) 조합**으로 전환하여 해결했다.

### 2. 환경변수명 오류
`ANTHROPIC_OTEL_ENABLED` 가 아닌 `CLAUDE_CODE_ENABLE_TELEMETRY=1` 이 올바른 변수명이었다.  
공식 문서 확인 후 수정했다.

### 3. 회사 PC 방화벽 권한 문제
회사 도메인 계정은 방화벽 변경 권한이 없어 IT팀에 요청하여 TCP 4328 인바운드 허용을 받았다.

### 4. IDE 터미널 환경변수 미적용
IntelliJ/PyCharm 터미널은 시스템 환경변수 설정 시 재시작이 필요하다.  
IDE 재시작 또는 터미널 내 직접 설정 방법을 가이드에 추가했다.

### 5. Kibana Alert Gold 라이선스 제한
Kibana의 Slack/Webhook/Email 커넥터가 Gold 라이선스 필요했다.  
Python 스크립트로 ES 직접 조회 → Slack Webhook 전송 방식으로 우회 구현했다.

---

## 📈 구축 후 효과

- **실시간 모니터링**: Kibana에서 팀원별 프롬프트를 시간순으로 조회 가능
- **보안 감사**: 위험 키워드 입력 시 슬랙으로 즉시 알림
- **비용 추적**: 사용자별/모델별 비용 집계 가능
- **팀 현황 파악**: 어떤 모델을 얼마나 사용하는지 파악 가능
- **업무 투명성**: PM이 팀원 AI 활용 현황 파악 가능

---

## 🔒 보안 운영 원칙

1. **팀원 사전 고지 필수** — 프롬프트 로그 수집 사실 공지 및 동의
2. **ElasticSearch 외부 노출 금지** — 사내망 한정 운영
3. **열람 권한 최소화** — PM / 보안담당자만
4. **열람 시 로그 기록** — 누가 언제 봤는지 추적
5. **보관 기간 준수** — 정기적인 데이터 삭제 정책 적용

---

## 📁 파일 구성

```
claude-telemetry/
├── README.md                          # 프로젝트 개요 (현재 파일)
├── IMPLEMENTATION_PLAN.md             # 구축 계획서
├── claude_full_telemetry_monitoring_plan.md  # 초기 설계 문서
├── docker/
│   ├── docker-compose.yml             # 컨테이너 구성 (ES + Kibana + EDOT)
│   └── otel-config.yaml               # OTEL Collector 설정
├── alert/
│   ├── slack_alert.py                 # 슬랙 위험 키워드 알림 스크립트
│   ├── .env.example                   # 환경변수 예시
│   └── README.md                      # Alert 설정 가이드
└── guides/
    ├── team-env-setup.md              # 팀원 환경변수 설정 가이드
    ├── architecture.md                # 원리 및 플로우 상세 문서
    ├── firewall-setup.md              # 방화벽 설정 가이드
    └── progress-log.md               # 작업일지
```

---

## 👤 작성자

- **정도원** — 한일네트웍스 웹서비스파트 PM
- 구축일: 2026-05-07
- 문의: 웹서비스파트 정도원 대리
