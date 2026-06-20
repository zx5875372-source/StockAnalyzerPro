import unittest

from models.financial_data import FinancialData, FinancialPeriod
from modules.growth import calculate_growth
from modules.piotroski import calculate_piotroski
from modules.scoring import calculate_sap_score
from modules.valuation import calculate_valuation


def sample_data() -> FinancialData:
    return FinancialData(
        symbol="TEST",
        pe=10,
        pb=1.5,
        price=100,
        current=FinancialPeriod(
            net_income=120,
            total_assets=1000,
            total_equity=500,
            total_debt=100,
            long_term_debt=100,
            current_assets=300,
            current_liabilities=100,
            revenue=1200,
            gross_profit=600,
            operating_cashflow=150,
            free_cashflow=80,
            shares_outstanding=10,
            eps=12,
            book_value_per_share=50,
        ),
        previous=FinancialPeriod(
            net_income=80,
            total_assets=900,
            long_term_debt=120,
            current_assets=200,
            current_liabilities=100,
            revenue=1000,
            gross_profit=450,
            free_cashflow=40,
            shares_outstanding=11,
            eps=8,
        ),
    )


class SapScoreTest(unittest.TestCase):
    def test_calculates_total_score_and_categories(self):
        data = sample_data()
        piotroski = calculate_piotroski(data)
        valuation = calculate_valuation(data)
        growth = calculate_growth(data)

        result = calculate_sap_score(data, piotroski, valuation, growth)

        self.assertEqual(result["total_score"], 100)
        self.assertEqual(result["grade"], "S級")
        self.assertEqual(result["categories"]["piotroski"]["score"], 27)
        self.assertEqual(result["categories"]["growth"]["score"], 13)

    def test_empty_data_scores_zero(self):
        data = FinancialData(symbol="EMPTY")
        result = calculate_sap_score(data, calculate_piotroski(data), calculate_valuation(data), calculate_growth(data))

        self.assertEqual(result["total_score"], 0)
        self.assertEqual(result["grade"], "D級")


if __name__ == "__main__":
    unittest.main()
