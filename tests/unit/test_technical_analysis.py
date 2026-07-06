import unittest

import pandas as pd

from technical.indicators import macd, moving_average, rsi, volume_ratio
from technical.technical_engine import TechnicalAnalysis


class TechnicalAnalysisTests(unittest.TestCase):
    def test_moving_average_calculation(self):
        values = pd.Series(range(1, 31))

        self.assertEqual(moving_average(values, 20), 20.5)

    def test_rsi_calculation(self):
        values = pd.Series(range(1, 31))

        self.assertEqual(rsi(values, 14), 100.0)

    def test_macd_calculation(self):
        values = pd.Series(range(1, 80))

        result = macd(values)

        self.assertIsNotNone(result["macd"])
        self.assertIsNotNone(result["signal"])
        self.assertIsNotNone(result["histogram"])

    def test_volume_ratio_calculation(self):
        volumes = pd.Series([100] * 19 + [200])

        self.assertEqual(volume_ratio(volumes), 1.9)

    def test_trend_score_and_grade(self):
        score = TechnicalAnalysis._trend_score(
            current_price=150,
            ma20=140,
            ma60=130,
            ma120=120,
            ma240=110,
            rsi14=55,
            macd_value=2,
            macd_signal=1,
            volume_ratio=1.2,
        )

        self.assertEqual(score, 100)
        self.assertEqual(TechnicalAnalysis._technical_grade(score), "S")

    def test_analyze_uses_history_loader(self):
        analyzer = TechnicalAnalysis(history_loader=lambda symbol, period: sample_history(), period="1y")

        result = analyzer.analyze("2330")

        self.assertGreaterEqual(result.trend_score, 0)
        self.assertIn(result.technical_grade, {"S", "A", "B", "C", "D"})
        self.assertIsNotNone(result.ma20)
        self.assertIsNotNone(result.ma60)
        self.assertIsNotNone(result.ma120)
        self.assertIsNotNone(result.ma240)
        self.assertIsNotNone(result.rsi14)
        self.assertIsNotNone(result.macd)
        self.assertIsNotNone(result.volume_ratio)
        self.assertIn("technical_source: Yahoo Finance", result.diagnostics)
        self.assertIn("technical_period: 1y", result.diagnostics)

    def test_missing_data_does_not_crash(self):
        analyzer = TechnicalAnalysis(history_loader=lambda symbol, period: pd.DataFrame(), period="1y")

        result = analyzer.analyze("2330")

        self.assertEqual(result.trend_score, 0)
        self.assertEqual(result.technical_grade, "D")
        self.assertIn("technical_missing_fields: history", result.diagnostics)


def sample_history():
    closes = list(range(100, 360))
    volumes = [1000] * 240 + [2000] * 20
    return pd.DataFrame({"Close": closes, "Volume": volumes})


if __name__ == "__main__":
    unittest.main()
