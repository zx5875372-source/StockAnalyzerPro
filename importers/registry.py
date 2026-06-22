from __future__ import annotations

from collections.abc import Callable

from importers.base_importer import BaseImporter


ImporterBuilder = Callable[..., BaseImporter]


class ImporterRegistryError(ValueError):
    pass


class ImporterRegistry:
    def __init__(self):
        self._builders: dict[str, ImporterBuilder] = {}

    def register(self, name: str, builder: ImporterBuilder) -> None:
        normalized_name = self._normalize_name(name)
        if normalized_name in self._builders:
            raise ImporterRegistryError(f"Importer already registered: {name}")
        self._builders[normalized_name] = builder

    def unregister(self, name: str) -> None:
        normalized_name = self._normalize_name(name)
        if normalized_name not in self._builders:
            raise ImporterRegistryError(f"Importer not registered: {name}")
        self._builders.pop(normalized_name)

    def get(self, name: str, **kwargs) -> BaseImporter:
        normalized_name = self._normalize_name(name)
        builder = self._builders.get(normalized_name)
        if builder is None:
            available = ", ".join(self.list())
            raise ImporterRegistryError(f"Unknown importer '{name}'. Available importers: {available}")
        return builder(**kwargs)

    def list(self) -> list[str]:
        return sorted(self._builders)

    @staticmethod
    def _normalize_name(name: str) -> str:
        return name.strip().lower().replace("-", "_")


def create_default_registry() -> ImporterRegistry:
    from importers.csv_historical_importer import CSVHistoricalImporter
    from importers.finmind_importer import FinMindImporter
    from importers.mock_importer import MockImporter

    registry = ImporterRegistry()
    registry.register("csv", CSVHistoricalImporter)
    registry.register("csv_historical", CSVHistoricalImporter)
    registry.register("finmind", FinMindImporter)
    registry.register("mock", MockImporter)
    return registry
