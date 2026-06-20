import unittest

from models.financial_data import FinancialData, FinancialPeriod
from modules.growth import calculate_growth


class GrowthTest(unittest.TestCase):
    def test_scores_growth_items(self):
        data = FinancialData(
            symbol="TEST",
            current=FinancialPeriod(revenue=1200, eps=12, free_cashflow=80),
            previous=FinancialPeriod(revenue=1000, eps=10, free_cashflow=40),
        )

        result = calculate_growth(data)

        self.assertEqual(result["score"], 13)
        self.assertEqual([item["score"] for item in result["items"]], [5, 5, 3])
        self.assertEqual(result["diagnostics"], [])

    def test_missing_data_records_diagnostics(self):
        result = calculate_growth(FinancialData(symbol="EMPTY"))

        self.assertEqual(result["score"], 0)
        self.assertEqual(len(result["diagnostics"]), 3)


if __name__ == "__main__":
    unittest.main()
