import csv
import tempfile
import unittest
from pathlib import Path

from research_report import ResearchReportError, read_strategy_comparison, write_research_report


class ResearchReportTests(unittest.TestCase):
    def test_reads_strategy_comparison_csv(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "strategy_comparison.csv"
            write_sample_csv(csv_path)

            rows = read_strategy_comparison(csv_path)

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["strategy"], "SAP Score Strategy MVP")
        self.assertEqual(rows[0]["excess_return"], 0.4712)
        self.assertEqual(rows[1]["credibility_grade"], "C")

    def test_writes_markdown_report(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "strategy_comparison.csv"
            output_path = Path(temp_dir) / "research_report.md"
            write_sample_csv(csv_path)

            rows = read_strategy_comparison(csv_path)
            write_research_report(rows, output_path)
            content = output_path.read_text(encoding="utf-8")

        self.assertIn("## Executive Summary", content)
        self.assertIn("Best Strategy: SAP Score Strategy MVP", content)
        self.assertIn("## Strategy Ranking", content)
        self.assertIn("## Risk Comparison", content)
        self.assertIn("## Credibility Analysis", content)
        self.assertIn("目前結果僅供研究，不可視為正式投資績效。", content)

    def test_empty_csv_has_clear_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "empty.csv"
            with csv_path.open("w", encoding="utf-8", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
                writer.writeheader()

            with self.assertRaisesRegex(ResearchReportError, "empty"):
                read_strategy_comparison(csv_path)


FIELDNAMES = [
    "strategy",
    "total_return",
    "cagr",
    "max_drawdown",
    "win_rate",
    "benchmark_total_return",
    "excess_return",
    "credibility_grade",
    "selected_stock_count",
    "skipped_stock_count",
    "strategy_vs_benchmark",
]


def write_sample_csv(path: Path) -> None:
    rows = [
        {
            "strategy": "SAP Score Strategy MVP",
            "total_return": "2.0524",
            "cagr": "0.4506",
            "max_drawdown": "-0.1963",
            "win_rate": "0.6111",
            "benchmark_total_return": "1.5812",
            "excess_return": "0.4712",
            "credibility_grade": "D",
            "selected_stock_count": "1",
            "skipped_stock_count": "29",
            "strategy_vs_benchmark": "outperform",
        },
        {
            "strategy": "Piotroski Strategy",
            "total_return": "0.7128",
            "cagr": "0.1965",
            "max_drawdown": "-0.3276",
            "win_rate": "0.5",
            "benchmark_total_return": "1.5812",
            "excess_return": "-0.8684",
            "credibility_grade": "C",
            "selected_stock_count": "5",
            "skipped_stock_count": "25",
            "strategy_vs_benchmark": "underperform",
        },
    ]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    unittest.main()
