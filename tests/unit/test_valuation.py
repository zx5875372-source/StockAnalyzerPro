import unittest

from models.financial_data import FinancialData, FinancialPeriod
from modules.valuation import calculate_valuation
from valuation.valuation_profiles import get_valuation_profile


class ValuationTest(unittest.TestCase):
    def test_calculates_fair_prices_and_target(self):
        data = FinancialData(
            symbol="TEST",
            industry="Communication Equipment",
            price=100,
            current=FinancialPeriod(eps=5, book_value_per_share=20),
        )

        result = calculate_valuation(data)

        self.assertEqual(result["pe_fair_price"], 100)
        self.assertEqual(result["pb_fair_price"], 50)
        self.assertEqual(result["fair_price"], 75)
        self.assertEqual(result["first_target_price"], 86.25)
        self.assertEqual(result["upside_percent"], -13.75)

    def test_valuation_profile_lookup(self):
        profile, mapping = get_valuation_profile("Communication Equipment")

        self.assertEqual(profile.name, "通訊設備")
        self.assertEqual(profile.target_pe, 20)
        self.assertEqual(profile.target_pb, 2.5)
        self.assertEqual(mapping["profile"], "通訊設備")

    def test_industry_mapping_supports_chinese_label(self):
        profile, mapping = get_valuation_profile("通訊設備")

        self.assertEqual(profile.name, "通訊設備")
        self.assertEqual(mapping["industry"], "通訊設備")

    def test_unknown_industry_uses_fallback_profile(self):
        profile, mapping = get_valuation_profile("Unknown Industry")

        self.assertEqual(profile.name, "傳產")
        self.assertTrue(mapping["fallback_used"])

    def test_dynamic_pe_and_pb_are_used(self):
        data = FinancialData(
            symbol="6285.TW",
            industry="Communication Equipment",
            current=FinancialPeriod(eps=10, book_value_per_share=40),
        )

        result = calculate_valuation(data)

        self.assertEqual(result["reasonable_pe"], 20)
        self.assertEqual(result["reasonable_pb"], 2.5)
        self.assertEqual(result["pe_fair_price"], 200)
        self.assertEqual(result["pb_fair_price"], 100)
        self.assertEqual(result["valuation_profile"], "通訊設備")
        self.assertIn("valuation_profile: 通訊設備", result["diagnostics"])
        self.assertIn("valuation_source: industry_profile_v2", result["diagnostics"])
        self.assertIn("industry_mapping:", "\n".join(result["diagnostics"]))

    def test_missing_inputs_do_not_crash(self):
        result = calculate_valuation(FinancialData(symbol="EMPTY"))

        self.assertIsNone(result["fair_price"])
        self.assertGreaterEqual(len(result["diagnostics"]), 2)


if __name__ == "__main__":
    unittest.main()
