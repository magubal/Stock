# Mini Consistency Batch - Test Scenario

목적: 일관성 모니터링이 요구사항/계획/설계 누락을 차단하고, 배치는 차단 항목만 격리 후 계속 진행하는지 검증.

## Demo Script
- `scripts/demo/mini_consistency_batch.py`

## Input
- `data/demo/mini_input.csv`
- 6행 구성:
1. `ok` (정상)
2. `missing_requirement_refs` (요구사항 참조 누락)
3. `missing_plan_refs` (계획 참조 누락)
4. `missing_req_id` (REQ-ID 누락)
5. `consistency_off` (일관성 모니터링 비활성)
6. `ok` (정상)

## Run
```bash
python scripts/demo/mini_consistency_batch.py
```

## Expected
1. 총 6건 처리
2. `OK` 2건, `BLOCKED` 4건
3. `BLOCKED` 행에는 `incident_id`, `rule_code`, `reasons`가 기록됨
4. 배치가 중간 중단되지 않고 끝까지 진행됨

## Output
- `data/demo/mini_output.csv`

## Validation Commands
```bash
python -m unittest discover -s backend/tests -p "test_mini_consistency_batch.py" -v
python scripts/ci/check_entrypoint_monitoring.py --scope changed --base-ref HEAD~1
```
