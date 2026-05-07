# Claude Code Telemetry 원리 및 플로우 상세 문서

## 1. 전체 플로우 요약

```
팀원이 Claude Code에서 프롬프트 입력
        ↓
Claude Code가 OTEL 이벤트 생성
        ↓
OTEL Exporter가 PM PC로 HTTP 전송 (포트 4328)
        ↓
EDOT Collector가 수신 및 파싱
        ↓
ElasticSearch에 저장 (data stream)
        ↓
Kibana에서 조회
```

---

## 2. 각 구성요소 역할

### Claude Code (팀원 PC)
- Anthropic이 만든 CLI 기반 AI 코딩 어시스턴트
- 환경변수 `CLAUDE_CODE_ENABLE_TELEMETRY=1` 설정 시 OTEL 이벤트를 외부로 전송하는 기능이 활성화됨
- 프롬프트 입력, API 요청, 툴 실행 등 5가지 이벤트를 생성함

### OTEL Exporter (Claude Code 내장)
- Claude Code 내부에 내장된 OpenTelemetry 전송 모듈
- `OTEL_EXPORTER_OTLP_ENDPOINT` 에 설정된 주소로 HTTP/protobuf 형식으로 데이터 전송
- `OTEL_LOG_USER_PROMPTS=1` 설정 시 프롬프트 전문 포함, 미설정 시 `<REDACTED>` 처리

### EDOT Collector (PM PC - Docker)
- Elastic Distribution of OpenTelemetry Collector
- 팀원 PC들로부터 OTLP 데이터를 수신하는 게이트웨이 역할
- 수신한 데이터를 파싱하여 ElasticSearch로 전달

### ElasticSearch (PM PC - Docker)
- 수집된 로그를 저장하는 검색 엔진
- `logs-generic-default` data stream에 저장
- 필드별 인덱싱으로 빠른 검색 가능

### Kibana (PM PC - Docker)
- ElasticSearch 데이터를 시각화하는 대시보드 도구
- Discover에서 실시간 로그 조회
- 대시보드로 비용/사용량 시각화

---

## 3. 수집 이벤트 종류

Claude Code는 아래 5가지 이벤트를 생성한다.

| 이벤트명 | 설명 | 주요 필드 |
|---|---|---|
| `user_prompt` | 팀원이 입력한 프롬프트 | `prompt.value`, `prompt_length`, `session.id` |
| `api_request` | Claude API 호출 결과 | `model`, `input_tokens`, `output_tokens`, `cost_usd`, `duration_ms` |
| `tool_result` | 툴 실행 결과 | `tool_name`, `duration_ms` |
| `tool_decision` | 툴 실행 승인 여부 | `decision_type`, `decision_source` |
| `api_error` | API 오류 발생 | `error`, `error_code` |

---

## 4. 데이터 전송 플로우 상세

```
[팀원 PC]
Claude Code 실행
    │
    ├── 프롬프트 입력 감지
    │       └── user_prompt 이벤트 생성
    │               └── prompt.value: "실제 입력 내용" (OTEL_LOG_USER_PROMPTS=1 시)
    │
    ├── Anthropic API 호출
    │       └── api_request 이벤트 생성
    │               ├── model: "claude-sonnet-4-6"
    │               ├── input_tokens: 295
    │               ├── output_tokens: 30
    │               └── cost_usd: 0.006495
    │
    └── OTLP/HTTP로 PM PC 전송
            └── POST http://192.168.50.170:4328/v1/logs

[PM PC]
EDOT Collector 수신
    │
    └── ElasticSearch 저장
            └── .ds-logs-generic-default-2026.05.07-000001
                    └── Kibana에서 조회 가능
```

---

## 5. 환경변수 역할 설명

| 환경변수 | 역할 |
|---|---|
| `CLAUDE_CODE_ENABLE_TELEMETRY=1` | OTEL 전송 기능 활성화 (이게 없으면 아무것도 안됨) |
| `OTEL_LOGS_EXPORTER=otlp` | 로그를 OTLP 형식으로 전송 |
| `OTEL_METRICS_EXPORTER=otlp` | 메트릭을 OTLP 형식으로 전송 |
| `OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf` | HTTP + protobuf 방식으로 전송 |
| `OTEL_EXPORTER_OTLP_ENDPOINT=http://192.168.50.170:4328` | 수집 서버 주소 |
| `OTEL_LOG_USER_PROMPTS=1` | 프롬프트 전문 포함 (미설정 시 REDACTED) |

---

## 6. 수집 범위

| 클라이언트 | 수집 여부 | 이유 |
|---|---|---|
| 터미널 `claude` (CLI) | ✅ 수집 | 환경변수를 읽어 OTEL 전송 |
| Claude Code 데스크탑 앱 | ❌ 미수집 | 환경변수 미적용 |
| claude.ai 웹 | ❌ 미수집 | 브라우저 → Anthropic 서버 구간, 개입 불가 |

---

## 7. 보안 고려사항

### 전송 구간
- 팀원 PC → PM PC: 사내망 평문 HTTP (암호화 없음)
- 사내망 내부 통신이므로 외부 유출 위험은 낮음
- 보안 강화 필요 시 TLS 적용 가능

### 저장 데이터 민감도
아래 정보가 ElasticSearch에 평문으로 저장됨:
- 프롬프트 전문 (소스코드, DB 접속정보, API KEY 포함 가능)
- 사용자 이메일
- 세션 정보

### 권장 보안 설정
- ElasticSearch 외부 노출 금지 (사내망 한정)
- Kibana 접근 권한 PM/보안담당자만
- 정기적인 데이터 보관 기간 정책 적용

