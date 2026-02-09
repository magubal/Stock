#!/usr/bin/env python3
"""
프로젝트 요청 관리자
- 초기 요청 추적
- 변경 이력 관리  
- 진행 상황 모니터링
"""

import json
import os
from datetime import datetime
from pathlib import Path

class ProjectRequestManager:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.data_dir = self.project_root / "data" / "naver_blog_data"
        self.index_dir = self.data_dir / "index"
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        # 관리 파일들
        self.request_file = self.index_dir / "request_history.json"
        self.change_log_file = self.index_dir / "change_log.json"
        self.progress_file = self.index_dir / "progress_status.json"
        
        # 초기화
        self._initialize_tracking()
    
    def _initialize_tracking(self):
        """요청 추적 시스템 초기화"""
        
        # 초기 요청 기록 (이미 있으면 생략)
        if not self.request_file.exists():
            initial_request = {
                "initial_request": {
                    "date": datetime.now().isoformat(),
                    "requirement": "네이버 블로그 데이터를 이미지로 자동 수집",
                    "structure": "data/naver_blog_data/일자/블로거_순번.jpg",
                    "priority": "본문 정보 완성도",
                    "constraints": [
                        "매일 자동 실행",
                        "중복 방지", 
                        "이미지 품질 유지",
                        "시장 평가용 정보",
                        "하트/댓글/관련링크 제거"
                    ]
                }
            }
            self._save_json(self.request_file, initial_request)
            print("초기 요청 기록 완료")
        
        # 변경 로그 초기화
        if not self.change_log_file.exists():
            initial_log = {"changes": []}
            self._save_json(self.change_log_file, initial_log)
        
        # 진행 상태 초기화
        if not self.progress_file.exists():
            initial_progress = {
                "current_status": {
                    "phase": "초기 개발",
                    "completion": 10,
                    "issues": [],
                    "next_actions": ["기본 수집기 개발", "이미지 캡처 구현"]
                }
            }
            self._save_json(self.progress_file, initial_progress)
    
    def _save_json(self, file_path: Path, data: dict):
        """JSON 파일 저장"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _load_json(self, file_path: Path) -> dict:
        """JSON 파일 로드"""
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def record_change(self, requester: str, original: str, change: str, result: str = "", approved: bool = False):
        """변경 사항 기록"""
        log_data = self._load_json(self.change_log_file)
        
        new_change = {
            "date": datetime.now().isoformat(),
            "requester": requester,
            "original": original,
            "change": change,
            "result": result,
            "approved": approved
        }
        
        log_data["changes"].append(new_change)
        self._save_json(self.change_log_file, log_data)
        
        print(f"변경 기록: {requester} - {original} → {change}")
    
    def update_progress(self, phase: str, completion: int, issues: list = None, next_actions: list = None):
        """진행 상황 업데이트"""
        progress_data = {
            "current_status": {
                "phase": phase,
                "completion": completion,
                "issues": issues or [],
                "next_actions": next_actions or [],
                "last_updated": datetime.now().isoformat()
            }
        }
        
        self._save_json(self.progress_file, progress_data)
        print(f"진행 상황 업데이트: {phase} ({completion}%)")
    
    def get_original_request(self) -> dict:
        """초기 요청 내용 가져오기"""
        data = self._load_json(self.request_file)
        return data.get("initial_request", {})
    
    def get_change_history(self) -> list:
        """변경 이력 가져오기"""
        data = self._load_json(self.change_log_file)
        return data.get("changes", [])
    
    def get_current_progress(self) -> dict:
        """현재 진행 상황 가져오기"""
        data = self._load_json(self.progress_file)
        return data.get("current_status", {})
    
    def validate_structure(self) -> bool:
        """현재 구조가 초기 요청과 일관성 있는지 검증"""
        original_request = self.get_original_request()
        expected_structure = original_request.get("structure", "")
        
        # 현재 디렉토리 구조 확인
        if not self.data_dir.exists():
            return False
        
        # 일자별 폴더 확인
        date_dirs = [d for d in self.data_dir.iterdir() if d.is_dir() and d.name not in ['index']]
        
        # 파일 규칙 확인 (블로거_순번.jpg)
        for date_dir in date_dirs:
            files = [f for f in date_dir.glob("*.jpg")]
            for file in files:
                if not self._validate_filename(file.name):
                    print(f"규칙 위반: {file.name}")
                    return False
        
        print("구조 검증 완료")
        return True
    
    def _validate_filename(self, filename: str) -> bool:
        """파일명 규칙 검증: 블로거_순번.jpg"""
        if not filename.endswith('.jpg'):
            return False
        
        base_name = filename[:-4]  # .jpg 제거
        parts = base_name.split('_')
        
        # 블로거_순번 형식인지 확인
        if len(parts) != 2:
            return False
        
        # 순번이 숫자인지 확인
        try:
            int(parts[1])
            return True
        except ValueError:
            return False
    
    def check_request_consistency(self, new_requirement: str) -> dict:
        """새 요청과 기존 요청의 일관성 확인"""
        original_request = self.get_original_request()
        
        comparison = {
            "original_requirement": original_request.get("requirement", ""),
            "new_requirement": new_requirement,
            "is_consistent": True,
            "differences": [],
            "needs_review": False,
            "recommendation": ""
        }
        
        # 1. 완전히 동일한지 확인
        if original_request.get("requirement", "") == new_requirement:
            comparison["recommendation"] = "기존 요청과 동일합니다. 기존 프로세스를 계속 진행합니다."
            return comparison
        
        # 2. 핵심 키워드 비교
        original_keywords = set(original_request.get("requirement", "").lower().split())
        new_keywords = set(new_requirement.lower().split())
        
        # 3. 중요 요소 비교
        important_elements = {
            "네이버 블로그": ["네이버", "블로그", "naver", "blog"],
            "이미지 수집": ["이미지", "수집", "캡처", "저장"],
            "자동화": ["자동", "매일", "스케줄", "스케줄러"],
            "본문 추출": ["본문", "정보", "내용", "텍스트"],
            "파일 구조": ["폴더", "파일", "구조", "일자별"],
            "시장 평가": ["시장", "종목", "평가", "투자", "주식"]
        }
        
        for element, keywords in important_elements.items():
            original_has = any(kw in original_request.get("requirement", "").lower() for kw in keywords)
            new_has = any(kw in new_requirement.lower() for kw in keywords)
            
            if original_has != new_has:
                comparison["differences"].append({
                    "element": element,
                    "original": original_has,
                    "new": new_has,
                    "impact": "높음" if element in ["네이버 블로그", "이미지 수집"] else "보통"
                })
                comparison["is_consistent"] = False
        
        # 4. 일관성 평가 및 권장사항
        if not comparison["is_consistent"]:
            comparison["needs_review"] = True
            
            # 가장 중요한 변경 확인
            high_impact_changes = [d for d in comparison["differences"] if d["impact"] == "높음"]
            
            if high_impact_changes:
                comparison["recommendation"] = """
⚠️ 중요한 변경이 있습니다:
기존: 네이버 블로그 이미지 수집 (본문 정보 완성도)
변경: {}

변경이 필요한 경우 다음을 확인하세요:
1. 기존 프로젝트와 계속 진행할 것인가?
2. 새로운 프로젝트로 시작할 것인가?
3. 기존 기능과 병합할 것인가?

변경을 계속하시겠습니까? (y/n):
""".format(new_requirement)
            else:
                comparison["recommendation"] = """
📝 세부 사항 변경이 있습니다:
기존 요청과 일부 변경사항이 있습니다.
계속 진행하시겠습니까? (y/n):
"""
        
        return comparison
    
    def request_user_confirmation(self, comparison: dict) -> bool:
        """사용자에게 변경 확인 요청"""
        print("\n" + "="*60)
        print("🔄 요청 변경 확인")
        print("="*60)
        
        print(f"기존 요청: {comparison['original_requirement']}")
        print(f"새 요청:    {comparison['new_requirement']}")
        print(f"일관성: {'✅ 일치' if comparison['is_consistent'] else '❌ 불일치'}")
        
        if comparison["differences"]:
            print("\n📋 차이점:")
            for diff in comparison["differences"]:
                status = "추가" if diff["new"] and not diff["original"] else "제거" if not diff["new"] and diff["original"] else "변경"
                print(f"  • {diff['element']}: {status} (영향: {diff['impact']})")
        
        print(f"\n{comparison['recommendation']}")
        
        if comparison["needs_review"]:
            try:
                response = input("변경을 계속 진행하시겠습니까? (y/n): ").strip().lower()
                return response in ['y', 'yes', '예']
            except KeyboardInterrupt:
                print("\n요청이 취소되었습니다.")
                return False
        else:
            print("✅ 기존 요청과 일치합니다. 계속 진행합니다.")
            return True
    
    def record_request_change(self, old_request: str, new_request: str, user_confirmed: bool):
        """요청 변경 기록"""
        change_data = {
            "date": datetime.now().isoformat(),
            "type": "requirement_change",
            "old": old_request,
            "new": new_request,
            "user_confirmed": user_confirmed,
            "auto_processed": not user_confirmed  # 자동 처리된 경우
        }
        
        log_data = self._load_json(self.change_log_file)
        log_data["changes"].append(change_data)
        self._save_json(self.change_log_file, log_data)
    
    def process_new_request(self, new_requirement: str) -> bool:
        """새 요청 처리 프로세스"""
        print("🔍 새 요청 검증 중...")
        
        # 1. 일관성 확인
        comparison = self.check_request_consistency(new_requirement)
        
        # 2. 사용자 확인 (필요 시)
        if comparison["needs_review"]:
            confirmed = self.request_user_confirmation(comparison)
            
            if not confirmed:
                print("❌ 요청이 거부되었습니다. 기존 프로세스를 유지합니다.")
                return False
        else:
            print("✅ 요청이 확인되었습니다.")
        
        # 3. 변경 기록
        self.record_request_change(
            comparison["original_requirement"], 
            new_requirement, 
            comparison["is_consistent"]
        )
        
        return True
    
    def print_summary(self):
        """현재 상황 요약 출력"""
        print("=== 프로젝트 요청 관리 요약 ===")
        
        # 초기 요청
        original = self.get_original_request()
        print(f"초기 요청: {original.get('requirement', '없음')}")
        print(f"요청 구조: {original.get('structure', '없음')}")
        
        # 진행 상황
        progress = self.get_current_progress()
        print(f"현재 단계: {progress.get('phase', '없음')}")
        print(f"완료도: {progress.get('completion', 0)}%")
        
        # 변경 이력
        changes = self.get_change_history()
        print(f"총 변경 수: {len(changes)}")
        
        if changes:
            print("\n최근 변경:")
            for change in changes[-3:]:  # 최근 3개만
                change_type = change.get('type', 'unknown')
                if change_type == 'requirement_change':
                    print(f"  • 요청 변경: {change.get('old', '')[:30]}... → {change.get('new', '')[:30]}...")
                else:
                    print(f"  - {change['original']} → {change['change']}")
        
        # 구조 검증
        print(f"\n구조 일관성: {'OK' if self.validate_structure() else 'FAIL'}")
        
        print("\n💡 새 요청 시 'process_new_request()' 메서드를 호출하세요.")

def main():
    """프로젝트 관리자 실행"""
    project_root = "F:/PSJ/AntigravityWorkPlace/Stock/Test_02"
    
    manager = ProjectRequestManager(project_root)
    
    # 예시: 변경 기록
    manager.record_change(
        requester="user",
        original="정보 누락 문제 해결",
        change="파일 구조 표준화 (daybyday_001.jpg)",
        result="구조 일관성 확보",
        approved=True
    )
    
    # 진행 상황 업데이트
    manager.update_progress(
        phase="본문 추출 완성",
        completion=85,
        issues=["하트/댓글 제거 개선"],
        next_actions=["메인 수집기 통합", "자동화 테스트"]
    )
    
    # 요약 출력
    manager.print_summary()

if __name__ == "__main__":
    main()