"""Validator for API specifications."""

import re

from .base import SpecValidator, ValidationResult


class ApiValidator(SpecValidator):
    """Validates API endpoint specifications."""

    # Required sections
    REQUIRED_SECTIONS = ["## Purpose", "## Endpoints"]

    # HTTP methods
    HTTP_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]

    # Pattern for endpoint headers
    ENDPOINT_PATTERN = r"^###\s+(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+/.+"

    def validate(self) -> ValidationResult:
        """Validate the API specification.

        Returns:
            ValidationResult with any errors or warnings
        """
        result = ValidationResult(spec_path=str(self.spec_file))

        # Check for required sections
        self._validate_required_sections(result)

        # Check endpoint definitions
        self._validate_endpoints(result)

        # Check response definitions
        self._validate_responses(result)

        return result

    def _validate_required_sections(self, result: ValidationResult) -> None:
        """Validate that all required sections exist."""
        for section in self.REQUIRED_SECTIONS:
            if not self._has_section(section):
                result.add_error(
                    f"Missing required section: {section}", section=section
                )

    def _validate_endpoints(self, result: ValidationResult) -> None:
        """Validate endpoint definitions."""
        in_endpoints_section = False
        endpoint_count = 0

        for i, line in enumerate(self.lines):
            line_no = i + 1
            stripped = line.strip()

            # Track if we're in Endpoints section
            if stripped == "## Endpoints":
                in_endpoints_section = True
                continue
            elif stripped.startswith("## ") and stripped != "## Endpoints":
                in_endpoints_section = False

            if not in_endpoints_section:
                continue

            # Check endpoint headers
            if stripped.startswith("### "):
                endpoint_count += 1

                if not re.match(self.ENDPOINT_PATTERN, stripped):
                    result.add_error(
                        "Endpoint must follow format: '### METHOD /path' (e.g., '### GET /users')",
                        line=line_no,
                    )

        # Check if any endpoints exist
        if in_endpoints_section and endpoint_count == 0:
            line = self._get_section_line("## Endpoints")
            result.add_warning(
                "Endpoints section exists but contains no endpoints", line=line
            )

    def _validate_responses(self, result: ValidationResult) -> None:
        """Validate response definitions."""
        in_endpoints_section = False

        for i, line in enumerate(self.lines):
            line_no = i + 1
            stripped = line.strip()

            # Track section
            if stripped == "## Endpoints":
                in_endpoints_section = True
                continue
            elif stripped.startswith("## ") and stripped != "## Endpoints":
                in_endpoints_section = False

            if not in_endpoints_section:
                continue

            # Track current endpoint
            if stripped.startswith("### ") and re.match(
                self.ENDPOINT_PATTERN, stripped
            ):
                # Check for response definitions after endpoint
                has_responses = False
                for j in range(i + 1, min(i + 50, len(self.lines))):
                    check_line = self.lines[j].strip()

                    # Stop at next endpoint or section
                    if check_line.startswith("### ") or check_line.startswith("## "):
                        break

                    # Look for response headers (#### 200 OK, etc.)
                    if check_line.startswith("#### ") and any(
                        code in check_line
                        for code in [
                            "200",
                            "201",
                            "204",
                            "400",
                            "401",
                            "403",
                            "404",
                            "500",
                        ]
                    ):
                        has_responses = True
                        break

                if not has_responses:
                    result.add_warning(
                        "Endpoint should define response codes (#### 200 OK, etc.)",
                        line=line_no,
                    )
