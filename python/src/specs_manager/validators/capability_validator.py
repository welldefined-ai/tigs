"""Validator for capability specifications."""

import re
from pathlib import Path

from .base import SpecValidator, ValidationResult


class CapabilityValidator(SpecValidator):
    """Validates capability (behavioral) specifications."""

    # Required sections
    REQUIRED_SECTIONS = ["## Purpose", "## Requirements"]

    # Pattern for requirements
    REQUIREMENT_PATTERN = r"^###\s+Requirement:\s+.+"
    
    # Pattern for scenarios
    SCENARIO_PATTERN = r"^####\s+Scenario:\s+.+"
    
    # Required keywords in SHALL/MUST statements
    MODAL_VERBS = ["SHALL", "MUST", "SHOULD", "MAY"]

    def validate(self) -> ValidationResult:
        """Validate the capability specification.
        
        Returns:
            ValidationResult with any errors or warnings
        """
        result = ValidationResult(spec_path=str(self.spec_file))

        # Check for required sections
        self._validate_required_sections(result)

        # Check requirements format
        self._validate_requirements(result)

        # Check scenarios format
        self._validate_scenarios(result)

        return result

    def _validate_required_sections(self, result: ValidationResult) -> None:
        """Validate that all required sections exist."""
        for section in self.REQUIRED_SECTIONS:
            if not self._has_section(section):
                result.add_error(
                    f"Missing required section: {section}",
                    section=section
                )

    def _validate_requirements(self, result: ValidationResult) -> None:
        """Validate requirements format."""
        in_requirements_section = False
        requirement_count = 0

        for i, line in enumerate(self.lines):
            line_no = i + 1
            stripped = line.strip()

            # Track if we're in Requirements section
            if stripped == "## Requirements":
                in_requirements_section = True
                continue
            elif stripped.startswith("## ") and stripped != "## Requirements":
                in_requirements_section = False

            if not in_requirements_section:
                continue

            # Check requirement headers
            if stripped.startswith("### "):
                requirement_count += 1
                
                if not re.match(self.REQUIREMENT_PATTERN, stripped):
                    result.add_error(
                        "Requirement must follow format: '### Requirement: <Name>'",
                        line=line_no
                    )
                else:
                    # Check for modal verbs in the requirement description
                    # Look ahead for SHALL/MUST in next few lines
                    has_modal = False
                    for j in range(i + 1, min(i + 10, len(self.lines))):
                        if any(verb in self.lines[j] for verb in self.MODAL_VERBS):
                            has_modal = True
                            break
                        # Stop at next heading
                        if self.lines[j].strip().startswith("#"):
                            break
                    
                    if not has_modal:
                        result.add_warning(
                            "Requirement should include SHALL/MUST/SHOULD/MAY statement",
                            line=line_no
                        )

        # Check if any requirements exist
        if in_requirements_section and requirement_count == 0:
            line = self._get_section_line("## Requirements")
            result.add_warning(
                "Requirements section exists but contains no requirements",
                line=line
            )

    def _validate_scenarios(self, result: ValidationResult) -> None:
        """Validate scenario format."""
        in_requirements_section = False
        current_requirement = None

        for i, line in enumerate(self.lines):
            line_no = i + 1
            stripped = line.strip()

            # Track section
            if stripped == "## Requirements":
                in_requirements_section = True
                continue
            elif stripped.startswith("## ") and stripped != "## Requirements":
                in_requirements_section = False

            if not in_requirements_section:
                continue

            # Track current requirement
            if stripped.startswith("### Requirement:"):
                current_requirement = stripped
                continue

            # Check scenario headers
            if stripped.startswith("#### "):
                if not re.match(self.SCENARIO_PATTERN, stripped):
                    result.add_error(
                        "Scenario must follow format: '#### Scenario: <Description>'",
                        line=line_no
                    )
                else:
                    # Check for WHEN/THEN keywords
                    has_when = False
                    has_then = False
                    
                    # Look ahead for WHEN/THEN in scenario
                    for j in range(i + 1, min(i + 20, len(self.lines))):
                        scenario_line = self.lines[j]
                        
                        # Stop at next heading
                        if scenario_line.strip().startswith("#"):
                            break
                        
                        if "**WHEN**" in scenario_line:
                            has_when = True
                        if "**THEN**" in scenario_line:
                            has_then = True
                    
                    if not has_when or not has_then:
                        result.add_warning(
                            "Scenario should include **WHEN** and **THEN** keywords",
                            line=line_no
                        )
