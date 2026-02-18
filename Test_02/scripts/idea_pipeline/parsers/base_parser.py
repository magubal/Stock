"""범용 Parser 인터페이스"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import date


@dataclass
class DailyWorkRow:
    date: date
    category: str          # SECTOR, US_MARKET, THEME, RISK, NEXT_DAY, PORTFOLIO, AI_RESEARCH
    description: str = ""
    content: str = ""
    source_link: str = ""
    source_type: str = ""  # excel, csv, text, manual


class BaseParser(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> List[DailyWorkRow]:
        """파일을 파싱하여 DailyWorkRow 리스트 반환"""
        pass

    @abstractmethod
    def supports(self, file_path: str) -> bool:
        """이 파서가 해당 파일을 처리할 수 있는지 판별"""
        pass
