"""Structure loader for pluggable spec structures."""

from __future__ import annotations

import yaml
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class SpecType:
    """Represents a spec type within a structure."""
    name: str
    description: str
    directory: str


@dataclass
class Structure:
    """Represents a complete spec structure definition."""
    name: str
    version: str
    description: str
    author: str
    spec_types: Dict[str, SpecType]
    required_commands: List[str]
    structure_path: Path

    def get_spec_type_names(self) -> List[str]:
        """Get list of spec type names."""
        return list(self.spec_types.keys())

    def get_spec_type(self, name: str) -> Optional[SpecType]:
        """Get a specific spec type by name."""
        return self.spec_types.get(name)


class StructureLoader:
    """Loads and manages spec structure definitions."""

    def __init__(self, templates_dir: Optional[Path] = None):
        """Initialize the structure loader.

        Args:
            templates_dir: Path to templates directory. If None, uses package default.
        """
        if templates_dir is None:
            # Default to package templates directory
            templates_dir = Path(__file__).parent / "templates"

        self.templates_dir = templates_dir
        self.structures_dir = templates_dir / "structures"
        self._cache: Dict[str, Structure] = {}

    def list_structures(self) -> List[str]:
        """List all available structure names.

        Returns:
            List of structure names (directory names under structures/)
        """
        if not self.structures_dir.exists():
            return []

        structures = []
        for item in self.structures_dir.iterdir():
            if item.is_dir() and (item / "structure.yaml").exists():
                structures.append(item.name)

        return sorted(structures)

    def load_structure(self, name: str) -> Structure:
        """Load a structure definition by name.

        Args:
            name: Structure name (e.g., "web-app", "embedded-system")

        Returns:
            Structure object

        Raises:
            FileNotFoundError: If structure doesn't exist
            ValueError: If structure.yaml is invalid
        """
        # Check cache first
        if name in self._cache:
            return self._cache[name]

        structure_path = self.structures_dir / name
        if not structure_path.exists():
            raise FileNotFoundError(
                f"Structure '{name}' not found at {structure_path}"
            )

        structure_file = structure_path / "structure.yaml"
        if not structure_file.exists():
            raise FileNotFoundError(
                f"Structure definition file not found: {structure_file}"
            )

        # Load and parse YAML
        try:
            with open(structure_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {structure_file}: {e}") from e

        # Validate required fields
        required_fields = ['name', 'version', 'description', 'spec_types']
        for field in required_fields:
            if field not in data:
                raise ValueError(
                    f"Missing required field '{field}' in {structure_file}"
                )

        # Parse spec types
        spec_types = {}
        for type_name, type_data in data['spec_types'].items():
            if not isinstance(type_data, dict):
                raise ValueError(
                    f"Invalid spec type definition for '{type_name}' in {structure_file}"
                )

            spec_type = SpecType(
                name=type_name,
                description=type_data.get('description', ''),
                directory=type_data.get('directory', type_name)
            )
            spec_types[type_name] = spec_type

        # Create structure object
        structure = Structure(
            name=data['name'],
            version=data['version'],
            description=data['description'],
            author=data.get('author', 'Unknown'),
            spec_types=spec_types,
            required_commands=data.get('required_commands', []),
            structure_path=structure_path
        )

        # Cache it
        self._cache[name] = structure

        return structure

    def get_structure_info(self, name: str) -> Dict[str, any]:
        """Get structure information as a dictionary.

        Args:
            name: Structure name

        Returns:
            Dictionary with structure information
        """
        structure = self.load_structure(name)

        spec_types_info = {}
        for type_name, spec_type in structure.spec_types.items():
            spec_types_info[type_name] = {
                'description': spec_type.description,
                'directory': spec_type.directory
            }

        return {
            'name': structure.name,
            'version': structure.version,
            'description': structure.description,
            'author': structure.author,
            'spec_types': spec_types_info,
            'required_commands': structure.required_commands
        }

    def get_command_path(self, structure_name: str, command_name: str) -> Path:
        """Get path to a command file for a structure.

        Args:
            structure_name: Structure name
            command_name: Command name (without .md extension)

        Returns:
            Path to command file

        Raises:
            FileNotFoundError: If command file doesn't exist
        """
        structure = self.load_structure(structure_name)
        command_file = structure.structure_path / f"{command_name}.md"

        if not command_file.exists():
            raise FileNotFoundError(
                f"Command '{command_name}' not found for structure '{structure_name}'"
            )

        return command_file

    def get_examples_dir(self, structure_name: str) -> Path:
        """Get path to examples directory for a structure.

        Args:
            structure_name: Structure name

        Returns:
            Path to examples directory
        """
        structure = self.load_structure(structure_name)
        return structure.structure_path / "examples"
