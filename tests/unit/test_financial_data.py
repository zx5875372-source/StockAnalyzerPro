import math
import unittest

from models.financial_data import safe_divide


class SafeDivideTest(unittest.TestCase):
    def test_returns_ratio_for_valid_numbers(self):
        self.assertEqual(safe_divide(10, 4), 2.5)

    def test_returns_none_for_invalid_values(self):
        self.assertIsNone(safe_divide(None, 4))
        self.assertIsNone(safe_divide(10, None))
        self.assertIsNone(safe_divide(10, 0))
        self.assertIsNone(safe_divide(10, -2))
        self.assertIsNone(safe_divide(math.nan, 2))


if __name__ == "__main__":
    unittest.main()
