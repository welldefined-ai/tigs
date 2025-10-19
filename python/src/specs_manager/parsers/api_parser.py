"""Parser for API delta specifications."""

import re
from pathlib import Path
from typing import Dict, List


class ApiDeltaParser:
    """Parses API delta specifications."""

    def __init__(self, delta_file: Path):
        """Initialize parser with delta file.

        Args:
            delta_file: Path to the delta specification file
        """
        self.delta_file = delta_file
        self.content = delta_file.read_text() if delta_file.exists() else ""

    def parse(self) -> Dict[str, List[Dict[str, str]]]:
        """Parse delta specification into operations.

        Returns:
            Dictionary with keys: added, modified, removed
            Each value is a list of endpoint dicts with 'method', 'path', and 'content'
        """
        result = {
            "added": [],
            "modified": [],
            "removed": []
        }

        # Split by major sections
        sections = self._split_sections()

        for section_name, section_content in sections.items():
            if section_name == "added":
                result["added"] = self._parse_endpoints(section_content)
            elif section_name == "modified":
                result["modified"] = self._parse_endpoints(section_content)
            elif section_name == "removed":
                result["removed"] = self._parse_removed_endpoints(section_content)

        return result

    def _split_sections(self) -> Dict[str, str]:
        """Split content into ADDED/MODIFIED/REMOVED sections."""
        sections = {}

        # Find section headers
        patterns = {
            "added": r"##\s+ADDED\s+Endpoints",
            "modified": r"##\s+MODIFIED\s+Endpoints",
            "removed": r"##\s+REMOVED\s+Endpoints"
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, self.content, re.IGNORECASE)
            if match:
                start = match.end()
                # Find next section or end of file
                next_section = None
                for other_pattern in patterns.values():
                    other_match = re.search(other_pattern, self.content[start:], re.IGNORECASE)
                    if other_match:
                        if next_section is None or other_match.start() < next_section:
                            next_section = other_match.start()

                end = start + next_section if next_section else len(self.content)
                sections[key] = self.content[start:end].strip()

        return sections

    def _parse_endpoints(self, section_content: str) -> List[Dict[str, str]]:
        """Parse ADDED or MODIFIED endpoints section.

        Returns list of dicts with 'method', 'path', and 'content'
        """
        endpoints = []

        # Split by ### METHOD /path headers
        # Valid HTTP methods: GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS
        endpoint_pattern = r"###\s+(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+(/[^\n]*)(?=###\s+(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)|\Z)"
        matches = re.finditer(endpoint_pattern, section_content, re.DOTALL | re.IGNORECASE)

        for match in matches:
            method = match.group(1).upper()
            path = match.group(2).strip()
            endpoint_content = match.group(0).strip()
            endpoints.append({
                "method": method,
                "path": path,
                "signature": f"{method} {path}",  # For matching
                "content": endpoint_content
            })

        return endpoints

    def _parse_removed_endpoints(self, section_content: str) -> List[Dict[str, str]]:
        """Parse REMOVED endpoints section (only signatures needed)."""
        endpoints = []

        # Find endpoint signatures
        endpoint_pattern = r"###\s+(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+(/[^\n]*)"
        matches = re.finditer(endpoint_pattern, section_content, re.IGNORECASE)

        for match in matches:
            method = match.group(1).upper()
            path = match.group(2).strip()
            endpoints.append({
                "method": method,
                "path": path,
                "signature": f"{method} {path}",
                "content": ""  # No content needed for removal
            })

        return endpoints
