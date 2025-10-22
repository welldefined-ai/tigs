"""Validator for data model specifications."""

import re

from .base import SpecValidator, ValidationResult


class DataModelValidator(SpecValidator):
    """Validates data model (schema) specifications."""

    # Required sections
    REQUIRED_SECTIONS = ["## Purpose", "## Schema"]

    # Pattern for entity headers
    ENTITY_PATTERN = r"^###\s+Entity:\s+.+"

    # Pattern for table definition
    TABLE_PATTERN = r"^\*\*Table\*\*:\s+`.+`"

    def validate(self) -> ValidationResult:
        """Validate the data model specification.

        Returns:
            ValidationResult with any errors or warnings
        """
        result = ValidationResult(spec_path=str(self.spec_file))

        # Check for required sections
        self._validate_required_sections(result)

        # Check entity definitions
        self._validate_entities(result)

        # Check field tables
        self._validate_field_tables(result)

        return result

    def _validate_required_sections(self, result: ValidationResult) -> None:
        """Validate that all required sections exist."""
        for section in self.REQUIRED_SECTIONS:
            if not self._has_section(section):
                result.add_error(
                    f"Missing required section: {section}", section=section
                )

    def _validate_entities(self, result: ValidationResult) -> None:
        """Validate entity definitions."""
        in_schema_section = False
        entity_count = 0

        for i, line in enumerate(self.lines):
            line_no = i + 1
            stripped = line.strip()

            # Track if we're in Schema section
            if stripped == "## Schema":
                in_schema_section = True
                continue
            elif stripped.startswith("## ") and stripped != "## Schema":
                in_schema_section = False

            if not in_schema_section:
                continue

            # Check entity headers
            if stripped.startswith("### "):
                entity_count += 1

                if not re.match(self.ENTITY_PATTERN, stripped):
                    result.add_error(
                        "Entity must follow format: '### Entity: <Name>'", line=line_no
                    )
                else:
                    # Check for table definition
                    has_table = False
                    for j in range(i + 1, min(i + 10, len(self.lines))):
                        if re.match(self.TABLE_PATTERN, self.lines[j].strip()):
                            has_table = True
                            break
                        # Stop at next heading
                        if self.lines[j].strip().startswith("#"):
                            break

                    if not has_table:
                        result.add_warning(
                            "Entity should include table definition: **Table**: `table_name`",
                            line=line_no,
                        )

        # Check if any entities exist
        if in_schema_section and entity_count == 0:
            line = self._get_section_line("## Schema")
            result.add_warning(
                "Schema section exists but contains no entities", line=line
            )

    def _validate_field_tables(self, result: ValidationResult) -> None:
        """Validate field table format."""
        in_schema_section = False

        for i, line in enumerate(self.lines):
            line_no = i + 1
            stripped = line.strip()

            # Track section
            if stripped == "## Schema":
                in_schema_section = True
                continue
            elif stripped.startswith("## ") and stripped != "## Schema":
                in_schema_section = False

            if not in_schema_section:
                continue

            # Check for field table header
            if "| Field | Type | Constraints | Description |" in stripped:
                # Check for separator line
                if i + 1 < len(self.lines):
                    next_line = self.lines[i + 1].strip()
                    if not next_line.startswith("|---"):
                        result.add_error(
                            "Field table missing separator line", line=line_no + 1
                        )
                else:
                    result.add_error("Field table incomplete", line=line_no)
