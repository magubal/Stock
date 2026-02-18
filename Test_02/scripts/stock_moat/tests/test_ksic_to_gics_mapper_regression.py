import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT / ".agent/skills/stock-moat/utils"))

from ksic_to_gics_mapper import KSICtoGICSMapper  # noqa: E402


class KSICtoGICSMapperRegressionTests(unittest.TestCase):
    def setUp(self):
        self.mapper = KSICtoGICSMapper()

    def test_cosmetics_code_is_not_grouped_into_chemical(self):
        result = self.mapper.map_to_gics("20423", "한국콜마")
        self.assertEqual(result["korean_sector_top"], "화장품")
        self.assertEqual(result["korean_sector_sub"], "생활용품")

    def test_pharma_code_212_is_classified_as_bio(self):
        result = self.mapper.map_to_gics("212", "에스티팜")
        self.assertEqual(result["korean_sector_top"], "바이오")
        self.assertEqual(result["korean_sector_sub"], "의약품")

    def test_electronic_component_code_2629_is_not_grouped_into_chemical(self):
        result = self.mapper.map_to_gics("2629", "에스앤에스텍")
        self.assertEqual(result["korean_sector_top"], "반도체")
        self.assertEqual(result["korean_sector_sub"], "전자부품")

    def test_computer_peripheral_code_26329_is_not_grouped_into_chemical(self):
        result = self.mapper.map_to_gics("26329", "아이디피")
        self.assertEqual(result["korean_sector_top"], "전자")
        self.assertEqual(result["korean_sector_sub"], "IT하드웨어")

    def test_display_equipment_code_265_is_not_grouped_into_chemical(self):
        result = self.mapper.map_to_gics("265", "토비스")
        self.assertEqual(result["korean_sector_top"], "전자")
        self.assertEqual(result["korean_sector_sub"], "디스플레이/광학장비")


if __name__ == "__main__":
    unittest.main()
