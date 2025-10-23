"""Base validator classes for specification validation."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional


class Severity(Enum):
    """Validation issue severity levels."""

    ERROR = "error"
    WARNING = "warning"


@dataclass
class ValidationIssue:
    """Represents a single validation issue."""

    severity: Severity
    message: str
    line: Optional[int] = None
    section: Optional[str] = None

    def __str__(self) -> str:
        """Format issue for display."""
        parts = [f"[{self.severity.value.upper()}]"]

        if self.line:
            parts.append(f"Line {self.line}:")
        elif self.section:
            parts.append(f"Section '{self.section}':")

        parts.append(self.message)
        return " ".join(parts)


@dataclass
class ValidationResult:
    """Result of validating a specification."""

    spec_path: str
    errors: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Check if validation passed (no errors)."""
        return len(self.errors) == 0

    @property
    def has_issues(self) -> bool:
        """Check if there are any issues (errors or warnings)."""
        return len(self.errors) > 0 or len(self.warnings) > 0

    def add_error(
        self, message: str, line: Optional[int] = None, section: Optional[str] = None
    ) -> None:
        """Add an error to the result."""
        self.errors.append(ValidationIssue(Severity.ERROR, message, line, section))

    def add_warning(
        self, message: str, line: Optional[int] = None, section: Optional[str] = None
    ) -> None:
        """Add a warning to the result."""
        self.warnings.append(ValidationIssue(Severity.WARNING, message, line, section))


class SpecValidator:
    """Base class for specification validators."""

    def __init__(self, spec_file: Path):
        """Initialize validator.

        Args:
            spec_file: Path to the specification file
        """
        self.spec_file = spec_file
        self.content = spec_file.read_text() if spec_file.exists() else ""
        self.lines = self.content.split("\n")

    def validate(self) -> ValidationResult:
        """Validate the specification.

        Returns:
            ValidationResult with any errors or warnings
        """
        raise NotImplementedError("Subclasses must implement validate()")

    def _has_section(self, section_header: str) -> bool:
        """Check if a section exists in the spec.

        Args:
            section_header: Section header to look for (e.g., "## Purpose")

        Returns:
            True if section exists
        """
        return section_header in self.content

    def _get_section_line(self, section_header: str) -> Optional[int]:
        """Get the line number of a section header.

        Args:
            section_header: Section header to find

        Returns:
            Line number (1-indexed) or None if not found
        """
        for i, line in enumerate(self.lines):
            if line.strip() == section_header:
                return i + 1
        return None
