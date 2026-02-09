---
name: Implementation Guardian
description: 구현 과정이 계획 및 설계와 일치하는지 모니터링하고 가이드하는 스킬
---

# 구현 가디언 (Implementation Guardian)

## 개요
이 스킬은 개발자가 작성한 계획(`*.plan.md`)과 설계(`*.design.md`)가 실제 구현 단계에서 정확하게 반영되고 있는지 실시간으로 검증합니다. 계획에서 벗어나거나 중요한 요구사항이 누락된 경우 즉시 경고를 발생시킵니다.

## 주요 기능

### 1. 계획 정합성 검토 (Plan Alignment)
- 현재 작업 중인 단계의 계획 문서를 로드합니다.
- [ ] 체크리스트와 실제 파일 변경 사항을 대조합니다.
- 특히 **Critical** 및 **High** 우선순위 요구사항의 반영 여부를 추적합니다.

### 2. 이탈 탐지 (Deviation Detection)
- 계획에 없던 과도한 설계 변경이나 기능 추가를 감지합니다.
- 계획된 모듈 구조(예: `PhasePlan`)를 무시하는 구현을 식별합니다.

### 3. 품질 임계값 검증 (Quality Gating)
- 코드 스타일, 에러 핸들링, 주석 등 설계 문서에 명시된 품질 기준을 확인합니다.
- 문제 발견 시 구체적인 수정 가이드(Suggested Diffs)를 제시합니다.

## 작동 방식
1. **Context Load**: `CHANGELOG.md`(필수), `CLAUDE.md`, `TODO.md` 및 생성된 `*.plan.md` 파일을 읽습니다.
   - **중요**: `CHANGELOG.md`의 변경 이력과 Rationale을 먼저 파악해야 합니다.
2. **Execution Monitoring**: 현재 수행 중인 `run_command` 또는 `write_to_file` 결과를 캡처합니다.
3. **Verification**: 캡처된 결과가 계획된 `Success Criteria`를 충족하는지 비교 분석합니다.
4. **Action**:
   - 일치 시: 다음 단계 진행 승인.
   - 불일치 시: **[GUARDIAN ALERT]** 메시지와 함께 중단 및 수정 요청.

## 임계값 (Thresholds)
- **Critical Requirement Missed**: 즉시 중단 및 수정 필수.
- **Architectural Deviation**: 설계 문서와 다른 구조로 구현될 경우 경고 발생.
- **Performance/Safety Constraint Violated**: 리스크 리포트 생성.
