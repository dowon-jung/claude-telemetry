# 구축 진행 로그

## 2026-05-07 작업일지

### 목표
Claude Team 플랜 팀원들의 Claude Code 사용 내역을 OpenTelemetry로 수집하여 ElasticSearch에 저장하고 Kibana로 조회·감사한다.

---

### 전체 진행 타임라인

| 시간 | 작업 | 결과 |
|---|---|---|
| 오후 1시 | GitHub repo 생성 | `dowon-jung/claude-telemetry` |
| 오후 1시 | 구축 계획서 작성 | `IMPLEMENTATION_PLAN.md` |
| 오후 1시 | Docker Compose 구성 | ES/Kibana/OTEL 컨테이너 |
| 오후 1시 | 포트 충돌 해결 | 9201 / 5602 / 4328로 변경 |
| 오후 1시 | 컨테이너 정상 기동 | ES + Kibana + EDOT Collector ✅ |
| 오후 2시 | Claude Code 환경변수 설정 | `CLAUDE_CODE_ENABLE_TELEMETRY=1` |
| 오후 2시 | IT팀 방화벽 허용 | TCP 4328 인바운드 허용 완료 ✅ |
| 오후 2시 | OTEL 데이터 수신 확인 | 팀원/본인 프롬프트 수신 성공 ✅ |
| 오후 3시 | ES 저장 성공 | logs-generic-default data stream ✅ |
| 오후 3시 | Kibana Data View 설정 | claude-telemetry ✅ |
| 오후 3시 | 프롬프트 전문 수집 | OTEL_LOG_USER_PROMPTS=1 적용 ✅ |
| 오후 3시 | 팀원 수집 확인 | jyt@hanilnetworks.com 정상 수집 ✅ |
| 오후 4시 | Kibana 타임라인 대시보드 | 프롬프트 타임라인 패널 추가 ✅ |
| 오후 4시 | restart: always 설정 | PM PC 재부팅 시 자동 시작 ✅ |
| 오후 5시 | 슬랙 Alert 스크립트 | alert/slack_alert.py 작성 및 동작 확인 ✅ |
| 오후 5시 | 문서 정리 | README / 아키텍처 / OTEL 심층 가이드 작성 ✅ |

---

### 트러블슈팅 기록

#### 1. 포트 충돌 (9200)
- **원인**: 기존 ElasticSearch 컨테이너가 9200 점유 중
- **해결**: 외부 포트를 9201 / 5602 / 4328로 변경

#### 2. PowerShell 실행 권한 오류
- **원인**: Windows 보안 정책으로 스크립트 실행 차단
- **해결**: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

#### 3. 방화벽 인바운드 규칙 추가 권한 없음
- **원인**: 회사 도메인 계정(`HANILNETWORKS-IMG`)은 방화벽 변경 권한 없음
- **해결**: IT팀에 요청 → TCP 4328 인바운드 허용 완료
- **허용 범위**: 192.168.50.0/24 → 192.168.50.170:4328

#### 4. 환경변수명 오류
- **원인**: `ANTHROPIC_OTEL_ENABLED` (잘못된 변수명) 사용
- **해결**: `CLAUDE_CODE_ENABLE_TELEMETRY=1` 으로 수정

#### 5. ElasticSearch 저장 실패 (index_not_found_exception)
- **원인**: OTEL Collector v0.151.0 기본 매핑 모드가 `otel`로 변경되었고, ES 8.12+ 필요
- **시도1**: ES 8.13 + raw 모드 → 인덱스 자동생성 안됨
- **시도2**: ES 8.13 + 수동 인덱스 생성 → resource_not_found_exception
- **시도3**: ES 8.16 + otel 모드 → EDOT Collector 이미지 필요
- **해결**: ES 8.16 + elastic-agent(EDOT) 이미지로 전환 ✅

#### 6. EDOT Collector 이미지 태그 오류
- **원인**: `elastic-otel-collector:0.9.0` 이미지 없음
- **해결**: `elastic-agent:8.16.0` + `ELASTIC_AGENT_OTEL=true` 방식으로 전환

#### 7. IDE 터미널 환경변수 미적용
- **원인**: IntelliJ/PyCharm 터미널은 시스템 환경변수 설정 후 재시작 필요
- **해결**: IDE 재시작 또는 터미널 내 직접 설정 가이드 추가

#### 8. Kibana Alert Gold 라이선스 제한
- **원인**: Slack/Webhook/Email 커넥터 모두 Gold 라이선스 필요
- **해결**: Python 스크립트로 ES 직접 조회 → Slack Webhook 전송 방식으로 우회

---

### 최종 구축 환경

| 항목 | 값 |
|---|---|
| PM PC IP | 192.168.50.170 |
| Kibana | http://localhost:5602 |
| ElasticSearch | http://localhost:9201 |
| OTEL HTTP | localhost:4328 |
| ES 버전 | 8.16.0 |
| Kibana 버전 | 8.16.0 |
| OTEL Collector | elastic-agent:8.16.0 (EDOT 모드) |
| Data Stream | logs-generic-default |
| Kibana Data View | claude-telemetry |

---

### 최종 팀원 환경변수 목록

```powershell
CLAUDE_CODE_ENABLE_TELEMETRY=1
OTEL_METRICS_EXPORTER=otlp
OTEL_LOGS_EXPORTER=otlp
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
OTEL_EXPORTER_OTLP_ENDPOINT=http://192.168.50.170:4328
OTEL_LOG_USER_PROMPTS=1
```

---

### 수집 범위

| 클라이언트 | 수집 여부 | 이유 |
|---|---|---|
| 터미널 `claude` (CLI) | ✅ | 환경변수 적용됨 |
| Claude Code 데스크탑 앱 | ❌ | 환경변수 미적용 |
| claude.ai 웹 | ❌ | 브라우저 구간 개입 불가 |

---

### 향후 할 일

| 항목 | 우선순위 |
|---|---|
| Windows 작업 스케줄러로 슬랙 Alert 자동화 (5분마다) | 높음 |
| Kibana 대시보드 나머지 패널 (비용/모델/토큰) | 중간 |
| OTEL_LOG_TOOL_DETAILS=1 추가 (MCP/Bash 명령 수집) | 중간 |
| 전체 팀원 배포 완료 | 높음 |
| 데이터 보관 정책 (ILM) 설정 | 낮음 |
