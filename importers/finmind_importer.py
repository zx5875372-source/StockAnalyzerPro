from __future__ import annotations

from pathlib import Path

from historical.repository import HistoricalSnapshotRepository
from historical.validation import HistoricalValidator
from importers.base_importer import BaseImporter, ImporterError
from importers.finmind import FinMindAPIError, FinMindClient, FinMindMappingError, map_financial_statement_row
from importers.import_result import ImportResult


class FinMindImporter(BaseImporter):
    name = "finmind"
    version = "v1-integration"

    def __init__(
        self,
        client: FinMindClient | None = None,
        validator: HistoricalValidator | None = None,
    ):
        self.client = client or FinMindClient()
        self.validator = validator

    def supports(self, snapshot_type: str) -> bool:
        normalized = snapshot_type.strip().lower().replace("-", "_")
        return normalized in {
            "financial",
            "financial_statement",
            "financial_statements",
            "financial_statement_snapshot",
            "sap",
            "sap_score",
            "sap_score_snapshot",
        }

    def import_snapshot(
        self,
        source: str | Path,
        snapshot_type: str | None = None,
        repository: HistoricalSnapshotRepository | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> ImportResult:
        normalized = snapshot_type.strip().lower().replace("-", "_") if snapshot_type else "financial_statement"
        if normalized in {"financial", "financial_statement", "financial_statements", "financial_statement_snapshot"}:
            return self.import_financial_statements(
                symbol=str(source),
                start_date=start_date,
                end_date=end_date,
                repository=repository,
            )
        if normalized in {"sap", "sap_score", "sap_score_snapshot"}:
            raise NotImplementedError("FinMind SAP score snapshot import is not implemented yet")
        raise ImporterError(f"Unsupported FinMind snapshot type: {snapshot_type}")

    def import_financial_statements(
        self,
        symbol: str,
        start_date: str | None = None,
        end_date: str | None = None,
        repository: HistoricalSnapshotRepository | None = None,
    ) -> ImportResult:
        result = ImportResult(
            importer=self.name,
            importer_version=self.version,
            source=f"finmind:{symbol}",
        )
        validator = self.validator or HistoricalValidator()
        target_repository = repository

        try:
            response = self.client.get_financial_statement(
                symbol,
                start_date=start_date,
                end_date=end_date,
            )
        except FinMindAPIError as error:
            result.failed_count = 1
            result.errors.append(f"FinMind API error for {symbol}: {error}")
            return result

        for row_number, row in enumerate(response.data or [], start=1):
            try:
                snapshot = map_financial_statement_row(row)
            except (FinMindMappingError, TypeError, ValueError) as error:
                result.failed_count += 1
                result.errors.append(f"row {row_number}: {error}")
                continue

            validation = validator.validate_financial_snapshot(snapshot)
            if not validation.is_valid:
                result.failed_count += 1
                result.errors.extend(format_validation_messages(row_number, validation.errors))
                continue

            result.warnings.extend(format_validation_messages(row_number, validation.warnings))

            try:
                if target_repository is None:
                    target_repository = HistoricalSnapshotRepository()
                target_repository.insert_financial_snapshot(snapshot)
            except Exception as error:
                result.failed_count += 1
                result.errors.append(f"row {row_number}: repository write failed: {error}")
                continue

            result.financial_statement_snapshots.append(snapshot)
            result.imported_count += 1

        return result


def format_validation_messages(row_number: int, messages: list[str]) -> list[str]:
    return [f"row {row_number}: {message}" for message in messages]
