# PM PC 방화벽 설정 가이드

팀원 PC에서 수집 서버(PM PC)로 데이터가 들어올 수 있도록  
Windows 방화벽에서 4328 포트를 열어야 합니다.

## 방화벽 인바운드 규칙 추가

PowerShell을 **관리자 권한**으로 실행:

```powershell
New-NetFirewallRule -DisplayName "OTEL Collector 4328" -Direction Inbound -Protocol TCP -LocalPort 4328 -Action Allow
```

## 설정 확인

```powershell
Get-NetFirewallRule -DisplayName "OTEL Collector 4328"
```

`Enabled: True` 확인되면 완료.

## 팀원 연결 테스트

팀원 PC에서:

```powershell
curl http://192.168.50.170:4328
```

응답 오면 연결 성공.
