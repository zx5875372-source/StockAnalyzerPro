import unittest

from backtest.integrity import calculate_credibility


class BacktestIntegrityTests(unittest.TestCase):
    def test_not_point_in_time_warning_returns_c(self):
        result = calculate_credibility(
            look_ahead_safe=True,
            snapshot_warning_counts={"not_point_in_time": 12},
            selected_stock_count=3,
        )

        self.assertEqual(result["credibility_grade"], "C")
        self.assertIn("not_point_in_time", result["credibility_reason"])

    def test_too_few_selected_stocks_returns_d(self):
        result = calculate_credibility(
            look_ahead_safe=True,
            snapshot_warning_counts={},
            selected_stock_count=1,
        )

        self.assertEqual(result["credibility_grade"], "D")
        self.assertIn("入選股票數", result["credibility_reason"])

    def test_no_warning_and_look_ahead_safe_returns_a(self):
        result = calculate_credibility(
            look_ahead_safe=True,
            snapshot_warning_counts={},
            selected_stock_count=3,
        )

        self.assertEqual(result["credibility_grade"], "A")
        self.assertEqual(result["credibility_notice"], "")


if __name__ == "__main__":
    unittest.main()
