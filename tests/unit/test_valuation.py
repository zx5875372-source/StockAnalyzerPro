import unittest

from models.financial_data import FinancialData, FinancialPeriod
from modules.valuation import calculate_valuation


class ValuationTest(unittest.TestCase):
    def test_calculates_fair_prices_and_target(self):
        data = FinancialData(
            symbol="TEST",
            price=100,
            current=FinancialPeriod(eps=5, book_value_per_share=20),
        )

        result = calculate_valuation(data)

        self.assertEqual(result["pe_fair_price"], 100)
        self.assertEqual(result["pb_fair_price"], 60)
        self.assertEqual(result["fair_price"], 80)
        self.assertEqual(result["first_target_price"], 92)
        self.assertEqual(result["upside_percent"], -8)

    def test_missing_inputs_do_not_crash(self):
        result = calculate_valuation(FinancialData(symbol="EMPTY"))

        self.assertIsNone(result["fair_price"])
        self.assertGreaterEqual(len(result["diagnostics"]), 2)


if __name__ == "__main__":
    unittest.main()
