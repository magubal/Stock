# pdca-auto-register-v2 Plan

> AI가 CLAUDE.md 규칙을 skip할 때, 스크립트로 강제 등록하여 개발현황 대시보드 누락을 방지하는 건

## 배경

### 문제
- PDCA-013 `pdca-auto-register`가 CLAUDE.md 프로세스 규칙으로만 구현됨
- 에이전트가 규칙을 잊으면 신규 개발 건이 `.pdca-status.json`에 미등록 → 개발현황 대시보드에서 누락
- 동일 문제로 2번째 요청 — 프로세스 규칙은 자동화가 아닌 "희망사항"에 불과

### 근본 원인
| 항목 | v1 (PDCA-013) | v2 (이번) |
|------|---------------|-----------|
| 등록 메커니즘 | CLAUDE.md 텍스트 규칙 | Python 스크립트 (강제) |
| 에이전트 의존성 | 100% (기억해야 함) | 0% (스크립트가 강제 실행) |
| 소급 보정 | 불가 | 일괄 실행 모드 |

### ID 체계 (CRITICAL)
| 체계 | 용도 | 관리 주체 |
|------|------|-----------|
| **PDCA-XXX** | `/brain` `/bkit` `/pdca`로 개발한 건의 요청번호 | 이 프로젝트 (pdca_id_map.json) |
| **REQ-XXX** | 다른 Claude 인스턴스(Codex 등)가 관리하는 요청번호 | REQUESTS.md |
| **혼용 금지** | PDCA 건을 REQ-XXX로 재번호 매기면 중복 충돌 | — |

## 범위

### In Scope
1. **`scripts/pdca_auto_register.py`** — 강제 등록 스크립트
   - 프로젝트 내 구현 코드를 스캔하여 `.pdca-status.json`에 미등록된 건 감지
   - 미등록 건에 대해 **경량 Plan 자동 생성** (`docs/01-plan/features/{name}.plan.md`)
   - `.pdca-status.json`에 등록 (`planPath` 포함 → 대시보드 표시 가능)
   - `config/pdca_id_map.json`에 PDCA-XXX ID 자동 할당
   - dry-run 모드 (`--dry-run`)
   - 특정 피처 지정 (`--feature NAME`)

2. **CLAUDE.md 규칙 업데이트** — AI가 skip해도 스크립트로 강제 가능함을 명시

### Out of Scope
- **REQUESTS.md 수정 — 대상 아님** (REQ-XXX는 별도 체계)
- bkit 플러그인 자체 수정
- Hook 기반 자동화 (Phase 2)
- 대시보드 UI 변경

## 산출물

| 파일 | 변경 내용 |
|------|-----------|
| `scripts/pdca_auto_register.py` | **재작성** — .pdca-status.json + 경량 Plan 강제 등록 |
| `CLAUDE.md` | 규칙 업데이트 (스크립트 강제 등록 명시) |
| `config/pdca_id_map.json` | 신규 피처 PDCA-XXX ID 자동 할당 |
| `docs/.pdca-status.json` | 미등록 건 자동 추가 |
| `docs/01-plan/features/*.plan.md` | 미등록 건 경량 Plan 자동 생성 |

## 스크립트 상세

### `scripts/pdca_auto_register.py`

```
Usage:
  python scripts/pdca_auto_register.py              # 미등록 건 감지 + 강제 등록
  python scripts/pdca_auto_register.py --dry-run     # 실제 수정 없이 대상만 출력
  python scripts/pdca_auto_register.py --feature X   # 특정 피처만 등록
```

### 핵심 로직
1. `.pdca-status.json`의 `features` 스캔 → `planPath`가 없는 실제 피처 감지
2. 해당 피처에 대해:
   a. `docs/01-plan/features/{name}.plan.md` 경량 Plan 생성 (없을 때)
   b. `.pdca-status.json`에 `planPath` 추가
   c. `config/pdca_id_map.json`에 PDCA-XXX ID 할당 (없을 때)
3. 결과 리포트 출력

### 경량 Plan 템플릿
```markdown
# {feature-name} Plan

> {feature-name을 읽기 좋게 변환한 제목}

## 배경
- (자동 등록 — 상세 내용 추후 보완 필요)

## 범위
- `.pdca-status.json`에서 감지된 피처

## 산출물
| 파일 | 변경 내용 |
|------|-----------|
| (추후 보완) | — |
```

## 성공 기준 (DoD)
1. `--dry-run` 실행 시 `planPath` 없는 피처 목록 정확히 출력
2. 실행 시 경량 Plan 파일 생성 + `.pdca-status.json` planPath 등록
3. 등록 후 개발현황 대시보드에 해당 피처 표시됨
4. PDCA-XXX ID가 `pdca_id_map.json`에 정확히 할당됨
5. **REQUESTS.md는 건드리지 않음**
6. 재실행 시 이미 등록된 건은 skip

## 리스크/완화
- **R1**: 노이즈 피처 등록 (backend, scripts 등) → `planPath` 없는 것 중 실제 피처만 필터 (이름 패턴)
- **R2**: pdca_id_map.json ID 충돌 → `_nextId` 기반 단조증가 보장
- **R3**: 경량 Plan이 너무 빈약 → 최소 구조 보장 + "추후 보완" 마킹

## 완료 상태
- [ ] 미완료
