# Specs Management System

## Purpose

The Specs Management capability extends tig to support comprehensive specification management across multiple dimensions: behavioral requirements, data models, API contracts, and system architecture. This system enables teams to maintain structured, version-controlled specifications that evolve alongside code, bridging the gap between high-level design and implementation details.

## Requirements

### Requirement: Multi-dimensional Specification Support

The system SHALL support four distinct types of specifications, each with its own format optimized for its domain.

#### Scenario: Initializing specification structure

- **WHEN** user runs `tig init-specs` in their project directory
- **THEN** create `specs/` directory with four subdirectories:
  - `capabilities/` for behavioral specifications
  - `data-models/` for database schemas and entities
  - `api/` for REST/GraphQL endpoint definitions
  - `architecture/` for system design and components
- **AND** create `changes/` directory for incremental modifications
- **AND** generate `specs/README.md` with usage instructions

#### Scenario: Generating with examples

- **WHEN** user runs `tig init-specs --examples`
- **THEN** create specification structure
- **AND** populate each subdirectory with template examples
- **AND** include sample change proposal in `changes/`

### Requirement: Capabilities Specification Format

The system SHALL support behavioral specifications using OpenSpec-compatible format.

#### Scenario: Validating capabilities spec structure

- **WHEN** validating a capabilities spec
- **THEN** verify file contains `## Purpose` section
- **AND** verify file contains `## Requirements` section
- **AND** verify each requirement uses `### Requirement: [Name]` header
- **AND** verify each requirement contains SHALL or MUST statement
- **AND** verify each requirement has at least one `#### Scenario:` section
- **AND** verify scenarios use **WHEN**, **THEN**, **AND** keywords

#### Scenario: Example capabilities spec

- **GIVEN** a valid capabilities spec format:
  ```markdown
  # User Authentication

  ## Purpose
  Handles user authentication and session management.

  ## Requirements

  ### Requirement: Email Login
  The system SHALL authenticate users via email and password.

  #### Scenario: Successful login
  - **WHEN** user provides valid credentials
  - **THEN** create session token
  - **AND** return JWT token
  ```
- **THEN** this format SHALL be accepted by validation

### Requirement: Data Models Specification Format

The system SHALL support structured data model definitions with schemas, constraints, and relationships.

#### Scenario: Validating data model structure

- **WHEN** validating a data-models spec
- **THEN** verify file contains `## Purpose` section
- **AND** verify file contains `## Schema` section with entity definition
- **AND** verify entity includes table name and field definitions
- **AND** verify fields specify type, constraints, and description
- **AND** optionally verify `## Validation Rules` section
- **AND** optionally verify `## Related Specs` cross-references

#### Scenario: Example data model spec

- **GIVEN** a valid data model spec format:
  ```markdown
  # User Model

  ## Purpose
  Core user entity for authentication and profiles.

  ## Schema

  ### Entity: User

  **Table**: `users`

  | Field | Type | Constraints | Description |
  |-------|------|-------------|-------------|
  | id | UUID | PRIMARY KEY | Unique identifier |
  | email | VARCHAR(255) | UNIQUE, NOT NULL | Email address |

  ## Validation Rules

  ### Rule: Email Format
  - **MUST** match RFC 5322 format
  - **MUST** be unique
  ```
- **THEN** this format SHALL be accepted by validation

### Requirement: API Specification Format

The system SHALL support API endpoint definitions with request/response schemas and status codes.

#### Scenario: Validating API spec structure

- **WHEN** validating an API spec
- **THEN** verify file contains `## Purpose` section
- **AND** verify file contains `## Endpoints` section
- **AND** verify each endpoint specifies HTTP method and path
- **AND** verify each endpoint includes request and response formats
- **AND** verify each endpoint documents status codes
- **AND** optionally verify `## Error Codes` section

#### Scenario: Example API spec

- **GIVEN** a valid API spec format:
  ```markdown
  # Authentication API

  ## Purpose
  Provides REST endpoints for user authentication.

  ## Endpoints

  ### POST /login
  Authenticate user and create session.

  **Request**:
  ```json
  {
    "email": "user@example.com",
    "password": "password"
  }
  ```

  **Responses**:

  #### 200 OK - Success
  ```json
  {
    "token": "eyJ...",
    "user": {...}
  }
  ```

  #### 401 Unauthorized
  Invalid credentials.
  ```
- **THEN** this format SHALL be accepted by validation

### Requirement: Architecture Specification Format

The system SHALL support architecture documentation with component definitions and design decisions.

#### Scenario: Validating architecture spec structure

- **WHEN** validating an architecture spec
- **THEN** verify file contains `## Purpose` section
- **AND** verify file contains `## Components` section
- **AND** verify components specify type, technology, and responsibilities
- **AND** optionally verify `## Design Decisions` section with ADR format
- **AND** optionally verify `## Related Specs` cross-references

#### Scenario: Example architecture spec

- **GIVEN** a valid architecture spec format:
  ```markdown
  # Authentication Service Architecture

  ## Purpose
  Defines authentication service design.

  ## Components

  ### Component: Auth Service
  **Type**: Microservice
  **Technology**: Node.js + Express
  **Responsibility**: User authentication

  ## Design Decisions

  ### Decision: JWT for Sessions
  **Status**: Accepted
  **Date**: 2024-01-10

  **Context**: Need stateless authentication.

  **Decision**: Use JWT tokens with 15min expiration.

  **Consequences**:
  - ✅ Stateless, easy to scale
  - ⚠️ Cannot revoke before expiration
  ```
- **THEN** this format SHALL be accepted by validation

### Requirement: Specification Listing

The system SHALL provide commands to list and discover existing specifications.

#### Scenario: Listing all specifications

- **WHEN** user runs `tig list-specs`
- **THEN** display all specifications grouped by type
- **AND** show count for each category
- **AND** format output as:
  ```
  Capabilities (2):
    - user-auth
    - payment-processing

  Data Models (3):
    - user
    - transaction
    - session
  ```

#### Scenario: Filtering by type

- **WHEN** user runs `tig list-specs --type capabilities`
- **THEN** display only capabilities specifications
- **AND** exclude other types

#### Scenario: JSON output

- **WHEN** user runs `tig list-specs --json`
- **THEN** output specifications as JSON array
- **AND** include metadata (path, type, last modified)

### Requirement: Specification Display

The system SHALL provide commands to view specification content.

#### Scenario: Showing specific specification

- **WHEN** user runs `tig show-spec user-auth`
- **THEN** search for spec named "user-auth" across all types
- **AND** display formatted content to terminal
- **AND** highlight Markdown syntax for readability

#### Scenario: Disambiguating with type

- **WHEN** user runs `tig show-spec user --type data-models`
- **THEN** specifically show `data-models/user/schema.md`
- **AND** skip searching other directories

#### Scenario: JSON output for processing

- **WHEN** user runs `tig show-spec user-auth --json`
- **THEN** output spec content as structured JSON
- **AND** include metadata and parsed sections

### Requirement: Incremental Change Management

The system SHALL support delta-based changes across all specification types.

#### Scenario: Creating change proposal structure

- **WHEN** user creates directory `changes/add-oauth-support/`
- **THEN** allow subdirectories matching main spec structure:
  - `capabilities/` for behavioral changes
  - `data-models/` for schema changes
  - `api/` for endpoint changes
  - `architecture/` for design changes
- **AND** require `proposal.md` describing why and what
- **AND** optionally include `tasks.md` for implementation checklist

#### Scenario: Capabilities change uses delta format

- **WHEN** creating change in `changes/[id]/capabilities/[name]/spec.md`
- **THEN** support OpenSpec delta operations:
  - `## ADDED Requirements` for new requirements
  - `## MODIFIED Requirements` for updated requirements
  - `## REMOVED Requirements` for deleted requirements
  - `## RENAMED Requirements` for renamed requirements
- **AND** each section SHALL use same format as main spec

#### Scenario: Data models change describes modifications

- **WHEN** creating change in `changes/[id]/data-models/[name]/schema.md`
- **THEN** support delta format:
  ```markdown
  ## ADDED Models
  ### Model: OAuthToken
  [Full schema definition]

  ## MODIFIED Models
  ### Model: User
  **Changes**:
  - Added field: `oauth_provider` (VARCHAR(50))
  - Added index: `idx_oauth` ON (`oauth_provider`, `oauth_id`)
  ```

#### Scenario: API change describes endpoint modifications

- **WHEN** creating change in `changes/[id]/api/[name]/spec.md`
- **THEN** support delta format:
  ```markdown
  ## ADDED Endpoints
  ### POST /oauth/google
  [Full endpoint definition]

  ## MODIFIED Endpoints
  ### POST /login
  **Changes**:
  - Added optional field: `oauth_token`
  - Added error code: `OAUTH_ERROR`
  ```

### Requirement: Change Validation

The system SHALL validate change proposals before allowing archive.

#### Scenario: Validating change completeness

- **WHEN** user runs `tig validate-specs my-change`
- **THEN** verify `proposal.md` exists and is non-empty
- **AND** verify at least one delta spec exists
- **AND** validate each delta spec according to its type
- **AND** report all validation errors with file paths

#### Scenario: Validating delta operations

- **WHEN** validating capabilities delta with MODIFIED operation
- **THEN** verify referenced requirement exists in main spec
- **AND** verify header name matches exactly (case-sensitive, whitespace-trimmed)

#### Scenario: Validating cross-references

- **WHEN** spec contains `## Related Specs` section
- **THEN** verify each referenced spec file exists
- **AND** report broken references as warnings

### Requirement: Change Archival

The system SHALL merge completed changes into main specifications and move to archive.

#### Scenario: Archiving completed change

- **WHEN** user runs `tig archive-change add-oauth-support`
- **THEN** validate change completeness first
- **AND** apply delta operations to main specs
- **AND** move change directory to `changes/archive/2024-01-15-add-oauth-support/`
- **AND** display summary of modifications

#### Scenario: Applying capabilities deltas

- **WHEN** archiving change with capabilities deltas
- **THEN** apply operations in order: RENAMED → REMOVED → MODIFIED → ADDED
- **AND** for ADDED, append requirement to main spec
- **AND** for MODIFIED, replace entire requirement block
- **AND** for REMOVED, delete requirement from main spec
- **AND** for RENAMED, update requirement header

#### Scenario: Applying data model deltas

- **WHEN** archiving change with data-models deltas
- **THEN** if ADDED model, create new schema file
- **AND** if MODIFIED model, update field definitions
- **AND** preserve schema evolution in `migrations.md`

#### Scenario: Applying API deltas

- **WHEN** archiving change with API deltas
- **THEN** if ADDED endpoint, append to spec
- **AND** if MODIFIED endpoint, update definition
- **AND** maintain endpoint ordering

#### Scenario: Skipping spec updates

- **WHEN** user runs `tig archive-change my-change --skip-specs`
- **THEN** skip all delta merging operations
- **AND** only move change to archive
- **AND** display warning that specs were not updated

#### Scenario: Confirming before archive

- **WHEN** user runs `tig archive-change my-change` without `--yes` flag
- **THEN** display change summary and affected specs
- **AND** prompt for confirmation with default "yes"
- **AND** abort if user declines

### Requirement: Validation Command

The system SHALL provide comprehensive validation across all specification types.

#### Scenario: Validating all specs

- **WHEN** user runs `tig validate-specs --all`
- **THEN** validate all specs in `capabilities/`, `data-models/`, `api/`, `architecture/`
- **AND** validate all changes in `changes/` (excluding archive)
- **AND** display summary with error count per category

#### Scenario: Validating specific type

- **WHEN** user runs `tig validate-specs --capabilities`
- **THEN** validate only specs in `capabilities/` directory
- **AND** skip other types

#### Scenario: Strict validation mode

- **WHEN** user runs `tig validate-specs --strict`
- **THEN** enable additional checks:
  - Verify all cross-references are valid
  - Check for duplicate requirement names
  - Validate consistent terminology
- **AND** fail if any warnings are found

#### Scenario: Validation report format

- **WHEN** validation completes
- **THEN** display results grouped by file
- **AND** show error level (ERROR/WARNING/INFO)
- **AND** include line numbers when applicable
- **AND** exit with non-zero code if errors found

### Requirement: Template Generation

The system SHALL provide templates for creating new specifications.

#### Scenario: Generating capability template

- **WHEN** user runs `tig new-spec user-auth --type capability`
- **THEN** create `specs/capabilities/user-auth/spec.md`
- **AND** populate with template including Purpose and Requirements sections
- **AND** include example requirement and scenario

#### Scenario: Generating data model template

- **WHEN** user runs `tig new-spec user --type data-model`
- **THEN** create `specs/data-models/user/schema.md`
- **AND** populate with template including Schema section
- **AND** include example field definitions and validation rules

#### Scenario: Generating API template

- **WHEN** user runs `tig new-spec auth --type api`
- **THEN** create `specs/api/auth/spec.md`
- **AND** populate with template including Endpoints section
- **AND** include example endpoint with request/response

#### Scenario: Generating architecture template

- **WHEN** user runs `tig new-spec auth-service --type architecture`
- **THEN** create `specs/architecture/auth-service/spec.md`
- **AND** populate with template including Components and Design Decisions
- **AND** include example component and ADR

### Requirement: Cross-reference Validation

The system SHALL detect and report broken references between specifications.

#### Scenario: Validating related specs links

- **WHEN** spec contains:
  ```markdown
  ## Related Specs
  - **Capabilities**: `capabilities/user-auth/spec.md`
  - **Data Models**: `data-models/user/schema.md`
  ```
- **THEN** verify each referenced file exists
- **AND** report missing files as ERROR
- **AND** suggest correct paths if similar files found

#### Scenario: Building dependency graph

- **WHEN** user runs `tig validate-specs --show-deps`
- **THEN** parse all cross-references
- **AND** build directed graph of dependencies
- **AND** display or output graph in DOT format
- **AND** detect circular dependencies

## Why These Decisions

**Four-type taxonomy**: Separates concerns - behavior, data, interface, design - allowing each to use optimal format without compromising others.

**OpenSpec compatibility for capabilities**: Maintains interoperability with existing OpenSpec tooling and allows gradual adoption.

**Delta-based changes**: Preserves change history and enables review of what changed, not just the new state.

**Strict validation**: Catches errors early and enforces consistency, critical for multi-person teams and AI-generated content.

**Self-documenting**: Using tig's own spec format to define tig demonstrates format expressiveness and serves as living example.
