"""Core specs management functionality."""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any

from .parsers import (
    CapabilityDeltaParser,
    CapabilityMerger,
    DataModelDeltaParser,
    DataModelMerger,
    ApiDeltaParser,
    ApiMerger,
    ArchitectureDeltaParser,
    ArchitectureMerger,
)
from .validators import (
    CapabilityValidator,
    DataModelValidator,
    ApiValidator,
    ArchitectureValidator,
    ValidationResult,
)


class SpecsManager:
    """Manages specification directory structure and operations."""

    # Directory structure
    SPECS_DIR = "specs"
    SUBDIRS = ["capabilities", "data-models", "api", "architecture", "changes"]

    # File naming conventions for each type
    SPEC_FILES = {
        "capabilities": "spec.md",
        "data-models": "schema.md",
        "api": "spec.md",
        "architecture": "spec.md",
    }

    def __init__(self, root_path: Path):
        """Initialize specs manager.

        Args:
            root_path: Root directory where specs/ will be created
        """
        self.root_path = Path(root_path)
        self.specs_path = self.root_path / self.SPECS_DIR

    def init_structure(self, with_examples: bool = False) -> dict:
        """Initialize specs directory structure and Claude Code slash commands.

        Args:
            with_examples: Whether to generate example specs

        Returns:
            dict with 'created' list of paths and 'existed' list

        Raises:
            FileExistsError: If specs/ already exists
        """
        if self.specs_path.exists():
            raise FileExistsError(
                f"Specs directory already exists at {self.specs_path}"
            )

        created = []

        # Create main specs directory
        self.specs_path.mkdir()
        created.append(str(self.specs_path))

        # Create subdirectories
        for subdir in self.SUBDIRS:
            subdir_path = self.specs_path / subdir
            subdir_path.mkdir()
            created.append(str(subdir_path))

        # Create changes/archive directory
        archive_path = self.specs_path / "changes" / "archive"
        archive_path.mkdir()
        created.append(str(archive_path))

        # Generate README
        readme_path = self.specs_path / "README.md"
        self._generate_readme(readme_path)
        created.append(str(readme_path))

        # Generate AGENTS.md for AI assistants
        agents_path = self.root_path / "AGENTS.md"
        self._generate_agents_md(agents_path)
        created.append(str(agents_path))

        # Create .claude/commands/ directory and copy slash command templates
        claude_commands_paths = self._create_claude_commands()
        created.extend(claude_commands_paths)

        # Generate examples if requested
        if with_examples:
            example_paths = self._generate_examples()
            created.extend(example_paths)

        return {"created": created, "existed": []}

    def list_specs(self, spec_type: Optional[str] = None) -> Dict[str, List[Dict[str, str]]]:
        """List all specifications, optionally filtered by type.

        Args:
            spec_type: Optional type filter (capabilities, data-models, api, architecture)

        Returns:
            Dictionary mapping spec types to lists of spec info dicts.
            Each spec info dict contains:
                - name: The spec name (directory name)
                - path: Relative path to the spec file
                - file: The spec filename

        Raises:
            FileNotFoundError: If specs/ directory doesn't exist
            ValueError: If spec_type is invalid
        """
        if not self.specs_path.exists():
            raise FileNotFoundError(
                f"Specs directory not found at {self.specs_path}. "
                f"Run 'tigs init-specs' first."
            )

        # Validate spec_type if provided
        if spec_type is not None:
            valid_types = list(self.SPEC_FILES.keys())
            if spec_type not in valid_types:
                raise ValueError(
                    f"Invalid spec type '{spec_type}'. "
                    f"Must be one of: {', '.join(valid_types)}"
                )

        result: Dict[str, List[Dict[str, str]]] = {}
        types_to_scan = [spec_type] if spec_type else list(self.SPEC_FILES.keys())

        for stype in types_to_scan:
            specs = []
            type_dir = self.specs_path / stype

            if not type_dir.exists():
                result[stype] = []
                continue

            # Scan for spec directories
            expected_filename = self.SPEC_FILES[stype]
            for spec_dir in sorted(type_dir.iterdir()):
                if not spec_dir.is_dir():
                    continue

                spec_file = spec_dir / expected_filename
                if spec_file.exists():
                    specs.append({
                        "name": spec_dir.name,
                        "path": str(spec_file.relative_to(self.root_path)),
                        "file": expected_filename,
                    })

            result[stype] = specs

        return result

    def show_spec(self, name: str, spec_type: Optional[str] = None) -> Dict[str, str]:
        """Show content of a specification.

        Args:
            name: The spec name (directory name)
            spec_type: Optional type to disambiguate (capabilities, data-models, api, architecture)

        Returns:
            Dictionary containing:
                - name: The spec name
                - type: The spec type
                - path: Relative path to the spec file
                - content: The spec file content

        Raises:
            FileNotFoundError: If specs/ directory doesn't exist or spec not found
            ValueError: If spec_type is invalid or name is ambiguous
        """
        if not self.specs_path.exists():
            raise FileNotFoundError(
                f"Specs directory not found at {self.specs_path}. "
                f"Run 'tigs init-specs' first."
            )

        # Validate spec_type if provided
        if spec_type is not None:
            valid_types = list(self.SPEC_FILES.keys())
            if spec_type not in valid_types:
                raise ValueError(
                    f"Invalid spec type '{spec_type}'. "
                    f"Must be one of: {', '.join(valid_types)}"
                )

        # Search for the spec
        found_specs = []
        types_to_search = [spec_type] if spec_type else list(self.SPEC_FILES.keys())

        for stype in types_to_search:
            type_dir = self.specs_path / stype
            if not type_dir.exists():
                continue

            spec_dir = type_dir / name
            expected_filename = self.SPEC_FILES[stype]
            spec_file = spec_dir / expected_filename

            if spec_file.exists():
                found_specs.append({
                    "name": name,
                    "type": stype,
                    "path": str(spec_file.relative_to(self.root_path)),
                    "file": expected_filename,
                    "full_path": spec_file,
                })

        # Handle results
        if not found_specs:
            if spec_type:
                raise FileNotFoundError(
                    f"Spec '{name}' not found in {spec_type}/. "
                    f"Use 'tigs list-specs' to see available specs."
                )
            else:
                raise FileNotFoundError(
                    f"Spec '{name}' not found in any type. "
                    f"Use 'tigs list-specs' to see available specs."
                )

        if len(found_specs) > 1:
            types = [s["type"] for s in found_specs]
            raise ValueError(
                f"Spec name '{name}' is ambiguous. Found in: {', '.join(types)}. "
                f"Use --type to specify which one to show."
            )

        # Read and return spec content
        spec_info = found_specs[0]
        content = spec_info["full_path"].read_text()

        return {
            "name": spec_info["name"],
            "type": spec_info["type"],
            "path": spec_info["path"],
            "content": content,
        }

    def _generate_readme(self, target_path: Path) -> None:
        """Generate README from template.

        Args:
            target_path: Where to write README.md
        """
        template_path = Path(__file__).parent / "templates" / "README_template.md"

        if not template_path.exists():
            # Fallback: create basic README
            content = "# Specifications\n\nThis directory contains project specifications.\n"
            target_path.write_text(content)
            return

        # Copy template (no variable substitution needed for README)
        shutil.copy(template_path, target_path)

    def _generate_agents_md(self, target_path: Path) -> None:
        """Generate AGENTS.md from template.

        Args:
            target_path: Where to write AGENTS.md
        """
        template_path = Path(__file__).parent / "templates" / "AGENTS_template.md"

        if not template_path.exists():
            # Fallback: create basic AGENTS.md
            content = """# AI Assistant Guide

This project uses Tigs for specification management.

See the spec files in specs/ for details.
"""
            target_path.write_text(content)
            return

        # Copy template
        shutil.copy(template_path, target_path)

    def _create_claude_commands(self) -> list[str]:
        """Create .claude/commands/ directory and copy slash command templates.

        Returns:
            List of created file paths
        """
        created = []

        # Create .claude/commands/ directory in root (not in specs/)
        claude_dir = self.root_path / ".claude"
        commands_dir = claude_dir / "commands"
        commands_dir.mkdir(parents=True, exist_ok=True)
        created.append(str(commands_dir))

        # Get templates directory
        templates_dir = Path(__file__).parent / "templates" / "commands"

        if not templates_dir.exists():
            # No templates to copy
            return created

        # Copy all command templates
        command_files = [
            "bootstrap.md",
            "change.md",
            "validate.md",
            "archive.md",
        ]

        for command_file in command_files:
            template_path = templates_dir / command_file
            if template_path.exists():
                target_path = commands_dir / command_file
                shutil.copy(template_path, target_path)
                created.append(str(target_path))

        return created

    def _generate_examples(self) -> list[str]:
        """Generate example specs for each type.

        Returns:
            List of created file paths
        """
        created = []

        # Example capability
        cap_dir = self.specs_path / "capabilities" / "example-feature"
        cap_dir.mkdir()
        cap_spec = cap_dir / "spec.md"
        cap_spec.write_text(self._get_example_capability())
        created.append(str(cap_spec))

        # Example data model
        dm_dir = self.specs_path / "data-models" / "example-model"
        dm_dir.mkdir()
        dm_spec = dm_dir / "schema.md"
        dm_spec.write_text(self._get_example_data_model())
        created.append(str(dm_spec))

        # Example API
        api_dir = self.specs_path / "api" / "example-api"
        api_dir.mkdir()
        api_spec = api_dir / "spec.md"
        api_spec.write_text(self._get_example_api())
        created.append(str(api_spec))

        # Example architecture
        arch_dir = self.specs_path / "architecture" / "example-component"
        arch_dir.mkdir()
        arch_spec = arch_dir / "spec.md"
        arch_spec.write_text(self._get_example_architecture())
        created.append(str(arch_spec))

        return created

    def _get_example_capability(self) -> str:
        """Get example capability spec content."""
        return """# Example Feature

## Purpose

This is an example behavioral specification showing the format for capabilities.

## Requirements

### Requirement: Basic Functionality

The system SHALL provide basic functionality for demonstration purposes.

#### Scenario: User performs action

- **WHEN** user initiates the action
- **THEN** system responds appropriately
- **AND** result is displayed to user

#### Scenario: Error handling

- **WHEN** invalid input is provided
- **THEN** system returns error message
- **AND** user is prompted to correct input

### Requirement: Configuration Support

The system SHALL allow configuration through settings.

#### Scenario: User updates settings

- **WHEN** user changes configuration
- **THEN** new settings are saved
- **AND** changes take effect immediately
"""

    def _get_example_data_model(self) -> str:
        """Get example data model spec content."""
        return """# Example Model

## Purpose

Demonstrates data model specification format with schema definition.

## Schema

### Entity: ExampleEntity

Represents an example entity in the system.

**Table**: `example_entities`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, NOT NULL | Unique identifier |
| `name` | VARCHAR(100) | NOT NULL | Entity name |
| `description` | TEXT | NULL | Optional description |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'active' | Entity status |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last update timestamp |

**Indexes**:
- `idx_example_name` ON `name`
- `idx_example_status` ON `status`

**Relationships**:
```typescript
ExampleEntity {
  hasMany: []
  belongsTo: []
}
```

## Validation Rules

### Rule: Name Requirements

- **MUST** be between 1 and 100 characters
- **MUST NOT** contain only whitespace
- **MUST** be unique within the system

### Rule: Status Values

- **MUST** be one of: 'active', 'inactive', 'archived'
- **MUST NOT** be null

## Related Specs

- **Capabilities**: `capabilities/example-feature/spec.md`
"""

    def _get_example_api(self) -> str:
        """Get example API spec content."""
        return """# Example API

## Purpose

Demonstrates API specification format with endpoint definitions.

## Base Configuration

**Base URL**: `/api/v1/examples`
**Authentication**: Bearer token required

## Endpoints

### GET /examples

List all examples with pagination.

**Authentication**: Required

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | No | Page number (default: 1) |
| `limit` | integer | No | Items per page (default: 20) |
| `status` | string | No | Filter by status |

**Responses**:

#### 200 OK - Success

```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Example 1",
      "status": "active"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 42
  }
}
```

#### 401 Unauthorized

```json
{
  "error": "UNAUTHORIZED",
  "message": "Authentication required"
}
```

### POST /examples

Create new example.

**Authentication**: Required

**Request**:

```json
{
  "name": "New Example",
  "description": "Optional description"
}
```

**Responses**:

#### 201 Created

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "New Example",
  "status": "active",
  "created_at": "2024-01-15T10:00:00Z"
}
```

#### 400 Bad Request

```json
{
  "error": "VALIDATION_ERROR",
  "message": "Invalid request data",
  "details": [
    {
      "field": "name",
      "message": "Name is required"
    }
  ]
}
```

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Missing or invalid authentication |
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `NOT_FOUND` | 404 | Resource not found |

## Related Specs

- **Capabilities**: `capabilities/example-feature/spec.md`
- **Data Models**: `data-models/example-model/schema.md`
"""

    def _get_example_architecture(self) -> str:
        """Get example architecture spec content."""
        return """# Example Component Architecture

## Purpose

Demonstrates architecture specification format with component definitions and design decisions.

## System Context

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTPS
       ↓
┌─────────────────────┐
│   Example Component │
│   (Node.js)         │
└──────┬──────────────┘
       │
       ↓
┌─────────────┐
│  Database   │
└─────────────┘
```

## Components

### Component: Example Service

**Type**: Microservice
**Technology**: Node.js + Express
**Responsibility**: Handles example entity operations

**Interfaces**:
- REST API (port 3000)
- Health check endpoint

**Dependencies**:
- PostgreSQL database
- Redis cache (optional)

**Scaling**: Horizontal (stateless, load balanced)

## Design Decisions

### Decision: Use Node.js for Service

**Status**: Accepted
**Date**: 2024-01-10

**Context**: Need to choose technology stack for new service.

**Decision**: Use Node.js with Express framework.

**Consequences**:
- ✅ Fast development with JavaScript ecosystem
- ✅ Good async I/O performance
- ⚠️ Requires discipline for type safety

**Alternatives Considered**:
1. **Python + FastAPI**: Rejected due to slower cold start
2. **Go**: Rejected due to team expertise gap

### Decision: PostgreSQL for Persistence

**Status**: Accepted
**Date**: 2024-01-10

**Context**: Need relational database for structured data.

**Decision**: Use PostgreSQL 15.

**Consequences**:
- ✅ ACID compliance
- ✅ Rich feature set
- ✅ Team familiarity

## Performance Requirements

| Metric | Target | Measurement |
|--------|--------|-------------|
| Response time (P95) | < 100ms | API endpoint latency |
| Throughput | 1000 req/s | Single instance capacity |
| Availability | 99.9% | Monthly uptime |

## Related Specs

- **Capabilities**: `capabilities/example-feature/spec.md`
- **APIs**: `api/example-api/spec.md`
- **Data Models**: `data-models/example-model/schema.md`
"""

    def archive_change(self, change_id: str, skip_validation: bool = False) -> Dict[str, Any]:
        """Archive a change by merging delta specs into main specs.

        Args:
            change_id: The change directory name
            skip_validation: Skip validation checks if True

        Returns:
            Dictionary with:
                - change_id: The change ID
                - merged: List of merged spec paths
                - archive_path: Where the change was archived

        Raises:
            FileNotFoundError: If change directory doesn't exist
            ValueError: If change validation fails
        """
        change_dir = self.specs_path / "changes" / change_id

        if not change_dir.exists():
            raise FileNotFoundError(
                f"Change '{change_id}' not found at {change_dir}. "
                f"Available changes: {self._list_changes()}"
            )

        # Validate change structure
        if not skip_validation:
            self._validate_change(change_dir)

        merged_specs = []

        # Map spec types to parsers and mergers
        type_handlers = {
            "capabilities": (CapabilityDeltaParser, CapabilityMerger, "spec.md"),
            "data-models": (DataModelDeltaParser, DataModelMerger, "schema.md"),
            "api": (ApiDeltaParser, ApiMerger, "spec.md"),
            "architecture": (ArchitectureDeltaParser, ArchitectureMerger, "spec.md"),
        }

        # Process each spec type
        for spec_type, (parser_class, merger_class, filename) in type_handlers.items():
            delta_dir = change_dir / spec_type
            if not delta_dir.exists():
                continue

            for spec_dir in delta_dir.iterdir():
                if not spec_dir.is_dir():
                    continue

                spec_name = spec_dir.name
                delta_file = spec_dir / filename

                if not delta_file.exists():
                    continue

                # Parse delta
                parser = parser_class(delta_file)
                delta = parser.parse()

                # Get or create main spec
                main_spec_dir = self.specs_path / spec_type / spec_name
                main_spec_file = main_spec_dir / filename

                if not main_spec_dir.exists():
                    main_spec_dir.mkdir(parents=True)

                # Merge changes
                merger = merger_class(main_spec_file)
                updated_content = merger.apply_changes(delta)

                # Write updated spec
                main_spec_file.write_text(updated_content)
                merged_specs.append(str(main_spec_file.relative_to(self.root_path)))

        # Archive the change directory
        archive_path = self._archive_change_directory(change_dir, change_id)

        return {
            "change_id": change_id,
            "merged": merged_specs,
            "archive_path": str(archive_path.relative_to(self.root_path))
        }

    def _list_changes(self) -> List[str]:
        """List all active changes."""
        changes_dir = self.specs_path / "changes"
        if not changes_dir.exists():
            return []

        changes = []
        for item in changes_dir.iterdir():
            if item.is_dir() and item.name != "archive":
                changes.append(item.name)

        return changes

    def _validate_change(self, change_dir: Path) -> None:
        """Validate change directory structure.

        Raises:
            ValueError: If validation fails
        """
        # Check for proposal.md
        proposal_file = change_dir / "proposal.md"
        if not proposal_file.exists():
            raise ValueError(
                f"Change validation failed: proposal.md not found in {change_dir.name}"
            )

        # Check for at least one delta spec
        has_deltas = False
        for spec_type in ["capabilities", "data-models", "api", "architecture"]:
            delta_dir = change_dir / spec_type
            if delta_dir.exists() and any(delta_dir.iterdir()):
                has_deltas = True
                break

        if not has_deltas:
            raise ValueError(
                f"Change validation failed: No delta specifications found in {change_dir.name}"
            )

    def _archive_change_directory(self, change_dir: Path, change_id: str) -> Path:
        """Move change directory to archive with date prefix.

        Args:
            change_dir: Path to the change directory
            change_id: The change ID

        Returns:
            Path to the archived directory
        """
        archive_dir = self.specs_path / "changes" / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)

        # Add date prefix
        date_prefix = datetime.now().strftime("%Y%m%d")
        archived_name = f"{date_prefix}-{change_id}"
        archive_path = archive_dir / archived_name

        # Move the directory
        shutil.move(str(change_dir), str(archive_path))

        return archive_path

    def validate_specs(
        self,
        spec_type: Optional[str] = None,
        change_id: Optional[str] = None,
        strict: bool = False
    ) -> Dict[str, List[ValidationResult]]:
        """Validate specifications.

        Args:
            spec_type: Optional type filter (capabilities, data-models, api, architecture)
            change_id: Optional change ID to validate only specs in a change
            strict: If True, warnings are treated as failures

        Returns:
            Dictionary mapping spec types to lists of ValidationResults

        Raises:
            FileNotFoundError: If specs/ directory doesn't exist
            ValueError: If spec_type is invalid
        """
        if not self.specs_path.exists():
            raise FileNotFoundError(
                f"Specs directory not found at {self.specs_path}. "
                f"Run 'tigs init-specs' first."
            )

        # Validate spec_type if provided
        if spec_type is not None:
            valid_types = list(self.SPEC_FILES.keys())
            if spec_type not in valid_types:
                raise ValueError(
                    f"Invalid spec type '{spec_type}'. "
                    f"Must be one of: {', '.join(valid_types)}"
                )

        # Determine base path
        if change_id:
            base_path = self.specs_path / "changes" / change_id
            if not base_path.exists():
                raise FileNotFoundError(f"Change '{change_id}' not found")
        else:
            base_path = self.specs_path

        # Map spec types to validators
        validators_map = {
            "capabilities": CapabilityValidator,
            "data-models": DataModelValidator,
            "api": ApiValidator,
            "architecture": ArchitectureValidator,
        }

        results: Dict[str, List[ValidationResult]] = {}
        types_to_validate = [spec_type] if spec_type else list(self.SPEC_FILES.keys())

        for stype in types_to_validate:
            type_results = []
            type_dir = base_path / stype

            if not type_dir.exists():
                results[stype] = []
                continue

            # Get validator class
            validator_class = validators_map[stype]
            expected_filename = self.SPEC_FILES[stype]

            # Scan for spec files
            for spec_dir in type_dir.iterdir():
                if not spec_dir.is_dir():
                    continue

                spec_file = spec_dir / expected_filename
                if not spec_file.exists():
                    continue

                # Validate the spec
                validator = validator_class(spec_file)
                result = validator.validate()
                type_results.append(result)

            results[stype] = type_results

        return results
