"""
DART Business Report Parser
Parses raw business report text (tags already stripped) into structured sections.

Target sections (from MGB-MOAT methodology):
- business_overview: 사업의 내용/개요
- major_products: 주요 제품 및 서비스
- competition: 경쟁 상황/시장 현황
- rnd: 연구개발 활동
- risk_factors: 위험 요인
- facilities: 생산설비/능력
- major_customers: 주요 고객/매출처

TOC Detection:
Uses "longest match" strategy - finds all section title matches,
extracts content for each, picks the longest (TOC entries are short).
"""

import re
import sys
from typing import Dict, List, Optional

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

MAX_SECTION_LENGTH = 15000


class DARTReportParser:
    """Parses DART business report text into structured sections"""

    TARGET_SECTIONS = {
        'business_overview': [
            r'사업의\s*내용',
            r'II\.\s*사업의\s*내용',
            r'1\.\s*사업의\s*개요',
            r'사업\s*개요',
        ],
        'major_products': [
            r'주요\s*제품\s*및\s*서비스',
            r'주요제품등의\s*현황',
            r'주요\s*제품\s*등의',
            r'주요\s*제품',
            r'주요\s*서비스',
        ],
        'competition': [
            r'산업의\s*특성',
            r'경쟁\s*상황',
            r'경쟁\s*현황',
            r'시장\s*현황',
            r'경쟁\s*요소',
            r'경쟁요소',
            r'시장\s*점유율',
            r'시장점유율',
        ],
        'rnd': [
            r'연구개발\s*활동',
            r'연구개발활동',
            r'연구\s*및\s*개발',
            r'연구\s*개발',
        ],
        'risk_factors': [
            r'위험\s*요인',
            r'사업의\s*위험',
            r'사업\s*위험',
            r'투자\s*위험',
            r'위험관리',
        ],
        'facilities': [
            r'생산\s*설비',
            r'원재료\s*및\s*생산설비',
            r'생산\s*능력',
            r'생산능력',
            r'설비\s*현황',
        ],
        'major_customers': [
            r'주요\s*고객',
            r'매출처',
            r'거래처',
            r'주요\s*매출처',
        ],
    }

    MAJOR_DELIMITERS = [
        r'III\.\s',
        r'IV\.\s',
        r'V\.\s',
        r'\[감사보고서\]',
        r'\[재무제표\]',
        r'재무에\s*관한\s*사항',
        r'이사의\s*경영진단',
    ]

    def parse_report(self, text: str) -> Dict[str, str]:
        """
        Parse business report text into structured sections.

        Args:
            text: Raw report text (HTML/XML tags already stripped)

        Returns:
            Dict mapping section names to extracted text
        """
        if not text or len(text) < 100:
            return {}

        sections = {}
        for section_name, patterns in self.TARGET_SECTIONS.items():
            extracted = self._extract_section(text, patterns, section_name)
            if extracted:
                sections[section_name] = self._clean_text(extracted)

        return sections

    def _extract_section(
        self, text: str, title_patterns: List[str], section_name: str
    ) -> Optional[str]:
        """
        Extract a section using "longest match" strategy.

        Finds ALL matches of section title patterns, extracts content
        for each match up to boundary, returns the longest result.
        This naturally skips TOC entries (which are short).
        """
        candidates = []

        for pattern in title_patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            for match in matches:
                # Skip cross-references
                before = text[max(0, match.start() - 20):match.start()]
                if "'" in before or "'" in before or "참고" in before:
                    continue

                start_pos = match.end()
                section_text = self._extract_until_boundary(
                    text, start_pos, section_name
                )

                if section_text and len(section_text.strip()) > 50:
                    candidates.append(section_text.strip())

        if not candidates:
            return None

        # Return the longest candidate (TOC entries are short, actual content is long)
        return max(candidates, key=len)

    def _extract_until_boundary(
        self, text: str, start_pos: int, section_name: str
    ) -> str:
        """Extract text from start_pos until the next major section boundary."""
        remaining = text[start_pos:]

        if section_name == 'business_overview':
            max_len = MAX_SECTION_LENGTH * 3
        else:
            max_len = MAX_SECTION_LENGTH

        # Find nearest major delimiter
        end_pos = max_len
        for delim_pattern in self.MAJOR_DELIMITERS:
            delim_match = re.search(delim_pattern, remaining[:max_len])
            if delim_match and delim_match.start() > 100:
                end_pos = min(end_pos, delim_match.start())

        # Sub-section boundaries for non-overview sections
        if section_name != 'business_overview':
            sub_section_re = r'\n\s*(?:\d+\.|[가-힣]\.)\s*(?:주요|경쟁|연구|위험|생산|매출|원재료)'
            sub_match = re.search(sub_section_re, remaining[200:max_len])
            if sub_match:
                candidate = 200 + sub_match.start()
                if candidate > 100:
                    end_pos = min(end_pos, candidate)

        return remaining[:end_pos]

    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        text = re.sub(r'&[a-zA-Z]+;', ' ', text)
        text = re.sub(r'&#\d+;', ' ', text)
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)

        if len(text) > MAX_SECTION_LENGTH:
            text = text[:MAX_SECTION_LENGTH]
            last_period = text.rfind('.')
            if last_period > MAX_SECTION_LENGTH * 0.8:
                text = text[:last_period + 1]

        return text.strip()

    def get_parse_quality(self, sections: Dict[str, str]) -> Dict:
        """Calculate parse quality metrics"""
        total_length = sum(len(v) for v in sections.values())
        return {
            'total_sections_found': len(sections),
            'total_sections_possible': len(self.TARGET_SECTIONS),
            'coverage': len(sections) / len(self.TARGET_SECTIONS),
            'total_text_length': total_length,
            'sections_found': list(sections.keys()),
            'sections_missing': [
                k for k in self.TARGET_SECTIONS if k not in sections
            ],
            'parsed_successfully': len(sections) >= 2,
        }
