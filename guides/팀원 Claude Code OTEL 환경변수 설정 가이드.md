# 팀원 Claude Code OTEL 환경변수 설정 가이드

## 개요

Claude Code 사용 내역이 수집 서버(PM PC)로 전송됩니다.

> ⚠️ **본 설정은 업무 보안 감사 목적으로 운영됩니다.**  
> Claude Code 사용 시 프롬프트 및 사용 내역이 기록됩니다.  
> 수집 데이터는 PM / 보안담당자만 열람 가능합니다.

---

## 설정 방식 선택

환경변수 설정에는 두 가지 방식이 있습니다.

| 방식 | 누가 설정 | 팀원 작업 필요 여부 |
|---|---|---|
| **관리자 중앙 배포 (Managed Settings)** | PM / 관리자가 일괄 적용 | ❌ 불필요 (자동 적용) |
| **팀원 개인 설정** | 팀원이 직접 PowerShell 실행 | ✅ 필요 |

> **관리자 중앙 배포가 완료된 경우 아래 개인 설정은 하지 않아도 됩니다.**  
> 이 가이드의 나머지 내용은 관리자 배포 전 임시 방법이거나, 개인이 직접 활성화할 때 사용합니다.

### 관리자 중앙 배포란?

Claude Team 플랜의 경우 PM이 아래 경로에서 OTEL 환경변수를 조직 전체에 일괄 적용할 수 있습니다.

> claude.ai → 좌측 메뉴 → **Claude Code** → 스크롤 내려서 **관리형 설정 (settings.json)** → **[관리]** 버튼

적용되면 팀원이 Claude Code 실행 시 자동으로 수집이 시작되며, 팀원이 설정을 임의로 끌 수 없습니다.

현재 적용 여부는 정도원 대리에게 문의하세요.

---

## 수집 서버 정보

| 항목 | 값 |
|---|---|
| 서버 IP | `192.168.50.170` |
| 수집 포트 | `4328` (HTTP) |

---

## 환경변수 개인 설정 (임시 방법 / 관리자 배포 전)

> 관리자 중앙 배포(Managed Settings)가 완료된 경우 아래 작업은 불필요합니다.

PowerShell 열고 아래 명령어 한번에 붙여넣기:

```powershell
[System.Environment]::SetEnvironmentVariable("CLAUDE_CODE_ENABLE_TELEMETRY", "1", "User")
[System.Environment]::SetEnvironmentVariable("OTEL_METRICS_EXPORTER", "otlp", "User")
[System.Environment]::SetEnvironmentVariable("OTEL_LOGS_EXPORTER", "otlp", "User")
[System.Environment]::SetEnvironmentVariable("OTEL_EXPORTER_OTLP_PROTOCOL", "http/protobuf", "User")
[System.Environment]::SetEnvironmentVariable("OTEL_EXPORTER_OTLP_ENDPOINT", "http://192.168.50.170:4328", "User")
[System.Environment]::SetEnvironmentVariable("OTEL_LOG_USER_PROMPTS", "1", "User")
[System.Environment]::SetEnvironmentVariable("OTEL_LOG_TOOL_DETAILS", "1", "User")
```

---

## 설정 확인

PowerShell **새 창** 열고:

```powershell
echo $env:CLAUDE_CODE_ENABLE_TELEMETRY
echo $env:OTEL_EXPORTER_OTLP_ENDPOINT
echo $env:OTEL_LOG_USER_PROMPTS
echo $env:OTEL_LOG_TOOL_DETAILS
```

결과:
```
1
http://192.168.50.170:4328
1
1
```

4개 값 모두 출력되면 완료입니다.

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
| Bash 명령어 | 실행한 명령 (OTEL_LOG_TOOL_DETAILS=1) |
| MCP 서버명/툴명 | MCP 사용 내역 (OTEL_LOG_TOOL_DETAILS=1) |

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
[System.Environment]::SetEnvironmentVariable("OTEL_LOG_TOOL_DETAILS", $null, "User")
```

실행 후 **새 PowerShell** 열면 완전 삭제됩니다.

---

## IDE 터미널에서 임시 설정 (IntelliJ / PyCharm)

IDE 터미널은 시스템 환경변수가 적용 안 될 수 있습니다.  
아래 명령어를 터미널에 붙여넣고 같은 창에서 `claude` 실행하세요.

```powershell
$env:CLAUDE_CODE_ENABLE_TELEMETRY = "1"
$env:OTEL_METRICS_EXPORTER = "otlp"
$env:OTEL_LOGS_EXPORTER = "otlp"
$env:OTEL_EXPORTER_OTLP_PROTOCOL = "http/protobuf"
$env:OTEL_EXPORTER_OTLP_ENDPOINT = "http://192.168.50.170:4328"
$env:OTEL_LOG_USER_PROMPTS = "1"
$env:OTEL_LOG_TOOL_DETAILS = "1"
claude
```

> ⚠️ 터미널 창을 닫으면 초기화됩니다. IDE 재시작 시 매번 실행 필요.  
> 영구 적용은 위의 시스템 환경변수 설정 방법을 사용하세요.

---

## 문의

설정 관련 문의: 웹서비스파트 정도원 대리
