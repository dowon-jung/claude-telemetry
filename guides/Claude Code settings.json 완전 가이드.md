# Claude Code settings.json 완전 가이드

> 공식 문서 기반 정리 | 조사일: 2026-05-11  
> 참고: https://code.claude.com/docs/en/settings  
> 참고: https://code.claude.com/docs/en/env-vars  
> 참고: https://code.claude.com/docs/en/permissions  
> 참고: https://code.claude.com/docs/en/hooks

---

## 📋 팀원용 한눈에 보기

> 이 문서가 처음이라면 여기만 읽어도 됩니다.

### settings.json이 뭔가요?

Claude Code의 동작 방식을 제어하는 설정 파일입니다. 크게 4가지를 제어합니다.

| 항목 | 쉽게 말하면 |
|---|---|
| `permissions` | Claude가 어떤 명령/파일에 접근할 수 있는지 허용·차단 |
| `env` | Claude Code 실행 시 자동으로 적용되는 환경변수 |
| `hooks` | 특정 상황 발생 시 자동으로 실행되는 스크립트 |
| `companyAnnouncements` | 팀원이 Claude Code 켤 때 표시되는 공지 문구 |

### 설정은 누가 어디서 관리하나요?

```
관리자(PM)  →  Managed 설정  →  팀원 전체 자동 적용  (팀원이 바꿀 수 없음)
팀원 개인   →  User 설정     →  나한테만 적용
프로젝트    →  Project 설정  →  해당 프로젝트 팀원 전체 적용
```

**한일네트웍스 현재 방식**: `claude.ai → Claude Code → 관리형 설정 (settings.json) → [관리] 버튼`  
PM이 JSON을 입력하고 저장하면 팀원이 다음 Claude Code 실행 시 자동 수신됩니다.

### 우리 팀에 적용 예정인 항목

| 설정 | 내용 | 상태 |
|---|---|---|
| `env` (OTEL) | 사용 내역 수집 (프롬프트, 비용, 명령어 포함) | ⬜ 예정 |
| `permissions.deny` | 위험 명령 차단 (`rm -rf`, `curl` 등) | ⬜ 예정 |
| `permissions.disableBypassPermissionsMode` | 권한 우회 잠금 | ⬜ 예정 |
| `companyAnnouncements` | "민감정보 입력 금지" 공지 표시 | ⬜ 예정 |

### 팀원이 알아야 할 핵심 3가지

1. **Claude Code 사용 내역이 수집됩니다** — 프롬프트 전문, 사용 모델, 비용, Bash 명령 포함. PM/보안담당자만 열람.
2. **일부 명령은 차단됩니다** — `rm -rf`, `curl` 등 위험 명령은 실행 전 자동 거부됩니다.
3. **별도 설정 없이 자동 적용됩니다** — 관리자가 배포하면 팀원은 아무것도 안 해도 됩니다.

---

## 목차

1. [설정 범위(Scope) 이해](#1-설정-범위scope-이해)
2. [파일 위치](#2-파일-위치)
3. [전체 키 목록](#3-전체-키-목록)
4. [permissions — 권한 제어](#4-permissions--권한-제어)
5. [env — 환경변수](#5-env--환경변수)
6. [hooks — 자동화 트리거](#6-hooks--자동화-트리거)
7. [모델 및 동작 설정](#7-모델-및-동작-설정)
8. [보안 및 MCP 제어 (Managed 전용)](#8-보안-및-mcp-제어-managed-전용)
9. [조직 운영 설정](#9-조직-운영-설정)
10. [샌드박스 설정](#10-샌드박스-설정)
11. [전체 예시 JSON](#11-전체-예시-json)
12. [한일네트웍스 권장 설정](#12-한일네트웍스-권장-설정)

---

## 1. 설정 범위(Scope) 이해

Claude Code는 계층적 설정 시스템을 사용한다. 우선순위가 높은 항목이 낮은 항목을 덮어쓴다.

| 범위 | 위치 | 적용 대상 | 팀 공유 | 우선순위 |
|---|---|---|---|---|
| **Managed** | 서버/MDM/파일 배포 | 조직 전체 | ✅ IT 배포 | 1 (최고) |
| **Command line** | `--settings` 플래그 | 현재 세션 | ❌ | 2 |
| **Local** | `.claude/settings.local.json` | 나 (이 프로젝트만) | ❌ | 3 |
| **Project** | `.claude/settings.json` | 프로젝트 전체 팀원 | ✅ git 커밋 | 4 |
| **User** | `~/.claude/settings.json` | 나 (전체 프로젝트) | ❌ | 5 (최저) |

> **핵심**: Managed 설정은 어떤 것으로도 덮어쓸 수 없다. 보안 정책은 반드시 Managed 범위에 넣어야 한다.

### Managed 설정 배포 방법

| 방법 | 경로/위치 | 환경 |
|---|---|---|
| **Server-managed** (권장) | claude.ai → Claude Code → 관리형 설정 | MDM 없을 때 |
| **파일 배포 (Windows)** | `C:\Program Files\ClaudeCode\managed-settings.json` | GPO/MDM |
| **파일 배포 (macOS)** | `/Library/Application Support/ClaudeCode/managed-settings.json` | Jamf/Kandji |
| **파일 배포 (Linux)** | `/etc/claude-code/managed-settings.json` | 서버 환경 |
| **Windows 레지스트리** | `HKLM\SOFTWARE\Policies\ClaudeCode` > `Settings` (REG_SZ) | GPO/Intune |
| **macOS MDM** | `com.anthropic.claudecode` managed preferences domain | Jamf 등 |

> **주의**: `C:\ProgramData\ClaudeCode\managed-settings.json` 경로는 v2.1.75부터 지원 종료. `C:\Program Files\ClaudeCode\` 로 이전 필요.

### 드롭인 디렉토리 (분할 관리)

`managed-settings.d/` 디렉토리에 여러 `.json` 파일을 넣으면 알파벳 순으로 병합된다.  
팀별로 독립적인 정책 파일을 관리할 때 유용하다.

```
C:\Program Files\ClaudeCode\
├── managed-settings.json        ← 베이스
└── managed-settings.d\
    ├── 10-telemetry.json        ← 먼저 병합
    └── 20-security.json         ← 나중에 병합 (충돌 시 우선)
```

---

## 2. 파일 위치

| 파일 | 위치 (Windows) | 위치 (macOS/Linux) |
|---|---|---|
| User 설정 | `%USERPROFILE%\.claude\settings.json` | `~/.claude/settings.json` |
| Project 설정 | `.claude\settings.json` (프로젝트 루트) | `.claude/settings.json` |
| Local 설정 | `.claude\settings.local.json` | `.claude/settings.local.json` |
| Managed 설정 | `C:\Program Files\ClaudeCode\managed-settings.json` | `/Library/Application Support/ClaudeCode/managed-settings.json` |
| MCP 설정 | `~\.claude.json` (유저) / `.mcp.json` (프로젝트) | 동일 |

---

## 3. 전체 키 목록

공식 문서 기준 settings.json에서 사용 가능한 모든 최상위 키:

| 키 | 타입 | 범위 | 설명 |
|---|---|---|---|
| `$schema` | string | 모두 | JSON Schema 참조 (VS Code 자동완성용) |
| `agent` | string | 모두 | 기본 subagent 지정 |
| `allowedChannelPlugins` | array | Managed | 허용된 채널 플러그인 목록 |
| `allowedHttpHookUrls` | array | 모두 | HTTP Hook이 호출 가능한 URL 패턴 허용 목록 |
| `allowedMcpServers` | array | Managed | 허용된 MCP 서버 목록 |
| `allowManagedHooksOnly` | boolean | Managed | Managed 정의 Hook만 허용 |
| `allowManagedMcpServersOnly` | boolean | Managed | Managed 정의 MCP 서버만 허용 |
| `allowManagedPermissionRulesOnly` | boolean | Managed | Managed 정의 권한 규칙만 허용 |
| `alwaysThinkingEnabled` | boolean | 모두 | Extended thinking 기본 활성화 |
| `apiKeyHelper` | string | 모두 | API 키 동적 생성 스크립트 경로 |
| `attribution` | object | 모두 | git 커밋/PR 저작권 표시 커스터마이징 |
| `autoMemoryDirectory` | string | Policy/User | 자동 메모리 저장 디렉토리 |
| `autoMemoryEnabled` | boolean | 모두 | 자동 메모리 기능 활성화 |
| `autoUpdatesChannel` | string | 모두 | 업데이트 채널 (`stable` / `latest`) |
| `autoMode` | object | 모두 | Auto 권한 모드 환경 설정 |
| `availableModels` | array | Managed | 선택 가능한 모델 목록 제한 |
| `channelsEnabled` | boolean | 모두 | 채널 기능 활성화 |
| `cleanupPeriodDays` | number | 모두 | 대화 기록 보관 기간 (일) |
| `companyAnnouncements` | array | 모두 | Claude Code 실행 시 팀원에게 표시할 공지 |
| `defaultMode` | string | 모두 | 기본 권한 모드 |
| `deniedMcpServers` | array | 모두 | 차단할 MCP 서버 목록 |
| `enabledPlugins` | array | 모두 | 활성화할 플러그인 목록 |
| `env` | object | 모두 | 환경변수 설정 |
| `extraKnownMarketplaces` | object | Managed | 추가 플러그인 마켓플레이스 정의 |
| `hooks` | object | 모두 | 자동화 훅 설정 |
| `minimumVersion` | string | 모두 | 최소 Claude Code 버전 강제 |
| `model` | string | 모두 | 기본 모델 지정 |
| `modelOverrides` | object | 모두 | 모델 별칭 오버라이드 |
| `permissions` | object | 모두 | 권한 규칙 (allow/deny/ask) |
| `persistSession` | boolean | 모두 | 세션 기록 저장 여부 |
| `policyHelper` | string | Managed(MDM) | 정책 동적 생성 스크립트 경로 |
| `sandbox` | object | 모두 | 샌드박스 파일/네트워크 제한 |
| `strictKnownMarketplaces` | boolean | Managed | 마켓플레이스 제한 |
| `wslInheritsWindowsSettings` | boolean | Managed(MDM) | WSL이 Windows 설정 상속 |

---

## 4. permissions — 권한 제어

### 기본 구조

```json
"permissions": {
  "allow": [],
  "ask": [],
  "deny": [],
  "defaultMode": "default",
  "disableBypassPermissionsMode": "disable",
  "disableAutoMode": "disable",
  "allowManagedPermissionRulesOnly": true
}
```

### 권한 모드 (defaultMode)

| 모드 | 설명 | 권장 환경 |
|---|---|---|
| `default` | 처음 사용하는 툴마다 확인 요청 | 일반 개발 |
| `acceptEdits` | 파일 편집 및 일반 파일시스템 명령 자동 허용 | 신뢰하는 프로젝트 |
| `plan` | 분석만 가능, 파일 수정/명령 실행 불가 | 코드 리뷰 |
| `auto` | AI가 자동 판단하여 승인 (안전성 검사 포함) | 자동화 환경 |
| `dontAsk` | 사전 허용된 것만 자동 실행, 나머지 자동 거부 | 엄격한 제어 |
| `bypassPermissions` | 모든 권한 확인 생략 (위험) | 격리된 컨테이너 환경만 |

### 권한 규칙 문법

규칙 평가 순서: **deny → ask → allow** (deny가 항상 우선)

```
Tool               모든 사용 허용
Tool(specifier)    특정 조건만 허용
Tool(*)            모든 사용 허용 (Tool과 동일)
```

#### Bash 규칙 예시

```json
"permissions": {
  "allow": [
    "Bash(npm run *)",           // npm run으로 시작하는 모든 명령
    "Bash(git commit *)",        // git commit 명령
    "Bash(git * main)",          // main 브랜치 관련 git 명령
    "Bash(* --version)",         // 버전 확인 명령
    "Read(~/.zshrc)"             // 특정 파일 읽기
  ],
  "deny": [
    "Bash(rm -rf *)",            // 재귀 삭제 차단
    "Bash(curl *)",              // curl 차단
    "Bash(wget *)",              // wget 차단
    "Bash(git push *)",          // git push 차단
    "Bash(DROP TABLE *)",        // DB 삭제 차단
    "Bash(kubectl delete *)",    // k8s 삭제 차단
    "Read(./.env)",              // .env 파일 읽기 차단
    "Read(./.env.*)",
    "Read(./secrets/**)"
  ]
}
```

> **주의**: `Bash(ls *)` 와 `Bash(ls*)` 는 다르다.  
> - `Bash(ls *)` → `ls -la` 허용, `lsof` 차단  
> - `Bash(ls*)` → `ls -la`와 `lsof` 모두 허용

#### 지원하는 Tool 목록

```
Bash, PowerShell, Read, Edit, Write, WebFetch, WebSearch,
Glob, Grep, Agent, Skill, TodoWrite, TaskCreate, TaskGet,
TaskList, TaskOutput, TaskStop, TaskUpdate, KillShell,
ExitPlanMode, Monitor, NotebookEdit, LSP, mcp__<서버명>
```

#### WebFetch 도메인 제한

```json
"permissions": {
  "allow": ["WebFetch(domain:github.com)", "WebFetch(domain:docs.company.com)"],
  "deny": ["WebFetch"]
}
```

#### 복합 명령 처리

- `&&`, `||`, `;`, `|` 등으로 연결된 명령은 각각 독립적으로 평가
- `Bash(safe-cmd *)` 규칙은 `safe-cmd && rm -rf /` 명령을 허용하지 않음
- `timeout`, `time`, `nice`, `nohup`, `stdbuf`, `xargs` 등 래퍼는 자동으로 제거 후 평가

#### 기본적으로 허용되는 읽기 전용 명령 (별도 설정 불필요)

`ls`, `cat`, `head`, `tail`, `grep`, `find`, `wc`, `diff`, `stat`, `du`, `cd`, `git (읽기 전용)`

### Managed 전용 보안 설정

```json
"permissions": {
  "disableBypassPermissionsMode": "disable",  // bypass 모드 사용 불가
  "disableAutoMode": "disable"                 // auto 모드 사용 불가
},
"allowManagedPermissionRulesOnly": true        // Managed 규칙만 적용
```

---

## 5. env — 환경변수

settings.json의 `env` 키에 환경변수를 넣으면 Claude Code 실행 시 자동 적용된다.  
Managed settings에 넣으면 팀원이 덮어쓸 수 없다.

### 인증 관련

| 변수 | 설명 | 기본값 |
|---|---|---|
| `ANTHROPIC_API_KEY` | API 키 (로그인 대신 사용) | — |
| `ANTHROPIC_AUTH_TOKEN` | Authorization 헤더 커스텀 값 | — |
| `ANTHROPIC_BASE_URL` | API 엔드포인트 오버라이드 (프록시/게이트웨이) | — |
| `ANTHROPIC_CUSTOM_HEADERS` | 요청에 추가할 커스텀 헤더 (`Name: Value` 형식) | — |
| `ANTHROPIC_BETAS` | 추가 anthropic-beta 헤더 값 (콤마 구분) | — |

### 모델 관련

| 변수 | 설명 |
|---|---|
| `ANTHROPIC_MODEL` | 기본 모델 지정 (`claude-opus-4-6`, `claude-sonnet-4-6` 등) |
| `ANTHROPIC_DEFAULT_SONNET_MODEL` | Sonnet 계열 기본 모델 지정 |
| `ANTHROPIC_DEFAULT_OPUS_MODEL` | Opus 계열 기본 모델 지정 |
| `ANTHROPIC_DEFAULT_HAIKU_MODEL` | Haiku 계열 기본 모델 지정 |
| `ANTHROPIC_CUSTOM_MODEL_OPTION` | `/model` 선택기에 커스텀 모델 추가 |
| `CLAUDE_CODE_DISABLE_1M_CONTEXT` | `1` = 1M 컨텍스트 창 비활성화 |
| `CLAUDE_CODE_EFFORT_LEVEL` | 추론 노력 수준 (`low`, `medium`, `high`, `xhigh`, `max`, `auto`) |
| `CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING` | `1` = 적응형 추론 비활성화 |
| `CLAUDE_CODE_DISABLE_THINKING` | `1` = Extended thinking 비활성화 |
| `CLAUDE_CODE_DISABLE_FAST_MODE` | `1` = 빠른 모드 비활성화 |

### OTEL 텔레메트리

| 변수 | 설명 | 예시 |
|---|---|---|
| `CLAUDE_CODE_ENABLE_TELEMETRY` | `1` = OTEL 텔레메트리 활성화 | `"1"` |
| `OTEL_METRICS_EXPORTER` | 메트릭 내보내기 방식 | `"otlp"`, `"prometheus"`, `"console"`, `"none"` |
| `OTEL_LOGS_EXPORTER` | 로그 내보내기 방식 | `"otlp"`, `"console"`, `"none"` |
| `OTEL_TRACES_EXPORTER` | 트레이스 내보내기 방식 (베타) | `"otlp"`, `"none"` |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | OTLP 프로토콜 | `"grpc"`, `"http/protobuf"`, `"http/json"` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP 수집 엔드포인트 | `"http://192.168.50.170:4328"` |
| `OTEL_EXPORTER_OTLP_HEADERS` | OTLP 인증 헤더 | `"Authorization=Bearer token"` |
| `OTEL_EXPORTER_OTLP_METRICS_PROTOCOL` | 메트릭 전용 프로토콜 (일반 설정 오버라이드) | — |
| `OTEL_EXPORTER_OTLP_METRICS_ENDPOINT` | 메트릭 전용 엔드포인트 | — |
| `OTEL_EXPORTER_OTLP_LOGS_PROTOCOL` | 로그 전용 프로토콜 | — |
| `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT` | 로그 전용 엔드포인트 | — |
| `OTEL_LOG_USER_PROMPTS` | `1` = 프롬프트 전문 수집 | `"1"` |
| `OTEL_LOG_TOOL_DETAILS` | `1` = Tool 입력/출력 상세 수집 | `"1"` |
| `OTEL_METRIC_EXPORT_INTERVAL` | 메트릭 내보내기 간격 (ms, 기본 60000) | `"10000"` |
| `OTEL_LOGS_EXPORT_INTERVAL` | 로그 내보내기 간격 (ms, 기본 5000) | `"5000"` |
| `CLAUDE_CODE_ENHANCED_TELEMETRY_BETA` | `1` = 향상된 트레이스 수집 (베타) | `"1"` |

### 타임아웃 및 성능

| 변수 | 설명 | 기본값 |
|---|---|---|
| `API_TIMEOUT_MS` | API 요청 타임아웃 | `600000` (10분) |
| `BASH_DEFAULT_TIMEOUT_MS` | Bash 명령 기본 타임아웃 | `120000` (2분) |
| `BASH_MAX_TIMEOUT_MS` | Bash 명령 최대 타임아웃 | `600000` (10분) |
| `BASH_MAX_OUTPUT_LENGTH` | Bash 출력 최대 길이 (초과 시 중간 생략) | — |
| `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` | 자동 컨텍스트 압축 트리거 비율 (1-100, 기본 ~95) | — |
| `CLAUDE_CODE_AUTO_COMPACT_WINDOW` | 자동 압축 계산용 컨텍스트 창 크기 (토큰) | 모델 기본값 |

### 자동화 및 동작 제어

| 변수 | 설명 |
|---|---|
| `DISABLE_AUTOUPDATER` | `1` = 자동 업데이터 비활성화 |
| `DISABLE_UPDATES` | `1` = 모든 업데이트 경로 차단 (수동 포함) |
| `DISABLE_TELEMETRY` | `1` = Anthropic으로의 사용 데이터 전송 중단 |
| `DISABLE_NON_ESSENTIAL_TRAFFIC` | `1` = 분석/텔레메트리 등 비필수 트래픽 차단 |
| `DISABLE_INTERACTIVITY` | `1` = 대화형 프롬프트 비활성화 (CI 환경) |
| `CLAUDE_CODE_DISABLE_AUTO_MEMORY` | `1` = 자동 메모리 비활성화 |
| `CLAUDE_CODE_DISABLE_CLAUDE_MDS` | `1` = CLAUDE.md 파일 로딩 차단 |
| `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS` | `1` = 백그라운드 작업 비활성화 |
| `CLAUDE_CODE_DISABLE_CRON` | `1` = 스케줄 작업 비활성화 |
| `CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY` | `1` = 세션 품질 설문 비활성화 |
| `CLAUDE_CODE_DISABLE_ATTACHMENTS` | `1` = 파일 첨부 처리 비활성화 (`@` 문법 → 텍스트로 전송) |
| `CLAUDE_CODE_SKIP_PROMPT_HISTORY` | `1` = 프롬프트 기록 저장 생략 |
| `CLAUDE_AUTO_BACKGROUND_TASKS` | `1` = 장시간 작업 자동 백그라운드 처리 강제 활성화 |
| `CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR` | `1` = 각 Bash/PowerShell 명령 후 원래 작업 디렉토리로 복귀 |

### 클라우드 연동

| 변수 | 설명 |
|---|---|
| `ANTHROPIC_VERTEX_PROJECT_ID` | Google Vertex AI GCP 프로젝트 ID |
| `ANTHROPIC_VERTEX_BASE_URL` | Vertex AI 엔드포인트 오버라이드 |
| `ANTHROPIC_BEDROCK_BASE_URL` | Amazon Bedrock 엔드포인트 오버라이드 |
| `AWS_BEARER_TOKEN_BEDROCK` | Bedrock API 키 |
| `ANTHROPIC_FOUNDRY_API_KEY` | Microsoft Foundry API 키 |
| `ANTHROPIC_FOUNDRY_BASE_URL` | Foundry 베이스 URL |

### TLS/보안

| 변수 | 설명 |
|---|---|
| `CLAUDE_CODE_CERT_STORE` | CA 인증서 소스 (`bundled`, `system`, 기본: `bundled,system`) |
| `CLAUDE_CODE_CLIENT_CERT` | mTLS 클라이언트 인증서 경로 |
| `CLAUDE_CODE_CLIENT_KEY` | mTLS 클라이언트 개인키 경로 |
| `CLAUDE_CODE_CLIENT_KEY_PASSPHRASE` | 암호화된 클라이언트 키 패스프레이즈 |

### 디버그

| 변수 | 설명 |
|---|---|
| `CLAUDE_CODE_DEBUG_LOGS_DIR` | 디버그 로그 파일 경로 오버라이드 |
| `CLAUDE_CODE_DEBUG_LOG_LEVEL` | 로그 레벨 (`verbose`, `debug`, `info`, `warn`, `error`) |
| `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS` | `1` = 실험적 베타 헤더 제거 (게이트웨이 호환성) |

---

## 6. hooks — 자동화 트리거

특정 이벤트 발생 시 스크립트/HTTP/LLM을 자동 실행한다.

### Hook 이벤트 전체 목록

| 이벤트 | 발생 시점 | 차단 가능 |
|---|---|---|
| `SessionStart` | 세션 시작/재개 시 | ❌ |
| `Setup` | `--init-only` 또는 `-p` 모드로 시작 시 | ❌ |
| `UserPromptSubmit` | 프롬프트 제출 직후 (처리 전) | ✅ |
| `UserPromptExpansion` | 슬래시 명령이 프롬프트로 확장될 때 | ✅ |
| `PreToolUse` | 툴 실행 **전** | ✅ |
| `PermissionRequest` | 권한 확인 대화상자 표시 시 | ✅ |
| `PermissionDenied` | auto 모드에서 툴 거부 시 | ❌ |
| `PostToolUse` | 툴 실행 **후** 성공 | ❌ |
| `PostToolUseFailure` | 툴 실행 실패 시 | ❌ |
| `PostToolBatch` | 병렬 툴 실행 묶음 완료 후 | ❌ |
| `SubagentStart` | Subagent 생성 시 | ❌ |
| `SubagentStop` | Subagent 종료 시 | ❌ |
| `TaskCreated` | 작업 생성 시 | ✅ |
| `TaskCompleted` | 작업 완료 시 | ❌ |
| `Stop` | Claude 응답 완료 시 | ❌ |
| `StopFailure` | API 오류로 턴 종료 시 | ❌ |
| `TeammateIdle` | 에이전트 팀원이 유휴 상태 전환 시 | ❌ |
| `InstructionsLoaded` | CLAUDE.md 파일이 컨텍스트에 로드될 때 | ❌ |
| `ConfigChange` | 설정 파일 변경 감지 시 | ❌ |
| `CwdChanged` | 작업 디렉토리 변경 시 (cd 명령 등) | ❌ |
| `FileChanged` | 감시 중인 파일 변경 시 | ❌ |
| `WorktreeCreate` | Worktree 생성 시 | ✅ |
| `WorktreeRemove` | Worktree 제거 시 | ✅ |
| `PreCompact` | 컨텍스트 압축 전 | ✅ |
| `PostCompact` | 컨텍스트 압축 완료 후 | ❌ |
| `Elicitation` | MCP 서버가 사용자 입력 요청 시 | ✅ |
| `ElicitationResult` | 사용자가 MCP 요청에 응답 후 | ✅ |
| `SessionEnd` | 세션 종료 시 | ❌ |
| `Notification` | Claude Code 알림 발송 시 | ❌ |

### Hook 타입

#### command (쉘 명령)

```json
{
  "type": "command",
  "command": "/path/to/script.sh",
  "timeout": 30,
  "async": false,
  "asyncRewake": false,
  "shell": "bash",
  "if": "Bash(rm *)",
  "statusMessage": "보안 검사 중..."
}
```

- `async: true` → 백그라운드 실행 (Claude를 차단하지 않음)
- `asyncRewake: true` → 백그라운드 실행 후 종료 코드 2 반환 시 Claude 재개
- `shell` → `bash` (기본) 또는 `powershell`
- `if` → 추가 권한 규칙 조건 (PreToolUse, PostToolUse 이벤트에서만 작동)

#### http (웹훅)

```json
{
  "type": "http",
  "url": "https://hooks.slack.com/services/xxx",
  "headers": {
    "Authorization": "Bearer ${SLACK_TOKEN}"
  },
  "allowedEnvVars": ["SLACK_TOKEN"],
  "timeout": 30
}
```

#### prompt (LLM 판단)

```json
{
  "type": "prompt",
  "prompt": "이 Bash 명령이 안전한지 판단해: $ARGUMENTS",
  "model": "claude-haiku-4-5-20251001",
  "timeout": 30
}
```

#### agent (멀티턴 LLM 검증)

```json
{
  "type": "agent",
  "prompt": "이 파일 수정이 보안 정책을 위반하는지 툴을 사용해서 검증해: $ARGUMENTS",
  "model": "claude-haiku-4-5-20251001",
  "timeout": 60
}
```

#### mcp_tool (MCP 서버 툴 호출)

```json
{
  "type": "mcp_tool",
  "server": "audit-server",
  "tool": "log_action",
  "input": {
    "file_path": "${tool_input.file_path}",
    "cwd": "${cwd}"
  },
  "timeout": 60
}
```

### Hook 설정 구조

```json
"hooks": {
  "PreToolUse": [
    {
      "matcher": "Bash",
      "hooks": [
        {
          "type": "command",
          "if": "Bash(rm *)",
          "command": "/usr/local/bin/block-rm.sh"
        }
      ]
    }
  ],
  "PostToolUse": [
    {
      "matcher": "Edit|Write",
      "hooks": [
        {
          "type": "command",
          "command": "/usr/local/bin/audit-edit.sh",
          "async": true
        }
      ]
    }
  ],
  "SessionStart": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "echo $(date) - Session started >> /var/log/claude-sessions.log",
          "async": true
        }
      ]
    }
  ]
}
```

### Hook 종료 코드 의미

| 종료 코드 | PreToolUse | PostToolUse | UserPromptSubmit |
|---|---|---|---|
| `0` | 허용 | 계속 | 허용 |
| `1` | 오류 (허용) | 오류 기록 | 오류 (허용) |
| `2` | **차단** | — | **차단** |

### Managed 전용 Hook 제어

```json
"allowManagedHooksOnly": true,          // Managed Hook만 허용
"allowedHttpHookUrls": [                // HTTP Hook URL 허용 목록
  "https://hooks.slack.com/*",
  "https://internal-audit.company.com/*"
]
```

---

## 7. 모델 및 동작 설정

```json
{
  "model": "claude-sonnet-4-6",
  "availableModels": ["sonnet", "opus"],
  "modelOverrides": {
    "opus": "anthropic.claude-opus-4-6-20251101-v1:0"
  },
  "alwaysThinkingEnabled": false,
  "defaultMode": "default",
  "autoMode": {
    "environment": [
      "Trusted repos: github.com/hanilnetworks",
      "Trusted internal domains: *.hanil.co.kr"
    ],
    "allow": [],
    "soft_deny": [],
    "hard_deny": []
  },
  "cleanupPeriodDays": 30,
  "autoUpdatesChannel": "stable",
  "minimumVersion": "2.1.38",
  "persistSession": true,
  "autoMemoryEnabled": true,
  "autoMemoryDirectory": "~/claude-memory"
}
```

### availableModels (Managed)

관리자가 선택 가능한 모델을 제한할 수 있다.

```json
"availableModels": ["sonnet", "haiku"]
// 설정 시 팀원은 /model, --model, ANTHROPIC_MODEL 로도 다른 모델 선택 불가
```

### attribution

git 커밋/PR에 표시되는 저작권 문구 커스터마이징.

```json
"attribution": {
  "commit": "🤖 Generated with Claude Code",
  "pr": "Generated with Claude Code assistance"
}
```

---

## 8. 보안 및 MCP 제어 (Managed 전용)

### MCP 서버 제어

```json
"allowManagedMcpServersOnly": true,     // Managed 정의 MCP만 허용
"allowedMcpServers": [
  { "serverName": "github" },
  { "serverName": "slack" }
],
"deniedMcpServers": [
  { "serverName": "external-unknown" }
]
```

### 플러그인 마켓플레이스 제한

```json
"strictKnownMarketplaces": true,        // 승인된 마켓플레이스만 허용
"extraKnownMarketplaces": {
  "team-tools": {
    "source": {
      "source": "settings",
      "name": "team-tools",
      "plugins": [
        {
          "name": "code-formatter",
          "source": { "source": "github", "repo": "company/code-formatter" }
        }
      ]
    }
  }
}
```

### policyHelper (MDM 전용)

디바이스 상태/신원 기반으로 동적으로 정책을 생성하는 스크립트.  
MDM 또는 시스템 managed-settings.json에서만 작동. 다른 범위에서는 무시.

```json
"policyHelper": "/usr/local/bin/compute-claude-policy.sh"
```

---

## 9. 조직 운영 설정

### companyAnnouncements

Claude Code 실행 시 팀원에게 표시되는 공지 메시지.

```json
"companyAnnouncements": [
  "코드 리뷰는 모든 PR에 필수입니다",
  "DB 접속정보를 AI에 입력하지 마세요",
  "보안 정책 변경: 2026-05-01부터 적용"
]
```

### apiKeyHelper

API 키를 동적으로 생성하는 스크립트. 임시 자격증명 시스템과 연동할 때 유용.

```json
"apiKeyHelper": "/usr/local/bin/generate-api-key.sh"
```

갱신 주기 설정:

```json
"env": {
  "CLAUDE_CODE_API_KEY_HELPER_TTL_MS": "3600000"
}
```

---

## 10. 샌드박스 설정

파일 시스템 및 네트워크 접근을 제한한다.

```json
"sandbox": {
  "filesystem": {
    "allowWrite": [
      "/tmp/**",
      "./src/**"
    ]
  },
  "network": {
    "allowedDomains": ["api.github.com", "*.company.com"],
    "deniedDomains": ["social-media.com"]
  }
}
```

> `sandbox.network.deniedDomains` — 더 넓은 allowedDomains 와일드카드에서 특정 도메인을 제외할 때 사용 (2026-04 추가).

---

## 11. 전체 예시 JSON

### 조직 Managed Settings 예시 (보안 중심)

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",

  "env": {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "OTEL_METRICS_EXPORTER": "otlp",
    "OTEL_LOGS_EXPORTER": "otlp",
    "OTEL_EXPORTER_OTLP_PROTOCOL": "http/protobuf",
    "OTEL_EXPORTER_OTLP_ENDPOINT": "http://192.168.50.170:4328",
    "OTEL_LOG_USER_PROMPTS": "1",
    "OTEL_LOG_TOOL_DETAILS": "1",
    "DISABLE_AUTOUPDATER": "0",
    "ANTHROPIC_MODEL": "claude-sonnet-4-6"
  },

  "permissions": {
    "deny": [
      "Bash(rm -rf *)",
      "Bash(curl *)",
      "Bash(wget *)",
      "Bash(git push *)",
      "Bash(kubectl delete *)",
      "Bash(DROP TABLE *)",
      "Bash(aws secret *)",
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)"
    ],
    "disableBypassPermissionsMode": "disable",
    "disableAutoMode": "disable"
  },

  "allowManagedPermissionRulesOnly": true,
  "allowManagedMcpServersOnly": true,
  "allowManagedHooksOnly": true,

  "companyAnnouncements": [
    "⚠️ Claude Code 사용 내역이 보안 감사 목적으로 수집됩니다",
    "DB 접속정보, API KEY, 개인정보를 AI에 입력하지 마세요",
    "문의: 웹서비스파트 정도원 대리"
  ],

  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "if": "Bash(rm -rf *)",
            "command": "echo '[BLOCKED] rm -rf 명령 차단됨' >> /var/log/claude-audit.log",
            "async": true
          }
        ]
      }
    ]
  },

  "cleanupPeriodDays": 30,
  "minimumVersion": "2.1.38",
  "autoUpdatesChannel": "stable"
}
```

### 개인 User Settings 예시 (개발 편의 중심)

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",

  "model": "claude-sonnet-4-6",
  "defaultMode": "acceptEdits",
  "alwaysThinkingEnabled": false,
  "autoMemoryEnabled": true,

  "permissions": {
    "allow": [
      "Bash(npm run *)",
      "Bash(git add *)",
      "Bash(git commit *)",
      "Bash(git status)",
      "Bash(git log *)",
      "Bash(git diff *)",
      "Bash(mvn *)",
      "Bash(gradle *)"
    ]
  },

  "attribution": {
    "commit": "Co-authored with Claude Code"
  }
}
```

---

## 12. 한일네트웍스 권장 설정

### 현재 구축 목표 기준 권장 Managed Settings

```json
{
  "env": {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "OTEL_METRICS_EXPORTER": "otlp",
    "OTEL_LOGS_EXPORTER": "otlp",
    "OTEL_EXPORTER_OTLP_PROTOCOL": "http/protobuf",
    "OTEL_EXPORTER_OTLP_ENDPOINT": "http://192.168.50.170:4328",
    "OTEL_LOG_USER_PROMPTS": "1",
    "OTEL_LOG_TOOL_DETAILS": "1"
  },

  "permissions": {
    "deny": [
      "Bash(rm -rf *)",
      "Bash(curl *)",
      "Bash(wget *)",
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)"
    ],
    "disableBypassPermissionsMode": "disable"
  },

  "companyAnnouncements": [
    "Claude Code 사용 내역이 보안 감사 목적으로 수집됩니다. 민감정보 입력 주의."
  ],

  "minimumVersion": "2.1.38"
}
```

### 단계별 적용 계획

| 단계 | 항목 | 상태 |
|---|---|---|
| 1단계 | `env` (OTEL 텔레메트리) | ⬜ 예정 |
| 2단계 | `permissions.deny` (위험 명령 차단) | ⬜ 예정 |
| 2단계 | `permissions.disableBypassPermissionsMode` | ⬜ 예정 |
| 3단계 | `companyAnnouncements` (팀원 공지) | ⬜ 예정 |
| 3단계 | `hooks` (실시간 Slack 알림) | ⬜ 예정 |
| 4단계 | `allowManagedMcpServersOnly` | ⬜ 검토 필요 |
| 4단계 | `allowManagedPermissionRulesOnly` | ⬜ 검토 필요 |

---

*공식 문서 링크*

- 설정 전체: https://code.claude.com/docs/en/settings
- 환경변수: https://code.claude.com/docs/en/env-vars
- 권한: https://code.claude.com/docs/en/permissions
- Hooks: https://code.claude.com/docs/en/hooks
- 서버 관리형 설정: https://code.claude.com/docs/en/server-managed-settings
- JSON Schema: https://json.schemastore.org/claude-code-settings.json
