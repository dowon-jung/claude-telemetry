# Claude Code Telemetry 구축 계획

## 목표

Claude Code(CLI) 사용 내역을 OpenTelemetry로 수집하여  
ElasticSearch에 저장하고 Kibana로 조회·감사한다.

---

## 수집 대상

| 항목 | 내용 | 수집 여부 |
|---|---|---|
| Prompt | 팀원이 입력한 전체 프롬프트 | ✅ OTEL_LOG_USER_PROMPTS=1 |
| Tool Input | Bash 명령, MCP 서버/툴명 등 | ✅ OTEL_LOG_TOOL_DETAILS=1 |
| Token / Cost | 사용량 및 비용 | ✅ 기본 수집 |
| Session ID | 세션 식별자 | ✅ 기본 수집 |
| Latency | 응답 시간 | ✅ 기본 수집 |
| Error | 오류 정보 | ✅ 기본 수집 |
| Response | Claude 응답 전문 | ❌ 현재 미지원 |

---

## 전체 아키텍처

```
팀원 PC
└── Claude Code (CLI)
    └── OTEL Exporter (환경변수 활성화)
            ↓ HTTP / 포트 4328
PM PC (192.168.50.170)
└── Docker Compose
    ├── EDOT Collector (elastic-agent:8.16.0 / 포트 4328)
    ├── ElasticSearch 8.16.0 (포트 9201)
    └── Kibana 8.16.0 (포트 5602)
```

---

## 단계별 구축 순서

### Phase 1. 서버 환경 구성
- [x] Docker / Docker Compose 설치 확인
- [x] docker-compose.yml 작성
- [x] otel-config.yaml 작성
- [x] 컨테이너 실행 및 정상 확인

### Phase 2. Claude Code 연동
- [x] 팀원 PC 환경변수 설정 가이드 작성
- [x] OTEL 수집 테스트 (PM PC 먼저)
- [x] 데이터 수집 확인 (Kibana)

### Phase 3. 대시보드 구성
- [x] Data View 설정 (claude-telemetry)
- [x] 프롬프트 타임라인 뷰 (Discover 저장)
- [ ] 토큰/비용 집계 뷰
- [x] 위험 명령 탐지 Alert (슬랙 스크립트)

### Phase 4. 운영 정책 수립
- [x] 팀원 고지 및 동의
- [x] 열람 권한 정책 문서화
- [ ] 보관 기간 정책 적용 (ILM)
- [ ] 관리자 접근 감사 로그 설정

---

## 사전 준비 사항

| 항목 | 비고 | 상태 |
|---|---|---|
| Docker 설치된 서버 or PC | PM PC(Windows) 사용 | ✅ |
| 팀원 PC → 서버 네트워크 연결 | IT팀 통해 포트 4328 오픈 | ✅ |
| 팀원 Claude Code 설치 여부 확인 | CLI 환경 필수 | ✅ |

---

## 보안 운영 원칙

1. **팀원 사전 고지 필수** — 프롬프트 로그 수집 사실 공지
2. **ElasticSearch 외부 노출 금지** — 사내망 한정 운영
3. **열람 권한 최소화** — PM / 보안담당자만
4. **열람 시 로그 기록** — 누가 언제 봤는지 추적
5. **보관 기간 준수** — ILM 설정 예정

---

## 최종 파일 구성

```
claude-telemetry/
├── README.md                          # 프로젝트 개요
├── IMPLEMENTATION_PLAN.md             # 구축 계획서 (현재 문서)
├── claude_full_telemetry_monitoring_plan.md  # 초기 설계 문서
├── docker/
│   ├── docker-compose.yml             # 컨테이너 구성
│   └── otel-config.yaml               # OTEL Collector 설정
├── alert/
│   ├── slack_alert.py                 # 슬랙 알림 스크립트
│   ├── .env.example                   # 환경변수 예시
│   └── README.md                      # Alert 가이드
└── guides/
    ├── team-env-setup.md              # 팀원 환경변수 설정 가이드
    ├── architecture.md                # 원리 및 플로우 문서
    ├── otel-deep-dive.md              # OpenTelemetry 심층 가이드
    ├── firewall-setup.md              # 방화벽 설정 가이드
    └── progress-log.md               # 작업일지
```
