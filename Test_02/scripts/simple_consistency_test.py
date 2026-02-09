#!/usr/bin/env python3
"""
간단한 요청 일관성 확인 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from project_request_manager import ProjectRequestManager

def main():
    print("요청 일관성 확인 테스트")
    print("=" * 40)
    
    project_root = "F:/PSJ/AntigravityWorkPlace/Stock/Test_02"
    manager = ProjectRequestManager(project_root)
    
    # 기존 요청 확인
    original_request = manager.get_original_request()
    print("기존 요청:", original_request.get("requirement", ""))
    
    # 새 요청 테스트
    new_request = "네이버 블로그 이미지 수집 시스템 개선"
    print("새 요청:", new_request)
    
    # 일관성 확인
    comparison = manager.check_request_consistency(new_request)
    
    print("일관성:", "일치" if comparison['is_consistent'] else "불일치")
    
    if comparison['differences']:
        print("차이점:")
        for diff in comparison['differences']:
            print("  - {}: {}".format(diff['element'], diff['impact']))
    
    print("\n확인 완료")

if __name__ == "__main__":
    main()