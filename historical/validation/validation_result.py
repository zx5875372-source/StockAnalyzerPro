from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    is_valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    field_count: int = 0
    missing_fields: list[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def add_missing_field(self, field_name: str) -> None:
        self.missing_fields.append(field_name)
        self.add_error(f"Missing required field: {field_name}")
