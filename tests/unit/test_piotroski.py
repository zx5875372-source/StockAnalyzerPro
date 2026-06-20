import unittest

from models.financial_data import FinancialData, FinancialPeriod
from modules.piotroski import calculate_piotroski


def sample_financial_data() -> FinancialData:
    return FinancialData(
        symbol="TEST",
        current=FinancialPeriod(
            net_income=120,
            total_assets=1000,
            total_equity=500,
            long_term_debt=100,
            current_assets=300,
            current_liabilities=100,
            revenue=1200,
            gross_profit=600,
            operating_cashflow=150,
            shares_outstanding=10,
        ),
        previous=FinancialPeriod(
            net_income=80,
            total_assets=900,
            long_term_debt=120,
            current_assets=200,
            current_liabilities=100,
            revenue=1000,
            gross_profit=450,
            shares_outstanding=11,
        ),
    )


class PiotroskiTest(unittest.TestCase):
    def test_full_score_with_strong_financials(self):
        result = calculate_piotroski(sample_financial_data())

        self.assertEqual(result["score"], 9)
        self.assertEqual(result["available"], 9)
        self.assertEqual(result["total"], 9)

    def test_missing_data_does_not_crash(self):
        result = calculate_piotroski(FinancialData(symbol="EMPTY"))

        self.assertEqual(result["score"], 0)
        self.assertEqual(result["available"], 0)
        self.assertTrue(all(item["passed"] is None for item in result["items"]))


if __name__ == "__main__":
    unittest.main()
