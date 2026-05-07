# 팀원 Claude Code OTEL 환경변수 설정 가이드

## 개요

Claude Code 사용 내역이 수집 서버(PM PC)로 전송됩니다.  
아래 설정을 완료해야 로그 수집이 시작됩니다.

> ⚠️ **반드시 사내망(유선 이더넷)에 연결된 상태**에서 사용해야 수집됩니다.

---

## 수집 서버 정보

| 항목 | 값 |
|---|---|
| 서버 IP | `192.168.50.170` |
| 수집 포트 | `4328` (HTTP) |

---

## 환경변수 설정 (PowerShell)

### 기존 잘못된 변수 제거

```powershell
[System.Environment]::SetEnvironmentVariable("ANTHROPIC_OTEL_ENABLED", $null, "User")
```

### 올바른 변수 설정

```powershell
[System.Environment]::SetEnvironmentVariable("CLAUDE_CODE_ENABLE_TELEMETRY", "1", "User")
[System.Environment]::SetEnvironmentVariable("OTEL_METRICS_EXPORTER", "otlp", "User")
[System.Environment]::SetEnvironmentVariable("OTEL_LOGS_EXPORTER", "otlp", "User")
[System.Environment]::SetEnvironmentVariable("OTEL_EXPORTER_OTLP_PROTOCOL", "http/protobuf", "User")
[System.Environment]::SetEnvironmentVariable("OTEL_EXPORTER_OTLP_ENDPOINT", "http://192.168.50.170:4328", "User")
```

---

## 설정 확인

PowerShell **새 창** 열고:

```powershell
echo $env:CLAUDE_CODE_ENABLE_TELEMETRY
echo $env:OTEL_EXPORTER_OTLP_ENDPOINT
```

결과:
```
1
http://192.168.50.170:4328
```

---

## Claude Code 실행

```powershell
claude
```

이후 사용하는 모든 프롬프트가 수집 서버로 전송됩니다.

---

## 주의사항

- 본 설정은 **업무 보안 감사 목적**으로 운영됩니다
- Claude Code 사용 시 Prompt 및 Response가 로그로 기록됩니다
- 수집 데이터는 PM / 보안담당자만 열람 가능합니다
- 문의: 웹서비스파트 정도원 대리
