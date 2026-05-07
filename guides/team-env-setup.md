# 팀원 Claude Code OTEL 환경변수 설정 가이드

## 개요

팀원 PC에서 Claude Code 사용 시 Telemetry가 수집 서버로 전송됩니다.  
아래 설정을 완료해야 로그 수집이 시작됩니다.

---

## Windows 환경변수 설정 방법

### 방법 1. 시스템 환경변수 (영구 적용, 권장)

1. `Windows 검색` → **"시스템 환경 변수 편집"** 열기
2. 하단 **"환경 변수"** 클릭
3. **시스템 변수** 영역에서 **"새로 만들기"** 클릭
4. 아래 변수 두 개 추가

| 변수 이름 | 값 |
|---|---|
| `ANTHROPIC_OTEL_ENABLED` | `true` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://[서버IP]:4318` |

5. 확인 → **CMD / PowerShell 재시작**

---

### 방법 2. PowerShell (임시 적용, 테스트용)

```powershell
$env:ANTHROPIC_OTEL_ENABLED = "true"
$env:OTEL_EXPORTER_OTLP_ENDPOINT = "http://[서버IP]:4318"
```

> ⚠️ PowerShell 창을 닫으면 초기화됩니다.

---

## 설정 확인

```powershell
echo $env:ANTHROPIC_OTEL_ENABLED
echo $env:OTEL_EXPORTER_OTLP_ENDPOINT
```

둘 다 값이 출력되면 정상입니다.

---

## Claude Code 실행

```powershell
claude
```

이후 사용하는 모든 프롬프트가 수집 서버로 전송됩니다.

---

## 문의

설정 관련 문의: 웹서비스파트 정도원 대리
