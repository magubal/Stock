#!/usr/bin/env python3
"""
마스터플랜 기반 프로젝트 상태 분석 스크립트
다른 모델이 현재 진행 상황 파악 및 개발 가이드
"""

import os
import json
from pathlib import Path
from datetime import datetime

class MasterPlanAnalyzer:
    def __init__(self):
        self.project_root = Path(".")
        self.workflows_dir = self.project_root / ".agent/workflows"
        self.skills_dir = self.project_root / ".agent/skills"
        
    def analyze_current_status(self):
        """현재 프로젝트 상태 분석"""
        print("=" * 60)
        print("Stock Research ONE - 마스터플랜 상태 분석")
        print("=" * 60)
        
        # 1. 워크플로우 상태
        self.analyze_workflows()
        
        # 2. 스킬 상태  
        self.analyze_skills()
        
        # 3. TODO 연동 상태
        self.analyze_todo_integration()
        
        # 4. 현재 개발 현황
        self.analyze_current_development()
        
        print("\n" + "=" * 60)
        print("🎯 다른 모델 개발 가이드")
        print("=" * 60)
        self.development_guidance()
        
    def analyze_workflows(self):
        """워크플로우 상태 분석"""
        print("\n7단계 워크플로우 상태:")
        
        workflows = [
            ("01-data-collection", "데이터 수집", 85),
            ("02-context-analysis", "맥락연결/영향분석", 0),
            ("03-importance-evaluation", "중요도 파악", 0), 
            ("04-decision-scenario", "의사결정 시나리오", 0),
            ("05-execution-check", "실질확인", 0),
            ("06-review-improvement", "결과확인/복기", 0),
            ("07-trend-research", "트렌드 핵심정리", 0)
        ]
        
        for step, name, completion in workflows:
            file_path = self.workflows_dir / f"{step}.md"
            status = "[완료]" if file_path.exists() else "[미완료]"
            print(f"  {status} {step}: {name} ({completion}% 완료)")
            
    def analyze_skills(self):
        """스킬 상태 분석"""
        print("\n스킬 시스템 상태:")
        
        if self.skills_dir.exists():
            skills = [d for d in self.skills_dir.iterdir() if d.is_dir()]
            for skill in skills:
                print(f"  [완료] {skill.name}: 스킬 정의됨")
        else:
            print("  [없음] 스킬 디렉토리 없음")
            
    def analyze_todo_integration(self):
        """TODO 연동 상태 분석"""
        print("\n📝 TODO 연동 상태:")
        
        # 현재 TODO 상태 읽기 시도
        try:
            import subprocess
            result = subprocess.run(['opencode', 'todoread'], 
                                capture_output=True, text=True)
            if result.returncode == 0:
                print("  ✅ TODO 상태 확인 가능")
                # TODO 내용 분석
                lines = result.stdout.split('\n')
                pending = len([l for l in lines if 'pending' in l.lower()])
                completed = len([l for l in lines if 'completed' in l.lower()])
                print(f"  📊 완료: {completed}, 진행중: {pending}")
            else:
                print("  ⚠️  TODO 확인 실패")
        except:
            print("  ❌ TODO 명령어 없음")
            
    def analyze_current_development(self):
        """현재 개발 현황 분석"""
        print("\n🔥 현재 개발 현황:")
        
        # 개발 로그 확인
        today = datetime.now().strftime('%Y-%m-%d')
        dev_log = self.project_root / f"docs/development_log_{today}.md"
        
        if dev_log.exists():
            print(f"  ✅ 오늘 개발 로그: {dev_log}")
            
            # 로그 내용 분석
            with open(dev_log, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if "85%" in content:
                print("  📈 현재 단계: 블로그 본문 추출 (85% 완료)")
            if "하트/댓글 제거" in content:
                print("  🎯 남은 과제: DOM 클리닝")
        else:
            print("  ❌ 오늘 개발 로그 없음")
            
    def development_guidance(self):
        """다른 모델 개발 가이드"""
        print("다른 모델은 다음 작업을 바로 시작할 수 있습니다:")
        
        print("\n🚀 바로 시작 가능한 작업:")
        print("1. 📊 스킬 시스템 개발")
        print("   - .agent/skills/context-analysis/ 개발")
        print("   - .agent/skills/importance-evaluation/ 개발")
        
        print("\n2. 🔄 워크플로우 2단계 시작")
        print("   - 02-context-analysis.md 구체화")
        print("   - 맥락연결/영향분석 알고리즘 개발")
        
        print("\n3. 📝 현재 작업 완료")
        print("   - 하트/댓글 영역 DOM 제거")
        print("   - 관련링크/사이드바 영역 제거")
        
        print("\n📖 자세한 내용:")
        print("- docs/development_log_2026-02-02.md 참조")
        print("- .agent/workflows/01-data-collection.md 확인")
        print("- `todoread`로 현재 TODO 상태 확인")

def main():
    analyzer = MasterPlanAnalyzer()
    analyzer.analyze_current_status()

if __name__ == "__main__":
    main()