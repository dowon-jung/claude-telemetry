# Claude Code Telemetry Monitoring

> **Claude Team 플랜 팀원들의 Claude Code 사용 내역을 실시간으로 수집·저장·조회하는 보안 감사 시스템**

---

## 프로젝트 개요

### 시작한 이유

한일네트웍스 웹서비스파트에서 Claude Team 플랜을 도입하면서 아래 문제가 생겼다.

- 팀원들이 Claude Code로 무슨 작업을 하는지 PM이 파악하기 어려움
- 소스코드, DB 접속정보, API KEY 등 민감정보가 AI에 입력될 가능성
- 토큰 비용이 얼마나 발생하는지 추적 불가
- 보안 감사 목적의 로그 체계 부재

이를 해결하기 위해 **OpenTelemetry 기반 Claude Code 사용 로그 수집 시스템**을 구축했다.

---

## 시스템 아키텍처

```
팀원 PC (Claude Code)
    └── OTEL Exporter (환경변수 활성화)
            ↓ HTTP/4328
PM PC (192.168.50.170)
    └── Docker Compose
        ├── EDOT Collector (elastic-agent)
        ├── ElasticSearch 8.16
        └── Kibana 8.16
```

---

## 수집 데이터

| 항목 | 필드명 |
|---|---|
| 사용자 이메일 | `Attributes.user.email` |
| 프롬프트 전문 | `Attributes.prompt.value` |
| 사용 모델 | `Attributes.model` |
| 비용 | `Attributes.cost_usd` |
| 토큰 사용량 | `Attributes.input_tokens` / `Attributes.output_tokens` |
| 세션 ID | `Attributes.session.id` |
| 이벤트 시각 | `@timestamp` |

---

## 구축 과정에서 어려웠던 점

### 1. OTEL Collector ↔ ElasticSearch 버전 호환 문제
OTEL Collector v0.151.0의 기본 매핑 모드가 `otel`로 변경되면서 ES 8.12+ 이상이 필요했다. 처음에 ES 8.13으로 시작했으나 `index_not_found_exception` 오류가 반복되었고, ES 8.16 + EDOT Collector(elastic-agent) 조합으로 전환하여 해결했다.

### 2. 환경변수명 오류
`ANTHROPIC_OTEL_ENABLED` 가 아닌 `CLAUDE_CODE_ENABLE_TELEMETRY=1` 이 올바른 변수명이었다. 공식 문서 확인 후 수정했다.

### 3. 회사 PC 방화벽 권한 문제
회사 도메인 계정(`HANILNETWORKS-IMG`)은 방화벽 변경 권한이 없어 IT팀에 요청하여 TCP 4328 인바운드 허용을 받았다.

### 4. IDE 터미널 환경변수 미적용
팀원이 IntelliJ/PyCharm 터미널에서 Claude Code를 실행할 경우 시스템 환경변수가 적용되지 않는 문제가 있었다. IDE 터미널 내에서 직접 환경변수를 설정하는 방법을 가이드에 추가했다.

---

## 구축 후 효과

- **실시간 모니터링**: Kibana Discover에서 팀원별 프롬프트를 시간순으로 조회 가능
- **비용 추적**: `Attributes.cost_usd` 필드로 사용자별 비용 집계 가능
- **보안 감사**: 민감정보 입력 여부 사후 추적 가능
- **팀원 현황 파악**: 어떤 모델을 얼마나 사용하는지 파악 가능

---

## 기술 스택

| 영역 | 기술 |
|---|---|
| Telemetry | OpenTelemetry (OTLP/HTTP) |
| Collector | Elastic Agent 8.16 (EDOT 모드) |
| Storage | ElasticSearch 8.16 |
| Dashboard | Kibana 8.16 |
| Container | Docker Compose |

---

## 파일 구성

```
claude-telemetry/
├── README.md                          # 프로젝트 개요 (현재 파일)
├── IMPLEMENTATION_PLAN.md             # 구축 계획서
├── claude_full_telemetry_monitoring_plan.md  # 초기 설계 문서
├── docker/
│   ├── docker-compose.yml             # 컨테이너 구성
│   └── otel-config.yaml               # OTEL Collector 설정
└── guides/
    ├── team-env-setup.md              # 팀원 환경변수 설정 가이드
    ├── firewall-setup.md              # 방화벽 설정 가이드
    └── progress-log.md               # 작업일지
```

---

## 빠른 시작

### 1. 수집 서버 실행 (PM PC)

```powershell
git clone https://github.com/dowon-jung/claude-telemetry.git
cd claude-telemetry\docker
docker compose up -d
```

### 2. 팀원 환경변수 설정

```powershell
[System.Environment]::SetEnvironmentVariable("CLAUDE_CODE_ENABLE_TELEMETRY", "1", "User")
[System.Environment]::SetEnvironmentVariable("OTEL_METRICS_EXPORTER", "otlp", "User")
[System.Environment]::SetEnvironmentVariable("OTEL_LOGS_EXPORTER", "otlp", "User")
[System.Environment]::SetEnvironmentVariable("OTEL_EXPORTER_OTLP_PROTOCOL", "http/protobuf", "User")
[System.Environment]::SetEnvironmentVariable("OTEL_EXPORTER_OTLP_ENDPOINT", "http://192.168.50.170:4328", "User")
[System.Environment]::SetEnvironmentVariable("OTEL_LOG_USER_PROMPTS", "1", "User")
```

### 3. Kibana 접속

| 서비스 | URL |
|---|---|
| Kibana | http://localhost:5602 |
| ElasticSearch | http://localhost:9201 |

---

## 보안 운영 원칙

1. **팀원 사전 고지 필수** — 프롬프트 로그 수집 사실 공지
2. **ElasticSearch 외부 노출 금지** — 사내망 한정 운영
3. **열람 권한 최소화** — PM / 보안담당자만
4. **열람 시 로그 기록** — 누가 언제 봤는지 추적

---

## 작성자

- **정도원** — 한일네트웍스 웹서비스파트 PM
- 구축일: 2026-05-07
