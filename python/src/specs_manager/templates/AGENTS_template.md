# AI Assistant Guide for Tigs Specifications

This guide helps AI assistants work effectively with the Tigs specification system.

## Overview

Tigs is a spec-driven development tool that maintains four types of specifications:

1. **Capabilities** (`capabilities/`) - Behavioral requirements with WHEN/THEN scenarios
2. **Data Models** (`data-models/`) - Database schemas and entity definitions
3. **API** (`api/`) - REST/GraphQL endpoint specifications
4. **Architecture** (`architecture/`) - System design and Architecture Decision Records (ADRs)

All new features and changes are tracked as **delta specifications** in `specs/changes/` before being merged into the main specs.

## Core Workflow

### 1. Create Change Proposal

When a user wants to add or modify features:

```bash
# Create change directory structure
specs/changes/<change-id>/
├── proposal.md       # Why, what, impact, success criteria
├── tasks.md          # Implementation checklist
└── <type>/<name>/    # Delta specifications
```

**Use slash command**: `/change`

### 2. Write Delta Specifications

Delta specs use operations to describe changes:
- `## ADDED` - New requirements/entities/endpoints/components
- `## MODIFIED` - Updates to existing items
- `## REMOVED` - Deletions (with reason and migration path)
- `## RENAMED` - Name changes only

**Note**: This is part of the `/change` workflow (Step 6: Write Detailed Delta Specs)

### 3. Validate Specifications

Before archiving, always validate:

```bash
tigs validate-specs --change <change-id>
```

**Use slash command**: `/validate`

### 4. Archive Change

After implementation is complete and tested:

```bash
tigs archive-change <change-id>
```

This merges delta specs into main specs and moves the change to `specs/changes/archive/`.

**Use slash command**: `/archive`

## Specification Formats

### Capabilities (spec.md)

Behavioral requirements with scenario-based validation.

**Required sections**: `## Purpose`, `## Requirements`

**Requirement format**:
```markdown
### Requirement: <Name>
The system SHALL/MUST/SHOULD/MAY <requirement>

#### Scenario: <Description>
- **WHEN** <condition>
- **THEN** <expected result>
- **AND** <additional result>
```

**Delta operations**:
```markdown
## ADDED Requirements
### Requirement: New Feature
...

## MODIFIED Requirements
### Requirement: Existing Feature
<Complete updated requirement with all scenarios>

## REMOVED Requirements
### Requirement: Deprecated Feature
**Reason**: <Why removing>
**Migration**: <How users should adapt>

## RENAMED Requirements
### Requirement: Old Name → New Name
```

**Cross-references**:
```markdown
## Related Specs
- **Data Models**: `data-models/<name>/schema.md`
- **APIs**: `api/<name>/spec.md`
```

### Data Models (schema.md)

Database schemas and entity definitions.

**Required sections**: `## Purpose`, `## Schema`

**Entity format**:
```markdown
### Entity: <Name>
<Description>

**Table**: `table_name`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, NOT NULL | Unique identifier |
| `name` | VARCHAR(100) | NOT NULL | Entity name |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Creation time |

**Indexes**:
- `idx_name` ON `name`

**Relationships**:
```typescript
EntityName {
  hasMany: [OtherEntity]
  belongsTo: [ParentEntity]
}
```
```

**Validation rules**:
```markdown
## Validation Rules

### Rule: Name Requirements
- **MUST** be between 1 and 100 characters
- **MUST NOT** contain only whitespace
```

**Delta operations**:
```markdown
## ADDED Entities
### Entity: NewEntity
...

## MODIFIED Entities
### Entity: ExistingEntity
<Complete updated schema>

## REMOVED Entities
### Entity: DeprecatedEntity
**Reason**: <Why removing>
**Migration**: <Data migration plan>
```

### API (spec.md)

REST/GraphQL endpoint specifications.

**Required sections**: `## Purpose`, `## Endpoints`

**Endpoint format**:
```markdown
### GET /path/{id}
<Description>

**Authentication**: Required/Optional/None

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Resource identifier |

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `filter` | string | No | Filter criteria |

**Request** (for POST/PUT/PATCH):
```json
{
  "field": "value"
}
```

**Responses**:

#### 200 OK - Success
```json
{
  "data": {...}
}
```

#### 400 Bad Request
```json
{
  "error": "ERROR_CODE",
  "message": "Error description"
}
```
```

**Delta operations**:
```markdown
## ADDED Endpoints
### POST /new-resource
...

## MODIFIED Endpoints
### GET /existing-resource
<Complete updated endpoint spec>

## REMOVED Endpoints
### DELETE /deprecated-endpoint
**Reason**: <Why removing>
**Migration**: <Alternative endpoint>
```

### Architecture (spec.md)

System design and Architecture Decision Records.

**Required sections**: `## Purpose`, `## Components`

**Component format**:
```markdown
### Component: <Name>
**Type**: Microservice/Library/Database/Queue/etc
**Technology**: Node.js/Python/PostgreSQL/etc
**Responsibility**: <What it does>

**Interfaces**:
- REST API (port 3000)
- gRPC service

**Dependencies**:
- Database: PostgreSQL
- Cache: Redis
- Message Queue: RabbitMQ

**Scaling**: Horizontal/Vertical/Stateless
```

**ADR format** (in `## Design Decisions`):
```markdown
### Decision: <Title>
**Status**: Proposed/Accepted/Rejected/Superseded/Deprecated
**Date**: YYYY-MM-DD

**Context**: <Situation and problem>

**Decision**: <What we decided>

**Consequences**:
- ✅ Benefit 1
- ✅ Benefit 2
- ⚠️ Trade-off or concern
- ❌ Drawback

**Alternatives Considered**:
1. **Option A**: Rejected because <reason>
2. **Option B**: Rejected because <reason>
```

**Delta operations**:
```markdown
## ADDED Components
### Component: NewService
...

## MODIFIED Components
### Component: ExistingService
<Complete updated component spec>

## REMOVED Components
### Component: DeprecatedService
**Reason**: <Why removing>
**Migration**: <Replacement or migration path>
```

## Common Tasks

### Task: User wants to add a new feature

1. **Clarify requirements** - Ask 1-2 questions if needed
2. **Choose change ID** - Use kebab-case: `add-feature-name`
3. **Create change structure**:
   ```
   specs/changes/add-feature-name/
   ├── proposal.md
   ├── tasks.md
   ├── capabilities/<name>/spec.md (ADDED requirements)
   ├── data-models/<name>/schema.md (if data storage needed)
   ├── api/<name>/spec.md (if API exposure needed)
   └── architecture/<name>/spec.md (if new services/components)
   ```
4. **Write comprehensive specs** - Include scenarios, validation rules, cross-references
5. **Validate** - `tigs validate-specs --change add-feature-name`
6. **Report** - Summarize what was created and next steps

**Use**: `/change`

### Task: User wants to modify existing behavior

1. **Identify affected specs** - Which specs need updates?
2. **Create change** with `update-` prefix: `update-feature-name`
3. **Write MODIFIED delta specs** - Complete updated content
4. **Document breaking changes** in proposal.md with **BREAKING** marker
5. **Validate and report**

**Use**: `/change`

### Task: User wants to remove deprecated features

1. **Create change** with `remove-` prefix: `remove-feature-name`
2. **Write REMOVED delta specs** with:
   - **Reason**: Why removing
   - **Migration**: How users should adapt
3. **Document in proposal.md** - Impact analysis
4. **Validate and report**

**Use**: `/change`

### Task: User asks to validate specs

1. **Determine scope**:
   - All specs: `--all`
   - Specific type: `--type capabilities`
   - Change only: `--change <change-id>`
2. **Run validation**: `tigs validate-specs <options>`
3. **Report results** - Summarize errors/warnings
4. **Suggest fixes** if errors found

**Use**: `/validate`

### Task: User wants to archive a change

1. **Validate first** - Must pass validation
2. **Review what will be archived** - `tigs list-specs --change <change-id>`
3. **Run archive** - `tigs archive-change <change-id>`
4. **Verify merge** - Check main specs were updated correctly
5. **Report** - Summarize merged specs and archive location

**Use**: `/archive`

## Best Practices

### Writing Good Requirements

- **Use modal verbs consistently**:
  - **SHALL/MUST** - Mandatory requirements
  - **SHOULD** - Recommended but not mandatory
  - **MAY** - Optional capabilities

- **Write clear scenarios**:
  - Start with **WHEN** (precondition)
  - Follow with **THEN** (expected result)
  - Add **AND** for additional results
  - Be specific and testable

- **One requirement per requirement block** - Don't combine unrelated functionality

### Change Management

- **Keep changes focused** - Aim for 1-2 weeks of work maximum
- **Write proposal.md first** - Clarifies scope before writing specs
- **Break down large changes** - Multiple small changes > one huge change
- **Cross-reference related specs** - Helps maintain consistency
- **Validate early and often** - Catch format errors before implementation

### Delta Specifications

- **ADDED**: Complete new content, ready to append to main spec
- **MODIFIED**: Include ALL content for the item, not just changes
- **REMOVED**: Document reason and migration path, not just deletion
- **RENAMED**: Use for name changes only; combine with MODIFIED if content also changes

### Documentation Quality

- **Be specific** - Vague requirements lead to implementation ambiguity
- **Include examples** - JSON examples for API, field values for data models
- **Document edge cases** - Error scenarios, validation rules, constraints
- **Maintain cross-references** - Keep Related Specs sections up to date

## Validation Rules

### All Spec Types

- ✅ **ERROR**: Required sections missing
- ✅ **ERROR**: Wrong heading levels or format
- ⚠️ **WARNING**: Conventions not followed (still valid but not ideal)

### Capabilities

- ✅ Requirement format: `### Requirement: <Name>`
- ⚠️ Modal verbs: Should use SHALL/MUST/SHOULD/MAY
- ✅ Scenario format: `#### Scenario: <Description>`
- ⚠️ Scenario keywords: Should include **WHEN**/**THEN**/**AND**

### Data Models

- ✅ Entity format: `### Entity: <Name>`
- ⚠️ Table definition: Should have `**Table**: \`name\``
- ⚠️ Field table: Should have proper markdown table structure

### API

- ✅ Endpoint format: `### METHOD /path`
- ✅ Valid HTTP methods: GET/POST/PUT/PATCH/DELETE
- ⚠️ Response codes: Should use format `#### 200 OK`

### Architecture

- ✅ Component format: `### Component: <Name>`
- ⚠️ Component metadata: Should have **Type** and **Responsibility**
- ⚠️ ADR format: Should follow Status/Context/Decision/Consequences structure

## CLI Commands

AI assistants should be familiar with these commands:

```bash
# Initialize specs directory structure
tigs init-specs [--examples] [--path PATH]

# List all specifications
tigs list-specs [--type TYPE] [--json]

# Show specification content
tigs show-spec NAME [--type TYPE] [--json]

# Validate specifications
tigs validate-specs --all
tigs validate-specs --type capabilities
tigs validate-specs --change CHANGE_ID
tigs validate-specs --all --strict  # Warnings as errors

# Archive change (merge delta specs into main)
tigs archive-change CHANGE_ID [--no-validate] [--yes]
```

## Slash Commands

When working in Claude Code, use these slash commands:

- **/change** - Create comprehensive change proposal with detailed specifications
- **/validate** - Validate specification format and structure
- **/archive** - Archive a completed change

Each command provides step-by-step guidance for the task.

## Working with OpenSpec Compatibility

Tigs capabilities follow OpenSpec behavioral spec format:
- Same `## Requirements` structure
- Same scenario format with **WHEN**/**THEN**/**AND**
- Same modal verb usage (SHALL/MUST/SHOULD/MAY)

This means:
- ✅ OpenSpec capability specs can be used as-is in Tigs
- ✅ Tigs capability specs are valid OpenSpec behavioral specs
- ✅ Tools and processes built for OpenSpec work with Tigs capabilities

## Tips for AI Assistants

1. **Always validate before archiving** - Use `/validate` or `tigs validate-specs`
2. **Start with proposal.md** - Clarify "why" before diving into "what"
3. **Use examples** - Include concrete examples in specs (JSON, SQL, code snippets)
4. **Think cross-cutting** - Consider all four spec types when analyzing features
5. **Maintain traceability** - Use Related Specs sections to link connected specs
6. **Be proactive** - Suggest validation, identify missing specs, recommend best practices

## Example Session

```
User: "I want to add user authentication with JWT tokens"