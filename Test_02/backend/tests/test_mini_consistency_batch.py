import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "demo" / "mini_consistency_batch.py"


class MiniConsistencyBatchTests(unittest.TestCase):
    def test_demo_batch_processes_and_blocks_expected_rows(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            input_csv = tmp / "input.csv"
            output_csv = tmp / "output.csv"

            input_csv.write_text(
                "\n".join(
                    [
                        "row_id,name,text,scenario",
                        "1,Alpha,Valid row,ok",
                        "2,Beta,Bad req refs,missing_requirement_refs",
                        "3,Gamma,Bad plan refs,missing_plan_refs",
                        "4,Delta,Bad req id,missing_req_id",
                        "5,Epsilon,Disabled consistency,consistency_off",
                        "6,Zeta,Valid row2,ok",
                    ]
                ),
                encoding="utf-8",
            )

            proc = subprocess.run(
                [sys.executable, str(SCRIPT), "--input", str(input_csv), "--output", str(output_csv)],
                cwd=str(ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="ignore",
            )
            self.assertEqual(proc.returncode, 0, msg=f"stdout={proc.stdout}\nstderr={proc.stderr}")
            self.assertTrue(output_csv.exists())

            with output_csv.open("r", encoding="utf-8", newline="") as rf:
                rows = list(csv.DictReader(rf))
            self.assertEqual(len(rows), 6)
            ok_rows = [r for r in rows if r["status"] == "OK"]
            blocked_rows = [r for r in rows if r["status"] == "BLOCKED"]

            self.assertEqual(len(ok_rows), 2)
            self.assertEqual(len(blocked_rows), 4)
            self.assertTrue(all(int(r["score"]) > 0 for r in ok_rows))
            self.assertTrue(all(r["incident_id"] for r in blocked_rows))
            self.assertTrue(all(r["rule_code"] for r in blocked_rows))


if __name__ == "__main__":
    unittest.main()
