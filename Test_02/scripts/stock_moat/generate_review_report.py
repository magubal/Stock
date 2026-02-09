"""
Generate Review Report for Low-Confidence Stocks
Creates JSON file with AI suggestions for batch review
"""

import sys
import os
import json
from datetime import datetime

# Fix encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root
project_root = "F:/PSJ/AntigravityWorkPlace/Stock/Test_02"
sys.path.insert(0, f"{project_root}/.agent/skills/stock-moat/utils")
sys.path.insert(0, f"{project_root}/scripts/stock_moat")

from excel_io import ExcelIO
from dart_client import DARTClient
import pandas as pd


def analyze_industry_code(code: str, company: str) -> dict:
    """Enhanced industry code analysis"""
    patterns = {
        # 스포츠/레저
        '319': ('레저', '스포츠/레저', '기타 스포츠 및 레크리에이션 관련 서비스업'),
        '31991': ('레저', '스포츠용품', '운동 및 경기용품 소매업'),

        # 여행/관광
        '752': ('여행', '여행/관광', '여행사 및 여행보조 서비스업'),
        '75210': ('여행', '여행사', '여행사업'),

        # 유통/소매
        '471': ('유통', '종합소매', '종합소매업'),
        '47111': ('유통', '백화점', '백화점'),
        '464': ('유통', '도매', '가정용품 도매업'),
        '465': ('유통', '도매', '기계장비 도매업'),
        '46510': ('유통', 'IT도매', '컴퓨터 및 주변기기 도매업'),
        '46522': ('유통', '전자부품도매', '전자부품 도매업'),
        '468': ('유통', '도매', '기타 전문 도소매업'),
        '479': ('유통', '소매', '기타 소매업'),

        # 광고/마케팅
        '713': ('광고', '광고/마케팅', '광고업'),

        # 제조업
        '171': ('제조업', '제지/펄프', '펄프, 종이 및 판지 제조업'),
        '172': ('제조업', '종이제품', '골판지, 종이 상자 및 종이 용기 제조업'),
        '179': ('제조업', '종이제품', '기타 종이 및 판지 제품 제조업'),
        '182': ('제조업', '인쇄', '인쇄 및 인쇄관련 산업'),
        '201': ('화학', '기초화학', '기초 화학물질 제조업'),
        '202': ('화학', '비료/농약', '비료 및 질소화합물 제조업'),
        '204': ('화학', '기타화학', '기타 화학제품 제조업'),
        '20422': ('화학', '화장품', '화장품 제조업'),
        '20423': ('화학', '화장품', '비누 및 세제 제조업'),
        '211': ('바이오', '의약품', '의약품 제조업'),
        '222': ('제조업', '플라스틱', '플라스틱 제품 제조업'),
        '2229': ('제조업', '플라스틱', '기타 플라스틱 제품 제조업'),
        '22232': ('제조업', '플라스틱', '플라스틱 필름·시트·판·관·호스 및 피복제조업'),
        '231': ('제조업', '유리', '판유리 및 유리제품 제조업'),
        '23192': ('제조업', '유리', '기타 요업제품 제조업'),
        '259': ('제조업', '금속', '기타 금속가공제품 제조업'),
        '25923': ('제조업', '금속', '배관, 보일러 및 판금 제품 제조업'),
        '271': ('전자', '전기장비', '전동기, 발전기 및 전기 변환·공급·제어 장치 제조업'),
        '27199': ('전자', '전기장비', '기타 전기 장비 제조업'),
        '27212': ('전자', '축전지', '축전지 제조업'),
        '27216': ('전자', '전선', '전선 및 케이블 제조업'),
        '281': ('제조업', '기계', '일반 목적용 기계 제조업'),
        '28111': ('제조업', '엔진', '내연기관 제조업'),
        '291': ('제조업', '자동차', '자동차용 엔진 및 자동차 제조업'),
        '292': ('제조업', '자동차부품', '자동차 차체 및 트레일러 제조업'),
        '29221': ('제조업', '기계', '운반하역기계 제조업'),
        '29271': ('제조업', '전문기계', '특수 목적용 기계 제조업'),
        '29272': ('제조업', '전문기계', '기타 특수 목적용 기계 제조업'),
        '29229': ('제조업', '기계', '기타 일반 목적용 기계 제조업'),

        # 금융
        '641': ('은행', '은행', '은행 및 저축기관'),
        '649': ('금융', '기타금융', '기타 금융업'),
        '64992': ('금융', '지주회사', '기타 금융 지원 서비스업'),

        # IT/소프트웨어
        '424': ('IT', '인터넷', '자료처리, 호스팅, 포털 및 기타 인터넷 정보매개 서비스업'),
        '581': ('IT', '소프트웨어', '소프트웨어 개발 및 공급업'),
        '58221': ('IT', '게임', '게임 소프트웨어 개발 및 공급업'),
        '620': ('IT', 'IT서비스', '컴퓨터 프로그래밍, 시스템 통합 및 관리업'),
        '639': ('IT', '정보서비스', '기타 정보서비스업'),

        # 전문서비스
        '739': ('기타', '전문서비스', '기타 전문, 과학 및 기술 서비스업'),

        # 기타
        '141': ('제조업', '의류', '봉제의복 제조업'),
        '311': ('제조업', '가구', '가구 제조업'),
        '4610': ('유통', '종합상사', '상품 종합 도매업'),
        '463': ('유통', '식품도매', '음·식료품 및 담배 도매업'),
    }

    # Try exact match
    if code in patterns:
        sector, sub, desc = patterns[code]
        return {
            'sector': sector,
            'sub': sub,
            'confidence': 0.9,
            'reasoning': f'{desc} (KSIC {code})'
        }

    # Try prefix match (3 digits)
    for pattern_code, (sector, sub, desc) in patterns.items():
        if code.startswith(pattern_code[:3]):
            return {
                'sector': sector,
                'sub': sub,
                'confidence': 0.7,
                'reasoning': f'{desc} (KSIC {code}, 추정)'
            }

    # Default
    return {
        'sector': '기타',
        'sub': '미분류',
        'confidence': 0.3,
        'reasoning': f'KSIC {code} - 미등록 업종코드'
    }


def generate_review_report():
    """Generate review report with AI suggestions"""

    excel_path = f"{project_root}/data/ask/stock_core_master_v2_korean_taxonomy_2026-01-30_요청용_011.xlsx"
    excel_io = ExcelIO(excel_path)
    dart = DARTClient("7f7abfddcd974b4d07de58eb46b602ca22d0e45d")

    # Load low-confidence stocks
    df = excel_io.load_stock_data()
    low_conf = df[(df['해자강도'].notna()) & (df['core_sector_top'] == '기타')].copy()

    print(f"\n{'='*60}")
    print(f"📋 저신뢰도 종목 분석 보고서 생성")
    print(f"{'='*60}\n")
    print(f"총 {len(low_conf)}개 종목 분석 중...\n")

    review_data = {
        'generated_at': datetime.now().isoformat(),
        'total_stocks': len(low_conf),
        'stocks': []
    }

    for idx, (row_idx, stock) in enumerate(low_conf.iterrows(), start=1):
        ticker = stock['ticker']
        name = stock['name']

        print(f"[{idx}/{len(low_conf)}] {name} ({ticker})")

        # Get DART data
        dart_result = dart.analyze_stock(ticker)

        if dart_result:
            industry_code = dart_result.get('industry_code', '')
            suggestion = analyze_industry_code(industry_code, name)

            stock_data = {
                'ticker': ticker,
                'name': name,
                'current_sector': stock.get('core_sector_top', '기타'),
                'current_sub': stock.get('core_sector_sub', '미분류'),
                'dart_code': industry_code,
                'company_name': dart_result.get('corp_name', name),
                'homepage': dart_result.get('homepage', ''),
                'suggested_sector': suggestion['sector'],
                'suggested_sub': suggestion['sub'],
                'confidence': suggestion['confidence'],
                'reasoning': suggestion['reasoning'],
                'action': 'approve'  # User can change to: approve, reject, custom
            }

            review_data['stocks'].append(stock_data)
        else:
            print(f"  ⚠️  DART 데이터 없음")

    # Save to JSON
    output_path = f"{project_root}/data/stock_moat/low_confidence_review.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(review_data, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"✅ 분석 보고서 생성 완료!")
    print(f"{'='*60}")
    print(f"파일: {output_path}")
    print(f"\n검토 방법:")
    print(f"1. JSON 파일을 열어 suggested_sector, suggested_sub 확인")
    print(f"2. action 필드를 수정:")
    print(f"   - 'approve': AI 제안 수용")
    print(f"   - 'reject': 현재 유지")
    print(f"   - 'custom': custom_sector, custom_sub 필드 추가")
    print(f"3. apply_review.py 실행하여 Excel 업데이트")
    print(f"{'='*60}\n")

    return review_data


if __name__ == "__main__":
    generate_review_report()
