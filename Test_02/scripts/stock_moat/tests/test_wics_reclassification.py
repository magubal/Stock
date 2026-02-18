import importlib.util
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "reclassify_bm_by_wics.py"
SPEC = importlib.util.spec_from_file_location("reclassify_bm_by_wics", SCRIPT_PATH)
wics_module = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(wics_module)


class WicsReclassificationTests(unittest.TestCase):
    def test_extract_wics_from_html(self):
        html = '<dt class="line-left">WICS : 화장품</dt>'
        self.assertEqual(wics_module.extract_wics_from_html(html), "화장품")

    def test_extract_wics_from_html_with_spaces(self):
        html = '<dt>WICS :   반도체  </dt>'
        self.assertEqual(wics_module.extract_wics_from_html(html), "반도체")

    def test_extract_wics_returns_none_when_missing(self):
        html = "<html><body>no sector here</body></html>"
        self.assertIsNone(wics_module.extract_wics_from_html(html))


if __name__ == "__main__":
    unittest.main()
