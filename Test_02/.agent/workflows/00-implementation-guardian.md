---
description: 구현 가디언(Implementation Guardian)을 통한 계획 준수 여부 검증 워크플로우
---

구현 단계에서 계획 및 설계 문서와의 정합성을 검토합니다.

1. **대상 식별**
   - 현재 진행 중인 기능의 `*.plan.md` 또는 `*.design.md` 파일을 확인합니다.
   - 변경된 소스 코드 파일 목록을 확인합니다.

2. **가디언 호출**
   // turbo
   - `claude execute .agent/agents/implementation-guardian --task "Check if the current implementation in [FILE_PATH] aligns with the plan [PLAN_PATH]"` 명령을 실행합니다.

3. **결과 분석**
   - **[PASS]**: 계획대로 구현됨. 다음 단계로 진행합니다.
   - **[ALERT]**: 미흡하거나 이탈된 항목이 발견됨. 가디언의 추천 사항을 바탕으로 코드를 수정합니다.
   - **[CRITICAL]**: 필수 요구사항 누락. 즉시 수정을 완료한 후 다시 검증을 수행합니다.

4. **수정 및 재검증**
   - 이탈 사항이 해결될 때까지 2~3 단계를 반복합니다.
