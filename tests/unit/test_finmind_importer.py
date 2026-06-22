import unittest

from importers import FinMindImporter
from importers.registry import create_default_registry


class FinMindImporterTests(unittest.TestCase):
    def test_default_registry_has_finmind(self):
        registry = create_default_registry()

        self.assertIn("finmind", registry.list())
        self.assertIsInstance(registry.get("finmind"), FinMindImporter)

    def test_importer_metadata(self):
        importer = FinMindImporter()

        self.assertEqual(importer.name, "finmind")
        self.assertEqual(importer.version, "v0-architecture")

    def test_supports_planned_snapshot_types(self):
        importer = FinMindImporter()

        self.assertTrue(importer.supports("financial"))
        self.assertTrue(importer.supports("financial_statement"))
        self.assertTrue(importer.supports("sap"))
        self.assertTrue(importer.supports("sap_score"))
        self.assertFalse(importer.supports("price_history"))
        self.assertFalse(importer.supports("unknown"))

    def test_import_methods_are_not_implemented_yet(self):
        importer = FinMindImporter()

        with self.assertRaisesRegex(NotImplementedError, "architecture-only"):
            importer.import_snapshot("unused", snapshot_type="financial")

        with self.assertRaisesRegex(NotImplementedError, "architecture-only"):
            importer.import_financial_statements("unused")


if __name__ == "__main__":
    unittest.main()
