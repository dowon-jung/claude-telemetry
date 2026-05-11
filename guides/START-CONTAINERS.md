# cement-rag-assistant 컨테이너 시작 가이드

재부팅 후 개발 환경 복구 순서

---

## 현재 컨테이너 구성

| 그룹 | 컨테이너 | 이미지 | 포트 | 재부팅 후 |
|------|---------|-------|------|---------|
| docker | otel-collector | elastic-agent:8.16.0 | 4327:4317 | 🟢 자동 시작 |
| docker | kibana | kibana:8.16.0 | 5602:5601 | 🟢 자동 시작 |
| docker | elasticsearch | elasticsearch:8.16.0 | 9201:9200 | 🟢 자동 시작 |
| infra | cement-redis | redis:7-alpine | 6379:6379 | ⚪ 수동 시작 필요 |
| infra | cement-kafka | confluentinc/cp-kafka:7.5.0 | 9092:9092 | ⚪ 수동 시작 필요 |
| infra | cement-qdrant | qdrant:latest | 6333:6333 | ⚪ 수동 시작 필요 |
| infra | cement-neo4j | neo4j:5-community | 7474:7474 | ⚪ 수동 시작 필요 |
| cement-postgres | postgres:16 | 5432:5432 | ⚪ 수동 시작 필요 |
| cement-elasticsearch | elasticsearch:8.13.0 | 9200:9200 | ⚪ 수동 시작 필요 |

> ⚠️ `elasticsearch`(9201)와 `cement-elasticsearch`(9200)는 포트가 다르므로 충돌 없음

---

## 재부팅 후 복구 순서

### Step 1 — docker 그룹 자동 시작 확인

```powershell
docker ps | findstr "otel-collector\|kibana\|elasticsearch"
```

3개 모두 `Up` 상태이면 OK. 아니면:

```powershell
# docker 그룹 위