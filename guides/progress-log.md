# 구축 진행 로그

## 2026-05-07

### 완료 ✅

| 항목 | 내용 |
|---|---|
| GitHub repo 생성 | dowon-jung/claude-telemetry |
| Docker Compose 구성 | ES(9201), Kibana(5602), OTEL(4328) |
| 컨테이너 기동 | elasticsearch / kibana / otel-collector 정상 실행 |
| Claude Code 실행 | Sonnet 4.6 · Claude Team · Hanilnetworks 정상 연결 |
| 환경변수 설정 | ANTHROPIC_OTEL_ENABLED=true / OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4328 |
| 팀원 가이드 작성 | guides/team-env-setup.md (IP: 192.168.50.170) |
| 방화벽 가이드 작성 | guides/firewall-setup.md |

### 미완료 🔲

| 항목 | 사유 | 예정 |
|---|---|---|
| Claude Code → OTEL 데이터 수신 확인 | 토큰 소진 | 14:00 이후 |
| Kibana Index Pattern 설정 | 데이터 수신 후 진행 | 14:00 이후 |
| 팀원 PC 방화벽 허용 | 회사 IT 정책 제한 → IT팀 요청 필요 | 별도 협의 |
| 팀원 환경변수 배포 | 방화벽 이후 진행 | 별도 협의 |

### 접속 정보

| 서비스 | URL |
|---|---|
| Kibana | http://localhost:5602 |
| ElasticSearch | http://localhost:9201 |
| OTEL Collector | http://localhost:4328 |

