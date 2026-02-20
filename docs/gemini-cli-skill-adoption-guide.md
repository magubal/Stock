# Gemini CLI Skill Adoption Guide
# Claude Code 스킬을 Gemini CLI에서 사용하기

> **Date**: 2026-02-20
> **Scope**: `/kill-port` 커맨드 마이그레이션 (다른 스킬도 같은 패턴 적용 가능)

---

## 1. Overview / 개요

이 프로젝트는 **Claude Code**에서 커스텀 슬래시 커맨드와 Agent Skills를 사용 중입니다.
이 가이드는 동일한 스킬 체계를 **Gemini CLI**에서도 사용하기 위한 마이그레이션 방법을 설명합니다.

**핵심 사실:**
- **Custom Commands**: 파일 형식이 다름 (Claude: `.md` → Gemini: `.toml`)
- **Agent Skills**: SKILL.md 포맷이 동일 — 변환 없이 공유 가능
- **Python Scripts**: AI 모델과 무관한 OS 레벨 스크립트 — 수정 불필요

---

## 2. Directory Structure Comparison / 디렉토리 구조 비교

| 구분 | Claude Code | Gemini CLI |
|------|-------------|------------|
| Context file | `CLAUDE.md` | `GEMINI.md` |
| Custom commands | `.claude/commands/*.md` | `.gemini/commands/*.toml` |
| Skills (workspace) | `.agent/skills/*/SKILL.md` | `.gemini/skills/*/SKILL.md` 또는 `.agents/skills/` |
| Skills (global) | — | `~/.gemini/skills/` |
| Settings | `.claude/settings.local.json` | `settings.json` |
| Agent rules | `.agent/rules.md` | `GEMINI.md`에 통합 |

> **주의**: Gemini CLI의 스킬 alias는 `.agents/skills/` (복수형)입니다.
> 이 프로젝트의 `.agent/skills/` (단수형)과 다릅니다.
> `.gemini/skills/`에 심볼릭 링크를 만들거나 별도 복사하세요.

---

## 3. Migration: `/kill-port` Command / 마이그레이션 예시

### Before — Claude Code (`.claude/commands/kill-port.md`)

```markdown
포트를 점유하고 있는 좀비 프로세스를 정리합니다. 인자: $ARGUMENTS

## 실행 방법

1. 인자가 없으면 기본 8000만 정리 (uvicorn 좀비가 주 원인)
2. `all` 이면 전체 포트 정리 (8000, 8080, 3000)
3. 숫자 인자면 해당 포트만 정리 (예: `/kill-port 8000 3000`)

아래 명령을 실행하세요:

```bash
python scripts/kill_port.py $ARGUMENTS
\```

## 동작 원리
- `netstat -ano` 로 LISTENING 상태의 PID를 탐지
- `taskkill /PID <pid> /F /T` 로 프로세스 트리 전체 종료
- PowerShell 파이프라인 미사용 (AhnLab V3 오탐 회피)
- 아무것도 없으면 "All ports are free" 출력 (에러 없음)
```

### After — Gemini CLI (`.gemini/commands/kill-port.toml`)

```toml
description = "포트를 점유하고 있는 좀비 프로세스를 정리합니다"

prompt = """
포트를 점유하고 있는 좀비 프로세스를 정리합니다.

## 실행 방법

1. 인자가 없으면 기본 8000만 정리 (uvicorn 좀비가 주 원인)
2. `all` 이면 전체 포트 정리 (8000, 8080, 3000)
3. 숫자 인자면 해당 포트만 정리 (예: `/kill-port 8000 3000`)

아래 명령을 실행하세요:

```bash
python scripts/kill_port.py {{args}}
```

## 동작 원리
- `netstat -ano` 로 LISTENING 상태의 PID를 탐지
- `taskkill /PID <pid> /F /T` 로 프로세스 트리 전체 종료
- PowerShell 파이프라인 미사용 (AhnLab V3 오탐 회피)
- 아무것도 없으면 "All ports are free" 출력 (에러 없음)

## 사용 시나리오
- 서버 시작 시 "port already in use" 에러 발생
- VS Code Run/Debug 전에 이전 세션 잔여 프로세스 정리
- uvicorn --reload 후 좀비 워커 프로세스 잔존
"""
```

### Key Differences / 주요 차이점

| 항목 | Claude Code | Gemini CLI |
|------|-------------|------------|
| 파일 형식 | Markdown (`.md`) | TOML (`.toml`) |
| 인자 변수 | `$ARGUMENTS` | `{{args}}` |
| 설명 | 본문 첫 줄 | `description` 필드 |
| 프롬프트 | 파일 전체가 프롬프트 | `prompt` 필드 안에 작성 |
| 멀티라인 | 기본 지원 | `"""` 트리플 쿼트 사용 |

### Python Script — 수정 불필요

`scripts/kill_port.py`는 AI 모델과 무관한 OS 레벨 유틸리티입니다.
Claude Code든 Gemini CLI든 동일하게 호출됩니다.

---

## 4. Setup Steps / 설정 순서

### Step 1: `.gemini/commands/` 디렉토리 생성

```bash
mkdir -p .gemini/commands
```

### Step 2: `kill-port.toml` 생성

위 [After 섹션](#after--gemini-cli-geminicommandskill-porttoml)의 내용을 `.gemini/commands/kill-port.toml`에 저장합니다.

### Step 3: (선택) 스킬 공유

`.agent/skills/`의 스킬을 Gemini CLI에서도 사용하려면:

```bash
# 옵션 A: 심볼릭 링크 (원본 1벌 유지, 권장)
# Windows (관리자 권한 필요):
mklink /D .gemini\skills .agent\skills

# 옵션 B: 디렉토리 복사
cp -r .agent/skills .gemini/skills
```

### Step 4: (선택) GEMINI.md 생성

프로젝트 루트에 `GEMINI.md`를 만들어 Gemini CLI에 컨텍스트를 제공합니다.
`CLAUDE.md`에서 핵심 내용을 발췌합니다:

```markdown
# Stock Research ONE

## Project Context
- 한국어 주식 리서치 자동화 프로젝트
- Stack: React + FastAPI + Python scripts
- Key Feature: DART API 기반 해자(moat) 평가 + 투자 대시보드

## Custom Commands
- `/kill-port` — Windows 좀비 프로세스 정리 (8000/8080/3000)

## Rules
- PowerShell 파이프라인 미사용 (AhnLab V3 오탐 회피)
- 한국어로 응답
```

### Step 5: 커맨드 리로드

Gemini CLI 세션 중에 커맨드 파일을 수정했다면:

```
/commands reload
```

---

## 5. Shared Skills / 스킬 공유 전략

이 프로젝트의 `.agent/skills/` 안의 SKILL.md 파일은 Gemini CLI와 **동일한 포맷**입니다.

```
.agent/skills/
├── analysis/SKILL.md          ← 맥락분석, 영향력 평가
├── brain/SKILL.md             ← 브레인스토밍 워크플로우
├── data-collection/SKILL.md   ← 뉴스, 보고서 수집
├── decision/SKILL.md          ← 의사결정 지원
├── research/SKILL.md          ← 기업분석, 트렌드 리서치
├── terminal-best-practices/SKILL.md  ← 터미널 명령 검증
└── ui-ux-pro-max/             ← UI/UX 디자인 (data/ + scripts/ 포함)
    ├── SKILL.md
    ├── data/
    └── scripts/
```

**SKILL.md 포맷 (양쪽 동일):**
```yaml
---
name: skill-name
description: 스킬 설명
---

# Skill Title

마크다운 지시사항...
```

---

## 6. Applying the Same Pattern / 다른 커맨드 변환 체크리스트

`/kill-port` 외의 커맨드도 같은 패턴으로 변환합니다:

- [ ] `.claude/commands/<name>.md` 파일 확인
- [ ] `.gemini/commands/<name>.toml` 생성
- [ ] `$ARGUMENTS` → `{{args}}`로 치환
- [ ] 본문을 `prompt = """..."""` 안에 넣기
- [ ] 첫 줄 설명을 `description = "..."` 필드로 분리
- [ ] Gemini CLI에서 `/<name>` 실행하여 테스트

### `/brain` 변환 예시 (참고)

```toml
# .gemini/commands/brain.toml
description = "브레인스토밍 워크플로우. 발산→수렴→Design Brief"

prompt = """
브레인스토밍 워크플로우를 실행합니다. 사용자가 제공한 주제: {{args}}
(이하 .claude/commands/brain.md 본문과 동일)
"""
```

---

## 7. Gemini CLI Specific Features / Gemini 전용 기능

Claude Code에는 없는 Gemini CLI 전용 기능을 활용할 수 있습니다:

### Shell Command Injection (`!{...}`)
```toml
prompt = """
현재 포트 상태를 확인하고 정리하세요:
!{netstat -ano | findstr LISTENING}
"""
```

### File Content Injection (`@{...}`)
```toml
prompt = """
아래 스크립트를 참고하여 포트를 정리하세요:
@{scripts/kill_port.py}
"""
```

### Namespaced Commands
```
.gemini/commands/
├── kill-port.toml        → /kill-port
└── dev/
    ├── start.toml        → /dev:start
    └── stop.toml         → /dev:stop
```

---

## 8. Caveats / 주의사항

| 항목 | 설명 |
|------|------|
| **OS 호환성** | `kill_port.py`는 Windows 전용 (`taskkill`, `netstat`). macOS/Linux에서는 별도 스크립트 필요 |
| **AhnLab V3** | Python subprocess 방식이므로 Gemini CLI에서도 오탐 회피 동일 |
| **기본 셸** | Gemini CLI의 기본 셸이 bash인지 PowerShell인지 확인 필요 |
| **TOML 이스케이프** | 프롬프트 안의 `\`는 TOML에서 이스케이프 문자. `\\`로 써야 할 수 있음 |
| **스킬 경로** | Gemini는 `.agents/skills/` (복수형), 프로젝트는 `.agent/` (단수형) — 심볼릭 링크 권장 |

---

## 9. Quick Reference / 빠른 참조

```
# Claude Code                          # Gemini CLI
/.claude/commands/kill-port.md    →    .gemini/commands/kill-port.toml
$ARGUMENTS                        →    {{args}}
CLAUDE.md                         →    GEMINI.md
.agent/skills/                    →    .gemini/skills/ (or .agents/skills/)
(자동 리로드)                      →    /commands reload
```

---

## Sources / 참고자료

- [Gemini CLI Custom Commands](https://geminicli.com/docs/cli/custom-commands/)
- [Gemini CLI Agent Skills](https://geminicli.com/docs/cli/skills/)
- [Creating Agent Skills](https://geminicli.com/docs/cli/creating-skills/)
- [Gemini CLI GitHub (custom-commands.md)](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/custom-commands.md)
