# Consistency Monitoring Branch Protection

목표: `master/main` 브랜치에서 일관성 모니터링 필수 체크 없이 머지되지 않도록 강제한다.

## Required Check
- `consistency-monitoring-gate / consistency-monitoring-gate`

## 1) 자동 적용 스크립트
토큰에 저장소 admin 권한이 있어야 한다.

```bash
python scripts/ci/apply_branch_protection.py --repo <owner/repo> --branch master --strict
```

메인 브랜치가 `main`이면:

```bash
python scripts/ci/apply_branch_protection.py --repo <owner/repo> --branch main --strict
```

## 2) 수동 확인 항목
1. Branch protection rule 활성화
2. Require a pull request before merging
3. Require status checks to pass before merging
4. Required checks에 아래 항목 포함
   - `consistency-monitoring-gate / consistency-monitoring-gate`
5. Restrict force pushes (권장)
6. Include administrators (권장)

## 3) CI 게이트 내용
워크플로: `.github/workflows/consistency-monitoring-gate.yml`

1. 신규 엔트리포인트 모니터링 호출 누락 정적 검사
2. 모니터링 가드 테스트
3. 협업 트리아지 회귀 테스트
