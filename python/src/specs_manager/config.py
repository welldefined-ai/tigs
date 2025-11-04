"""Configuration management for spec structures."""

from __future__ import annotations

import yaml
from pathlib import Path
from typing import Optional


class SpecsConfig:
    """Manages .tigsrc configuration file in specs directory."""

    CONFIG_FILENAME = ".tigsrc"
    DEFAULT_STRUCTURE = "web-app"

    def __init__(self, specs_dir: Path):
        """Initialize config manager.

        Args:
            specs_dir: Path to specs directory
        """
        self.specs_dir = Path(specs_dir)
        self.config_file = self.specs_dir / self.CONFIG_FILENAME

    def exists(self) -> bool:
        """Check if config file exists."""
        return self.config_file.exists()

    def load(self) -> dict:
        """Load configuration from .tigsrc file.

        Returns:
            Configuration dictionary

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file is invalid
        """
        if not self.config_file.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_file}")

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {self.config_file}: {e}") from e

        if not isinstance(data, dict):
            raise ValueError(f"Config file must contain a YAML dictionary")

        return data

    def save(self, config: dict) -> None:
        """Save configuration to .tigsrc file.

        Args:
            config: Configuration dictionary to save
        """
        self.specs_dir.mkdir(parents=True, exist_ok=True)

        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    def get_structure(self) -> str:
        """Get the configured structure name.

        Returns:
            Structure name, or DEFAULT_STRUCTURE if not configured
        """
        if not self.exists():
            return self.DEFAULT_STRUCTURE

        try:
            config = self.load()
            return config.get('structure', self.DEFAULT_STRUCTURE)
        except (FileNotFoundError, ValueError):
            return self.DEFAULT_STRUCTURE

    def set_structure(self, structure_name: str, structure_version: Optional[str] = None) -> None:
        """Set the structure name in config.

        Args:
            structure_name: Name of the structure
            structure_version: Optional version string
        """
        config = {}
        if self.exists():
            try:
                config = self.load()
            except (FileNotFoundError, ValueError):
                pass

        config['structure'] = structure_name
        if structure_version:
            config['structure_version'] = structure_version

        self.save(config)

    @classmethod
    def detect_structure_from_directory(cls, specs_dir: Path) -> Optional[str]:
        """Detect structure type from existing specs directory layout.

        Args:
            specs_dir: Path to specs directory

        Returns:
            Detected structure name, or None if can't determine
        """
        if not specs_dir.exists():
            return None

        # Check for web-app structure (capabilities, data-models, api, architecture)
        web_app_types = {'capabilities', 'data-models', 'api', 'architecture'}
        existing_dirs = {d.name for d in specs_dir.iterdir() if d.is_dir()}

        # If has all 4 web-app types, it's likely web-app
        if web_app_types.issubset(existing_dirs):
            return 'web-app'

        # Check for embedded-system structure
        embedded_types = {'hardware', 'firmware', 'protocols', 'power-management'}
        if embedded_types.issubset(existing_dirs):
            return 'embedded-system'

        # Check for pipeline structure
        pipeline_types = {'sources', 'transforms', 'sinks', 'schemas', 'orchestration'}
        if pipeline_types.issubset(existing_dirs):
            return 'pipeline'

        # Can't determine - default to web-app
        return None
