# 팀원 Claude Code OTEL 환경변수 설정 가이드

## 개요

Claude Code 사용 내역이 수집 서버(PM PC)로 전송됩니다.  
아래 설정을 완료해야 로그 수집이 시작됩니다.

> ⚠️ **본 설정은 업무 보안 감사 목적으로 운영됩니다.**  
> Claude Code 사용 시 프롬프트 및 응답이 로그로 기록됩니다.  
> 수집 데이터는 PM / 보안담당자만 열람 가능합니다.

---

## 수집 서버 정보

| 항목 | 값 |
|---|---|
| 서버 IP | `192.168.50.170` |
| 수집 포트 | `4328` (HTTP) |

---

## 환경변수 설정 (PowerShell)

PowerShell 열고 아래 명령어 한번에 붙여넣기:

```powershell
[System.Environment]::SetEnvironmentVariable("CLAUDE_CODE_ENABLE_TELEMETRY", "1", "User")
[System.Environment]::SetEnvironmentVariable("OTEL_METRICS_EXPORTER", "otlp", "User")
[System.Environment]::SetEnvironmentVariable("OTEL_LOGS_EXPORTER", "otlp", "User")
[System.Environment]::SetEnvironmentVariable("OTEL_EXPORTER_OTLP_PROTOCOL", "http/protobuf", "User")
[System.Environment]::SetEnvironmentVariable("OTEL_EXPORTER_OTLP_ENDPOINT", "http://192.168.50.170:4328", "User")
[System.Environment]::SetEnvironmentVariable("OTEL_LOG_USER_PROMPTS", "1", "User")
```

---

## 설정 확인

PowerShell **새 창** 열고:

```powershell
echo $env:CLAUDE_CODE_ENABLE_TELEMETRY
echo $env:OTEL_EXPORTER_OTLP_ENDPOINT
echo $env:OTEL_LOG_USER_PROMPTS
```

결과:
```
1
http://192.168.50.170:4328
1
```

세 값 모두 출력되면 완료입니다.

---

## Claude Code 실행

```powershell
claude
```

이후 사용하는 모든 프롬프트가 수집 서버로 전송됩니다.

---

## 수집되는 정보

| 항목 | 내용 |
|---|---|
| 프롬프트 전문 | 입력한 모든 내용 |
| 모델 | 사용 모델명 |
| 토큰 / 비용 | 사용량 및 비용 |
| 세션 ID | 세션 식별자 |
| 이메일 | 사용자 계정 |
| 시간 | 요청 시각 |

---

## 문의

설정 관련 문의: 웹서비스파트 정도원 대리

---

## 환경변수 삭제 방법

수집 중단이 필요할 때 PowerShell에서 실행:

```powershell
[System.Environment]::SetEnvironmentVariable("CLAUDE_CODE_ENABLE_TELEMETRY", $null, "User")
[System.Environment]::SetEnvironmentVariable("OTEL_METRICS_EXPORTER", $null, "User")
[System.Environment]::SetEnvironmentVariable("OTEL_LOGS_EXPORTER", $null, "User")
[System.Environment]::SetEnvironmentVariable("OTEL_EXPORTER_OTLP_PROTOCOL", $null, "User")
[System.Environment]::SetEnvironmentVariable("OTEL_EXPORTER_OTLP_ENDPOINT", $null, "User")
[System.Environment]::SetEnvironmentVariable("OTEL_LOG_USER_PROMPTS", $null, "User")
```

실행 후 **새 PowerShell** 열면 완전 삭제됩니다.
