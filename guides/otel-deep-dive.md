# OpenTelemetry (OTEL) 심층 가이드

## 1. OpenTelemetry란?

OpenTelemetry(OTel)는 **CNCF(Cloud Native Computing Foundation)** 에서 관리하는 오픈소스 관측성(Observability) 프레임워크다.

애플리케이션에서 발생하는 **Traces(추적), Metrics(지표), Logs(로그)** 세 가지 신호를 수집하고 전송하는 표준 규격을 제공한다.

벤더 중립적(Vendor-neutral) 설계로, 한 번 계측하면 Elastic, Datadog, Grafana, Jaeger 등 어떤 백엔드로도 데이터를 보낼 수 있다.

---

## 2. 세 가지 신호 (Signals)

### Traces (분산 추적)
- 하나의 요청이 여러 서비스를 거치는 전체 흐름을 추적
- Span 단위로 기록 (시작 시각, 종료 시각, 부모-자식 관계)
- 예: API 요청 → DB 조회 → 캐시 조회 → 응답 전체 흐름

### Metrics (지표)
- 시간에 따른 수치 데이터
- 예: 요청 수, 응답 시간, 토큰 사용량, 비용

### Logs (로그)
- 특정 시점의 이벤트 기록
- 예: 사용자 프롬프트 입력, API 호출, 오류 발생

> Claude Code는 주로 **Logs** 신호를 사용하여 이벤트를 전송한다.

---

## 3. OpenTelemetry 구성요소

```
애플리케이션 (Claude Code)
    │
    ├── SDK (계측 코드 내장)
    │       └── 이벤트 생성 및 OTLP 형식으로 변환
    │
    └── Exporter (전송 모듈)
            └── OTLP/HTTP 또는 OTLP/gRPC로 Collector에 전송

OTEL Collector
    │
    ├── Receiver (수신)  ← 여러 소스에서 데이터 수신
    ├── Processor (처리) ← 필터링, 변환, 배치
    └── Exporter (내보내기) ← 백엔드(ES, Datadog 등)로 전송
```

---

## 4. OTLP (OpenTelemetry Protocol)

OTLP는 OTel의 공식 데이터 전송 프로토콜이다.

| 방식 | 포트 | 특징 |
|---|---|---|
| OTLP/gRPC | 4317 | 바이너리, 고성능, 스트리밍 지원 |
| OTLP/HTTP | 4318 | JSON/Protobuf, 방화벽 친화적 |

> 본 프로젝트에서는 **OTLP/HTTP (포트 4318)** 를 사용한다.  
> HTTP가 사내 방화벽 환경에서 더 호환성이 좋기 때문이다.

---

## 5. Claude Code의 OTEL 구현

### 수집 활성화 방식
Claude Code는 환경변수로 OTEL 기능을 제어한다.

```
CLAUDE_CODE_ENABLE_TELEMETRY=1   → OTEL 전송 활성화
OTEL_LOGS_EXPORTER=otlp          → 로그를 OTLP로 전송
OTEL_METRICS_EXPORTER=otlp       → 메트릭을 OTLP로 전송
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf → HTTP + Protobuf 방식
OTEL_EXPORTER_OTLP_ENDPOINT=...  → 수집 서버 주소
OTEL_LOG_USER_PROMPTS=1          → 프롬프트 전문 포함 (기본 REDACTED)
OTEL_LOG_TOOL_DETAILS=1          → 툴 입력/출력 상세 포함
```

### 생성되는 이벤트 (5종)

```
claude_code.user_prompt     ← 프롬프트 입력
claude_code.api_request     ← API 호출 결과 (토큰, 비용, 모델)
claude_code.tool_result     ← 툴 실행 결과
claude_code.tool_decision   ← 툴 실행 승인 여부
claude_code.api_error       ← API 오류
```

### 데이터 흐름

```
사용자 입력
    ↓
Claude Code 내부 SDK가 user_prompt 이벤트 생성
    ↓
OTLP/HTTP로 Collector 전송 (POST /v1/logs)
    ↓
Anthropic API 호출
    ↓
api_request 이벤트 생성 (모델, 토큰, 비용, 응답시간)
    ↓
OTLP/HTTP로 Collector 전송
```

---

## 6. EDOT Collector (Elastic Distribution)

본 프로젝트에서는 표준 `otel/opentelemetry-collector-contrib` 대신 **EDOT(Elastic Distribution of OpenTelemetry) Collector**를 사용한다.

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

## 7. ElasticSearch data_stream

EDOT Collector는 데이터를 **data_stream** 방식으로 저장한다.

### data_stream이란?
- 시계열(time-series) 데이터에 최적화된 ES 인덱스 관리 방식
- 날짜별로 인덱스를 자동 분할 관리
- 본 프로젝트에서는 `logs-generic-default` data_stream에 저장됨

### 인덱스 명명 규칙
```
.ds-logs-generic-default-2026.05.07-000001
    │    │       │            │
    │    │       │            └── 날짜
    │    │       └── dataset
    │    └── type (logs)
    └── data stream prefix
```

---

## 8. 보안 고려사항

### 기본 보호 기능
- 프롬프트는 기본적으로 `<REDACTED>` 처리됨
- 툴 입력/출력도 기본적으로 수집 안 됨
- 명시적 환경변수 설정 시에만 전문 수집

### 전송 구간 보안
- 현재: HTTP 평문 전송 (사내망 한정)
- 강화 방안: TLS 적용 (`https://` 엔드포인트 사용)

### 저장 데이터 민감도
아래 정보가 ES에 평문으로 저장될 수 있음:
- 소스코드
- DB 접속정보
- API KEY
- 내부 시스템 URL
- 고객정보

### 권장 보안 조치
- ES 외부 노출 금지
- Kibana 접근 권한 제한
- 정기적인 데이터 삭제 정책 (ILM)
- 팀원 사전 동의 및 고지

---

## 9. 향후 확장 가능성

### 다른 백엔드 연동
OTEL 표준을 사용하므로 Collector 설정만 바꾸면 다른 백엔드로 전환 가능:

```yaml
exporters:
  # Datadog
  datadog:
    api:
      key: ${DD_API_KEY}

  # Grafana Cloud
  otlp:
    endpoint: https://otlp-gateway.grafana.net

  # Jaeger
  jaeger:
    endpoint: http://jaeger:14250
```

### 추가 수집 가능 항목
- `OTEL_LOG_TOOL_DETAILS=1` — 툴 입력/출력 상세 (bash 명령어, 파일 경로 등)
- 향후 Anthropic이 Response 전문 수집 지원 시 활용 가능

### 멀티 테넌트 구조
여러 팀/조직의 데이터를 분리 수집하려면:
- `data_stream.dataset` 속성으로 팀별 분리
- Kibana Space로 팀별 접근 권한 분리

---

## 10. 참고 문서

- [Claude Code Monitoring 공식 문서](https://docs.anthropic.com/en/docs/claude-code/monitoring-usage)
- [OpenTelemetry 공식 사이트](https://opentelemetry.io)
- [EDOT Collector 문서](https://www.elastic.co/docs/reference/edot-collector)
- [Elastic Security Labs - Claude Code Monitoring](https://www.elastic.co/security-labs/claude-code-cowork-monitoring-otel-elastic)
- [OTLP 스펙](https://opentelemetry.io/docs/specs/otlp/)

