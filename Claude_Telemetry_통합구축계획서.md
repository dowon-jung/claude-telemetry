# Claude Code Telemetry Monitoring — 구축 계획 및 운영 현황 통합 문서

> 한일네트웍스 DI사업부 웹서비스파트 | 작성자: 정도원 | 작성일: 2026-05-11 | ver 1.0

---

## 목차

1. [개요](#1-개요)
2. [구축 목표](#2-구축-목표)
3. [전체 아키텍처](#3-전체-아키텍처)
4. [수집 데이터](#4-수집-데이터)
5. [Docker Compose 구성](#5-docker-compose-구성)
6. [환경변수 설정](#6-환경변수-설정)
7. [Kibana 조회 및 대시보드](#7-kibana-조회-및-대시보드)
8. [위험 명령 Alert](#8-위험-명령-alert)
9. [보관 정책](#9-보관-정책)
10. [보안 설정 및 위험 관리](#10-보안-설정-및-위험-관리)
11. [구축 과정 트러블슈팅](#11-구축-과정-트러블슈팅)
12. [구축 진행 현황](#12-구축-진행-현황)
13. [향후 확장 계획](#13-향후-확장-계획)
14. [레포지토리 파일 구성](#14-레포지토리-파일-구성)
15. [운영 원칙](#15-운영-원칙)

---

## 1. 개요

본 문서는 Claude Team 플랜 도입 이후 팀원들의 Claude Code 사용 내역을 Full Telemetry 기반으로 수집·저장·조회하기 위한 구축 계획 및 운영 현황을 통합 정리한 문서이다.

### 1.1 시작한 이유

한일네트웍스 웹서비스파트에서 Claude Team 플랜을 도입하면서 아래 문제가 발생했다.

- 팀원들이 Claude Code로 무슨 작업을 하는지 PM이 파악하기 어려움
- 소스코드, DB 접속정보, API KEY 등 민감정보가 AI에 입력될 가능성
- 토큰 비용이 얼마나 발생하는지 추적 불가
- 보안 감사 목적의 로그 체계 부재

이를 해결하기 위해 **OpenTelemetry 기반 Claude Code 사용 로그 수집 시스템**을 구축하였다.

---

## 2. 구축 목표

### 2.1 운영 목적

| 목표 항목 | 설명 |
|---|---|
| 사용자별 사용 내역 확인 | 팀원별 Claude Code 작업 현황 파악 |
| Prompt 검색 | 특정 키워드·작업 이력 조회 |
| 코드 생성 이력 조회 | 어떤 코드를 생성했는지 추적 |
| 비용 분석 | 사용자·날짜별 토큰 및 비용 집계 |
| 모델 사용 패턴 분석 | 어떤 모델을 얼마나 사용하는지 파악 |
| 장애 추적 | 에러 발생 시 원인 분석 |

### 2.2 보안 목적

| 보안 목표 | 설명 |
|---|---|
| 위험 명령 탐지 | rm -rf, DROP TABLE 등 위험 명령 실시간 감지 |
| 민감 작업 Audit | DB 접속정보·API KEY 입력 여부 사후 추적 |
| 이상행위 탐지 | 비정상적 사용 패턴 모니터링 |
| Session 추적 | 세션 단위 작업 흐름 파악 |

---

## 3. 전체 아키텍처

### 3.1 시스템 구성도

```
팀원 PC (Claude Code CLI)
  └── OTEL Exporter (환경변수 활성화)
          │
          │  HTTP / 포트 4328
          ↓
PM PC (192.168.50.170)
  └── Docker Compose
      ├── EDOT Collector (elastic-agent:8.16.0 / 포트 4328)
      ├── ElasticSearch 8.16.0 (포트 9201)
      └── Kibana 8.16.0 (포트 5602)
```

### 3.2 기술 스택

| 영역 | 기술 | 버전/비고 |
|---|---|---|
| Telemetry | OpenTelemetry (OTLP/HTTP) | OTLP over HTTP |
| Collector | Elastic Agent (EDOT 모드) | 8.16.0 |
| Storage | ElasticSearch | 8.16.0 / 포트 9201 |
| Dashboard | Kibana | 8.16.0 / 포트 5602 |
| Container | Docker Compose | PM PC (Windows) |
| Alert | Python Slack 스크립트 | Webhook 기반 |

---

## 4. 수집 데이터

| 항목 | 필드명 | 수집 여부 | 활성화 방법 |
|---|---|---|---|
| 사용자 이메일 | `Attributes.user.email` | ✅ 수집 | 기본 수집 |
| 프롬프트 전문 | `Attributes.prompt.value` | ✅ 수집 | `OTEL_LOG_USER_PROMPTS=1` |
| Tool 입력값 | `Attributes.tool_input` | ✅ 수집 | `OTEL_LOG_TOOL_DETAILS=1` |
| 사용 모델 | `Attributes.model` | ✅ 수집 | 기본 수집 |
| 비용 | `Attributes.cost_usd` | ✅ 수집 | 기본 수집 |
| 토큰 사용량 | `Attributes.input_tokens` / `output_tokens` | ✅ 수집 | 기본 수집 |
| 세션 ID | `Attributes.session.id` | ✅ 수집 | 기본 수집 |
| 응답시간 | `Attributes.latency` | ✅ 수집 | 기본 수집 |
| 에러 정보 | `Attributes.error` | ✅ 수집 | 기본 수집 |
| 이벤트 시각 | `@timestamp` | ✅ 수집 | 기본 수집 |
| Claude 응답 전문 | — | ❌ 미지원 | 현재 Claude Code 미지원 |
| Bash 명령 전문 | — | ⚠️ 부분 | Tool Input에 포함 |

---

## 5. Docker Compose 구성

### 5.1 docker-compose.yml

```yaml
services:

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.16.0
    container_name: elasticsearch
    restart: always
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - ES_JAVA_OPTS=-Xms512m -Xmx512m
    ports:
      - "9201:9200"
    volumes:
      - es-data:/usr/share/elasticsearch/data

  kibana:
    image: docker.elastic.co/kibana/kibana:8.16.0
    container_name: kibana
    restart: always
    ports:
      - "5602:5601"
    environment:
      ELASTICSEARCH_HOSTS: http://elasticsearch:9200
      XPACK_ENCRYPTEDSAVEDOBJECTS_ENCRYPTIONKEY: "hanilnetworks-kibana-alert-key-32chars"
      XPACK_REPORTING_ENCRYPTIONKEY: "hanilnetworks-kibana-report-key-32ch"
      XPACK_SECURITY_ENCRYPTIONKEY: "hanilnetworks-kibana-secure-key-32ch"
    depends_on:
      - elasticsearch

  otel-collector:
    image: docker.elastic.co/elastic-agent/elastic-agent:8.16.0
    container_name: otel-collector
    restart: always
    environment:
      - ELASTIC_AGENT_OTEL=true
    command: ["--config=/etc/otel-config.yaml"]
    volumes:
      - ./otel-config.yaml:/etc/otel-config.yaml
    ports:
      - "4327:4317"
      - "4328:4318"
    depends_on:
      - elasticsearch

volumes:
  es-data:
    driver: local
```

### 5.2 otel-config.yaml

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 5s
  transform/route:
    log_statements:
      - context: log
        conditions:
          - resource.attributes["service.name"] == "claude-code"
        statements:
          - set(resource.attributes["data_stream.dataset"], "claude_code")

exporters:
  debug:
    verbosity: detailed
  elasticsearch:
    endpoints: ["http://elasticsearch:9200"]

service:
  pipelines:
    logs:
      receivers: [otlp]
      processors: [batch, transform/route]
      exporters: [debug, elasticsearch]
```

---

## 6. 환경변수 설정

> **요약:** 관리자가 Managed Settings로 중앙 배포하면 팀원 개인 설정이 불필요하다.
> 개인 설정 방식(6.2)은 Managed Settings 배포 전 임시 방법이거나, 관리자 설정 없이 개인이 직접 활성화할 때 사용한다.

### 6.1 관리자 중앙 배포 (권장)

공식 문서 기준으로 관리자가 Managed Settings를 배포하면 팀원이 아무것도 설정하지 않아도 자동 적용된다.
설정한 환경변수는 **팀원이 덮어쓸 수 없다** (high precedence).

참고: https://code.claude.com/docs/en/monitoring-usage#administrator-configuration

#### 방법 A — Server-managed settings (Claude.ai 콘솔, MDM 없을 때 권장)

Claude Team / Enterprise 플랜 필요. Claude Code 2.1.38 이상 필요.

1. claude.ai → 좌측 메뉴 → **Claude Code**
2. 스크롤 내려서 **관리형 설정 (settings.json)** → **[관리]** 버튼 클릭
3. 아래 JSON 입력 후 저장
4. 팀원이 다음 Claude Code 실행 시 자동 수신

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

#### 방법 B — Endpoint-managed settings (MDM / GPO 있을 때)

IT팀이 MDM(또는 Windows GPO)으로 아래 파일을 각 PC에 배포한다.

**파일 경로 (Windows):**
```
%APPDATA%\Claude\managed-settings.json
```

**파일 내용:**
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

> 방법 A와 B 중 한일네트웍스 현재 환경에서는 **방법 A (Server-managed settings)** 가 IT팀 도움 없이 PM이 직접 처리할 수 있어 더 간편하다.

---

### 6.2 팀원 개인 설정 (임시 방법 / 관리자 배포 전)

> Managed Settings 배포가 완료되면 아래 개인 설정은 불필요하다. 현재는 임시 방법으로 운영 중.

#### Windows PowerShell 설정 명령

새 PowerShell을 열고 아래 명령어를 실행한다.

```powershell
[System.Environment]::SetEnvironmentVariable("CLAUDE_CODE_ENABLE_TELEMETRY", "1", "User")
[System.Environment]::SetEnvironmentVariable("OTEL_METRICS_EXPORTER", "otlp", "User")
[System.Environment]::SetEnvironmentVariable("OTEL_LOGS_EXPORTER", "otlp", "User")
[System.Environment]::SetEnvironmentVariable("OTEL_EXPORTER_OTLP_PROTOCOL", "http/protobuf", "User")
[System.Environment]::SetEnvironmentVariable("OTEL_EXPORTER_OTLP_ENDPOINT", "http://192.168.50.170:4328", "User")
[System.Environment]::SetEnvironmentVariable("OTEL_LOG_USER_PROMPTS", "1", "User")
[System.Environment]::SetEnvironmentVariable("OTEL_LOG_TOOL_DETAILS", "1", "User")
```

### 6.3 설정 확인 방법

설정 후 **새 PowerShell**을 열고 아래 명령으로 확인한다.

```powershell
echo $env:CLAUDE_CODE_ENABLE_TELEMETRY    # → 1
echo $env:OTEL_LOGS_EXPORTER              # → otlp
echo $env:OTEL_EXPORTER_OTLP_ENDPOINT     # → http://192.168.50.170:4328
echo $env:OTEL_LOG_USER_PROMPTS           # → 1
```

4개 값이 모두 출력되면 설정 완료. 이후 `claude` 실행 시 자동으로 PM PC로 수집된다.

### 6.4 IntelliJ / PyCharm 터미널 주의사항

IDE 내장 터미널은 시스템 환경변수가 적용되지 않을 수 있다. IDE 터미널에서 직접 아래와 같이 설정한다.

```powershell
$env:CLAUDE_CODE_ENABLE_TELEMETRY = "1"
$env:OTEL_LOGS_EXPORTER = "otlp"
$env:OTEL_EXPORTER_OTLP_PROTOCOL = "http/protobuf"
$env:OTEL_EXPORTER_OTLP_ENDPOINT = "http://192.168.50.170:4328"
$env:OTEL_LOG_USER_PROMPTS = "1"
```

---

## 7. Kibana 조회 및 대시보드

### 7.1 접속 정보

| 서비스 | URL | 비고 |
|---|---|---|
| Kibana | http://localhost:5602 | PM PC에서 접속 |
| ElasticSearch | http://localhost:9201 | 직접 API 조회 시 |

### 7.2 Data View 설정

Kibana → Stack Management → Data Views → Create data view

- Index pattern: `claude-telemetry*`
- Timestamp field: `@timestamp`

### 7.3 주요 조회 쿼리 (KQL)

| 목적 | KQL 쿼리 |
|---|---|
| 사용자별 프롬프트 조회 | `Attributes.user.email : "dev1@company.com"` |
| 특정 키워드 검색 | `Attributes.prompt.value : "jwt"` |
| 위험 명령 검색 | `Attributes.tool_input : "rm -rf"` |
| 특정 URL 접근 확인 | `Attributes.url : "/admin"` |
| 에러 발생 조회 | `Attributes.error : *` |
| 특정 모델 사용 조회 | `Attributes.model : "claude-opus*"` |

### 7.4 인덱스 구조

권장 인덱스명: `claude-telemetry-YYYY.MM.DD` (일별 롤링)

---

## 8. 위험 명령 Alert

### 8.1 탐지 패턴

아래 패턴이 Tool Input에 포함될 경우 Slack으로 알림을 발송한다.

| 패턴 | 위험 유형 |
|---|---|
| `rm -rf` | 파일 시스템 삭제 |
| `DROP TABLE` | DB 테이블 삭제 |
| `kubectl delete` | 운영 컨테이너 삭제 |
| `aws secret` | AWS 자격증명 접근 |
| `password` | 패스워드 노출 가능성 |
| `api_key` / `apikey` | API KEY 노출 가능성 |

### 8.2 스크립트 구성

```
alert/
├── slack_alert.py     # ElasticSearch polling → 위험 패턴 탐지 → Slack Webhook 발송
├── .env.example       # 환경변수 예시
└── README.md
```

`.env` 설정:

```
ELASTICSEARCH_URL=http://localhost:9201
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx
CHECK_INTERVAL_SECONDS=60
```

---

## 9. 보관 정책 (ILM)

| 티어 | 기간 | 설명 | 적용 상태 |
|---|---|---|---|
| Hot Data | 7일 | 즉시 조회 가능 | ⬜ 미설정 (예정) |
| Warm Data | 30일 | 조회 가능, 검색 속도 저하 | ⬜ 미설정 (예정) |
| Cold / 장기보관 | — | 권장하지 않음 | — |

ILM(Index Lifecycle Management) 설정은 Phase 4에서 적용 예정이다.

---

## 10. 보안 설정 및 위험 관리

### 10.1 보안 권장 사항

| 항목 | 권장 사항 | 적용 상태 |
|---|---|---|
| 접근 제한 | Kibana 사내망 한정 운영 | ✅ 적용 |
| 팀원 고지 | 프롬프트 수집 사실 사전 공지 및 동의 | ✅ 완료 |
| 열람 권한 | PM / 보안담당자만 접근 허용 | ✅ 정책 수립 |
| MFA | 관리자 계정 MFA 적용 | ⬜ 예정 |
| TLS | HTTPS + 인증서 적용 | ⬜ 예정 |
| Elastic 인증 | xpack.security 활성화 | ⬜ 예정 (현재 비활성) |
| IP 제한 | 관리자 IP 화이트리스트 | ⬜ 예정 |
| 감사 로그 | 관리자 접근 로그 기록 | ⬜ Phase 4 예정 |

### 10.2 위험 요소

ElasticSearch에 아래 민감정보가 저장될 수 있으므로 저장소 보안이 최우선이다.

- 소스코드
- DB 접속정보
- API KEY
- 내부 URL 및 서버 정보
- 고객 개인정보
- 운영 명령어

ElasticSearch 유출 시 Prompt 전문·코드·내부 시스템 정보 전체가 유출될 수 있으므로 외부 노출 차단이 필수이다.

---

## 11. 구축 과정 트러블슈팅

| 이슈 | 원인 | 해결 |
|---|---|---|
| OTEL Collector ↔ ES 버전 호환 오류 (`index_not_found_exception`) | OTEL Collector v0.151.0 기본 매핑 모드가 `otel`로 변경됨. ES 8.12+ 필요 | ES 8.16 + EDOT Collector (elastic-agent) 조합으로 전환 |
| 환경변수명 오류 | `ANTHROPIC_OTEL_ENABLED` 사용 | `CLAUDE_CODE_ENABLE_TELEMETRY=1` 로 수정 |
| 회사 PC 방화벽 권한 문제 | 도메인 계정으로는 방화벽 변경 불가 | IT팀에 TCP 4328 인바운드 허용 요청 처리 |
| IDE 터미널 환경변수 미적용 | IntelliJ/PyCharm 터미널은 시스템 환경변수 미상속 | IDE 터미널 내 직접 환경변수 설정 가이드 별도 제공 |

---

## 12. 구축 진행 현황

### Phase 1 — 서버 환경 구성

- [x] Docker 환경 구성 (docker-compose.yml 작성)
- [x] ElasticSearch 8.16 실행 확인
- [x] Kibana 8.16 실행 확인
- [x] EDOT Collector 연결 및 수신 확인

### Phase 2 — Claude Code 연동

- [x] 팀원 환경변수 설정 가이드 작성
- [x] PM PC 자체 수집 테스트
- [x] Kibana Data View 설정
- [x] IT팀 방화벽 4328 포트 오픈

### Phase 3 — 대시보드 구성

- [x] 프롬프트 타임라인 Discover 뷰 저장
- [x] 위험 명령 탐지 Alert 스크립트 작성
- [ ] 토큰/비용 집계 대시보드 구성

### Phase 4 — 운영 정책 수립

- [ ] 팀원 전체 환경변수 배포 및 고지 완료
- [ ] 보관 기간 정책 ILM 설정
- [ ] 관리자 접근 감사 로그 설정
- [ ] TLS / Elastic 인증 활성화

---

## 13. 향후 확장 계획

| 항목 | 설명 | 우선순위 |
|---|---|---|
| 토큰/비용 대시보드 | 팀원별·날짜별 비용 집계 차트 | 🔴 높음 |
| ILM 보관 정책 적용 | Hot 7일 / Warm 30일 자동 전환 | 🔴 높음 |
| Elastic 인증 활성화 | xpack.security + TLS 적용 | 🔴 높음 |
| 팀원 전체 배포 | IT팀 통해 GPO 또는 가이드 배포 | 🟡 중간 |
| Session Replay | 세션 단위 작업 흐름 재현 | 🟢 낮음 |
| Prompt Diff | 프롬프트 변경 이력 추적 | 🟢 낮음 |
| 이상행위 자동 탐지 | ML 기반 비정상 패턴 감지 | 🟢 낮음 |
| Secret Detection | 코드 내 시크릿 자동 탐지 | 🟢 낮음 |

---

## 14. 레포지토리 파일 구성

```
claude-telemetry/
├── README.md                               # 프로젝트 개요
├── Claude_Telemetry_통합구축계획서.md       # 통합 문서 (현재 파일)
├── docker/
│   ├── docker-compose.yml                  # 컨테이너 구성
│   └── otel-config.yaml                    # OTEL Collector 설정
├── alert/
│   ├── slack_alert.py                      # Slack 알림 스크립트
│   ├── .env.example                        # 환경변수 예시
│   └── README.md                           # Alert 가이드
└── guides/
    ├── team-env-setup.md                   # 팀원 환경변수 설정 가이드
    ├── firewall-setup.md                   # 방화벽 설정 가이드
    ├── otel-deep-dive.md                   # OpenTelemetry 심층 가이드
    ├── 아키텍쳐.md                          # 원리 및 플로우 문서
    └── progress-log.md                     # 작업일지
```

---

## 15. 운영 원칙

아래 원칙은 시스템 운영 전 기간 동안 반드시 준수한다.

1. **팀원 사전 고지 필수** — 프롬프트 로그 수집 사실 공지 및 동의 획득
2. **ElasticSearch 외부 노출 금지** — 사내망 한정 운영, 외부 IP 접근 차단
3. **열람 권한 최소화** — PM / 보안담당자만 Kibana 접근 허용
4. **열람 시 로그 기록** — 누가 언제 어떤 목적으로 조회했는지 추적
5. **보관 기간 준수** — ILM 설정 후 30일 초과 데이터 자동 삭제

특히 Full Prompt / Tool Input 저장은 민감정보 저장 가능성이 높으므로, 운영 정책을 명확히 정의한 후 적용해야 한다.
