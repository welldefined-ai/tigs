# /bootstrap - Bootstrap Existing Project

Generate baseline specifications for an existing codebase by analyzing the current implementation.

## Use Case

**When to use this command:**
- ✅ Introducing tigs to an existing project with working code
- ✅ Need to capture what's already implemented
- ✅ Want to create baseline specifications for future changes
- ✅ Retroactively adding spec-driven specifications

**When NOT to use:**
- ❌ Starting a new feature (use `/change` instead)
- ❌ Modifying existing behavior (use `/change` with MODIFIED)
- ❌ Working with specs that already exist

## Key Differences from /change

| Aspect | /bootstrap | /change |
|--------|-----------|---------|
| **Target** | `specs/<type>/` (main specs) | `specs/changes/<id>/` (delta specs) |
| **Format** | Standard sections (no delta operations) | Delta operations (ADDED/MODIFIED/REMOVED) |
| **Context** | Code already exists | Planning future implementation |
| **Workflow** | Code → Specs | Specs → Code |
| **Files** | Only spec files | proposal.md + tasks.md + spec files |

## Your Task

Analyze the existing codebase and create comprehensive specifications directly in the main `specs/` directory.

## Workflow

### Step 1: Understand the Codebase

**Ask the user:**
1. "What component/feature should I bootstrap?" (e.g., "user authentication system")
2. "Where is the relevant code?" (e.g., "src/auth/", "api/auth.py")
3. "Are there any existing docs I should reference?" (README, API docs, etc.)

**Analyze the code:**
- Read the implementation files
- Identify key components, APIs, data models
- Understand the behavior and requirements
- Look for edge cases and error handling

### Step 2: Determine Spec Types Needed

Based on the code analysis:

**Capabilities** - Always needed
- Extract behavioral requirements from code logic
- Infer scenarios from test cases or code paths
- Document what the system DOES

**Data Models** - If database/storage exists
- Extract schema from models/migrations
- Document entity relationships
- Add validation rules from code

**API** - If endpoints exist
- Document all routes/endpoints
- Extract request/response schemas
- Document authentication and error codes

**Architecture** - If needed
- Document system components
- Capture design decisions (from code comments, git history, team knowledge)
- Document dependencies and configuration

### Step 3: Create Directory Structure

**IMPORTANT**: Create directly in `specs/`, NOT in `specs/changes/`

```
specs/
├── capabilities/
│   └── <feature-name>/
│       └── spec.md          # ← Direct, no delta operations
├── data-models/
│   └── <model-name>/
│       └── schema.md        # ← Direct, no delta operations
├── api/
│   └── <api-name>/
│       └── spec.md          # ← Direct, no delta operations
└── architecture/
    └── <component-name>/
        └── spec.md          # ← Direct, no delta operations
```

### Step 4: Write Specifications

**Format**: Standard sections WITHOUT delta operation headers

---

#### **Capabilities Format** (specs/capabilities/<name>/spec.md)

```markdown
# <Feature Name>

## Purpose

<1-2 sentence description of what this capability does>

## Requirements

### Requirement: <Name>

The system SHALL <requirement statement extracted from code behavior>

#### Scenario: <Scenario description>

- **WHEN** <condition from code>
- **THEN** <expected result from code>
- **AND** <additional behavior>

#### Scenario: <Edge case>

- **WHEN** <error condition>
- **THEN** <error handling behavior>

### Requirement: <Another Requirement>

The system SHALL <another requirement>

#### Scenario: <Description>

- **WHEN** <condition>
- **THEN** <result>

## Related Specs

- **Data Models**: `data-models/<name>/schema.md`
- **APIs**: `api/<name>/spec.md`
- **Architecture**: `architecture/<name>/spec.md`
```

**Key Points:**
- NO `## ADDED Requirements` header - just `## Requirements`
- Requirements derived from actual code behavior
- Scenarios based on code paths, tests, or observed behavior
- Use SHALL for what the code currently does (not what it should do)

---

#### **Data Models Format** (specs/data-models/<name>/schema.md)

```markdown
# <Model Name>

## Purpose

<Description of what this data model represents>

## Schema

### Entity: <EntityName>

<Description>

**Table**: `actual_table_name_from_db`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, NOT NULL | <from schema> |
| `field_name` | TYPE | CONSTRAINTS | <from schema> |
| ... | ... | ... | ... |

**Indexes**:
- `actual_index_name` ON `field` <from database>
- ...

**Relationships**:
```typescript
EntityName {
  hasMany: [RelatedEntity]  // from code
  belongsTo: [ParentEntity]  // from code
}
```

### Entity: <AnotherEntity>

<Repeat for all entities in the model>

## Validation Rules

### Rule: <Rule Name>

<Extract from code validators/constraints>

- **MUST** <requirement from code>
- **MUST NOT** <constraint from code>

## Related Specs

- **Capabilities**: `capabilities/<name>/spec.md`
- **APIs**: `api/<name>/spec.md`
```

**Key Points:**
- NO `## ADDED Entities` header - just `## Schema`
- Extract exact schema from database/ORM models
- Document all constraints and indexes from actual schema
- Validation rules from code (validators, business logic)

---

#### **API Format** (specs/api/<name>/spec.md)

```markdown
# <API Name>

## Purpose

<What this API provides>

## Base Configuration

**Base URL**: `/actual/base/path` <from code>
**Authentication**: <actual auth method from code>

## Endpoints

### <METHOD> /actual/path

<Description from docstring or code comments>

**Authentication**: Required/Optional/None <from code>

**Path Parameters**: <if any from route definition>

| Parameter | Type | Description |
|-----------|------|-------------|
| `param` | type | <from route> |

**Query Parameters**: <if any from handler>

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `param` | type | Yes/No | <from code> |

**Request**: <if POST/PUT/PATCH>

```json
{
  "field": "value"  // from actual request schema
}
```

**Responses**:

#### <STATUS> <NAME> - <Description>

<From actual response in code>

```json
{
  "actual": "response",
  "from": "code"
}
```

<Repeat for all status codes the endpoint can return>

### <NEXT METHOD> /next/path

<Document all endpoints>

## Error Codes

<Extract from error handling code>

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `ERROR_CODE` | 4XX/5XX | <from error handler> |

## Related Specs

- **Capabilities**: `capabilities/<name>/spec.md`
- **Data Models**: `data-models/<name>/schema.md`
```

**Key Points:**
- NO `## ADDED Endpoints` header - just `## Endpoints`
- Extract ALL endpoints from route definitions
- Document actual request/response formats from code
- Include all error codes from error handling logic

---

#### **Architecture Format** (specs/architecture/<name>/spec.md)

```markdown
# <Component Name> Architecture

## Purpose

<What this component does in the system>

## System Context

<Optional diagram showing relationships>

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ↓
┌─────────────────────┐
│  This Component     │
└──────┬──────────────┘
       │
       ↓
┌─────────────┐
│ Dependencies│
└─────────────┘
```

## Components

### Component: <Name>

**Type**: <from code structure - Microservice/Library/Module/etc>
**Technology**: <actual tech stack with versions from package.json/requirements.txt>
**Responsibility**: <from code analysis>

**Interfaces**:
- <actual interfaces from code - ports, protocols, etc>

**Dependencies**:
- <actual dependencies from package manager>
- <external services the code connects to>

**Configuration**:
- <environment variables from code>
- <config files the code reads>

**Scaling**: <from deployment config or architecture>

**Monitoring**: <if instrumentation exists in code>

## Design Decisions

### Decision: <Technology/Pattern Choice>

**Status**: Accepted <since it's implemented>
**Date**: <from git history or ask user>

**Context**:
<Why this was needed - from git history, comments, or team knowledge>

**Decision**:
<What was chosen - evident from current code>

**Consequences**:
- ✅ <Benefits observed in the code>
- ⚠️ <Trade-offs visible in implementation>

**Alternatives Considered**:
<From git history, code comments, or team discussion>

## Performance Characteristics

<If measurable or documented>

| Metric | Current | Measurement |
|--------|---------|-------------|
| <metric> | <value> | <how measured> |

## Related Specs

- **Capabilities**: `capabilities/<name>/spec.md`
- **APIs**: `api/<name>/spec.md`
- **Data Models**: `data-models/<name>/schema.md`
```

**Key Points:**
- NO `## ADDED Components` header - just `## Components`
- Document actual technology stack with versions
- ADRs based on what's implemented (Status: Accepted)
- Design decisions from git history, comments, or team knowledge

---

### Step 5: Validate

```bash
tigs validate-specs --type capabilities  # or data-models, api, architecture
```

No need for `--change` flag since these are main specs.

### Step 6: Report

Tell the user:
- What specifications were created
- File locations in main specs/
- Validation status
- Suggestion to review and refine

## Complete Example

User: "Bootstrap our user authentication system"

You:
1. **Clarify**:
   - "Where is the auth code?" → `src/auth/` and `api/routes/auth.py`
   - "What database?" → PostgreSQL with `users` and `sessions` tables
   - "Any existing docs?" → README.md has basic overview

2. **Analyze code**:
   ```python
   # Read src/auth/*.py
   # Read api/routes/auth.py
   # Read migrations/001_users.sql
   # Read tests/test_auth.py for scenarios
   ```

3. **Identify specs needed**:
   ```
   ✅ Capabilities: user-authentication (login, logout, session management)
   ✅ Data Models: user (users table), session (sessions table)
   ✅ API: auth (login/logout endpoints)
   ❌ Architecture: Not needed unless auth is a separate service
   ```

4. **Create structure**:
   ```
   specs/
   ├── capabilities/
   │   └── user-authentication/
   │       └── spec.md
   ├── data-models/
   │   ├── user/
   │   │   └── schema.md
   │   └── session/
   │       └── schema.md
   └── api/
       └── auth/
           └── spec.md
   ```

5. **Write specs** (based on actual code):

**specs/capabilities/user-authentication/spec.md**:
```markdown
# User Authentication

## Purpose

Provides secure user authentication with email/password and session management.

## Requirements

### Requirement: User Login

The system SHALL authenticate users with email and password credentials.

#### Scenario: Successful login with valid credentials

- **WHEN** user provides valid email and password
- **THEN** system validates credentials against database
- **AND** system creates new session with JWT token
- **AND** system returns token with 24-hour expiration

#### Scenario: Failed login with invalid password

- **WHEN** user provides valid email but incorrect password
- **THEN** system returns 401 Unauthorized
- **AND** system increments failed login counter
- **AND** system locks account after 5 failed attempts within 15 minutes

#### Scenario: Failed login with non-existent email

- **WHEN** user provides email not in database
- **THEN** system returns 401 Unauthorized
- **AND** system uses same timing as invalid password (prevent user enumeration)

### Requirement: Session Management

The system SHALL maintain user sessions with JWT tokens.

#### Scenario: Accessing protected resource with valid token

- **WHEN** request includes valid unexpired JWT token
- **THEN** system validates token signature
- **AND** system allows access to protected resource

#### Scenario: Token expiration

- **WHEN** request includes expired JWT token
- **THEN** system returns 401 Unauthorized
- **AND** system requires user to re-authenticate

### Requirement: User Logout

The system SHALL allow users to end their session.

#### Scenario: Explicit logout

- **WHEN** user initiates logout
- **THEN** system invalidates session in database
- **AND** system adds token to blacklist (Redis)
- **AND** system returns success confirmation

## Related Specs

- **Data Models**: `data-models/user/schema.md`, `data-models/session/schema.md`
- **APIs**: `api/auth/spec.md`
```

**specs/data-models/user/schema.md**:
```markdown
# User

## Purpose

Stores user account information for authentication and authorization.

## Schema

### Entity: User

Represents a user account in the system.

**Table**: `users`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, NOT NULL | Unique user identifier |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | User email address (used for login) |
| `password_hash` | VARCHAR(255) | NOT NULL | Bcrypt hashed password (cost factor 12) |
| `failed_login_attempts` | INTEGER | NOT NULL, DEFAULT 0 | Counter for rate limiting |
| `locked_until` | TIMESTAMP | NULL | Account lock expiration time |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Account creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last modification timestamp |

**Indexes**:
- `idx_users_email` ON `email` (for fast login lookups)
- `idx_users_locked_until` ON `locked_until` (for cleanup job)

**Relationships**:
```typescript
User {
  hasMany: [Session]
  belongsTo: []
}
```

## Validation Rules

### Rule: Email Format

- **MUST** be valid email format (RFC 5322)
- **MUST** be unique across all users
- **MUST NOT** exceed 255 characters

### Rule: Password Requirements

- **MUST** be at least 8 characters
- **MUST** contain at least one uppercase letter
- **MUST** contain at least one lowercase letter
- **MUST** contain at least one digit
- **MUST** contain at least one special character

### Rule: Account Locking

- **MUST** lock account for 15 minutes after 5 failed login attempts
- **MUST** reset failed_login_attempts to 0 on successful login
- **MUST** allow login after lock period expires

## Related Specs

- **Capabilities**: `capabilities/user-authentication/spec.md`
- **APIs**: `api/auth/spec.md`
```

**specs/data-models/session/schema.md**:
```markdown
# Session

## Purpose

Tracks active user sessions for authentication state management.

## Schema

### Entity: Session

Represents an active user session.

**Table**: `sessions`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, NOT NULL | Unique session identifier |
| `user_id` | UUID | NOT NULL, FOREIGN KEY → users(id) | Associated user |
| `token_hash` | VARCHAR(64) | NOT NULL, UNIQUE | SHA-256 hash of JWT token |
| `ip_address` | VARCHAR(45) | NULL | Client IP address (for security) |
| `user_agent` | TEXT | NULL | Client user agent string |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Session start time |
| `expires_at` | TIMESTAMP | NOT NULL | Session expiration time |
| `last_activity_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last request timestamp |

**Indexes**:
- `idx_sessions_user_id` ON `user_id` (for user session queries)
- `idx_sessions_token_hash` ON `token_hash` (for token validation)
- `idx_sessions_expires_at` ON `expires_at` (for cleanup job)

**Relationships**:
```typescript
Session {
  hasMany: []
  belongsTo: [User]
}
```

## Validation Rules

### Rule: Session Expiration

- **MUST** expire 24 hours after creation
- **MUST** update last_activity_at on each authenticated request
- **MUST** be cleaned up by background job after expiration

### Rule: Token Storage

- **MUST** store only hash of JWT token, never plaintext
- **MUST** use SHA-256 for token hashing

## Related Specs

- **Capabilities**: `capabilities/user-authentication/spec.md`
- **APIs**: `api/auth/spec.md`
- **Data Models**: `data-models/user/schema.md`
```

**specs/api/auth/spec.md**:
```markdown
# Authentication API

## Purpose

Provides RESTful endpoints for user authentication and session management.

## Base Configuration

**Base URL**: `/api/v1/auth`
**Authentication**: Most endpoints require Bearer token (except login)

## Endpoints

### POST /login

Authenticate user and create session.

**Authentication**: None (public endpoint)

**Request**:

```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Request Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | Yes | User email address |
| `password` | string | Yes | User password (plaintext, hashed on server) |

**Responses**:

#### 200 OK - Success

User authenticated successfully.

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "created_at": "2024-01-15T10:00:00Z"
  },
  "expires_at": "2024-01-16T10:00:00Z"
}
```

#### 400 Bad Request - Validation Error

```json
{
  "error": "VALIDATION_ERROR",
  "message": "Invalid request data",
  "details": [
    {
      "field": "email",
      "message": "Invalid email format"
    }
  ]
}
```

#### 401 Unauthorized - Invalid Credentials

```json
{
  "error": "INVALID_CREDENTIALS",
  "message": "Email or password is incorrect"
}
```

#### 403 Forbidden - Account Locked

```json
{
  "error": "ACCOUNT_LOCKED",
  "message": "Account locked due to too many failed login attempts",
  "locked_until": "2024-01-15T10:15:00Z"
}
```

#### 429 Too Many Requests - Rate Limited

```json
{
  "error": "RATE_LIMITED",
  "message": "Too many requests. Try again in 60 seconds."
}
```

### POST /logout

End current user session.

**Authentication**: Required (Bearer token)

**Request**: Empty body

**Responses**:

#### 200 OK - Success

```json
{
  "message": "Logged out successfully"
}
```

#### 401 Unauthorized - Invalid Token

```json
{
  "error": "UNAUTHORIZED",
  "message": "Invalid or expired token"
}
```

### GET /session

Get current session information.

**Authentication**: Required (Bearer token)

**Responses**:

#### 200 OK - Success

```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com"
  },
  "session": {
    "created_at": "2024-01-15T10:00:00Z",
    "expires_at": "2024-01-16T10:00:00Z",
    "last_activity_at": "2024-01-15T14:30:00Z"
  }
}
```

#### 401 Unauthorized

```json
{
  "error": "UNAUTHORIZED",
  "message": "Invalid or expired token"
}
```

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Request data validation failed |
| `INVALID_CREDENTIALS` | 401 | Email or password incorrect |
| `UNAUTHORIZED` | 401 | Missing, invalid, or expired token |
| `ACCOUNT_LOCKED` | 403 | Account locked due to failed attempts |
| `RATE_LIMITED` | 429 | Too many requests from client |

## Related Specs

- **Capabilities**: `capabilities/user-authentication/spec.md`
- **Data Models**: `data-models/user/schema.md`, `data-models/session/schema.md`
```

6. **Validate**:
```bash
tigs validate-specs --type capabilities
tigs validate-specs --type data-models
tigs validate-specs --type api
```

7. **Report**:
```
✓ Bootstrapped user authentication system

Created main specifications:
  specs/capabilities/user-authentication/spec.md
  specs/data-models/user/schema.md
  specs/data-models/session/schema.md
  specs/api/auth/spec.md

All validations passed ✓

These specifications document the current implementation. You can now:
1. Review and refine the generated specs
2. Use them as baseline for future changes with /change
3. Keep them updated as the code evolves
```

## Important Guidelines

### Bootstrapping vs Designing

- **Bootstrapping (this command)**: Describe what EXISTS in code
  - Use SHALL for current behavior
  - Extract from actual implementation
  - Focus on accuracy to current code

- **Designing (/change)**: Describe what SHOULD exist
  - Use SHALL for future requirements
  - Plan before implementation
  - Focus on intended design

### Be Faithful to the Code

- Document what the code **actually does**, not what it should do
- If you find bugs or issues, note them but document the current behavior
- If code is unclear, ask the user for clarification
- Use actual field names, endpoints, error codes from the code

### Handle Incomplete Information

If code analysis doesn't provide enough detail:
- **DO**: Ask user for clarification
- **DO**: Note uncertainty in the spec ("Based on code analysis, appears to...")
- **DO**: Mark sections as needing review
- **DON'T**: Guess or make up details
- **DON'T**: Document ideal behavior that doesn't exist in code

### Iterative Bootstrapping

It's OK to:
- Start with one component/feature at a time
- Bootstrap incrementally as you understand more
- Revise specs as you discover more details
- Ask user to review and correct your analysis

## Tips

- **Start small**: Document one feature/component at a time
- **Read tests**: Test files are goldmines for scenarios and edge cases
- **Check migrations**: Database migrations show schema evolution
- **Review git history**: Commits and PR descriptions explain design decisions
- **Ask the team**: When code is unclear, ask the user/team for context
- **Use existing docs**: README, API docs, comments as starting points
- **Validate often**: Run validation after each spec to catch format errors

## Common Pitfalls

❌ **Don't** add delta operation headers (`## ADDED Requirements`)
   → These are main specs, not changes

❌ **Don't** create in `specs/changes/`
   → Create directly in `specs/<type>/`

❌ **Don't** capture ideal/future behavior
   → Capture current implementation only

❌ **Don't** skip validation rules
   → Extract from code validators

❌ **Don't** forget cross-references
   → Link related specs together

## Next Steps After Bootstrapping

Once initial specs are created:

1. **Review with team** - Ensure specs accurately reflect code
2. **Fix any discrepancies** - Update specs if code analysis was wrong
3. **Establish baseline** - These specs represent "current state"
4. **Future changes** - Use `/change` for new features/modifications
5. **Keep updated** - Update specs when code changes

The specs become the source of truth going forward!
