import importlib.util
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scheduled_moat_sync.py"
SPEC = importlib.util.spec_from_file_location("scheduled_moat_sync", SCRIPT_PATH)
scheduled_moat_sync = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(scheduled_moat_sync)


class ScheduledMoatSyncTests(unittest.TestCase):
    def _temp_source(self) -> str:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        source = Path(temp_dir.name) / "source.xlsx"
        source.write_bytes(b"test-workbook")
        return str(source)

    def test_skip_when_no_change(self):
        source = self._temp_source()
        current = scheduled_moat_sync._fingerprint(Path(source))
        saved = {}

        def _save_state(_path, payload):
            saved.update(payload)

        with patch.object(
            scheduled_moat_sync,
            "enforce_monitoring",
            return_value=SimpleNamespace(blocked=False, incident_id=0, rule_code="", reasons=[]),
        ), patch.object(scheduled_moat_sync, "XLSX_PATH", source), patch.object(
            scheduled_moat_sync,
            "_load_state",
            return_value={"last_source": current},
        ), patch.object(scheduled_moat_sync, "_save_state", side_effect=_save_state), patch.object(
            scheduled_moat_sync, "_append_log"
        ), patch.object(scheduled_moat_sync, "extract") as mocked_extract:
            rc = scheduled_moat_sync.run(force=False, scheduled=True)

        self.assertEqual(rc, 0)
        self.assertEqual(saved.get("last_result"), "skipped_no_change")
        mocked_extract.assert_not_called()

    def test_sync_when_changed(self):
        source = self._temp_source()
        saved = {}

        def _save_state(_path, payload):
            saved.update(payload)

        with patch.object(
            scheduled_moat_sync,
            "enforce_monitoring",
            return_value=SimpleNamespace(blocked=False, incident_id=0, rule_code="", reasons=[]),
        ), patch.object(scheduled_moat_sync, "XLSX_PATH", source), patch.object(
            scheduled_moat_sync,
            "_load_state",
            return_value={},
        ), patch.object(scheduled_moat_sync, "_save_state", side_effect=_save_state), patch.object(
            scheduled_moat_sync, "_append_log"
        ), patch.object(
            scheduled_moat_sync,
            "extract",
            return_value={"sync": {"run_id": 9, "inserted": 1, "updated": 0, "unchanged": 0, "deactivated": 0}},
        ) as mocked_extract:
            rc = scheduled_moat_sync.run(force=False, scheduled=True)

        self.assertEqual(rc, 0)
        self.assertEqual(saved.get("last_result"), "synced")
        self.assertEqual(saved.get("last_sync", {}).get("run_id"), 9)
        mocked_extract.assert_called_once()

    def test_blocked_guard_returns_3(self):
        source = self._temp_source()
        with patch.object(
            scheduled_moat_sync,
            "enforce_monitoring",
            return_value=SimpleNamespace(blocked=True, incident_id=77, rule_code="rule", reasons=["x"]),
        ), patch.object(scheduled_moat_sync, "XLSX_PATH", source), patch.object(
            scheduled_moat_sync, "_append_log"
        ):
            rc = scheduled_moat_sync.run(force=False, scheduled=True)
        self.assertEqual(rc, 3)


if __name__ == "__main__":
    unittest.main()
