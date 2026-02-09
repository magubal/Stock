from abc import ABC, abstractmethod
from typing import List, Dict, Any
import asyncio
from datetime import datetime

class BaseCollector(ABC):
    """데이터 수집기 기본 클래스"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = self.__class__.__name__
    
    @abstractmethod
    async def collect(self) -> List[Dict[str, Any]]:
        """데이터 수집 메서드"""
        pass
    
    @abstractmethod
    def parse_data(self, raw_data: Any) -> Dict[str, Any]:
        """데이터 파싱 메서드"""
        pass
    
    async def save_to_db(self, data: Dict[str, Any]):
        """데이터베이스 저장 (구현 필요)"""
        pass
    
    def get_headers(self) -> Dict[str, str]:
        """HTTP 요청 헤더"""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    async def run(self) -> List[Dict[str, Any]]:
        """전체 실행 프로세스"""
        try:
            print(f"🔍 {self.name} 데이터 수집 시작...")
            raw_data = await self.collect()
            parsed_data = [self.parse_data(data) for data in raw_data]
            
            # 데이터베이스 저장
            for data in parsed_data:
                await self.save_to_db(data)
            
            print(f"✅ {self.name}: {len(parsed_data)}개 데이터 수집 완료")
            return parsed_data
            
        except Exception as e:
            print(f"❌ {self.name} 데이터 수집 실패: {str(e)}")
            return []