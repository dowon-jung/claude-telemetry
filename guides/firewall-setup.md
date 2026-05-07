# PM PC 방화벽 설정 가이드

팀원 PC에서 수집 서버(PM PC)로 데이터가 들어올 수 있도록  
Windows 방화벽에서 4328 포트를 열어야 합니다.

---

## ✅ 현재 상태

**IT팀을 통해 방화벽 허용 완료 (2026-05-07)**

- 허용 범위: `192.168.50.0/24` → `192.168.50.170:4328`
- 프로토콜: TCP 인바운드

---

## 방화벽 인바운드 규칙 추가 (재설정 필요 시)

> 회사 도메인 계정은 방화벽 변경 권한이 없습니다.  
> IT팀에 아래 명령어 실행을 요청하거나 원격으로 적용 요청하세요.

PowerShell **관리자 권한**으로 실행:

```powershell
New-NetFirewallRule -DisplayName "OTEL Collector 4328" -Direction Inbound -Protocol TCP -LocalPort 4328 -RemoteAddress 192.168.50.0/24 -Action Allow
```

---

## 설정 확인

```powershell
Get-NetFirewallRule -DisplayName "OTEL Collector 4328"
```

`Enabled: True` 확인되면 완료.

---

## 팀원 연결 테스트

팀원 PC에서:

```powershell
curl http://192.168.50.170:4328
```

`404 page not found` 응답이 오면 연결 성공입니다.  
(404는 서버가 응답한다는 의미 — 정상)

---

## IT팀 요청 시 전달 내용

> "팀원 PC들에서 제 PC(192.168.50.170)로 들어오는 트래픽입니다.  
> 출발지: 192.168.50.0/24 (사내망)  
> 목적지: 192.168.50.170 포트 4328 TCP 인바운드 허용 요청드립니다."
