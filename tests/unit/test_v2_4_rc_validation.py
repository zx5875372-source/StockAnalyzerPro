import json
import tempfile
import unittest
from pathlib import Path

from v2_4_rc_validation import (
    RCValidationSummary,
    build_validation_report,
    load_qualification_summary,
    write_validation_report,
)


class V24RCValidationTests(unittest.TestCase):
    def test_validation_script_contains_required_flow(self):
        script = Path("scripts/v2_4_rc_validation.ps1").read_text(encoding="utf-8")

        self.assertIn("v2_4_rc_test.db", script)
        self.assertIn("historical_import.py", script)
        self.assertIn("tests/sample_data/historical/financial_snapshots_valid.csv", script)
        self.assertIn("historical_generate_sap.py", script)
        self.assertIn("backtest.py", script)
        self.assertIn("--snapshot-source", script)
        self.assertIn("repository", script)
        self.assertIn("strategy_compare.py", script)
        self.assertIn("research_report.py", script)
        self.assertIn("reports/v2_4_rc_validation.md", script)
        self.assertIn("reports/v2_4_rc_validation.log", script)
        self.assertIn("--log-path", script)

    def test_summary_report_can_be_generated(self):
        summary = RCValidationSummary(
            import_status="pass",
            generator_status="pass",
            backtest_status="pass",
            strategy_comparison_status="pass",
            research_report_status="pass",
            qualification=sample_qualification(),
        )

        content = build_validation_report(summary)

        self.assertIn("# v2.4 Historical Backtesting RC Validation", content)
        self.assertIn("| Import | pass |", content)
        self.assertIn("| Backtest | pass |", content)
        self.assertIn("## Qualification Summary", content)
        self.assertIn("| Qualification Grade | C |", content)
        self.assertIn("## Known Limitations", content)

    def test_write_summary_report(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "v2_4_rc_validation.md"
            summary = RCValidationSummary(
                import_status="pass",
                generator_status="pass",
                backtest_status="pass",
                strategy_comparison_status="pass",
                research_report_status="pass",
                qualification=sample_qualification(is_formal_point_in_time=True),
                log_path="reports/v2_4_rc_validation.log",
            )

            write_validation_report(summary, output_path)
            content = output_path.read_text(encoding="utf-8")

        self.assertIn("| Is Formal Point-in-Time | true |", content)
        self.assertIn("- RC validation status: formal", content)
        self.assertIn("Full command output: `reports/v2_4_rc_validation.log`", content)

    def test_load_qualification_summary_reads_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "backtest_qualification.json"
            path.write_text(json.dumps(sample_qualification()), encoding="utf-8")

            result = load_qualification_summary(path)

        self.assertEqual(result["snapshot_source"], "repository")
        self.assertEqual(result["snapshot_db"], "v2_4_rc_test.db")
        self.assertEqual(result["qualification_grade"], "C")
        self.assertFalse(result["is_formal_point_in_time"])

    def test_missing_qualification_summary_has_clear_defaults(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = load_qualification_summary(Path(temp_dir) / "missing.json")

        self.assertEqual(result["snapshot_source"], "unknown")
        self.assertEqual(result["qualification_grade"], "unknown")
        self.assertFalse(result["is_formal_point_in_time"])
        self.assertIn("qualification export not found", result["qualification_reason"])


def sample_qualification(is_formal_point_in_time=False):
    return {
        "snapshot_source": "repository",
        "snapshot_db": "v2_4_rc_test.db",
        "qualification_grade": "A" if is_formal_point_in_time else "C",
        "qualification_reason": (
            "All repository SAP snapshots are point-in-time qualified."
            if is_formal_point_in_time
            else "Repository contains research-only snapshots."
        ),
        "research_only_count": 0 if is_formal_point_in_time else 2,
        "point_in_time_count": 2 if is_formal_point_in_time else 0,
        "missing_published_date_count": 0,
        "not_point_in_time_count": 0 if is_formal_point_in_time else 2,
        "is_formal_point_in_time": is_formal_point_in_time,
        "generated_at": "2026-06-23T00:00:00+00:00",
    }


if __name__ == "__main__":
    unittest.main()
