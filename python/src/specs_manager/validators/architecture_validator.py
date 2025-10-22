"""Validator for architecture specifications."""

import re

from .base import SpecValidator, ValidationResult


class ArchitectureValidator(SpecValidator):
    """Validates architecture design specifications."""

    # Required sections
    REQUIRED_SECTIONS = ["## Purpose", "## Components"]

    # Pattern for component headers
    COMPONENT_PATTERN = r"^###\s+Component:\s+.+"

    # Pattern for decision headers
    DECISION_PATTERN = r"^###\s+Decision:\s+.+"

    def validate(self) -> ValidationResult:
        """Validate the architecture specification.

        Returns:
            ValidationResult with any errors or warnings
        """
        result = ValidationResult(spec_path=str(self.spec_file))

        # Check for required sections
        self._validate_required_sections(result)

        # Check component definitions
        self._validate_components(result)

        # Check design decisions (ADRs)
        self._validate_decisions(result)

        return result

    def _validate_required_sections(self, result: ValidationResult) -> None:
        """Validate that all required sections exist."""
        for section in self.REQUIRED_SECTIONS:
            if not self._has_section(section):
                result.add_error(
                    f"Missing required section: {section}", section=section
                )

    def _validate_components(self, result: ValidationResult) -> None:
        """Validate component definitions."""
        in_components_section = False
        component_count = 0

        for i, line in enumerate(self.lines):
            line_no = i + 1
            stripped = line.strip()

            # Track if we're in Components section
            if stripped == "## Components":
                in_components_section = True
                continue
            elif stripped.startswith("## ") and stripped != "## Components":
                in_components_section = False

            if not in_components_section:
                continue

            # Check component headers
            if stripped.startswith("### "):
                component_count += 1

                if not re.match(self.COMPONENT_PATTERN, stripped):
                    result.add_error(
                        "Component must follow format: '### Component: <Name>'",
                        line=line_no,
                    )
                else:
                    # Check for component metadata
                    has_type = False
                    has_responsibility = False

                    for j in range(i + 1, min(i + 15, len(self.lines))):
                        check_line = self.lines[j].strip()

                        # Stop at next heading
                        if check_line.startswith("#"):
                            break

                        if check_line.startswith("**Type**:"):
                            has_type = True
                        if check_line.startswith("**Responsibility**:"):
                            has_responsibility = True

                    if not has_type:
                        result.add_warning(
                            "Component should include **Type**: field", line=line_no
                        )

                    if not has_responsibility:
                        result.add_warning(
                            "Component should include **Responsibility**: field",
                            line=line_no,
                        )

        # Check if any components exist
        if in_components_section and component_count == 0:
            line = self._get_section_line("## Components")
            result.add_warning(
                "Components section exists but contains no components", line=line
            )

    def _validate_decisions(self, result: ValidationResult) -> None:
        """Validate design decision (ADR) format."""
        # Design Decisions section is optional, but if present, validate format
        if not self._has_section("## Design Decisions"):
            return

        in_decisions_section = False

        for i, line in enumerate(self.lines):
            line_no = i + 1
            stripped = line.strip()

            # Track section
            if stripped == "## Design Decisions":
                in_decisions_section = True
                continue
            elif stripped.startswith("## ") and stripped != "## Design Decisions":
                in_decisions_section = False

            if not in_decisions_section:
                continue

            # Check decision headers
            if stripped.startswith("### "):
                if not re.match(self.DECISION_PATTERN, stripped):
                    result.add_warning(
                        "Decision should follow format: '### Decision: <Title>'",
                        line=line_no,
                    )
                else:
                    # Check for ADR fields
                    has_status = False
                    has_context = False
                    has_decision = False

                    for j in range(i + 1, min(i + 30, len(self.lines))):
                        check_line = self.lines[j].strip()

                        # Stop at next heading
                        if check_line.startswith("#"):
                            break

                        if check_line.startswith("**Status**:"):
                            has_status = True
                        if check_line.startswith("**Context**:"):
                            has_context = True
                        if check_line.startswith("**Decision**:"):
                            has_decision = True

                    if not (has_status and has_context and has_decision):
                        result.add_warning(
                            "ADR should include **Status**, **Context**, and **Decision** fields",
                            line=line_no,
                        )
