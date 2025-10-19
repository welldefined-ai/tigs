# /new-spec - Create New Specification

Analyze the user's requirement and create comprehensive specifications across multiple dimensions.

## Your Task

1. **Understand the requirement**: Ask 1-2 clarifying questions if the request is ambiguous
2. **Identify affected spec types**: Determine which of these are needed:
   - `capabilities/` - Behavioral requirements (always needed for features)
   - `data-models/` - Database schemas, entities (if data storage involved)
   - `api/` - REST/GraphQL endpoints (if API exposure needed)
   - `architecture/` - System design, components (if new services/patterns involved)
3. **Create delta specs** in `specs/changes/<change-id>/` following the format
4. **Validate** the created specs using `tigs validate-specs --change <change-id>`
5. **Report** what was created and next steps

## Workflow

### Step 1: Analyze Requirement
```
User requirement: "Add user authentication with email and password"

Analysis:
- Capabilities: Yes (login, logout, session management behaviors)
- Data Models: Yes (User entity, Session entity)
- API: Yes (POST /auth/login, POST /auth/logout, GET /auth/session)
- Architecture: Maybe (if introducing auth service, otherwise No)
```

### Step 2: Choose Change ID
- Use kebab-case, verb-led
- Examples: `add-user-auth`, `update-payment-flow`, `remove-legacy-api`

### Step 3: Create Change Structure
```
specs/changes/<change-id>/
├── proposal.md
├── tasks.md
└── capabilities/
    └── <spec-name>/
        └── spec.md
```

### Step 4: Write Specifications

**Capabilities Format** (specs/changes/<change-id>/capabilities/<name>/spec.md):
```markdown
# <Feature Name>

## Purpose
<Brief description>

## ADDED Requirements

### Requirement: <Name>
The system SHALL <requirement>

#### Scenario: <Description>
- **WHEN** <condition>
- **THEN** <expected result>
- **AND** <additional result>

## Related Specs
- **Data Models**: `data-models/<name>/schema.md`
- **APIs**: `api/<name>/spec.md`
```

**Data Models Format** (specs/changes/<change-id>/data-models/<name>/schema.md):
```markdown
# <Model Name>

## Purpose
<Brief description>

## ADDED Entities

### Entity: <Name>
<Description>

**Table**: `table_name`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | ... |
| ... | ... | ... | ... |
```

**API Format** (specs/changes/<change-id>/api/<name>/spec.md):
```markdown
# <API Name>

## Purpose
<Brief description>

## ADDED Endpoints

### POST /path
<Description>

**Request**:
```json
{ "field": "value" }
```

**Responses**:

#### 200 OK - Success
```json
{ "result": "data" }
```
```

**Architecture Format** (specs/changes/<change-id>/architecture/<name>/spec.md):
```markdown
# <Component> Architecture

## Purpose
<Brief description>

## ADDED Components

### Component: <Name>
**Type**: Microservice/Library/etc
**Responsibility**: <What it does>
```

### Step 5: Validate
Run: `tigs validate-specs --change <change-id>`

Fix any errors before archiving.

### Step 6: Report
Tell the user:
- What specs were created
- File locations
- How to archive: `tigs archive-change <change-id>`

## Important Rules

1. **Use delta operations**: ADDED/MODIFIED/REMOVED/RENAMED
2. **Include scenarios**: Every requirement needs at least one scenario
3. **Use modal verbs**: SHALL/MUST for requirements
4. **Bold keywords**: **WHEN**/**THEN**/**AND** in scenarios
5. **Cross-reference**: Link related specs

## Example Output

```
Created specifications for "add-user-auth":

📁 specs/changes/add-user-auth/
  ├── proposal.md
  ├── tasks.md
  ├── capabilities/user-authentication/spec.md
  ├── data-models/user/schema.md
  └── api/auth/spec.md

Next steps:
1. Review the generated specs
2. Validate: tigs validate-specs --change add-user-auth
3. Archive: tigs archive-change add-user-auth
```

## Tips

- Start simple: Only create specs that are truly needed
- Be specific: Use concrete examples in scenarios
- Think end-to-end: Consider the full user journey
- Validate early: Run validation after creating each spec
