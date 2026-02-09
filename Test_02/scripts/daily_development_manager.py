#!/usr/bin/env python3
"""
AI 어시스턴트 일일 개발 운영 매니저
- 일일 개발 로그 자동 생성
- 요청 추적 및 교차 확인
- 진행 상황 실시간 관리
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

class DailyDevelopmentManager:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.ops_dir = self.project_root / "project_management" / "daily_operations"
        self.ops_dir.mkdir(parents=True, exist_ok=True)
        
        # 관리 파일들
        self.daily_log_file = self.ops_dir / "daily_development_log.md"
        self.request_tracking_file = self.ops_dir / "request_tracking.md"
        self.cross_check_file = self.ops_dir / "cross_check_notes.md"
        self.milestones_file = self.ops_dir / "project_milestones.md"
        
        # 초기화
        self._initialize_daily_ops()
    
    def _initialize_daily_ops(self):
        """일일 운영 시스템 초기화"""
        
        # 마일스톤 초기화
        if not self.milestones_file.exists():
            initial_milestones = {
                "current_phase": "개발",
                "completion": 70,
                "milestones": [
                    {
                        "phase": "기본 수집기 개발",
                        "status": "완료",
                        "completion": 100,
                        "date": "2026-02-01"
                    },
                    {
                        "phase": "이미지 캡처 시스템",
                        "status": "진행 중",
                        "completion": 85,
                        "date": "2026-02-02"
                    },
                    {
                        "phase": "프로젝트 관리 시스템",
                        "status": "완료", 
                        "completion": 100,
                        "date": "2026-02-02"
                    },
                    {
                        "phase": "메인 수집기 통합",
                        "status": "대기",
                        "completion": 0,
                        "date": "2026-02-03"
                    },
                    {
                        "phase": "자동화 및 안정화",
                        "status": "대기",
                        "completion": 0,
                        "date": "2026-02-04"
                    }
                ]
            }
            self._save_json(self.milestones_file, initial_milestones)
    
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
    
    def start_morning_report(self, today_tasks: list = None):
        """아침 시작 보고"""
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # 어제 요약 읽기
        yesterday_summary = self._get_yesterday_summary(yesterday)
        
        # 오늘 보고 생성
        morning_report = f"""# 🌅 아침 개발 시작 보고 - {today}

## 전일 요약 ({yesterday})
{yesterday_summary}

## 오늘 계획
"""
        
        if today_tasks:
            for i, task in enumerate(today_tasks, 1):
                morning_report += f"{i}. {task}\n"
        else:
            # 기본 계획
            morning_report += """1. 메인 수집기에 본문 추출 로직 적용
2. 일자별/블로거_순번.jpg 구조 확정
3. 자동 스케줄러 시스템 통합
4. 프로젝트 관리 시스템 최종 확립
"""
        
        # 현재 상태
        current_status = self._get_current_status()
        morning_report += f"""
## 진행 상태
- 현재 단계: {current_status['phase']} ({current_status['completion']}%)
- 긴급 요청: {current_status['urgent_requests']}
- 예상 완료: {current_status['estimated_completion']}

---

⏰ 개발 시작 시간: {datetime.now().strftime('%H:%M')}
🎯 목표: 완성형 프로젝트 전환
"""
        
        # 일일 로그에 추가
        self._append_to_daily_log(today, morning_report)
        
        print("🌅 아침 보고 작성 완료")
        return morning_report
    
    def progress_report(self, progress_items: list):
        """진행 상황 중간 보고"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        progress_report = f"""
## 중간 보고 - {datetime.now().strftime('%H:%M')}

"""
        
        for item in progress_items:
            status_icon = "✅" if item.get('completed') else "🔄" if item.get('in_progress') else "⚠️"
            progress_report += f"{status_icon} {item.get('task', '')}\n"
            
            if item.get('details'):
                progress_report += f"   └ {item['details']}\n"
        
        progress_report += f"📋 다음: {progress_items[-1].get('next_task', 'TBD')}\n---\n"
        
        self._append_to_daily_log(today, progress_report)
        print("중간 진행 보고 완료")
    
    def evening_summary(self, completed_features: list, technical_decisions: list, remaining_tasks: list, validation_requests: list):
        """저녁 종료 요약"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        summary = f"""
# 🌙 일일 개발 요약 - {today}

## 완료된 기능
"""
        for i, feature in enumerate(completed_features, 1):
            summary += f"{i}. {feature}\n"
        
        summary += f"""
## 기술적 결정
"""
        for decision in technical_decisions:
            summary += f"- {decision}\n"
        
        summary += f"""
## 남은 과제
"""
        for i, task in enumerate(remaining_tasks, 1):
            summary += f"{i}. {task}\n"
        
        summary += f"""
## 사용자 검증 요청
"""
        for request in validation_requests:
            icon = "✅" if request.get('validated') else "❌"
            summary += f"{icon} {request.get('item', '')}\n"
            if request.get('details'):
                summary += f"   └ {request['details']}\n"
        
        summary += f"""
## 내일 계획
1. 사용자 피드백 반영
2. 메인 수집기 최종 버전 완성
3. 자동화 테스트 및 안정화
4. 프로덕션 환경 설정 준비

---
🏆 오늘 성과: {len(completed_features)}개 기능 완료
📈 전체 진행률: {self._update_progress(len(completed_features))}%
🎯 목표: 완성형 Stock Research ONE

⏰ 작업 종료: {datetime.now().strftime('%H:%M')}
"""
        
        # 일일 로그에 추가
        self._append_to_daily_log(today, summary)
        
        # 요청 추적 업데이트
        self._update_request_tracking(today, validation_requests)
        
        print("🌙 저녁 요약 작성 완료")
        return summary
    
    def _get_yesterday_summary(self, yesterday: str) -> str:
        """어제 요약 가져오기"""
        if self.daily_log_file.exists():
            content = self.daily_log_file.read_text(encoding='utf-8')
            # 어제 날짜 섹션 찾기
            yesterday_section = f"# 🌙 일일 개발 요약 - {yesterday}"
            if yesterday_section in content:
                start_idx = content.find(yesterday_section)
                end_idx = content.find("# 🌅 아침 개발 시작 보고", start_idx)
                if end_idx == -1:
                    end_idx = len(content)
                
                yesterday_content = content[start_idx:end_idx]
                return "✅ 어제 내용 있음"
        
        return "📝 어제 내용 없음"
    
    def _get_current_status(self) -> dict:
        """현재 상태 가져오기"""
        milestones = self._load_json(self.milestones_file)
        
        current_phase = "개발 중"
        completion = 70
        urgent_requests = "없음"
        estimated_completion = "오늘 오후"
        
        # 가장 최근 마일스톤 확인
        if "milestones" in milestones:
            for milestone in reversed(milestones["milestones"]):
                if milestone.get("status") == "진행 중":
                    current_phase = milestone.get("phase", "")
                    completion = milestone.get("completion", 0)
                    break
        
        return {
            "phase": current_phase,
            "completion": completion,
            "urgent_requests": urgent_requests,
            "estimated_completion": estimated_completion
        }
    
    def _update_progress(self, completed_count: int) -> int:
        """전체 진행률 업데이트"""
        milestones = self._load_json(self.milestones_file)
        
        # 간단한 진행률 계산
        base_progress = 70
        additional_progress = completed_count * 5
        
        total_progress = min(base_progress + additional_progress, 95)
        
        # 마일스톤 업데이트
        if "milestones" in milestones:
            for milestone in milestones["milestones"]:
                if milestone.get("status") == "진행 중":
                    milestone["completion"] = total_progress
                    break
        
        self._save_json(self.milestones_file, milestones)
        return total_progress
    
    def _update_request_tracking(self, date: str, validation_requests: list):
        """요청 추적 업데이트"""
        tracking_data = {
            "date": date,
            "requests": validation_requests,
            "status": "검증 대기 중",
            "timestamp": datetime.now().isoformat()
        }
        
        # 기존 내용에 추가
        if self.request_tracking_file.exists():
            existing_content = self.request_tracking_file.read_text(encoding='utf-8')
            new_content = existing_content + f"\n\n{json.dumps(tracking_data, ensure_ascii=False, indent=2)}"
        else:
            new_content = json.dumps(tracking_data, ensure_ascii=False, indent=2)
        
        self.request_tracking_file.write_text(new_content, encoding='utf-8')
    
    def _append_to_daily_log(self, date: str, content: str):
        """일일 로그에 내용 추가"""
        if self.daily_log_file.exists():
            existing_content = self.daily_log_file.read_text(encoding='utf-8')
            # 오늘 날짜가 있으면 추가, 없으면 새로 생성
            if f"# 🌅 아침 개발 시작 보고 - {date}" in existing_content:
                # 종료 요약 추가
                if "# 🌙 일일 개발 요약" in content:
                    content = "\n" + content
                existing_content = existing_content + content
            else:
                existing_content = existing_content + "\n\n" + content
        else:
            existing_content = content
        
        self.daily_log_file.write_text(existing_content, encoding='utf-8')
    
    def get_daily_summary(self) -> str:
        """일일 요약 가져오기"""
        if self.daily_log_file.exists():
            content = self.daily_log_file.read_text(encoding='utf-8')
            # 오늘 날짜 섹션 추출
            today = datetime.now().strftime('%Y-%m-%d')
            
            # 오늘 아침 보고부터 끝까지
            morning_pattern = f"# 🌅 아침 개발 시작 보고 - {today}"
            if morning_pattern in content:
                start_idx = content.find(morning_pattern)
                return content[start_idx:]
        
        return "오늘 개발 내용이 없습니다."

def main():
    """일일 개발 운영 테스트"""
    project_root = "F:/PSJ/AntigravityWorkPlace/Stock/Test_02"
    manager = DailyDevelopmentManager(project_root)
    
    # 아침 보고 테스트
    print("=== 아침 보고 테스트 ===")
    manager.start_morning_report([
        "메인 수집기에 본문 추출 로직 적용",
        "프로젝트 관리 시스템 확정",
        "사용자 검증 대기"
    ])
    
    # 중간 보고 테스트
    print("\n=== 중간 보고 테스트 ===")
    manager.progress_report([
        {
            "task": "본문 추출 로직 적용",
            "completed": True,
            "details": "Playwright 기반으로 95% 완료"
        },
        {
            "task": "파일 구조 표준화",
            "in_progress": True,
            "details": "daybyday_001.jpg 형식 확정",
            "next_task": "메인 수집기 통합"
        }
    ])
    
    # 저녁 요약 테스트
    print("\n=== 저녁 요약 테스트 ===")
    manager.evening_summary(
        completed_features=[
            "본문만 추출 Playwright 캡처 (5.2MB, 완전 정보)",
            "요청 일관성 확인 시스템 구축", 
            "프로젝트 관리 정책 수립",
            "일자별/블로거_순번.jpg 구조 확정"
        ],
        technical_decisions=[
            "Playwright > Selenium (안정성 우선)",
            "본문 정리: JS 기반 DOM 클리닝",
            "품질: 정보 완성도 > 용량 (Quality 70)"
        ],
        remaining_tasks=[
            "메인 수집기 최종 통합",
            "자동 스케줄러 안정화 테스트",
            "사용자 검증 대기"
        ],
        validation_requests=[
            {
                "item": "일자별 폴더 구조",
                "validated": True,
                "details": "daybyday_001.jpg 확인 완료"
            },
            {
                "item": "본문 완전성", 
                "validated": True,
                "details": "22:15 → 2/5일 데이터 연속성 보장"
            },
            {
                "item": "불필요 요소 제거",
                "validated": True,
                "details": "하트/댓글/관련링크 제거 완료"
            },
            {
                "item": "파일 크기",
                "validated": False,
                "details": "현재 5.2MB → 조정 필요?"
            }
        ]
    )
    
    # 결과 확인
    print("\n=== 일일 요약 확인 ===")
    print(manager.get_daily_summary())

if __name__ == "__main__":
    main()