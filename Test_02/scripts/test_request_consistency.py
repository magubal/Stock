#!/usr/bin/env python3
"""
요청 일관성 확인 시스템 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from project_request_manager import ProjectRequestManager

def test_request_consistency():
    """요청 일관성 확인 시스템 테스트"""
    
    print("요청 일관성 확인 시스템 테스트")
    print("="*50)
    
    # 프로젝트 관리자 초기화
    project_root = "F:/PSJ/AntigravityWorkPlace/Stock/Test_02"
    manager = ProjectRequestManager(project_root)
    
    # 테스트 케이스들
    test_cases = [
        {
            "name": "동일 요청",
            "request": "네이버 블로그 데이터를 이미지로 자동 수집",
            "expected": "일치"
        },
        {
            "name": "약간 다른 요청",
            "request": "네이버 블로그 이미지 수집 시스템 개선",
            "expected": "확인 필요"
        },
        {
            "name": "중요 변경 요청",
            "request": "다음 블로그 정보 텍스트로 추출해줘",
            "expected": "중요 변경"
        },
        {
            "name": "완전히 다른 요청",
            "request": "웹사이트 개발 프로젝트 시작",
            "expected": "완전 변경"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print("-" * 30)
        print(f"요청: {test_case['request']}")
        
        # 일관성 확인 (자동 모드로 테스트)
        comparison = manager.check_request_consistency(test_case['request'])
        
        print("결과:", comparison['recommendation'])
        
        if comparison['differences']:
            print("차이점:")
            for diff in comparison['differences']:
                print("  • {}: {} 영향".format(diff['element'], diff['impact']))
    
    print("\n" + "="*50)
    print("테스트 완료")

def interactive_request_test():
    """대화형 요청 테스트"""
    print("\n🔄 대화형 요청 테스트")
    print("새 요청을 입력해보세요 (종료: q)")
    
    project_root = "F:/PSJ/AntigravityWorkPlace/Stock/Test_02"
    manager = ProjectRequestManager(project_root)
    
    while True:
        try:
            user_input = input("\n새 요청 > ").strip()
            
            if user_input.lower() in ['q', 'quit', '종료']:
                print("테스트를 종료합니다.")
                break
            
            if not user_input:
                continue
            
            # 요청 처리
            confirmed = manager.process_new_request(user_input)
            
            if confirmed:
                print("✅ 요청이 처리되었습니다.")
            else:
                print("❌ 요청이 거부되었습니다.")
                
        except KeyboardInterrupt:
            print("\n테스트를 종료합니다.")
            break
        except Exception as e:
            print(f"오류: {e}")

def main():
    """메인 실행"""
    print("요청 일관성 확인 시스템 테스트를 선택하세요:")
    print("1. 자동 테스트")
    print("2. 대화형 테스트")
    
    choice = input("선택 (1/2): ").strip()
    
    if choice == "1":
        test_request_consistency()
    elif choice == "2":
        interactive_request_test()
    else:
        print("잘못된 선택입니다.")

if __name__ == "__main__":
    main()