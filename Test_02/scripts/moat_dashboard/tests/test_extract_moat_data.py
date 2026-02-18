import importlib.util
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "extract_moat_data.py"
SPEC = importlib.util.spec_from_file_location("extract_moat_data", SCRIPT_PATH)
extract_moat_data = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(extract_moat_data)


class ExtractMoatDataSectorKeyTests(unittest.TestCase):
    def test_manufacturing_uses_sub_sector(self):
        self.assertEqual(
            extract_moat_data.get_sector_key_from_bm("제조업/전문기계"),
            "전문기계",
        )

    def test_non_manufacturing_keeps_top_sector(self):
        self.assertEqual(
            extract_moat_data.get_sector_key_from_bm("반도체/전자부품"),
            "반도체",
        )

    def test_empty_bm_returns_empty_string(self):
        self.assertEqual(extract_moat_data.get_sector_key_from_bm(""), "")


class ExtractMoatDataBigoParserTests(unittest.TestCase):
    def test_parse_bigo_three_line_format(self):
        bigo = (
            "mgb.해자.4/5\n"
            "해자 5/5 | 증거18건(q30) | 성장+1 | 성장 우수\n"
            "투자가치 4/5 | TTM매출5.8조원 | 영업이익6,187억원(10.7%) | "
            "op_multiple 35.9x | 시총22.2조원 | 현재가2,384,000원 | [oracle/high 20253Q]"
        )
        parsed = extract_moat_data.parse_bigo(bigo)
        self.assertEqual(parsed.get("evidence_count"), 18)
        self.assertEqual(parsed.get("evidence_quality"), 30.0)
        self.assertEqual(parsed.get("growth_adj"), 1)
        self.assertEqual(parsed.get("ttm_revenue"), "5.8조")
        self.assertEqual(parsed.get("op_multiple"), 35.9)
        self.assertEqual(parsed.get("current_price"), 2384000)
        self.assertEqual(parsed.get("data_source"), "oracle/high 20253Q")
        self.assertIn("mgb.해자.4/5", parsed.get("markers", []))

    def test_parse_bigo_handles_many_lines(self):
        bigo = "\n".join(
            [
                "mgb.해자.3/5",
                "요약라인 A",
                "요약라인 B",
                "해자 3/5 | 증거9건(q16) | 성장-1",
                "추가참고1",
                "추가참고2",
                "투자가치 2/5 | TTM매출8,900억원 | 영업이익420억원(4.7%)",
                "op_multiple 8.3x | 시총1.1조원 | 현재가12,340원 | [oracle/high 20243Q]",
                "꼬리라인1",
                "꼬리라인2",
            ]
        )
        parsed = extract_moat_data.parse_bigo(bigo)
        self.assertEqual(parsed.get("evidence_count"), 9)
        self.assertEqual(parsed.get("growth_adj"), -1)
        self.assertEqual(parsed.get("ttm_revenue"), "8,900억")
        self.assertEqual(parsed.get("op_margin"), "4.7%")
        self.assertEqual(parsed.get("market_cap"), "1.1조")
        self.assertEqual(parsed.get("current_price"), 12340)
        self.assertEqual(len(parsed.get("raw_lines", [])), 10)


if __name__ == "__main__":
    unittest.main()
