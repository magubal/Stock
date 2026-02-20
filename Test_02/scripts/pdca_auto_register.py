#!/usr/bin/env python3
"""
PDCA Feature 강제 등록 스크립트 (v2 — 재작성)

AI가 CLAUDE.md 규칙을 skip할 때, .pdca-status.json에서 planPath 없는 피처를 감지하여:
  1. 경량 Plan 자동 생성 (docs/01-plan/features/)
  2. .pdca-status.json에 planPath 등록 → 개발현황 대시보드 표시
  3. config/pdca_id_map.json에 PDCA-XXX ID 할당

**REQUESTS.md는 대상이 아님** (REQ-XXX는 별도 체계)

Usage:
    python scripts/pdca_auto_register.py              # 미등록 건 감지 + 강제 등록
    python scripts/pdca_auto_register.py --dry-run     # 실제 수정 없이 대상만 출력
    python scripts/pdca_auto_register.py --feature X   # 특정 피처만 등록
"""

import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
PDCA_STATUS = ROOT / "docs" / ".pdca-status.json"
PDCA_ID_MAP = ROOT / "config" / "pdca_id_map.json"
PLAN_DIR = ROOT / "docs" / "01-plan" / "features"


def is_real_feature(name):
    """노이즈 필터: 실제 피처인지 판별.

    실제 피처: kebab-case, 하이픈 포함 (oracle-earnings-integration 등)
    노이즈: 단일 단어(backend), 파일명(insight_extractor.py), 디렉토리(stock_moat)
    """
    if "." in name:  # 파일명
        return False
    if "-" not in name:  # kebab-case가 아님 → 노이즈
        return False
    return True


def load_unregistered_features(feature_filter=None):
    """.pdca-status.json에서 planPath 없는 실제 피처 추출."""
    if not PDCA_STATUS.exists():
        print(f"[ERROR] {PDCA_STATUS} not found")
        sys.exit(1)

    with open(PDCA_STATUS, "r", encoding="utf-8") as f:
        data = json.load(f)

    unregistered = []
    for name, info in data.get("features", {}).items():
        if not isinstance(info, dict):
            continue

        # 특정 피처 필터
        if feature_filter and name != feature_filter:
            continue

        # 노이즈 필터
        if not is_real_feature(name):
            continue

        # bkit 파일 감시가 자동 생성한 엔트리 → 노이즈
        if "phaseNumber" in info or "timestamps" in info:
            continue

        # 이미 planPath가 있으면 skip (등록 완료)
        if info.get("planPath"):
            continue

        # archivedTo가 있으면 skip (아카이브 완료)
        if info.get("archivedTo"):
            continue

        phase = info.get("phase", "unknown")

        unregistered.append({
            "name": name,
            "phase": phase,
            "info": info,
        })

    return unregistered


def load_id_map():
    """pdca_id_map.json 로드."""
    if not PDCA_ID_MAP.exists():
        print(f"[ERROR] {PDCA_ID_MAP} not found")
        sys.exit(1)

    with open(PDCA_ID_MAP, "r", encoding="utf-8") as f:
        return json.load(f)


def save_id_map(id_data):
    """pdca_id_map.json 저장."""
    with open(PDCA_ID_MAP, "w", encoding="utf-8") as f:
        json.dump(id_data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def ensure_pdca_id(feature_name, id_data):
    """PDCA ID 할당 (없으면 _nextId 사용)."""
    existing_id = id_data.get("map", {}).get(feature_name)
    if existing_id:
        return existing_id

    next_id = id_data.get("_nextId", 1)
    id_data.setdefault("map", {})[feature_name] = next_id
    id_data["_nextId"] = next_id + 1
    return next_id


def feature_name_to_title(name):
    """feature-name → 읽기 좋은 제목."""
    return name.replace("-", " ").replace("_", " ").title()


def create_lightweight_plan(feature_name, pdca_id):
    """경량 Plan 파일 생성. 이미 있으면 skip."""
    plan_path = PLAN_DIR / f"{feature_name}.plan.md"
    relative_path = f"docs/01-plan/features/{feature_name}.plan.md"

    if plan_path.exists():
        print(f"    Plan 이미 존재: {relative_path}")
        return relative_path

    title = feature_name_to_title(feature_name)
    content = f"""# {title} Plan

> (자동 등록됨 — PDCA-{pdca_id:03d})

## 배경
- `.pdca-status.json`에서 `planPath` 없이 감지된 피처
- `scripts/pdca_auto_register.py`에 의해 자동 생성

## 범위
- {feature_name} 기능 구현

## 산출물
| 파일 | 변경 내용 |
|------|-----------|
| (추후 보완) | — |

## 완료 상태
- [ ] 미완료
"""

    PLAN_DIR.mkdir(parents=True, exist_ok=True)
    with open(plan_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"    Plan 생성: {relative_path}")
    return relative_path


def update_pdca_status(feature_name, plan_path):
    """.pdca-status.json에 planPath 추가."""
    with open(PDCA_STATUS, "r", encoding="utf-8") as f:
        data = json.load(f)

    features = data.get("features", {})
    if feature_name in features:
        features[feature_name]["planPath"] = plan_path
    else:
        features[feature_name] = {
            "phase": "do",
            "planPath": plan_path,
        }

    with open(PDCA_STATUS, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"    pdca-status.json 업데이트: planPath 등록")


def main():
    parser = argparse.ArgumentParser(description="PDCA 강제 등록 (planPath + 경량 Plan)")
    parser.add_argument("--dry-run", action="store_true", help="실제 수정 없이 대상만 출력")
    parser.add_argument("--feature", type=str, help="특정 피처만 등록")
    args = parser.parse_args()

    print("=" * 55)
    print("PDCA 강제 등록 — planPath 없는 피처 감지 + 경량 Plan 생성")
    print("=" * 55)

    # 1) 미등록 피처 로드
    unregistered = load_unregistered_features(feature_filter=args.feature)
    print(f"\n[SCAN] planPath 없는 실제 피처: {len(unregistered)}건")

    if not unregistered:
        print("[OK] 모든 피처가 정상 등록되어 있음 — 변경 불필요")
        print(f"\n{'=' * 55}")
        print("[완료] 0건 등록")
        print("=" * 55)
        return

    for feat in unregistered:
        print(f"  [{feat['phase']}] {feat['name']}")

    if args.dry_run:
        print(f"\n[DRY-RUN] {len(unregistered)}건 등록 대상 (파일 변경 없음)")
        print(f"\n{'=' * 55}")
        print(f"[DRY-RUN 완료] {len(unregistered)}건 대상 확인")
        print("=" * 55)
        return

    # 2) ID Map 로드
    id_data = load_id_map()

    # 3) 각 피처에 대해 등록 실행
    count = 0
    for feat in unregistered:
        name = feat["name"]
        print(f"\n[등록] {name}")

        # PDCA ID 할당
        pdca_id = ensure_pdca_id(name, id_data)
        print(f"    PDCA ID: PDCA-{pdca_id:03d}")

        # 경량 Plan 생성
        plan_path = create_lightweight_plan(name, pdca_id)

        # .pdca-status.json 업데이트
        update_pdca_status(name, plan_path)

        count += 1

    # 4) ID Map 저장 (한 번만)
    save_id_map(id_data)
    print(f"\n    pdca_id_map.json 저장 완료")

    print(f"\n{'=' * 55}")
    print(f"[완료] {count}건 등록")
    print("=" * 55)


if __name__ == "__main__":
    main()
