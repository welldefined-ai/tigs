# Specifications

This directory contains comprehensive specifications for the project, organized by type.

## Directory Structure

```
specs/
├── capabilities/     # Behavioral specifications
│   └── [name]/
│       └── spec.md   # Requirements and scenarios
├── data-models/      # Data structure specifications
│   └── [name]/
│       └── schema.md # Entity definitions and constraints
├── api/              # API specifications
│   └── [name]/
│       └── spec.md   # Endpoint definitions
├── architecture/     # Architecture specifications
│   └── [name]/
│       └── spec.md   # System design and decisions
└── changes/          # Incremental changes
    ├── [change-id]/  # Active changes
    └── archive/      # Completed changes
```

## Specification Types

### Capabilities
Behavioral requirements using OpenSpec-compatible format.
- Focus: What the system does
- Format: Requirements with Scenarios (WHEN/THEN/AND)
- Example: `capabilities/user-auth/spec.md`

### Data Models
Database schemas and entity definitions.
- Focus: Data structure and constraints
- Format: Table definitions with fields, indexes, relationships
- Example: `data-models/user/schema.md`

### API
REST/GraphQL endpoint specifications.
- Focus: Interface contracts
- Format: Endpoints with request/response schemas
- Example: `api/auth/spec.md`

### Architecture
System design and architectural decisions.
- Focus: Components and design rationale
- Format: Components with ADRs (Architecture Decision Records)
- Example: `architecture/auth-service/spec.md`

## Working with Specs

### Creating New Spec
```bash
tig new-spec [name] --type [capability|data-model|api|architecture]
```

### Listing Specs
```bash
tig list-specs                    # All specs
tig list-specs --type capabilities  # Filter by type
tig list-specs --json             # JSON output
```

### Viewing Spec
```bash
tig show-spec [name]                 # Auto-detect type
tig show-spec [name] --type api      # Specific type
```

### Validating Specs
```bash
tig validate-specs --all          # Validate everything
tig validate-specs --capabilities  # Validate capabilities
tig validate-specs my-change      # Validate change
```

## Change Management

### Creating Change
1. Create directory: `changes/[change-id]/`
2. Add `proposal.md` (why, what, impact)
3. Add `tasks.md` (implementation checklist)
4. Create delta specs in appropriate subdirectories

### Change Structure
```
changes/[change-id]/
├── proposal.md       # Why and what
├── tasks.md          # Implementation steps
├── capabilities/     # Behavioral changes (ADDED/MODIFIED/REMOVED)
├── data-models/      # Schema changes
├── api/              # Endpoint changes
└── architecture/     # Design changes
```

### Archiving Change
```bash
tig archive-change [change-id]    # Interactive confirmation
tig archive-change [change-id] -y  # Skip confirmation
```

This merges delta changes into main specs and moves to archive with date prefix.

## Format Rules

### All Specs Must Have
- `## Purpose` - What this spec describes
- Type-specific required sections (see below)
- `## Related Specs` - Cross-references (optional but recommended)

### Capabilities Format
```markdown
## Requirements
### Requirement: [Name]
SHALL statement

#### Scenario: [Description]
- **WHEN** condition
- **THEN** outcome
```

### Data Models Format
```markdown
## Schema
### Entity: [Name]
**Table**: `table_name`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
```

### API Format
```markdown
## Endpoints
### [METHOD] /path
**Request**: JSON
**Responses**: Status codes with examples
```

### Architecture Format
```markdown
## Components
### Component: [Name]
**Type**: Service/Library/Database

## Design Decisions
### Decision: [Title]
**Status**: Accepted/Rejected
```

## Best Practices

1. **Keep specs up to date** - Update specs when code changes
2. **Cross-reference specs** - Link related specifications
3. **Use delta changes** - Don't edit main specs directly, create changes
4. **Validate before archive** - Run validation before merging changes
5. **Write for humans and AI** - Clear, structured, parseable format

## Tools

This project uses [tig](https://github.com/welldefined-ai/tigs) for specification management.

For more information, see: `tig --help`
