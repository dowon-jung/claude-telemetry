# 팀원 Claude Code OTEL 환경변수 설정 가이드

## 개요

Claude Code 사용 내역이 수집 서버(PM PC)로 전송됩니다.  
아래 설정을 완료해야 로그 수집이 시작됩니다.

> ⚠️ **반드시 사내망(유선 이더넷)에 연결된 상태**에서 사용해야 수집됩니다.  
> 재택/외부 근무 시 VPN 연결 필요.

---

## 수집 서버 정보

| 항목 | 값 |
|---|---|
| 수집 서버 | PM PC (정도원 대리) |
| 서버 IP | `192.168.50.170` |
| 수집 포트 | `4328` (HTTP) |

---

## 환경변수 설정 (Windows)

### PowerShell을 **관리자 권한**으로 실행 후 아래 명령 입력

```powershell
[System.Environment]::SetEnvironmentVariable("ANTHROPIC_OTEL_ENABLED", "true", "User")
[System.Environment]::SetEnvironmentVariable("OTEL_EXPORTER_OTLP_ENDPOINT", "http://192.168.50.170:4328", "User")
```

---

## 설정 확인

PowerShell **새 창** 열고:

```powershell
echo $env:ANTHROPIC_OTEL_ENABLED
echo $env:OTEL_EXPORTER_OTLP_ENDPOINT
```

결과:
```
true
http://192.168.50.170:4328
```

두 값이 정상 출력되면 완료입니다.

---

## Claude Code 실행

```powershell
claude
```

이후 사용하는 모든 프롬프트가 수집 서버로 전송됩니다.

---

## 연결 테스트 (선택)

수집 서버가 응답하는지 확인:

```powershell
curl http://192.168.50.170:4328
```

---

## 주의사항

- 본 설정은 **업무 보안 감사 목적**으로 운영됩니다
- Claude Code 사용 시 Prompt 및 Response가 로그로 기록됩니다
- 수집 데이터는 PM / 보안담당자만 열람 가능합니다
- 문의: 웹서비스파트 정도원 대리

