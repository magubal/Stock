#!/usr/bin/env python3
"""
업무 연속성 자동 확인 스크립트
- 모든 모델이 세션 시작 시 자동으로 실행
- 업무 연속성 보장
"""

import os
from datetime import datetime
from pathlib import Path

def check_continuity():
    """업무 연속성 체크"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    print("=" * 60)
    print("🚨 업무 연속성 체크 - 모든 모델 필수 실행")
    print("=" * 60)
    
    # 1. 최신 개발 로그 확인
    dev_log = Path(f"docs/development_log_{today}.md")
    
    if dev_log.exists():
        print(f"✅ 개발 로그 존재: {dev_log}")
        with open(dev_log, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 핵심 정보 추출
        if "현재 프로젝트 상태" in content:
            print("✅ 프로젝트 상태 기록됨")
        if "결정 사항" in content:
            print("✅ 결정 사항 기록됨")
        if "다음 모델을 위한 컨텍스트" in content:
            print("✅ 컨텍스트 기록됨")
            
    else:
        print(f"❌ 개발 로그 없음: {dev_log}")
        print("⚠️  먼저 개발 로그부터 생성해주세요!")
        return False
    
    # 2. TODO 상태 확인
    try:
        import subprocess
        result = subprocess.run(['opencode', 'todoread'], 
                            capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ TODO 상태 확인 가능")
        else:
            print("⚠️  TODO 상태 확인 실패")
    except:
        print("⚠️  TODO 확인 명령어 없음")
    
    print("=" * 60)
    print("📋 필수 확인 완료 - 작업 시작 가능")
    print("=" * 60)
    
    return True

def main():
    check_continuity()

if __name__ == "__main__":
    main()