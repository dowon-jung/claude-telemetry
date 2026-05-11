# Claude Code + MySQL MCP 보안 가이드

**한일네트웍스 DI사업부 / 작성: 정도원 대리 / 최종수정: 2026-05-05**

> 본 문서는 Claude Code 도입 시 발생할 수 있는 데이터베이스 보안 위협을 분석하고, 팀원 사용 가이드와 관리자 정책 가이드를 통합 제공합니다. 특히 ERP 파트의 프로시저 중심 개발 환경과 운영 DB 직접 연결 위험에 초점을 맞춥니다.

---

## 1. 개요

### 1.1 문서 목적

Claude Code의 MCP(Model Context Protocol) 기능은 강력한 생산성을 제공하지만, MySQL MCP를 통해 LLM이 회사 DB에 직접 접근하게 되면서 다음과 같은 위험이 발생합니다.

- 운영 DB에 대한 의도치 않은 `INSERT`/`UPDATE`/`DELETE`
- 스키마 변경(`DROP TABLE`, `ALTER TABLE` 등 DDL)
- 저장 프로시저의 무단 호출 또는 변경 (ERP 파트 핵심 위험)
- 민감 정보(고객정보, 인사정보) 외부 유출
- 권한 우회를 통한 감사 추적 회피

본 가이드는 **DB 계정 권한 분리(1차 방어)** 와 **Claude Code 관리형 설정(2차 방어)** 의 이중 방어 체계를 제시합니다.

### 1.2 적용 대상

- **개발자(팀원)**: Windows 환경에서 Claude Code 사용 시 준수 사항
- **시스템 관리자**: Linux 서버 / Windows AD 환경에서 정책 배포 시 가이드
- **DBA**: MySQL 계정 권한 설계 가이드

### 1.3 핵심 원칙

| 원칙 | 설명 |
|------|------|
| **최소 권한** | MCP 계정은 필요한 최소 권한만 부여. 기본은 `SELECT` only |
| **이중 방어** | DB 권한 + Claude Code 설정 양쪽 모두에서 차단 |
| **운영 DB 격리** | LLM은 운영 DB에 절대 직결 불가. 개발/스테이징 또는 읽기 전용 복제본만 허용 |
| **감사 가능성** | 모든 MCP 쿼리는 로그로 추적 가능해야 함 |
| **관리자 우선권** | 팀원 설정으로 회사 정책을 우회할 수 없도록 Managed Settings로 강제 |

---

## 2. 위협 분석 (Threat Model)

### 2.1 MySQL MCP의 동작 방식

대부분의 MySQL MCP 서버(예: `@modelcontextprotocol/server-mysql`, `mysql-mcp-server` 등)는 다음과 같이 동작합니다.

1. Claude가 자연어로 "최근 3일치 견적 데이터 보여줘" 요청
2. MCP 서버가 SQL 문자열 생성 (`SELECT * FROM tb_quote WHERE ...`)
3. 설정된 DB 계정으로 MySQL에 그대로 실행
4. 결과를 Claude에 반환

**핵심 우려점**: MCP 서버 자체에는 SQL 종류별(SELECT/INSERT/DDL) 필터링 기능이 거의 없습니다. 즉, Claude가 `DROP TABLE` SQL을 생성하면 MCP는 그대로 실행을 시도합니다. **유일한 신뢰할 수 있는 방어선은 MySQL 계정 권한입니다.**

### 2.2 주요 위협 시나리오

#### 시나리오 A: 의도치 않은 데이터 변경
> 개발자가 "tb_user 테이블에서 테스트 사용자 정리해줘"라고 요청
> → Claude가 운영 DB에 `DELETE FROM tb_user WHERE ...` 실행
> → **실제 사용자 데이터 손실**

#### 시나리오 B: ERP 프로시저 변경 (한일 환경 특화)
> 개발자가 "SP_TB_INV_DAILY_PD_TEMP2 프로시저 최적화해줘"라고 요청
> → Claude가 `DROP PROCEDURE` 후 `CREATE PROCEDURE` 실행
> → **운영 중인 프로시저가 검증 없이 교체됨**
> → 일배치 실패, 재고 데이터 오류

#### 시나리오 C: 스키마 파괴
> 개발자가 "이 테이블 구조 좀 바꿔줘"라고 요청
> → Claude가 `ALTER TABLE` 또는 `DROP COLUMN` 실행
> → **외래키 제약 위반, 응용 시스템 장애**

#### 시나리오 D: 민감 정보 유출
> Claude의 컨텍스트에 고객 개인정보, 직원 인사정보가 적재됨
> → 대화 로그를 통해 외부에 노출될 가능성
> → **개인정보보호법 위반 리스크**

#### 시나리오 E: 감사 추적 회피
> 모든 쿼리가 단일 MCP 계정으로 실행
> → 누가 어떤 변경을 했는지 추적 불가
> → **사고 발생 시 책임 소재 불분명**

### 2.3 위험도 매트릭스

| 위협 | 발생 가능성 | 영향도 | 종합 위험도 |
|------|:---:|:---:|:---:|
| 운영 DB 직접 변경 | 높음 | 치명적 | 🔴 Critical |
| 프로시저 무단 변경 (ERP) | 중간 | 치명적 | 🔴 Critical |
| 스키마 DDL 실행 | 중간 | 높음 | 🟠 High |
| 개인정보 컨텍스트 적재 | 높음 | 높음 | 🟠 High |
| 감사 추적 불가 | 매우 높음 | 중간 | 🟡 Medium |
| 의도치 않은 INSERT | 중간 | 중간 | 🟡 Medium |

---

## 3. MySQL 계정 권한 설계 (1차 방어선)

### 3.1 권한 분리 원칙

**MCP 전용 계정은 일반 개발 계정과 반드시 분리해야 합니다.** Claude Code가 사용하는 계정에 부여된 권한 = LLM이 DB에 행사할 수 있는 모든 능력입니다.

### 3.2 권한 레벨 정의

한일네트웍스 환경 기준 권장 4단계 분리:

| 레벨 | 계정 예시 | 권한 | 용도 |
|------|----------|------|------|
| L1 (조회 전용) | `claude_ro` | `SELECT` only | **표준 권장**. 일반 개발자용 |
| L2 (테스트 변경) | `claude_dev` | `SELECT, INSERT, UPDATE, DELETE` | 개발 DB에서만. 스테이징/운영 금지 |
| L3 (프로시저 호출) | `claude_proc` | L1 + `EXECUTE` | ERP 프로시저 결과 확인용 (변경 불가) |
| L4 (DDL) | 사용 금지 | - | LLM에 절대 부여하지 않음 |

### 3.3 SQL 명령어별 필요 권한 매핑

| SQL 명령 | 필요 MySQL 권한 | L1 | L2 | L3 |
|---------|----------------|:--:|:--:|:--:|
| `SELECT` | `SELECT` | ✅ | ✅ | ✅ |
| `INSERT` | `INSERT` | ❌ | ✅ | ❌ |
| `UPDATE` | `UPDATE` | ❌ | ✅ | ❌ |
| `DELETE` | `DELETE` | ❌ | ✅ | ❌ |
| `CREATE TABLE` | `CREATE` | ❌ | ❌ | ❌ |
| `DROP TABLE` | `DROP` | ❌ | ❌ | ❌ |
| `ALTER TABLE` | `ALTER` | ❌ | ❌ | ❌ |
| `TRUNCATE` | `DROP` | ❌ | ❌ | ❌ |
| `CALL procedure` | `EXECUTE` | ❌ | ❌ | ✅ |
| `CREATE PROCEDURE` | `CREATE ROUTINE` | ❌ | ❌ | ❌ |
| `ALTER PROCEDURE` | `ALTER ROUTINE` | ❌ | ❌ | ❌ |
| `DROP PROCEDURE` | `ALTER ROUTINE` | ❌ | ❌ | ❌ |
| `GRANT` | `GRANT OPTION` | ❌ | ❌ | ❌ |

### 3.4 계정 생성 SQL (실전 템플릿)

#### L1: 조회 전용 계정 (가장 일반적인 권장 구성)

```sql
-- 전용 계정 생성. 비밀번호는 Vault/KeePass 등으로 관리
CREATE USER 'claude_ro'@'192.168.%.%' IDENTIFIED BY '<강력한_비밀번호>';

-- SELECT만 허용. 특정 DB로 제한
GRANT SELECT ON erp_dev.* TO 'claude_ro'@'192.168.%.%';

-- 민감 테이블은 명시적으로 제외 (REVOKE)
REVOKE SELECT ON erp_dev.tb_employee_personal FROM 'claude_ro'@'192.168.%.%';
REVOKE SELECT ON erp_dev.tb_customer_pii FROM 'claude_ro'@'192.168.%.%';

-- 리소스 제한 (DoS 방어)
ALTER USER 'claude_ro'@'192.168.%.%'
  WITH MAX_QUERIES_PER_HOUR 1000
       MAX_CONNECTIONS_PER_HOUR 100
       MAX_USER_CONNECTIONS 5;

FLUSH PRIVILEGES;
```

#### L2: 개발 DB 변경 가능 계정 (개발 환경 한정)

```sql
CREATE USER 'claude_dev'@'192.168.%.%' IDENTIFIED BY '<강력한_비밀번호>';

-- 개발 DB에만 DML 허용. DDL은 절대 금지
GRANT SELECT, INSERT, UPDATE, DELETE ON erp_dev.* TO 'claude_dev'@'192.168.%.%';

-- DDL/프로시저 변경 명시적 차단 (default deny이지만 가독성 위해 명시)
-- GRANT는 부여하지 않음 = 자동 거부

ALTER USER 'claude_dev'@'192.168.%.%'
  WITH MAX_QUERIES_PER_HOUR 2000
       MAX_USER_CONNECTIONS 5;

FLUSH PRIVILEGES;
```

#### L3: 프로시저 호출 가능 (ERP 파트용)

```sql
CREATE USER 'claude_proc'@'192.168.%.%' IDENTIFIED BY '<강력한_비밀번호>';

GRANT SELECT ON erp_dev.* TO 'claude_proc'@'192.168.%.%';

-- 특정 프로시저만 EXECUTE 허용 (와일드카드 X, 명시적으로)
GRANT EXECUTE ON PROCEDURE erp_dev.SP_TB_INV_DAILY_PD_TEMP2 TO 'claude_proc'@'192.168.%.%';
GRANT EXECUTE ON PROCEDURE erp_dev.SP_SD_INV_CW_WAREHOUSE TO 'claude_proc'@'192.168.%.%';

-- CREATE/ALTER/DROP ROUTINE은 부여하지 않음 = 변경 불가
FLUSH PRIVILEGES;
```

### 3.5 운영 DB 보호 정책 (절대 규칙)

> ⚠️ **운영 DB(`erp_prod`, `hanil_prod` 등)는 어떤 Claude MCP 계정도 직접 접근 불가**

- 운영 DB 분석이 필요한 경우 → **읽기 전용 복제본(replica)** 에 별도 `claude_ro` 계정 생성
- 운영 DB의 `bind-address`는 운영 서버군 IP만 허용 (개발 PC IP 차단)
- 운영 DB의 `event_scheduler` 로그 + general log를 통한 모든 접근 감사

### 3.6 권한 검증 체크리스트

계정 생성 후 반드시 다음을 확인:

```sql
-- 1. 부여된 권한 확인
SHOW GRANTS FOR 'claude_ro'@'192.168.%.%';

-- 2. INSERT/UPDATE/DELETE/DDL이 실제로 거부되는지 테스트
-- (claude_ro로 접속 후)
INSERT INTO erp_dev.tb_test VALUES (1);  -- 에러 1142: INSERT command denied
DROP TABLE erp_dev.tb_test;              -- 에러 1142: DROP command denied
CREATE PROCEDURE sp_test() BEGIN END;    -- 에러 1370: alter routine denied

-- 3. 민감 테이블 접근 차단 확인
SELECT * FROM erp_dev.tb_employee_personal LIMIT 1;  -- 에러 1142
```

---

## 4. Claude Code 관리형 설정 (2차 방어선)

### 4.1 Managed Settings 개요

Claude Code는 **Managed Settings**라는 최상위 우선순위 설정 계층을 제공합니다. 관리자가 배포한 이 설정은 **팀원이 어떤 user/project 설정을 추가해도 절대 우회할 수 없습니다.**

### 4.2 설정 파일 배포 위치

| OS | 경로 | 배포 방법 |
|----|------|----------|
| Windows (개발자 PC) | `C:\Program Files\ClaudeCode\managed-settings.json` | Group Policy / Intune / 수동 배포 |
| Windows 레지스트리 | `HKLM\SOFTWARE\Policies\ClaudeCode` (`Settings` 값) | GPO |
| Linux (서버) | `/etc/claude-code/managed-settings.json` | Ansible / 수동 배포 |
| macOS | `/Library/Application Support/ClaudeCode/managed-settings.json` | MDM (Jamf 등) |

### 4.3 한일네트웍스 표준 Managed Settings (전체)

다음은 한일네트웍스 환경에 맞춘 권장 표준 정책입니다.

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",

  "forceLoginMethod": "claudeai",
  "forceLoginOrgUUID": "<한일네트웍스_조직_UUID>",

  "allowManagedMcpServersOnly": true,
  "allowManagedPermissionRulesOnly": true,
  "allowManagedHooksOnly": true,

  "allowedMcpServers": [
    { "serverName": "github" },
    { "serverName": "atlassian" },
    { "serverName": "mysql-readonly" },
    { "serverName": "filesystem-project" }
  ],

  "deniedMcpServers": [
    { "serverName": "mysql-prod" },
    { "serverName": "mysql-admin" },
    { "serverName": "filesystem-root" }
  ],

  "permissions": {
    "deny": [
      "Bash(mysql -u root *)",
      "Bash(mysqldump *)",
      "Bash(psql *)",
      "Bash(mongosh *)",
      "Bash(redis-cli *)",
      "Bash(ssh root@*)",
      "Bash(scp * root@*)",
      "Bash(curl http://*internal*)",
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)",
      "Read(./config/credentials.json)",
      "Read(./config/database.yml)",
      "Read(~/.aws/credentials)",
      "Read(~/.ssh/id_*)",
      "WebFetch(domain:*.hanilcement.com)"
    ],
    "ask": [
      "Bash(git push *)",
      "Bash(git push --force *)",
      "Bash(npm publish *)"
    ]
  },

  "sandbox": {
    "enabled": true,
    "failIfUnavailable": false,
    "allowUnsandboxedCommands": false,
    "filesystem": {
      "denyRead": [
        "~/.aws/credentials",
        "~/.ssh",
        "~/AppData/Roaming/Microsoft/Credentials"
      ]
    },
    "network": {
      "allowedDomains": [
        "github.com",
        "*.npmjs.org",
        "registry.npmjs.org",
        "api.anthropic.com",
        "*.hanilnetworks.com"
      ],
      "deniedDomains": [
        "*.prod.hanilnetworks.com"
      ],
      "allowManagedDomainsOnly": true
    }
  },

  "disableBypassPermissionsMode": "disable",
  "disableAutoMode": "disable",
  "disableSkillShellExecution": false,

  "minimumVersion": "2.1.100",
  "autoUpdatesChannel": "stable",

  "env": {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "OTEL_METRICS_EXPORTER": "otlp"
  },

  "companyAnnouncements": [
    "[보안] 운영 DB 직접 연결은 절대 금지입니다.",
    "[보안] MCP 사용 시 회사 보안 가이드를 준수하세요.",
    "문의: 정보보안팀 / DI사업부 정도원 대리"
  ]
}
```

### 4.4 핵심 설정 항목 상세 설명

#### `allowManagedMcpServersOnly: true`
> 가장 중요한 항목. 이 값이 `true`면 **`allowedMcpServers` 목록 외의 MCP 서버는 팀원이 추가해도 동작하지 않습니다.** 팀원이 자기 PC에서 `mysql-prod` MCP를 등록해도 무시됨.

#### `allowedMcpServers` / `deniedMcpServers`
> Allowlist + Denylist 동시 운영. **Denylist가 항상 우선.** 따라서 `mysql-prod`는 Allowlist에 누가 잘못 추가해도 차단됩니다.

#### `permissions.deny`
> Bash 명령어 패턴, 파일 읽기 패턴 차단. `Bash(mysql -u root *)`로 root 계정 직접 접속 차단. `Read(./.env)`로 환경변수 파일 노출 차단.

#### `sandbox.enabled: true`
> OS 수준 격리. Linux/WSL2/macOS에서 동작. **Windows 네이티브에서는 미지원**이므로 개발자 PC가 Windows이면 sandbox는 부분적용.

#### `sandbox.network.allowManagedDomainsOnly: true`
> 관리자가 허용한 도메인 외의 모든 외부 통신 차단. 데이터 유출 방어선.

#### `disableBypassPermissionsMode: "disable"`
> `--dangerously-skip-permissions` CLI 플래그 자체를 봉쇄. 팀원이 이 플래그로 모든 권한 우회하는 것을 막음.

### 4.5 Windows 환경 추가 고려사항

> ⚠️ Windows 네이티브 환경에서는 `sandbox` 기능이 **동작하지 않습니다.** 따라서 개발자 PC의 경우 다음 중 하나를 선택해야 합니다.

| 옵션 | 설명 | 권장도 |
|------|------|:--:|
| WSL2에서 Claude Code 실행 | sandbox 정상 동작. Linux 배포판 활용 | ⭐⭐⭐ 강력 권장 |
| Windows 네이티브 + 강화된 permission rules | sandbox 없음. permissions/MCP allowlist에만 의존 | ⭐⭐ 차선책 |
| 가상머신(Hyper-V/VirtualBox) 내 Linux | sandbox 동작. 환경 분리 명확 | ⭐⭐⭐ 보안 우선 시 |

**한일 환경 권장**: 개발자는 **WSL2 + Ubuntu**에서 Claude Code 실행. Managed Settings는 WSL 안의 `/etc/claude-code/managed-settings.json`에 배포.

WSL이 Windows 정책을 상속받게 하려면:

```json
{
  "wslInheritsWindowsSettings": true
}
```

이를 `HKLM\SOFTWARE\Policies\ClaudeCode`에 설정하면, Windows의 GPO가 WSL Claude Code에도 적용됩니다.

### 4.6 적용 확인 방법

팀원 측에서 정책 적용 여부를 확인:

```bash
# Claude Code 실행 후
/status
```

다음과 같은 출력이 나와야 정상:

```
Settings sources:
  - Enterprise managed settings (file): /etc/claude-code/managed-settings.json
  - User settings: ~/.claude/settings.json
  ...
```

---

## 5. MCP 서버 구성 가이드

### 5.1 권장 MCP 구성 패턴

한일네트웍스 표준 MCP 구성 (개발 환경):

```json
{
  "mcpServers": {
    "mysql-readonly": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-mysql"],
      "env": {
        "MYSQL_HOST": "dev-db.internal.hanilnetworks.com",
        "MYSQL_PORT": "3306",
        "MYSQL_USER": "claude_ro",
        "MYSQL_PASSWORD": "<from_vault>",
        "MYSQL_DATABASE": "erp_dev"
      }
    }
  }
}
```

### 5.2 MCP 구성 시 절대 금지 사항

❌ **금지 1**: root 계정 사용
```json
"MYSQL_USER": "root"   // 절대 금지
```

❌ **금지 2**: 운영 DB 호스트 지정
```json
"MYSQL_HOST": "prod-db.hanilnetworks.com"   // 절대 금지
```

❌ **금지 3**: 평문 비밀번호를 git에 커밋
```json
"MYSQL_PASSWORD": "actualPassword123!"   // .gitignore 필수
```

❌ **금지 4**: 와일드카드 DB 권한
```sql
GRANT ALL PRIVILEGES ON *.* TO 'claude_ro'@'%';   -- 절대 금지
```

### 5.3 비밀번호 관리

- **개인 PC**: Windows 자격증명 관리자 또는 KeePass 사용
- **서버**: HashiCorp Vault 또는 환경변수 (서버 접근 권한자만)
- **절대 금지**: `.mcp.json`을 git에 커밋, Slack/메일로 평문 공유

---

## 6. 팀원(개발자) 사용 가이드

### 6.1 시작 전 체크리스트

- [ ] 사용하는 MCP 계정이 `claude_ro` 또는 `claude_dev`인지 확인
- [ ] 절대 `root` 계정 사용 금지
- [ ] `MYSQL_HOST`가 운영 DB가 아닌지 확인 (`dev-db`, `staging-db` OK)
- [ ] `.mcp.json`이 `.gitignore`에 포함되어 있는지 확인
- [ ] `/status` 명령으로 Managed Settings 적용 확인

### 6.2 안전한 프롬프트 작성

#### ✅ 권장 프롬프트
> "tb_quote 테이블의 최근 30일 견적 데이터를 조회해서 일별 건수를 분석해줘"
> → SELECT만 사용하므로 안전

> "이 프로시저 SP_TB_INV_DAILY_PD_TEMP2를 읽어서 로직 설명해줘"
> → 코드 분석은 안전 (단, EXECUTE 없는 계정으로는 호출 불가하니 안전)

#### ⚠️ 주의 필요 프롬프트
> "tb_user 테이블에서 테스트 데이터 삭제해줘"
> → DELETE 발생. **반드시 개발 DB에서만, claude_dev 계정으로**
> → 사전에 백업 후 진행

#### ❌ 금지 프롬프트
> "tb_quote 테이블 구조 변경해줘"
> → ALTER TABLE 시도. L1/L2/L3 모두 거부됨. 그러나 운영 계정 잘못 사용 시 위험

> "운영 DB에서 직접 확인해줘"
> → 정책 위반. 운영 DB는 어떤 경우에도 LLM 직결 불가

### 6.3 ERP 프로시저 작업 시 특별 주의사항

ERP 파트는 프로시저 중심 개발이므로 다음 규칙을 추가로 따릅니다.

| 작업 유형 | 허용 계정 | 비고 |
|----------|----------|------|
| 프로시저 코드 조회 | `claude_ro` | `INFORMATION_SCHEMA.ROUTINES` SELECT |
| 프로시저 실행 (테스트) | `claude_proc` | 개발 DB에서만 |
| 프로시저 디버깅 | `claude_proc` | 결과 확인 후 코드는 별도 IDE에서 수정 |
| 프로시저 생성/수정 | **MCP로 절대 금지** | DBeaver/MySQL Workbench로 사람이 직접 |

> 💡 **권장 워크플로우**: Claude에게 프로시저 코드 분석/리팩터링 안을 받되, **실제 `CREATE PROCEDURE` 실행은 사람이 IDE에서 검토 후 수동 실행.** Claude가 직접 실행하지 않도록 EXECUTE 외 권한을 주지 않습니다.

### 6.4 발생 가능한 사고 사례와 대응

#### 사례 1: "데이터가 사라졌어요"
- 즉시 Claude Code 종료
- 사용한 MCP 계정 확인: `claude_ro`였다면 DELETE 자체가 거부됨 → 다른 원인
- `claude_dev`였다면 어떤 DB에서 발생했는지 확인 → 개발 DB라면 복원, 운영 DB라면 즉시 정보보안팀 연락
- MySQL `general_log` 또는 `binlog`로 실제 실행된 쿼리 추적

#### 사례 2: "비밀번호가 노출된 것 같아요"
- 즉시 해당 MCP 계정 비밀번호 변경
- `git log`로 커밋 이력 확인. 노출됐다면 git 히스토리 정리 + force push
- 정보보안팀에 즉시 보고

---

## 7. 관리자(시스템) 운영 가이드

### 7.1 초기 배포 절차 (Linux 서버 기준)

```bash
# 1. 디렉터리 생성
sudo mkdir -p /etc/claude-code

# 2. 표준 Managed Settings 파일 배포
sudo cp managed-settings.json /etc/claude-code/managed-settings.json

# 3. 권한 설정 (root만 수정 가능, 모두 읽기 가능)
sudo chown root:root /etc/claude-code/managed-settings.json
sudo chmod 644 /etc/claude-code/managed-settings.json

# 4. 검증
cat /etc/claude-code/managed-settings.json | jq .
```

### 7.2 Windows GPO 배포 절차

1. AD 그룹정책관리 콘솔에서 새 GPO 생성
2. 컴퓨터 구성 → 기본 설정 → Windows 설정 → 레지스트리
3. 새 레지스트리 항목 생성:
   - 키: `HKLM\SOFTWARE\Policies\ClaudeCode`
   - 값: `Settings` (REG_SZ)
   - 데이터: managed-settings.json 전체 내용을 JSON 문자열로
4. WSL 상속 활성화: 같은 키에 `wslInheritsWindowsSettings` = `true`
5. 대상 OU에 GPO 연결

### 7.3 정기 점검 사항

| 주기 | 점검 항목 | 담당 |
|------|----------|------|
| 일간 | MySQL general_log에서 비정상 쿼리 패턴 검색 | DBA |
| 주간 | Claude Code 버전 확인 (`minimumVersion` 정책 준수) | DI사업부 |
| 월간 | MCP 계정별 사용량 리뷰 (MAX_QUERIES 도달 여부) | DBA |
| 분기 | Managed Settings 정책 리뷰 및 업데이트 | 정보보안팀 |
| 분기 | 권한 적정성 재검토 (REVOKE 누락 여부) | DBA + 보안팀 |

### 7.4 모니터링 쿼리

```sql
-- MCP 계정의 최근 쿼리 통계
SELECT
  USER,
  HOST,
  COUNT(*) AS query_count,
  MAX(EVENT_TIME) AS last_query
FROM mysql.general_log
WHERE USER LIKE 'claude_%'
  AND EVENT_TIME > NOW() - INTERVAL 1 DAY
GROUP BY USER, HOST;

-- 거부된 쿼리 추적 (error log 분석 필요)
-- ERROR 1142: command denied → 권한 부족
-- ERROR 1370: routine denied → 프로시저 권한 부족

-- 비정상 패턴 탐지
SELECT *
FROM mysql.general_log
WHERE USER LIKE 'claude_%'
  AND (
    ARGUMENT LIKE '%DROP%'
    OR ARGUMENT LIKE '%TRUNCATE%'
    OR ARGUMENT LIKE '%GRANT%'
    OR ARGUMENT LIKE '%CREATE PROCEDURE%'
  )
ORDER BY EVENT_TIME DESC;
```

### 7.5 사고 대응 절차

```
사고 인지
   ↓
1단계: 즉시 격리
   - 해당 MCP 계정 즉시 잠금: ALTER USER 'claude_xx'@'%' ACCOUNT LOCK;
   - 영향받은 시스템 식별
   ↓
2단계: 영향 분석
   - general_log / binlog 분석
   - 변경된 데이터 범위 파악
   ↓
3단계: 복구
   - 백업/복제본에서 데이터 복원
   - 프로시저는 SVN/Git에서 복원
   ↓
4단계: 재발 방지
   - 권한 정책 재검토
   - Managed Settings 강화
   - 사후 보고서 작성
```

---

## 8. 자주 묻는 질문 (FAQ)

**Q1. SELECT만 가능한 계정인데 굳이 Claude Code 차단 설정도 해야 하나요?**
> A. 네, 이중 방어가 원칙입니다. DB 권한이 1차 방어선이지만, 다음 이유로 Claude Code 설정도 필요합니다.
> ① 실수로 잘못된 계정이 설정될 수 있음
> ② DB 외 다른 경로(Bash 직접 명령)로 우회 가능
> ③ 컨텍스트에 민감 데이터 적재 자체를 차단해야 함

**Q2. INSERT/UPDATE/DELETE는 어떻게 막나요?**
> A. **MySQL 계정에 해당 권한을 부여하지 않으면 됩니다.** `claude_ro` 계정은 `SELECT`만 받았으므로 Claude가 INSERT SQL을 보내도 MySQL이 거부합니다 (ERROR 1142).

**Q3. DDL(CREATE/ALTER/DROP)은 어떻게 막나요?**
> A. **`claude_ro`/`claude_dev` 어느 계정에도 `CREATE`, `ALTER`, `DROP` 권한을 부여하지 않습니다.** DDL은 사람이 IDE에서 직접 수행해야 합니다.

**Q4. 프로시저는 호출은 되고 변경은 막을 수 있나요?**
> A. 네. `EXECUTE`만 부여하고 `CREATE ROUTINE`/`ALTER ROUTINE`을 부여하지 않으면 호출은 되지만 변경은 거부됩니다. 한일 ERP 환경에서 권장하는 구성입니다.

**Q5. 운영 DB 데이터를 분석하려면 어떻게 해야 하나요?**
> A. ① 운영 DB의 읽기 전용 복제본(replica)을 구성하고, ② 그 복제본에 `claude_ro` 계정만 생성하며, ③ Claude는 복제본에만 접속합니다. **운영 DB 직결은 어떤 경우에도 불가합니다.**

**Q6. 팀원이 자기 PC에서 임의로 MCP를 추가하면 어떻게 되나요?**
> A. Managed Settings에 `allowManagedMcpServersOnly: true`가 설정되어 있으면 **추가해도 동작하지 않습니다.** `/status`로 적용 여부 확인 가능.

**Q7. `--dangerously-skip-permissions` 플래그로 우회할 수 있나요?**
> A. Managed Settings에 `disableBypassPermissionsMode: "disable"`이 설정되어 있으면 **이 플래그 자체가 거부됩니다.**

**Q8. Windows 네이티브에서는 sandbox가 안 된다는데 어떻게 해야 하나요?**
> A. WSL2에서 Claude Code를 실행하는 것을 권장합니다. WSL2에서는 Linux와 동일하게 sandbox가 동작합니다. `wslInheritsWindowsSettings: true`로 GPO 정책 상속도 가능합니다.

**Q9. 비밀번호를 어떻게 안전하게 관리하나요?**
> A. ① 절대 git에 커밋하지 않고, ② Windows 자격증명 관리자/KeePass/Vault를 사용하며, ③ MCP 설정의 `env`에 직접 평문으로 넣지 말고 환경변수 참조를 활용합니다.

**Q10. 정책 위반이 발생하면 어떻게 알 수 있나요?**
> A. ① MySQL `general_log`에서 거부된 쿼리(ERROR 1142/1370) 추적, ② OpenTelemetry 텔레메트리로 Claude Code 사용 패턴 모니터링, ③ 정기 감사를 통해 확인합니다.

---

## 9. 체크리스트 요약

### 9.1 DBA용 체크리스트

- [ ] `claude_ro`, `claude_dev`, `claude_proc` 계정 생성 완료
- [ ] 각 계정에 최소 권한만 부여 (DDL, GRANT 권한 없음)
- [ ] 민감 테이블에 대한 REVOKE 적용
- [ ] 리소스 제한(MAX_QUERIES, MAX_CONNECTIONS) 설정
- [ ] 운영 DB는 MCP 계정 접근 불가하도록 차단
- [ ] `general_log` 활성화 및 모니터링 쿼리 등록
- [ ] 정기 권한 감사 일정 수립

### 9.2 시스템 관리자용 체크리스트

- [ ] Linux 서버: `/etc/claude-code/managed-settings.json` 배포
- [ ] Windows: GPO를 통한 레지스트리 배포
- [ ] WSL 상속 설정 (`wslInheritsWindowsSettings: true`)
- [ ] `forceLoginOrgUUID` 설정 (한일네트웍스 조직만 허용)
- [ ] `allowManagedMcpServersOnly: true` 적용 확인
- [ ] `disableBypassPermissionsMode: "disable"` 적용 확인
- [ ] `minimumVersion` 정책 설정
- [ ] 텔레메트리 수집 활성화
- [ ] 분기별 정책 리뷰 일정 수립

### 9.3 팀원(개발자)용 체크리스트

- [ ] 사용 중인 MCP 계정이 `claude_ro` 또는 `claude_dev`인지 확인
- [ ] root 계정 또는 운영 DB 호스트 사용하지 않는지 확인
- [ ] `.mcp.json`이 `.gitignore`에 포함되어 있는지 확인
- [ ] `/status`로 Managed Settings 적용 확인
- [ ] 비밀번호를 KeePass/자격증명 관리자에 보관
- [ ] DDL/프로시저 변경 작업은 IDE에서 직접 수행
- [ ] 운영 DB 분석 필요 시 복제본 사용 (직결 금지)

---

## 10. 부록

### 10.1 참고 자료

- Claude Code 공식 설정 문서: https://code.claude.com/docs/en/settings
- Claude Code Permissions 문서: https://code.claude.com/docs/en/permissions
- Claude Code MCP 문서: https://code.claude.com/docs/en/mcp
- MySQL 권한 시스템 문서: https://dev.mysql.com/doc/refman/8.0/en/privilege-system.html

### 10.2 변경 이력

| 버전 | 일자 | 작성자 | 주요 변경 |
|------|------|--------|----------|
| 1.0 | 2026-05-05 | 정도원 대리 | 최초 작성 |

### 10.3 문의

- DI사업부 웹서비스 1파트 / 정도원 대리
- 정보보안팀 (Managed Settings 배포 관련)
- DBA팀 (계정 권한 관련)

---

> **본 문서는 한일네트웍스 내부용입니다. 외부 유출 시 정보보호 정책 위반에 해당합니다.**
