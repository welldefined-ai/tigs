"""Parser for data model delta specifications."""

import re
from pathlib import Path
from typing import Dict, List


class DataModelDeltaParser:
    """Parses data model delta specifications."""

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
            Dictionary with keys: added, modified, removed, renamed
            Each value is a list of entity dicts with 'name' and 'content'
        """
        result = {"added": [], "modified": [], "removed": [], "renamed": []}

        # Split by major sections
        sections = self._split_sections()

        for section_name, section_content in sections.items():
            if section_name == "added":
                result["added"] = self._parse_entities(section_content)
            elif section_name == "modified":
                result["modified"] = self._parse_entities(section_content)
            elif section_name == "removed":
                result["removed"] = self._parse_removed_entities(section_content)
            elif section_name == "renamed":
                result["renamed"] = self._parse_renamed_entities(section_content)

        return result

    def _split_sections(self) -> Dict[str, str]:
        """Split content into ADDED/MODIFIED/REMOVED/RENAMED sections."""
        sections = {}

        # Find section headers
        patterns = {
            "added": r"##\s+ADDED\s+Entities",
            "modified": r"##\s+MODIFIED\s+Entities",
            "removed": r"##\s+REMOVED\s+Entities",
            "renamed": r"##\s+RENAMED\s+Entities",
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, self.content, re.IGNORECASE)
            if match:
                start = match.end()
                # Find next section or end of file
                next_section = None
                for other_pattern in patterns.values():
                    other_match = re.search(
                        other_pattern, self.content[start:], re.IGNORECASE
                    )
                    if other_match:
                        if next_section is None or other_match.start() < next_section:
                            next_section = other_match.start()

                end = start + next_section if next_section else len(self.content)
                sections[key] = self.content[start:end].strip()

        return sections

    def _parse_entities(self, section_content: str) -> List[Dict[str, str]]:
        """Parse ADDED or MODIFIED entities section.

        Returns list of dicts with 'name' and 'content'
        """
        entities = []

        # Split by ### Entity: headers
        entity_pattern = r"###\s+Entity:\s+(.+?)(?=###\s+Entity:|\Z)"
        matches = re.finditer(entity_pattern, section_content, re.DOTALL)

        for match in matches:
            entity_name = match.group(1).split("\n")[0].strip()
            entity_content = match.group(0).strip()
            entities.append({"name": entity_name, "content": entity_content})

        return entities

    def _parse_removed_entities(self, section_content: str) -> List[Dict[str, str]]:
        """Parse REMOVED entities section (only names needed)."""
        entities = []

        # Find entity names
        entity_pattern = r"###\s+Entity:\s+(.+?)(?:\n|$)"
        matches = re.finditer(entity_pattern, section_content)

        for match in matches:
            entity_name = match.group(1).strip()
            entities.append(
                {
                    "name": entity_name,
                    "content": "",  # No content needed for removal
                }
            )

        return entities

    def _parse_renamed_entities(self, section_content: str) -> List[Dict[str, str]]:
        """Parse RENAMED entities section.

        Returns list of dicts with 'old_name', 'new_name', and 'content'
        """
        entities = []

        # Find renamed entities: "Old Name → New Name" or "Old Name -> New Name"
        entity_pattern = r"###\s+Entity:\s+(.+?)\s*(?:→|->)\s*(.+?)(?:\n|$)"
        matches = re.finditer(entity_pattern, section_content)

        for match in matches:
            old_name = match.group(1).strip()
            new_name = match.group(2).strip()
            entities.append(
                {
                    "old_name": old_name,
                    "new_name": new_name,
                    "name": new_name,  # For consistency
                }
            )

        return entities
