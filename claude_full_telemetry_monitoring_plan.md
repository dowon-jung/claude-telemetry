# Claude Full Telemetry Monitoring 구축 계획서

# 1. 개요

본 문서는 Claude Cowork / Claude Code 사용 내역을 Full Telemetry 기반으로 수집·저장·조회하기 위한 구축 계획서이다.

본 시스템은 아래 항목을 중앙 수집 및 조회 가능하도록 구성한다.

- 전체 Prompt
- 전체 Response
- Tool Input
- Tool Output
- Bash Command
- File Path
- URL
- 사용자 정보
- Session 정보
- Token / Cost
- Error / Latency

---

# 2. 구축 목표

## 운영 목적
- 사용자별 Claude 사용 내역 확인
- Prompt 검색
- 코드 생성 이력 조회
- 비용 분석
- 모델 사용 패턴 분석
- 장애 추적

## 보안 목적
- 위험 명령 탐지
- 민감 작업 Audit
- 이상행위 탐지
- Session 추적

---

# 3. 전체 아키텍처

```text
Claude Code / Cowork
        ↓
OTEL Exporter
        ↓
OpenTelemetry Collector
        ↓
ElasticSearch
        ↓
Kibana Dashboard
```

---

# 4. 추천 기술 스택

| 영역 | 기술 |
|---|---|
| Telemetry | OpenTelemetry |
| Collector | OTEL Collector |
| Storage | ElasticSearch |
| Dashboard | Kibana |
| Container | Docker Compose |
| Alert | Elastic Alerting |

---

# 5. Docker Compose 구성

## docker-compose.yml

```yaml
version: '3.8'

services:

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.13.0
    container_name: elasticsearch

    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false

    ports:
      - "9200:9200"

  kibana:
    image: docker.elastic.co/kibana/kibana:8.13.0
    container_name: kibana

    ports:
      - "5601:5601"

    environment:
      ELASTICSEARCH_HOSTS: http://elasticsearch:9200

    depends_on:
      - elasticsearch

  otel-collector:
    image: otel/opentelemetry-collector:latest
    container_name: otel-collector

    command: ["--config=/etc/otel-config.yaml"]

    volumes:
      - ./otel-config.yaml:/etc/otel-config.yaml

    ports:
      - "4317:4317"
      - "4318:4318"

    depends_on:
      - elasticsearch
```

---

# 6. OTEL Collector 설정

## otel-config.yaml

```yaml
receivers:
  otlp:
    protocols:
      grpc:
      http:

processors:
  batch:

exporters:

  debug:
    verbosity: detailed

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [debug]
```

---

# 7. Claude OTEL 활성화

## 환경 변수 설정

```bash
export ANTHROPIC_OTEL_ENABLED=true
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
```

---

# 8. 수집 대상 데이터

| 항목 | 설명 |
|---|---|
| user.email | 사용자 식별 |
| prompt | 사용자 Prompt |
| response | 모델 응답 |
| tool_input | Tool 입력값 |
| tool_output | Tool 결과 |
| bash command | 실행 명령 |
| file path | 접근 파일 |
| url | 접근 URL |
| token usage | 토큰 사용량 |
| cost | 비용 |
| latency | 응답시간 |
| session_id | 세션 식별 |
| error | 오류 정보 |

---

# 9. Kibana 조회 예시

## 사용자별 Prompt 조회

```text
user.email : "dev1@company.com"
```

---

## 특정 키워드 검색

```text
prompt : "jwt"
```

---

## 특정 명령 검색

```text
tool_input : "rm -rf"
```

---

## 특정 URL 검색

```text
url : "/admin"
```

---

# 10. 권장 인덱스 구조

## 인덱스명

```text
claude-telemetry-YYYY.MM.DD
```

---

# 11. 보관 정책

| 항목 | 권장 |
|---|---|
| Hot Data | 7일 |
| Warm Data | 30일 |
| 장기보관 | 비권장 |

---

# 12. 권장 보안 설정

## 필수 권장 사항

- 관리자 MFA 적용
- Kibana 접근 제한
- 관리자 접근 로그 기록
- TLS 적용
- Elastic 인증 적용
- IP 제한 적용

---

# 13. 위험 요소

## 민감정보 저장 가능성

아래 정보가 저장될 수 있음:

- 소스코드
- DB 접속정보
- API KEY
- 내부 URL
- 고객정보
- 운영 명령

---

## 로그 저장소 자체가 고위험 자산

ElasticSearch 유출 시:
- Prompt
- 코드
- 응답
- 내부 시스템 정보

전체 유출 가능성 존재.

---

# 14. 운영 권장 사항

## 관리자 권한 최소화

권장:
- 읽기 전용 계정 분리
- Super Admin 제한
- Audit Log 활성화

---

## 위험 명령 Alert

권장 탐지 패턴:

```text
rm -rf
DROP TABLE
kubectl delete
aws secret
password
```

---

# 15. 향후 확장 항목

## 기능 확장

- Session Replay
- Prompt Diff
- 사용자별 비용 차트
- 팀별 사용량 분석
- 이상행위 탐지
- Secret Detection

---

# 16. 구축 순서

| 단계 | 작업 |
|---|---|
| 1 | Docker 환경 구성 |
| 2 | ElasticSearch 실행 |
| 3 | Kibana 실행 |
| 4 | OTEL Collector 연결 |
| 5 | Claude OTEL 활성화 |
| 6 | Telemetry 수집 확인 |
| 7 | Kibana Dashboard 구성 |
| 8 | Alert 설정 |
| 9 | 운영 반영 |

---

# 17. 결론

Claude Telemetry는 개발 활동 수준의 상세 로그 수집이 가능하다.

따라서:
- 저장소 보안
- 접근 통제
- 보관 정책
- 관리자 감사

체계를 반드시 함께 운영해야 한다.

특히 Full Prompt / Full Response 저장은 민감정보 저장 가능성이 높으므로 운영 정책을 명확히 정의한 후 적용해야 한다.
