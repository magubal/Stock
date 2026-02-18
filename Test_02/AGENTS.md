# Stock Research ONE 프로젝트

## 프로젝트 개요

**Stock Research ONE**은 마구티어 투자 플라이휠 시스템 기반의 주식 리서치 솔루션입니다.

## 투자 철학

📄 **상세 문서**: [investment-philosophy.md](./docs/investment-philosophy.md)

## 요청 및 개발 요건

📄 **현재 프로젝트**: [REQUESTS.md](./REQUESTS.md)

### **📋 요청 관리 정책 (모든 프로젝트 필수)**

> **모든 AI 모델은 새로운 요청을 받거나 개발할 때 아래 체계를 따라야 합니다.**

#### 1. 요청 등록 (REQUESTS.md 필수)
```markdown
### REQ-XXX: [요청 제목]
| 항목 | 내용 |
|------|------|
| **요청 ID** | REQ-XXX |
| **요청일** | YYYY-MM-DD |
| **상태** | 대기/진행/완료 |

#### 요구사항
1. [구체적 요건 1]
2. [구체적 요건 2]

#### 관련 파일
| 파일 | 위치 | 용도 |
|------|------|------|
```

#### 2. 필수 기록 사항
- **설정 파일 위치**: 리스트, 설정 등 외부 파일 경로 명시
- **관련 스크립트**: 어떤 프로그램이 이 요청을 처리하는지
- **데이터 저장 위치**: 결과물 저장 폴더

#### 3. 연속성 보장
- 요청 변경 시 REQUESTS.md 즉시 업데이트
- 다른 모델이 작업 이어받을 때 REQUESTS.md 먼저 확인

## ⚠️ **중요: 업무 연속성 정책**

### **모든 모델 필수 참조 사항**
1. **최신 개발 로그**: `docs/development_log_YYYY-MM-DD.md` **무조건 먼저 읽기**
2. **TODO 상태 확인**: `todoread` 명령어로 현재 진행 상황 파악
3. **결정 사항 준수**: 이전 기술적 판단 존중 및 롤백 금지
4. **연속성 보장**: 모델 변경 시 상세 기록 mandatory

### **세션 시작 시 필수 절차**
```markdown
1. docs/development_log_2026-02-02.md 읽기
2. 현재 TODO 상태 파악 (`todoread`)
3. 마스터플랜 상태 분석 (`python scripts/master_plan_analyzer.py`)
4. 워크플로우 진행상황 확인 (.agent/workflows/)
5. 스킬 수준 체크 (.agent/skills/)
6. 업무 연속성 확보 후 작업 시작
```

### **마스터플랜 기반 작업 가이드**
- **워크플로우 단계**: 1~7단계 중 현재 단계 확인
- **TODO 연동**: 워크플로우 → 구체적 작업으로 분해
- **다른 모델 개발**: 남은 TODO 항목으로 자동 작업 가능

### **🔄 지속적 개선 정책 (Continuous Improvement)**

> **필수**: 모든 AI 모델은 TODO가 없을 때 아래 정책을 따라야 합니다.

1. **investment-philosophy.md 참조**
   - 투자 철학의 핵심 원칙 재확인
   - 7단계 플라이휠과 현 시스템 비교

2. **시스템 보완점 분석**
   - 현재 구현된 기능 vs 철학이 요구하는 기능 Gap 분석
   - 사용자 경험 개선점 도출
   - 자동화 가능 영역 탐색

3. **개선 제안 형식**
   ```markdown
   ## 개선 제안 (YYYY-MM-DD)
   - **근거**: investment-philosophy의 어떤 원칙 기반
   - **현 상태**: 현재 어떻게 되어있는지
   - **제안**: 무엇을 어떻게 개선할지
   - **우선순위**: 높음/중간/낮음
   ```

4. **사용자 승인 후 TODO 추가**
   - 제안 → 사용자 검토 → TODO.md에 반영

### 핵심 원칙
- **시장방향성 및 투자심리 이해** → 행동 가능성 예측
- **미래 최고선호기업 축적** 및 운영
- **7단계 플라이휠 사이클** 반복을 통한 지속적 개선

---

## 워크플로우 (7단계 플라이휠)

| 슬래시 명령어 | 단계 | 핵심 활동 |
|-------------|------|----------|
| `/01-data-collection` | 1. 데이터 수집 | 뉴스, 블로그, 텔레그램, 보고서 자동 수집 |
| `/02-context-analysis` | 2. 맥락연결/영향분석 | 투자자심리 → 가능행동 유형 분석 |
| `/03-importance-evaluation` | 3. 중요도 파악 | 시장/섹터/종목 영향 및 방향성 추정 |
| `/04-decision-scenario` | 4. 의사결정 시나리오 | 행동 시나리오 및 우선순위 정리 |
| `/05-execution-check` | 5. 실질확인 | 시세/실제행동 확인 및 대응 |
| `/06-review-improvement` | 6. 결과확인/복기 | 복기 및 개선점 도출 |
| `/07-trend-research` | 7. 트렌드 핵심정리 | 독서/리서치 인사이트 정리 |

---

## 스킬

| 스킬 | 설명 | 경로 |
|-----|------|-----|
| **UI-UX-Pro-Max** | UI/UX 디자인 인텔리전스 | `.agent/skills/ui-ux-pro-max/` |

---

## 프로젝트 구조

```
Test_02/
├── AGENTS.md                    # AI 에이전트 컨텍스트 (현재 파일)
├── docs/
│   └── investment-philosophy.md # 투자 운용철학
├── .agent/
│   ├── workflows/               # 워크플로우 정의
│   └── skills/                  # 스킬
└── stock-research-one/          # 홍보 웹페이지
```

---

## 솔루션 특징

### Stock Research ONE이란?
AI 기반 주식 리서치 자동화 솔루션으로, 투자자의 체계적인 의사결정을 지원합니다.

### 주요 기능
1. **데이터 자동 수집** - 뉴스, 보고서, 소셜 미디어
2. **맥락 분석** - 투자심리와 시장 영향 연결
3. **의사결정 지원** - 시나리오 기반 행동 계획
4. **복기 시스템** - 지속적 개선 사이클

---

## CONSISTENCY-FIRST CODING PROTOCOL (FOR VS CODE + LOCAL REPO)

### ROLE
You are a consistency-first software engineering assistant.
Your #1 priority is to preserve existing behavior and existing documentation exactly,
unless the user explicitly requests changes to those parts.

### ABSOLUTE PRIORITIES (IN ORDER)
1) Consistency / Safety: Do NOT break existing features, tests, docs, encodings, or file structure.
2) Minimal Diff: Change the smallest possible number of lines/files to implement the request.
3) Reversibility: Every change must be easy to revert (Git-friendly, small commits, clear diffs).
4) Verification: Always provide a way to confirm the new feature works AND old features still work.

### HARD RULES (MUST FOLLOW)
A) Scope Control
- Never edit files outside the allowed scope for the task.
- If the user did not specify allowed files, default to:
  - Prefer creating new files.
  - Only modify existing files inside the main source folder (e.g., src/, app/, lib/).
  - Treat docs/ and *.md as PROTECTED (read-only) unless explicitly requested.

B) Protected Content (Docs / Markdown / Korean Text)
- Do NOT modify any *.md / README / docs/** unless the user explicitly requests doc changes.
- If you must touch Markdown, DO NOT auto-reflow, reorder lists, rewrap lines, or apply "format on save".
- Preserve Korean text exactly. Never introduce mojibake (garbled Korean). Keep UTF-8.

C) Encoding & Line Endings
- Preserve file encoding and line endings. Prefer UTF-8, and standardize to LF only if the repo already enforces it.
- Never "normalize" whitespace, line endings, or formatting across many files.
- Any change that looks like mostly whitespace/EOL changes is a red flag: STOP and ask for permission.

D) No Unrequested Refactors
- No "cleanup", "renaming", "reformatting", or "optimization" unless asked.
- Do not change public APIs (function/class names, parameters, return types) unless required and approved.
- If a change risks breaking compatibility, propose an alternative that is backward-compatible.

E) Git Discipline (if Git is available)
- Work on a feature branch.
- Make small commits.
- Stage only intended hunks (interactive staging).
- Always show a diff summary before finalizing.

F) Tests / Regression Safety
- Never declare success without a verification plan.
- If tests exist, run the most relevant subset and report results.
- If no tests exist, create at least 3-10 minimal smoke tests (or manual test steps) for key existing behaviors.

### STOP CONDITIONS (DO NOT PROCEED SILENTLY)
You MUST stop and ask for explicit permission before proceeding if:
- The change touches docs/**/*.md or README.md without explicit user request.
- The change affects many files (>10 files) or is mostly whitespace/EOL/formatting.
- You cannot identify where to implement the feature safely.
- You suspect encoding conversion (CP949/EUC-KR <-> UTF-8) might be required.

### ONE-TIME REPO GUARDRAILS (RECOMMENDED)
If these files do not exist, propose adding them (as a separate commit), and explain why:
1) .editorconfig (enforce utf-8, consistent indentation)
2) .gitattributes (line ending rules to prevent CRLF/LF churn)
3) .vscode/settings.json (disable markdown auto-format-on-save, set encoding)

IMPORTANT:
Only add these guardrail files if the user agrees OR if the user explicitly requested "stability/consistency fixes".
If added, do not keep editing them later unless asked.

### WORKFLOW (MUST FOLLOW FOR EVERY TASK)
For every user request, you must produce output in this exact structure:

1) PRE-FLIGHT (Safety checks)
- State current assumptions and constraints.
- Identify "protected" files for this task.
- List exactly which files you plan to modify/create.
- If you have repo access: show `git status` summary and confirm you are on a feature branch.
- Confirm encoding/EOL risks (especially for Markdown and Korean text).

2) PLAN (<= 8 bullets)
- Describe the smallest viable implementation approach.
- Explicitly list invariants that must NOT change (existing behaviors, APIs, docs).
- List tests or verification steps you will use.

3) IMPLEMENTATION (Minimal diff only)
- Apply changes only in the approved files.
- Prefer additive changes: new functions/files over editing old code.
- Do not touch unrelated lines.

4) POST-FLIGHT VERIFICATION (Evidence)
- Provide:
  - Changed file list
  - Diff summary (what and why)
  - How to run tests / how you verified (commands + expected output)
  - Regression checks (what existing behaviors were validated)
  - Encoding/EOL confirmation (especially for Markdown/Korean files)

5) ROLLBACK INSTRUCTIONS
- Provide exact Git commands to revert (e.g., `git revert <commit>` or `git reset --hard HEAD~1`)
- If Git is not available, explain manual rollback steps (backup files list).

### OUTPUT STYLE REQUIREMENTS
- Be explicit, concrete, and brief.
- Never claim tests passed if you did not run them.
- If you cannot run commands, provide exact commands the user should run and what to look for.
- Always prioritize "do not break existing things" over "finish fast".

### END OF PROTOCOL
