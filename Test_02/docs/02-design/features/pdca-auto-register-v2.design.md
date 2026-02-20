# pdca-auto-register-v2 Design

> Plan 참조: `docs/01-plan/features/pdca-auto-register-v2.plan.md`

## 1. 컴포넌트 구조

```
scripts/pdca_auto_register.py     <-- 핵심 스크립트 (재작성)
docs/.pdca-status.json            <-- 등록 대상 (planPath 추가)
config/pdca_id_map.json           <-- PDCA-XXX ID 할당
docs/01-plan/features/*.plan.md   <-- 경량 Plan 자동 생성
CLAUDE.md                         <-- 규칙 업데이트
```

**REQUESTS.md는 대상이 아님** (REQ-XXX는 별도 체계)

## 2. `scripts/pdca_auto_register.py` 상세 설계

### 2.1 CLI 인터페이스

```
python scripts/pdca_auto_register.py                  # 미등록 건 감지 + 강제 등록
python scripts/pdca_auto_register.py --dry-run         # 실제 수정 없이 대상만 출력
python scripts/pdca_auto_register.py --feature NAME    # 특정 피처만 등록
```

### 2.2 핵심 함수

#### `load_unregistered_features() -> list[dict]`
- `docs/.pdca-status.json` 읽기
- `features` 딕셔너리에서 **`planPath`가 없는** 항목 추출
- **노이즈 필터**: 아래 조건에 해당하면 제외
  1. 이름에 `-`가 없는 단일 단어 (backend, scripts, api 등)
  2. 이름에 `.`이 포함 (파일명: insight_extractor.py 등)
  3. `phase`가 없거나 의미 없는 항목
  4. `archivedTo`가 있는 항목 (이미 아카이브 완료)
- 반환: `[{name, phase, ...}, ...]`

#### `ensure_pdca_id(feature_name) -> int`
- `config/pdca_id_map.json` 읽기
- 이미 ID가 있으면 반환
- 없으면 `_nextId` 할당 후 `_nextId += 1` 저장
- 반환: PDCA ID (정수)

#### `create_lightweight_plan(feature_name, pdca_id) -> str`
- `docs/01-plan/features/{feature_name}.plan.md` 경로에 파일 생성
- 이미 파일이 존재하면 skip (경로만 반환)
- 최소 구조: 제목, 배경 (자동 등록), 범위, 산출물 테이블
- 반환: planPath 문자열 (프로젝트 루트 기준 상대 경로)

#### `update_pdca_status(feature_name, plan_path)`
- `.pdca-status.json` 읽기
- `features[feature_name]`에 `planPath` 추가
- 파일 저장

#### `run(dry_run, feature_name) -> int`
- 메인 오케스트레이션
- dry_run이면 출력만, 파일 수정 없음
- 반환: 등록된 건수

### 2.3 노이즈 필터 상세

`.pdca-status.json`의 `features`에는 실제 피처와 노이즈가 혼재:

| 구분 | 예시 | 특징 |
|------|------|------|
| 실제 피처 | `oracle-earnings-integration` | kebab-case, `-` 포함 |
| 노이즈 | `backend`, `scripts`, `api` | 단일 단어, `-` 없음 |
| 노이즈 | `insight_extractor.py` | `.` 포함 (파일명) |
| 노이즈 | `stock_moat`, `moat_dashboard` | `_` 사용 (디렉토리명) |

**필터 규칙**: 이름에 `-`(하이픈)이 **최소 1개** 포함되어야 실제 피처로 인식

### 2.4 경량 Plan 템플릿

```markdown
# {Feature Name} Plan

> (자동 등록됨 — PDCA-{id:03d})

## 배경
- `.pdca-status.json`에서 `planPath` 없이 감지된 피처
- `scripts/pdca_auto_register.py`에 의해 자동 생성

## 범위
- {feature-name} 기능 구현

## 산출물
| 파일 | 변경 내용 |
|------|-----------|
| (추후 보완) | — |

## 완료 상태
- [ ] 미완료
```

## 3. CLAUDE.md 규칙 변경

### Before (잘못된 v2)
```
- PDCA Feature Auto-Registration (MANDATORY, AUTOMATED):
  - /pdca plan 실행 후 반드시: python scripts/pdca_auto_register.py
  - 이 스크립트가 .pdca-status.json → REQUESTS.md 동기화를 자동 처리
```

### After (올바른 v2)
```
- PDCA Feature Registration (MANDATORY):
  - AI가 규칙을 skip해도 강제 등록 가능: `python scripts/pdca_auto_register.py`
  - 스크립트가 `.pdca-status.json`에서 planPath 없는 피처를 감지하여:
    1. 경량 Plan 자동 생성 (`docs/01-plan/features/`)
    2. `.pdca-status.json`에 planPath 등록
    3. `config/pdca_id_map.json`에 PDCA-XXX ID 할당
  - REQUESTS.md는 대상이 아님 (REQ-XXX는 별도 체계)
  - 사전 확인: `python scripts/pdca_auto_register.py --dry-run`
```

## 4. 구현 순서

| Step | 작업 | 파일 |
|------|------|------|
| 1 | 스크립트 기본 구조 + CLI argparse | `scripts/pdca_auto_register.py` |
| 2 | `load_unregistered_features()` — 노이즈 필터 | 위 동일 |
| 3 | `ensure_pdca_id()` — ID 할당 | 위 동일 |
| 4 | `create_lightweight_plan()` — 경량 Plan 생성 | 위 동일 |
| 5 | `update_pdca_status()` — planPath 등록 | 위 동일 |
| 6 | dry-run 모드 + 리포트 출력 | 위 동일 |
| 7 | CLAUDE.md 규칙 업데이트 | `CLAUDE.md` |
| 8 | E2E 테스트 | — |

## 5. 에러 처리

| 상황 | 처리 |
|------|------|
| .pdca-status.json 없음 | 에러 메시지 + exit 1 |
| pdca_id_map.json 없음 | 에러 메시지 + exit 1 |
| Plan 파일 이미 존재 | skip (경로만 반환) |
| features 항목이 dict가 아님 | skip |
| 한글 인코딩 | utf-8 명시, `sys.stdout.reconfigure(encoding='utf-8')` |

## 6. 테스트 시나리오

| # | 시나리오 | 기대 결과 |
|---|---------|------------|
| T1 | `--dry-run` 실행 | planPath 없는 실제 피처 목록 출력, 파일 변경 없음 |
| T2 | 실행 | 경량 Plan 생성 + .pdca-status.json planPath 등록 + pdca_id_map ID 할당 |
| T3 | 재실행 | 0건 (이미 등록된 건 skip) |
| T4 | `--feature NAME` | 해당 건만 등록 |
| T5 | 노이즈 필터 | backend, scripts 등 단일 단어 피처는 무시 |
| T6 | REQUESTS.md 무변경 | 실행 전후 REQUESTS.md diff 없음 |
