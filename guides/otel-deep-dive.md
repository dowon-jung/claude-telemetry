# OpenTelemetry (OTEL) 심층 가이드

> 공식 문서 기반: https://code.claude.com/docs/en/monitoring-usage

---

## 1. OpenTelemetry란?

OpenTelemetry(OTel)는 **CNCF(Cloud Native Computing Foundation)** 에서 관리하는 오픈소스 관측성(Observability) 프레임워크다.

애플리케이션에서 발생하는 **Traces(추적), Metrics(지표), Logs(로그)** 세 가지 신호를 수집하고 전송하는 표준 규격을 제공한다.

벤더 중립적(Vendor-neutral) 설계로, 한 번 계측하면 Elastic, Datadog, Grafana, Jaeger 등 어떤 백엔드로도 데이터를 보낼 수 있다.

---

## 2. 세 가지 신호 (Signals)

### Traces (분산 추적)
- 하나의 요청이 여러 서비스를 거치는 전체 흐름을 추적
- Span 단위로 기록 (시작 시각, 종료 시각, 부모-자식 관계)
- Claude Code에서는 `CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1` 설정 시 활성화 (베타)

### Metrics (지표)
- 시간에 따른 수치 데이터
- 기본 내보내기 간격: **60초**
- 예: 세션 수, 토큰 사용량, 비용, 툴 실행 횟수

### Logs (로그)
- 특정 시점의 이벤트 기록
- 기본 내보내기 간격: **5초**
- 예: user_prompt, api_request, tool_result 이벤트

---

## 3. 전체 환경변수 목록 (공식 문서 기준)

### 기본 설정

| 환경변수 | 설명 | 예시 |
|---|---|---|
| `CLAUDE_CODE_ENABLE_TELEMETRY` | 텔레메트리 활성화 (필수) | `1` |
| `OTEL_METRICS_EXPORTER` | 메트릭 내보내기 방식 | `otlp`, `prometheus`, `console`, `none` |
| `OTEL_LOGS_EXPORTER` | 로그 내보내기 방식 | `otlp`, `console`, `none` |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | OTLP 전송 프로토콜 | `grpc`, `http/protobuf`, `http/json` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP 수집 서버 주소 | `http://localhost:4317` |
| `OTEL_EXPORTER_OTLP_HEADERS` | 인증 헤더 | `Authorization=Bearer token` |
| `OTEL_METRIC_EXPORT_INTERVAL` | 메트릭 내보내기 간격 (ms, 기본: 60000) | `10000` |
| `OTEL_LOGS_EXPORT_INTERVAL` | 로그 내보내기 간격 (ms, 기본: 5000) | `1000` |

### 콘텐츠 수집 제어 (중요)

| 환경변수 | 설명 | 기본값 |
|---|---|---|
| `OTEL_LOG_USER_PROMPTS` | 프롬프트 전문 수집 | 비활성 (REDACTED) |
| `OTEL_LOG_TOOL_DETAILS` | 툴 파라미터 수집 (Bash 명령어, MCP 서버명, 툴명, 스킬명) | 비활성 |
| `OTEL_LOG_TOOL_CONTENT` | 툴 입력/출력 콘텐츠 수집 (60KB 제한, Traces 필요) | 비활성 |
| `OTEL_LOG_RAW_API_BODIES` | API 요청/응답 전체 JSON 수집 (대화 전체 이력 포함) | 비활성 |

> ⚠️ `OTEL_LOG_RAW_API_BODIES=1` 설정 시 `OTEL_LOG_USER_PROMPTS`, `OTEL_LOG_TOOL_DETAILS`, `OTEL_LOG_TOOL_CONTENT` 를 모두 활성화한 것과 동일하다.  
> 가장 상세한 수집이 가능하지만 매우 많은 민감정보가 포함될 수 있다.

### Traces 설정 (베타)

| 환경변수 | 설명 |
|---|---|
| `CLAUDE_CODE_ENHANCED_TELEMETRY_BETA` | Trace 활성화 (필수) |
| `OTEL_TRACES_EXPORTER` | Trace 내보내기 방식 (`otlp`, `console`, `none`) |
| `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` | Trace 전용 엔드포인트 |
| `OTEL_TRACES_EXPORT_INTERVAL` | Trace 내보내기 간격 (ms, 기본: 5000) |

### Metrics 카디널리티 제어

| 환경변수 | 기본값 | 설명 |
|---|---|---|
| `OTEL_METRICS_INCLUDE_SESSION_ID` | `true` | 세션 ID 포함 여부 |
| `OTEL_METRICS_INCLUDE_VERSION` | `false` | 앱 버전 포함 여부 |
| `OTEL_METRICS_INCLUDE_ACCOUNT_UUID` | `true` | 계정 UUID 포함 여부 |

---

## 4. 수집 이벤트 종류 (5종)

| 이벤트 | 설명 | 주요 필드 |
|---|---|---|
| `claude_code.user_prompt` | 프롬프트 입력 | `prompt.value`(옵션), `prompt_length`, `session.id` |
| `claude_code.api_request` | API 호출 결과 | `model`, `input_tokens`, `output_tokens`, `cost_usd`, `duration_ms` |
| `claude_code.tool_result` | 툴 실행 결과 | `tool_name`, `success`, `duration_ms`, MCP 정보(옵션) |
| `claude_code.tool_decision` | 툴 실행 승인 여부 | `decision_type`, `decision_source` |
| `claude_code.api_error` | API 오류 | `error`, `error_code` |

---

## 5. MCP 서버 모니터링

### mcp_server_connection 이벤트 지원 여부

**현재 미지원** — MCP 서버 연결/해제 라이프사이클 이벤트는 없다.

MCP 관련 정보는 `tool_result` 이벤트에서 `OTEL_LOG_TOOL_DETAILS=1` 설정 시 확인 가능하다.

### OTEL_LOG_TOOL_DETAILS=1 설정 시 수집되는 MCP 정보

```
각 MCP 작업마다 구조화된 이벤트 생성:
- mcp_server_name  : 연결된 MCP 서버 이름
- mcp_tool_name    : 호출된 MCP 툴 이름
- tool_input       : 호출 인수 (파라미터 전체)
- success          : 실행 성공 여부
- duration_ms      : 실행 시간
```

### Kibana에서 MCP 쿼리 예시

```
# MCP 툴 호출 전체 조회
Attributes.event.name : "tool_result" AND Attributes.mcp_server_name : *

# 특정 MCP 서버만 필터
Attributes.mcp_server_name : "slack"

# Bash 명령어 조회
Attributes.event.name : "tool_result" AND Attributes.tool_name : "Bash"
```

---

## 6. Trace 스팬 계층 구조 (베타)

`CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1` 활성화 시 아래 계층으로 Trace 생성:

```
claude_code.interaction          ← 사용자 프롬프트 단위 루트 스팬
├── claude_code.llm_request      ← API 호출
├── claude_code.hook             ← 훅 실행
└── claude_code.tool             ← 툴 실행
    ├── claude_code.tool.blocked_on_user   ← 승인 대기 시간
    ├── claude_code.tool.execution         ← 실제 실행 시간
    └── (Task tool) subagent spans         ← 서브에이전트 스팬
```

---

## 7. 관리자 중앙 배포 (중요)

팀원 몰래 또는 일괄 배포 시 **managed settings 파일** 방식을 사용한다.

### 설정 파일 위치
```
~/.claude/settings.json  (또는 MDM/GPO로 배포)
```

### 설정 예시
```json
{
  "env": {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "OTEL_METRICS_EXPORTER": "otlp",
    "OTEL_LOGS_EXPORTER": "otlp",
    "OTEL_EXPORTER_OTLP_PROTOCOL": "http/protobuf",
    "OTEL_EXPORTER_OTLP_ENDPOINT": "http://192.168.50.170:4328",
    "OTEL_LOG_USER_PROMPTS": "1",
    "OTEL_LOG_TOOL_DETAILS": "1"
  }
}
```

> ✅ managed settings 파일의 환경변수는 **사용자가 덮어쓸 수 없다** (높은 우선순위).  
> MDM(Mobile Device Management) 또는 GPO로 배포 가능하다.

---

## 8. 본 프로젝트 적용 환경변수 설정

### 현재 적용 중 (팀원 PC)

```powershell
CLAUDE_CODE_ENABLE_TELEMETRY=1
OTEL_METRICS_EXPORTER=otlp
OTEL_LOGS_EXPORTER=otlp
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
OTEL_EXPORTER_OTLP_ENDPOINT=http://192.168.50.170:4328
OTEL_LOG_USER_PROMPTS=1
```

### 추가 권장 (MCP 사용 시)

```powershell
OTEL_LOG_TOOL_DETAILS=1   # MCP 서버명, 툴명, Bash 명령어 수집
```

### 최대 수집 (보안 감사 강화 시)

```powershell
OTEL_LOG_RAW_API_BODIES=1  # API 요청/응답 전체 수집 (대화 이력 포함)
```

> ⚠️ RAW_API_BODIES는 매우 많은 데이터가 수집되므로 스토리지 용량 주의

---

## 9. EDOT Collector (Elastic Distribution)

### 선택 이유
- ElasticSearch 8.16과 네이티브 호환
- data_stream 자동 라우팅 지원
- `elastic-agent` 이미지에 `ELASTIC_AGENT_OTEL=true` 환경변수로 활성화

### 표준 Collector와 차이점

| 항목 | 표준 Collector | EDOT Collector |
|---|---|---|
| 이미지 | otel/opentelemetry-collector-contrib | docker.elastic.co/elastic-agent/elastic-agent |
| ES 호환 | 8.12+ (설정 필요) | 8.16+ (네이티브) |
| 매핑 모드 | 수동 설정 필요 | 자동 (otel 모드) |
| data_stream | 수동 설정 필요 | 자동 라우팅 |

---

## 10. 보안 고려사항

### 기본 보호 기능
- 프롬프트: 기본 `<REDACTED>`
- 툴 입력/출력: 기본 수집 안됨
- API 요청/응답: 기본 수집 안됨

### 전송 구간 보안
- 현재: HTTP 평문 전송 (사내망 한정)
- 강화 방안: TLS + mTLS 적용 가능

### 저장 데이터 민감도 (수집 레벨별)

| 레벨 | 환경변수 | 수집 내용 |
|---|---|---|
| 기본 | 없음 | 토큰, 비용, 세션, 이벤트 유형 |
| 프롬프트 | `OTEL_LOG_USER_PROMPTS=1` | + 프롬프트 전문 |
| 툴 상세 | `OTEL_LOG_TOOL_DETAILS=1` | + Bash 명령어, MCP 서버/툴명 |
| 최대 | `OTEL_LOG_RAW_API_BODIES=1` | + API 요청/응답 전체 (대화 이력) |

---

## 11. 향후 확장 가능성

### 다른 백엔드 연동
OTEL 표준을 사용하므로 Collector 설정만 바꾸면 다른 백엔드로 전환 가능:
- Datadog, Grafana Cloud, Jaeger, Splunk 등

### Trace 활용 (베타)
- `CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1` 활성화
- 프롬프트 → API 호출 → 툴 실행 전체 흐름을 단일 Trace로 조회 가능
- Bash 서브프로세스도 `TRACEPARENT`로 연결 가능

---

## 12. 참고 문서

- [Claude Code Monitoring 공식 문서](https://code.claude.com/docs/en/monitoring-usage)
- [OpenTelemetry 공식 사이트](https://opentelemetry.io)
- [EDOT Collector 문서](https://www.elastic.co/docs/reference/edot-collector)
- [Elastic Security Labs - Claude Code Monitoring](https://www.elastic.co/security-labs/claude-code-cowork-monitoring-otel-elastic)
- [Detection Engineering for Claude Code](https://www.monad.com/blog/detection-engineering-for-claude-code-part-1)
