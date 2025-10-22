"""Merger for API specifications."""

import re
from pathlib import Path
from typing import Dict, List


class ApiMerger:
    """Merges API delta changes into main specification."""

    def __init__(self, main_spec_file: Path):
        """Initialize merger with main spec file.

        Args:
            main_spec_file: Path to the main specification file
        """
        self.main_spec_file = main_spec_file
        self.content = main_spec_file.read_text() if main_spec_file.exists() else ""

    def apply_changes(self, delta: Dict[str, List[Dict[str, str]]]) -> str:
        """Apply delta changes to main specification.

        Args:
            delta: Parsed delta from ApiDeltaParser

        Returns:
            Updated specification content
        """
        content = self.content

        # Apply in order: REMOVED → MODIFIED → ADDED
        content = self._apply_removed(content, delta.get("removed", []))
        content = self._apply_modified(content, delta.get("modified", []))
        content = self._apply_added(content, delta.get("added", []))

        return content

    def _apply_removed(self, content: str, removed: List[Dict[str, str]]) -> str:
        """Apply REMOVED operations."""
        for item in removed:
            method = item.get("method", "")
            path = item.get("path", "")

            if not method or not path:
                continue

            # Find and remove the entire endpoint block
            # Match from ### METHOD /path to the next ### METHOD or end of Endpoints section
            pattern = rf"###\s+{re.escape(method)}\s+{re.escape(path)}.*?(?=###\s+(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)|##\s+(?!#)|$)"
            content = re.sub(pattern, "", content, flags=re.DOTALL | re.IGNORECASE)

        return content

    def _apply_modified(self, content: str, modified: List[Dict[str, str]]) -> str:
        """Apply MODIFIED operations."""
        for item in modified:
            method = item.get("method", "")
            path = item.get("path", "")
            new_content = item.get("content", "")

            if not method or not path or not new_content:
                continue

            # Find and replace the entire endpoint block
            pattern = rf"###\s+{re.escape(method)}\s+{re.escape(path)}.*?(?=###\s+(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)|##\s+(?!#)|$)"
            content = re.sub(
                pattern, new_content + "\n\n", content, flags=re.DOTALL | re.IGNORECASE
            )

        return content

    def _apply_added(self, content: str, added: List[Dict[str, str]]) -> str:
        """Apply ADDED operations."""
        if not added:
            return content

        # Find the Endpoints section
        endpoints_section_match = re.search(r"##\s+Endpoints", content)
        if not endpoints_section_match:
            # No Endpoints section, add one
            content += "\n\n## Endpoints\n\n"
            endpoints_section_match = re.search(r"##\s+Endpoints", content)

        # Find the end of Endpoints section (next ## header or end of file)
        start_pos = endpoints_section_match.end()
        next_section = re.search(r"\n##\s+(?!#)", content[start_pos:])

        if next_section:
            insert_pos = start_pos + next_section.start()
        else:
            insert_pos = len(content)

        # Insert all added endpoints
        added_content = "\n\n".join(
            item.get("content", "") for item in added if item.get("content")
        )
        if added_content:
            content = (
                content[:insert_pos]
                + "\n\n"
                + added_content
                + "\n"
                + content[insert_pos:]
            )

        return content
