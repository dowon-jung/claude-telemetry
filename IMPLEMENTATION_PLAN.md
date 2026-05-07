# Claude Code Telemetry 구축 계획

## 목표

Claude Code(CLI) 사용 내역을 OpenTelemetry로 수집하여  
ElasticSearch에 저장하고 Kibana로 조회·감사한다.

---

## 수집 대상

| 항목 | 내용 |
|---|---|
| Prompt | 팀원이 입력한 전체 프롬프트 |
| Response | Claude 응답 전문 |
| Tool Input | Bash 명령, 파일 경로, URL 등 |
| Tool Output | 명령 실행 결과 |
| Token / Cost | 사용량 및 비용 |
| Session ID | 세션 식별자 |
| Latency | 응답 시간 |
| Error | 오류 정보 |

---

## 전체 아키텍처

```
팀원 PC
└── Claude Code (CLI)
    └── OTEL Exporter (환경변수 활성화)
            ↓ HTTP/gRPC
    사내 서버 (또는 PM PC)
    └── Docker Compose
        ├── OTEL Collector (포트 4317/4318)
        ├── ElasticSearch (포트 9200)
        └── Kibana Dashboard (포트 5601)
```

---

## 단계별 구축 순서

### Phase 1. 서버 환경 구성
- [ ] Docker / Docker Compose 설치 확인
- [ ] docker-compose.yml 작성
- [ ] otel-config.yaml 작성
- [ ] 컨테이너 실행 및 정상 확인

### Phase 2. Claude Code 연동
- [ ] 팀원 PC 환경변수 설정 가이드 작성
- [ ] OTEL 수집 테스트 (PM PC 먼저)
- [ ] 데이터 수집 확인 (Kibana)

### Phase 3. 대시보드 구성
- [ ] Index Pattern 설정
- [ ] 사용자별 Prompt 조회 뷰
- [ ] 토큰/비용 집계 뷰
- [ ] 위험 명령 탐지 Alert

### Phase 4. 운영 정책 수립
- [ ] 팀원 고지 및 동의
- [ ] 열람 권한 정책 문서화
- [ ] 보관 기간 정책 적용
- [ ] 관리자 접근 감사 로그 설정

---

## 사전 준비 사항

| 항목 | 비고 |
|---|---|
| Docker 설치된 서버 or PC | 사내 서버 권장 |
| 팀원 PC → 서버 네트워크 연결 | 포트 4318 오픈 필요 |
| 팀원 Claude Code 설치 여부 확인 | CLI 환경 필수 |

---

## 보안 운영 원칙

1. **팀원 사전 고지 필수** — 프롬프트 로그 수집 사실 공지
2. **ElasticSearch 외부 노출 금지** — 사내망 한정 운영
3. **열람 권한 최소화** — PM / 보안담당자만
4. **열람 시 로그 기록** — 누가 언제 봤는지 추적
5. **보관 기간 준수** — Hot 7일, 이후 자동 삭제

---

## 파일 구성 (예정)

```
claude-telemetry/
├── README.md
├── IMPLEMENTATION_PLAN.md        ← 현재 문서
├── docker/
│   ├── docker-compose.yml
│   └── otel-config.yaml
├── guides/
│   └── team-env-setup.md         ← 팀원 환경변수 설정 가이드
└── dashboards/
    └── kibana-export.ndjson      ← Kibana 대시보드 설정
```

---

## 일정 (예상)

| 단계 | 소요 시간 |
|---|---|
| Phase 1. 서버 환경 구성 | 1일 |
| Phase 2. Claude Code 연동 | 1일 |
| Phase 3. 대시보드 구성 | 1~2일 |
| Phase 4. 운영 정책 수립 | 별도 협의 |

