import unittest

from ranking import IndustryRankingEngine


class IndustryRankingEngineTests(unittest.TestCase):
    def test_industry_ranking_sort(self):
        result = IndustryRankingEngine(sample_rows()).rank("2330.TW")

        self.assertEqual(result.industry_name, "半導體")
        self.assertEqual(result.industry_size, 4)
        self.assertEqual(result.sap_rank, 2)
        self.assertEqual(result.trend_rank, 2)
        self.assertEqual(result.total_rank, 2)

    def test_percentile_calculation(self):
        result = IndustryRankingEngine(sample_rows()).rank("2330.TW")

        self.assertEqual(result.sap_percentile, 50.0)
        self.assertEqual(result.total_percentile, 50.0)

    def test_top_percent_label(self):
        result = IndustryRankingEngine(sample_rows()).rank("3008.TW")

        self.assertEqual(result.top_percent, "前 25%")
        self.assertIn("前 25%", result.summary_text)

    def test_industry_size(self):
        result = IndustryRankingEngine(sample_rows()).rank("2454.TW")

        self.assertEqual(result.industry_size, 4)

    def test_unknown_industry(self):
        result = IndustryRankingEngine(sample_rows()).rank("9999.TW")

        self.assertEqual(result.industry_name, "未知產業")
        self.assertEqual(result.top_percent, "資料不足")
        self.assertEqual(result.summary_text, "產業資料不足，暫無法排名")

    def test_empty_input(self):
        result = IndustryRankingEngine([]).rank("2330.TW")

        self.assertEqual(result.industry_size, 0)
        self.assertIsNone(result.sap_rank)
        self.assertEqual(result.top_percent, "資料不足")

    def test_annotate_rows_adds_watchlist_ranking_fields(self):
        rows = IndustryRankingEngine(sample_rows()).annotate_rows(sample_rows())
        tsmc = next(row for row in rows if row["symbol"] == "2330.TW")

        self.assertEqual(tsmc["industry_rank_label"], "前 50%")
        self.assertEqual(tsmc["industry_size"], 4)
        self.assertEqual(tsmc["sap_rank"], 2)


def sample_rows():
    return [
        {
            "symbol": "3008.TW",
            "status": "success",
            "industry": "半導體",
            "sap_score": 96,
            "trend_score": 92,
            "total_score": 94.4,
        },
        {
            "symbol": "2330.TW",
            "status": "success",
            "industry": "半導體",
            "sap_score": 90,
            "trend_score": 80,
            "total_score": 86,
        },
        {
            "symbol": "2454.TW",
            "status": "success",
            "industry": "半導體",
            "sap_score": 70,
            "trend_score": 75,
            "total_score": 72,
        },
        {
            "symbol": "2303.TW",
            "status": "success",
            "industry": "半導體",
            "sap_score": 60,
            "trend_score": 55,
            "total_score": 58,
        },
        {
            "symbol": "9999.TW",
            "status": "success",
            "industry": "未知產業",
            "sap_score": 80,
            "trend_score": 80,
            "total_score": 80,
        },
    ]


if __name__ == "__main__":
    unittest.main()
