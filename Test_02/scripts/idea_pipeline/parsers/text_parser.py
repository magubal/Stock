"""텍스트 파일 파서"""
from datetime import date
from typing import List
from .base_parser import BaseParser, DailyWorkRow


class TextParser(BaseParser):
    def supports(self, file_path: str) -> bool:
        return file_path.lower().endswith((".txt", ".md"))

    def parse(self, file_path: str) -> List[DailyWorkRow]:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if not content.strip():
            return []

        return [DailyWorkRow(
            date=date.today(),
            category="UNKNOWN",
            description=file_path.split("/")[-1].split("\\")[-1],
            content=content,
            source_link=file_path,
            source_type="text",
        )]
