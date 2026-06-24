import io
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import app


class AppCLIv3Tests(unittest.TestCase):
    def test_main_menu_is_v3_chinese_number_menu(self):
        with patch("sys.stdout", new_callable=io.StringIO) as output:
            app.show_menu()

        menu = output.getvalue()
        self.assertIn("StockAnalyzerPro v3.0", menu)
        self.assertIn("【股票分析】", menu)
        self.assertIn("2. 分析自選股", menu)
        self.assertIn("4. 更新 FinMind 財報", menu)
        self.assertIn("8. 產生研究報告", menu)

    def test_select_common_stock_returns_stock_by_number(self):
        with patch("builtins.input", return_value="1"), patch("sys.stdout", new_callable=io.StringIO):
            symbol, name = app.select_common_stock()

        self.assertEqual(symbol, "2330")
        self.assertEqual(name, "台積電")

    def test_single_stock_result_can_open_report_and_return_to_menu(self):
        result = {"sap_score": 95, "grade": "A"}
        report_path = Path("reports/2330.md")

        with (
            patch("builtins.input", side_effect=["1", "0"]),
            patch("app.open_file") as open_file,
            patch("sys.stdout", new_callable=io.StringIO),
        ):
            action = app.show_single_stock_result(result, report_path, "2330", "台積電")

        open_file.assert_called_once_with(report_path)
        self.assertEqual(action, "menu")

    def test_scan_result_menu_opens_report_ranking_and_csv(self):
        rows = [
            {"symbol": "2330", "status": "success", "sap_score": 95},
            {"symbol": "2454", "status": "success", "sap_score": 91},
            {"symbol": "6290", "status": "success", "sap_score": 88},
        ]

        with (
            patch("builtins.input", side_effect=["1", "2", "3", "0"]),
            patch("app.open_file") as open_file,
            patch("sys.stdout", new_callable=io.StringIO),
        ):
            app.show_scan_result("自選股分析", rows, "watchlist")

        opened_paths = [call.args[0] for call in open_file.call_args_list]
        self.assertEqual(opened_paths, [app.WATCHLIST_REPORT_PATH, app.TOP10_PATH, app.OUTPUT_PATH])

    def test_run_cli_waits_before_returning_to_main_menu(self):
        completed = Mock(returncode=0)
        with (
            patch("app.subprocess.run", return_value=completed) as run,
            patch("builtins.input", side_effect=["0", ""]),
            patch("sys.stdout", new_callable=io.StringIO),
        ):
            app.run_cli("research_report.py", report_to_open=Path("reports/research_report.md"))

        run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
