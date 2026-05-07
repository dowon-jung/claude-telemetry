# 구축 진행 로그

## 2026-05-07 작업일지

### 목표
Claude Team 플랜 팀원들의 Claude Code 사용 내역을 OpenTelemetry로 수집하여 ElasticSearch에 저장하고 Kibana로 조회·감사한다.

---

### 완료 ✅

| 시간 | 작업 | 결과 |
|---|---|---|
| 오후 | GitHub repo 생성 | `dowon-jung/claude-telemetry` |
| 오후 | 구축 계획서 작성 | `IMPLEMENTATION_PLAN.md` |
| 오후 | Docker Compose 구성 | ES/Kibana/OTEL 컨테이너 |
| 오후 | 포트 충돌 해결 | 9201 / 5602 / 4328로 변경 |
| 오후 | 컨테이너 정상 기동 | ES + Kibana + OTEL Collector |
| 오후 | Claude Code 환경변수 설정 | `CLAUDE_CODE_ENABLE_TELEMETRY=1` |
| 오후 | 팀원 환경변수 설정 | IP: 192.168.50.170:4328 |
| 오후 | IT팀 방화벽 요청 | TCP 4328 인바운드 허용 완료 |
| 오후 | OTEL 데이터 수신 확인 | 팀원/본인 프롬프트 수신 성공 |

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
- **원인**: OTEL Collector v0.151.0 기본 매핑 모드가 `otel`로 변경되었고, 이는 ES 8.12+ 필요
- **시도1**: ES 8.13 + raw 모드 → 인덱스 자동생성 안됨
- **시도2**: ES 8.13 + 수동 인덱스 생성 → resource_not_found_exception
- **시도3**: ES 8.16 + otel 모드 → EDOT Collector 이미지 필요
- **현재**: ES 8.16 + elastic-agent(EDOT) 이미지로 전환 중

---

### 미완료 🔲

| 항목 | 사유 |
|---|---|
| ES 저장 확인 | EDOT Collector 이미지 전환 후 재테스트 필요 |
| Kibana Data View 설정 | ES 저장 성공 후 진행 |
| Kibana 대시보드 구성 | ES 저장 성공 후 진행 |
| 팀원 전체 배포 | 본인 테스트 완료 후 진행 |
| 운영 정책 문서화 | 별도 협의 필요 |

---

### 현재 환경 정보

| 항목 | 값 |
|---|---|
| PM PC IP | 192.168.50.170 |
| Kibana | http://localhost:5602 |
| ElasticSearch | http://localhost:9201 |
| OTEL HTTP | localhost:4328 |
| ES 버전 | 8.16.0 |
| Kibana 버전 | 8.16.0 |
| OTEL Collector | elastic-agent 8.16.0 (EDOT 모드) |

---

### 팀원 환경변수 설정값

```powershell
CLAUDE_CODE_ENABLE_TELEMETRY = 1
OTEL_METRICS_EXPORTER = otlp
OTEL_LOGS_EXPORTER = otlp
OTEL_EXPORTER_OTLP_PROTOCOL = http/protobuf
OTEL_EXPORTER_OTLP_ENDPOINT = http://192.168.50.170:4328
```

---

### 내일 할 일

1. EDOT Collector 기동 확인
2. Claude Code 프롬프트 → ES 저장 확인
3. Kibana Data View 설정
4. 대시보드 구성 (사용자별 프롬프트, 토큰/비용)
5. 팀원 전체 배포

