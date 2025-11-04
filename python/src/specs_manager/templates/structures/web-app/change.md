# /change - Create Change Proposal

Create a comprehensive change proposal with detailed specifications for adding, modifying, or removing features.

## Your Task

Guide the user through creating a complete change proposal with:
1. **Analyze requirement** - Understand what needs to change and why
2. **Identify spec types** - Determine which specifications are affected
3. **Write proposal.md** - Document why, what, impact, success criteria
4. **Write tasks.md** - Create implementation checklist
5. **Write detailed delta specs** - Create comprehensive specifications for all affected types
6. **Validate** - Ensure all specs follow the correct format

## When to Create a Change

**Create a change for:**
- ✅ New features or capabilities
- ✅ Modifying existing behavior
- ✅ Breaking changes (API, schema, architecture)
- ✅ Removing deprecated features
- ✅ Architecture changes

**Don't create a change for:**
- ❌ Bug fixes (restoring intended behavior)
- ❌ Typos or formatting
- ❌ Non-breaking dependency updates
- ❌ Adding tests for existing behavior

## Workflow

### Step 1: Analyze Requirement

Ask 1-2 clarifying questions if needed, then determine which spec types are affected:

**Spec Type Decision Matrix:**
```
User requirement: "Add user authentication with email and password"

Analysis:
- ✅ Capabilities: Yes (login, logout, session management behaviors)
- ✅ Data Models: Yes (User entity, Session entity)
- ✅ API: Yes (POST /auth/login, POST /auth/logout, GET /auth/session)
- ⚠️ Architecture: Maybe (only if introducing new auth service)
```

**Guidelines:**
- **Capabilities**: Always needed for features (behavioral requirements)
- **Data Models**: Needed if data storage/schema changes involved
- **API**: Needed if exposing endpoints or modifying API contracts
- **Architecture**: Needed if introducing new services, components, or design decisions

### Step 2: Choose Change ID

- Use kebab-case
- Verb-led: `add-`, `update-`, `remove-`, `refactor-`
- Examples: `add-user-auth`, `update-payment-api`, `remove-legacy-endpoints`

### Step 3: Create Directory Structure

```
specs/changes/<change-id>/
├── proposal.md           # Why, what, impact, success criteria
├── tasks.md             # Implementation checklist
├── capabilities/        # Behavioral requirements (if needed)
│   └── <name>/
│       └── spec.md
├── data-models/         # Database schemas (if needed)
│   └── <name>/
│       └── schema.md
├── api/                 # API endpoints (if needed)
│   └── <name>/
│       └── spec.md
└── architecture/        # System design (if needed)
    └── <name>/
        └── spec.md
```

### Step 4: Write proposal.md

```markdown
## Why

<1-2 sentences explaining the problem or opportunity>

## What Changes

- <Bullet list of changes>
- Mark breaking changes with **BREAKING**

## Impact

- **Affected specs**: <List capabilities/data-models/apis/architecture>
- **Affected code**: <Key files or systems>

## Success Criteria

- <How to know the change is complete>
```

### Step 5: Write tasks.md

Break down implementation into actionable steps:

```markdown
## 1. Database Schema (if applicable)

- [ ] 1.1 Design schema changes
- [ ] 1.2 Write migration scripts
- [ ] 1.3 Update database documentation

## 2. Backend Implementation

- [ ] 2.1 Implement business logic
- [ ] 2.2 Add API endpoints
- [ ] 2.3 Write unit tests
- [ ] 2.4 Update integration tests

## 3. Frontend Implementation (if applicable)

- [ ] 3.1 Update UI components
- [ ] 3.2 Add form validation
- [ ] 3.3 Write frontend tests

## 4. Validation & Documentation

- [ ] 4.1 Run `tigs validate-specs --change <change-id>`
- [ ] 4.2 Review all delta specs
- [ ] 4.3 Update user documentation
- [ ] 4.4 Update API documentation

## 5. Deployment

- [ ] 5.1 Archive change: `tigs archive-change <change-id>`
- [ ] 5.2 Deploy to staging
- [ ] 5.3 Run integration tests
- [ ] 5.4 Deploy to production
```

### Step 6: Write Detailed Delta Specs

**IMPORTANT**: Write comprehensive, detailed specifications with concrete examples.

---

#### **Capabilities Format** (capabilities/<name>/spec.md)

```markdown
# <Feature Name>

## Purpose

<1-2 sentence description of what this capability provides>

## ADDED Requirements

### Requirement: <Name>

The system SHALL <complete requirement statement>

#### Scenario: <Specific scenario description>

- **WHEN** <specific precondition>
- **THEN** <expected result>
- **AND** <additional result>

#### Scenario: <Another scenario>

- **WHEN** <different condition>
- **THEN** <expected outcome>
- **AND** <additional outcome>

### Requirement: <Another Requirement>

The system SHALL <another requirement>

#### Scenario: <Description>

- **WHEN** <condition>
- **THEN** <result>

## MODIFIED Requirements

### Requirement: <Existing Requirement Name>

<Complete updated requirement text with ALL scenarios, not just changes>

The system SHALL <updated requirement>

#### Scenario: <Updated scenario>

- **WHEN** <condition>
- **THEN** <result>

## REMOVED Requirements

### Requirement: <Requirement to Remove>

**Reason**: <Why removing this requirement>
**Migration**: <How users should adapt to the removal>

## RENAMED Requirements

### Requirement: <Old Name> → <New Name>

## Related Specs

- **Data Models**: `data-models/<name>/schema.md`
- **APIs**: `api/<name>/spec.md`
- **Architecture**: `architecture/<name>/spec.md`
```

**Key Points for Capabilities:**
- Use SHALL/MUST for mandatory, SHOULD for recommended, MAY for optional
- Every requirement needs at least one scenario
- Scenarios must have **WHEN** and **THEN**, can have **AND**
- Be specific and testable

---

#### **Data Models Format** (data-models/<name>/schema.md)

```markdown
# <Model Name>

## Purpose

<1-2 sentence description of what this data model represents>

## ADDED Entities

### Entity: <EntityName>

<Description of what this entity represents>

**Table**: `table_name`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, NOT NULL | Unique identifier |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | User email address |
| `password_hash` | VARCHAR(255) | NOT NULL | Bcrypt hashed password |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Account creation time |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last update time |

**Indexes**:
- `idx_users_email` ON `email` (for fast lookups)
- `idx_users_created_at` ON `created_at` (for sorting)

**Relationships**:
```typescript
User {
  hasMany: [Session, Profile]
  belongsTo: []
}
```

## MODIFIED Entities

### Entity: <ExistingEntity>

<Description>

**Table**: `existing_table`

<Complete updated field table with all fields, not just changes>

## REMOVED Entities

### Entity: <EntityToRemove>

**Reason**: <Why removing this entity>
**Migration**: <Data migration plan, how to handle existing data>

## Validation Rules

### Rule: <Rule Name>

- **MUST** <validation requirement>
- **MUST NOT** <constraint>
- **SHOULD** <recommendation>

## Related Specs

- **Capabilities**: `capabilities/<name>/spec.md`
- **APIs**: `api/<name>/spec.md`
```

**Key Points for Data Models:**
- Include ALL fields with types, constraints, descriptions
- Document indexes for performance-critical fields
- Specify relationships with other entities
- Add validation rules for business logic constraints

---

#### **API Format** (api/<name>/spec.md)

```markdown
# <API Name>

## Purpose

<1-2 sentence description of what this API provides>

## Base Configuration

**Base URL**: `/api/v1/<resource>`
**Authentication**: Bearer token required / Optional / None

## ADDED Endpoints

### POST /auth/login

Authenticate user with email and password.

**Authentication**: None (public endpoint)

**Request**:

```json
{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

**Request Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | Yes | User email address |
| `password` | string | Yes | User password (plaintext, will be hashed) |

**Responses**:

#### 200 OK - Success

User successfully authenticated.

```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
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

#### 429 Too Many Requests - Rate Limited

```json
{
  "error": "RATE_LIMITED",
  "message": "Too many login attempts. Try again in 15 minutes."
}
```

### GET /auth/session

Get current user session information.

**Authentication**: Required (Bearer token)

**Query Parameters**: None

**Responses**:

#### 200 OK - Success

```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com"
  },
  "expires_at": "2024-01-16T10:00:00Z"
}
```

#### 401 Unauthorized

```json
{
  "error": "UNAUTHORIZED",
  "message": "Invalid or expired token"
}
```

## MODIFIED Endpoints

### PUT /existing/endpoint

<Complete updated endpoint specification with all details>

## REMOVED Endpoints

### DELETE /deprecated/endpoint

**Reason**: <Why removing this endpoint>
**Migration**: <Alternative endpoint or approach>

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `INVALID_CREDENTIALS` | 401 | Authentication failed |
| `UNAUTHORIZED` | 401 | Missing or invalid token |
| `RATE_LIMITED` | 429 | Too many requests |

## Related Specs

- **Capabilities**: `capabilities/<name>/spec.md`
- **Data Models**: `data-models/<name>/schema.md`
```

**Key Points for APIs:**
- Document ALL request/response fields
- Include ALL response codes with examples
- Provide realistic JSON examples
- Document authentication requirements
- Include error handling details

---

#### **Architecture Format** (architecture/<name>/spec.md)

```markdown
# <Component Name> Architecture

## Purpose

<1-2 sentence description of this component's role>

## System Context

<Optional ASCII diagram showing how this fits in the system>

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTPS
       ↓
┌─────────────────────┐
│   Auth Service      │
│   (Node.js)         │
└──────┬──────────────┘
       │
       ↓
┌─────────────┐
│  Database   │
└─────────────┘
```

## ADDED Components

### Component: Auth Service

**Type**: Microservice
**Technology**: Node.js 20 + Express 4
**Responsibility**: Handles user authentication, session management, and token generation

**Interfaces**:
- REST API (port 3000)
- Health check endpoint (/health)
- Metrics endpoint (/metrics)

**Dependencies**:
- PostgreSQL 15 (user data, sessions)
- Redis 7 (session cache, rate limiting)
- SMTP server (password reset emails)

**Configuration**:
- Environment variables: DATABASE_URL, REDIS_URL, JWT_SECRET
- Session TTL: 24 hours (configurable)
- Rate limit: 5 login attempts per 15 minutes

**Scaling**: Horizontal (stateless, load balanced)

**Monitoring**:
- Health checks every 30 seconds
- Metrics: login_attempts, active_sessions, token_generation_time
- Alerts: error rate > 5%, response time > 500ms

## MODIFIED Components

### Component: <ExistingComponent>

<Complete updated component specification>

## REMOVED Components

### Component: <ComponentToRemove>

**Reason**: <Why removing>
**Migration**: <How to replace functionality>

## Design Decisions

### Decision: Use JWT for Session Tokens

**Status**: Accepted
**Date**: 2024-01-15

**Context**:
Need to choose session management approach. Options are server-side sessions,
JWT tokens, or database-backed tokens.

**Decision**:
Use JWT tokens with 24-hour expiration, stored in HTTP-only cookies.

**Consequences**:
- ✅ Stateless authentication (easier to scale horizontally)
- ✅ No database lookup on every request (better performance)
- ✅ Tokens can include user roles/permissions (fewer DB queries)
- ⚠️ Cannot revoke tokens before expiration (mitigated by short TTL)
- ⚠️ Token size larger than session ID (acceptable for our use case)

**Alternatives Considered**:
1. **Server-side sessions**: Rejected due to need for sticky sessions or shared session store
2. **Database-backed tokens**: Rejected due to performance overhead of DB lookup per request

## Performance Requirements

| Metric | Target | Measurement |
|--------|--------|-------------|
| Response time (P95) | < 100ms | Login endpoint latency |
| Throughput | 1000 req/s | Single instance capacity |
| Availability | 99.9% | Monthly uptime |

## Related Specs

- **Capabilities**: `capabilities/<name>/spec.md`
- **APIs**: `api/<name>/spec.md`
- **Data Models**: `data-models/<name>/schema.md`
```

**Key Points for Architecture:**
- Document concrete technology choices (versions!)
- Specify configuration and dependencies
- Include scaling strategy
- Document design decisions with reasoning
- Provide performance targets

---

### Step 7: Validate

```bash
tigs validate-specs --change <change-id>
```

Fix any validation errors before proceeding.

### Step 8: Report

Tell the user:
- Change ID and file locations
- What specs were created
- Validation status
- Next steps (implementation → archive)

## Complete Example

User: "I want to add two-factor authentication"

You:
1. **Clarify**: "Will this be optional or required? Which 2FA methods (SMS, TOTP, email)?"
   - User: "Optional, TOTP-based with backup codes"

2. **Analyze**:
   ```
   - ✅ Capabilities: user-authentication (MODIFIED - add 2FA requirements)
   - ✅ Data Models: user (MODIFIED - add 2FA fields), backup-codes (ADDED)
   - ✅ API: auth (MODIFIED - add 2FA endpoints)
   - ❌ Architecture: Not needed (no new services)
   ```

3. **Choose ID**: `add-two-factor-auth`

4. **Create structure** and **write detailed files**:

```
specs/changes/add-two-factor-auth/
├── proposal.md
├── tasks.md
├── capabilities/user-authentication/spec.md
├── data-models/user/schema.md
├── data-models/backup-codes/schema.md
└── api/auth/spec.md
```

5. **proposal.md**:
```markdown
## Why

Users need additional security beyond passwords. Industry best practice
requires multi-factor authentication for sensitive operations.

## What Changes

- Add TOTP-based 2FA setup and verification flow
- Generate and validate backup codes
- Update login flow to check 2FA when enabled
- **BREAKING**: Login endpoint now returns 2FA_REQUIRED status

## Impact

- **Affected specs**: capabilities/user-authentication, data-models/user, data-models/backup-codes, api/auth
- **Affected code**: auth-service (login flow), frontend (2FA setup page, login flow)

## Success Criteria

- Users can enable/disable 2FA in settings
- Login validates TOTP code when 2FA enabled
- Backup codes work if TOTP app unavailable
- Account lockout after 5 failed 2FA attempts
```

6. **tasks.md**:
```markdown
## 1. Database Schema

- [ ] 1.1 Add `two_factor_enabled`, `two_factor_secret` fields to users table
- [ ] 1.2 Create `backup_codes` table
- [ ] 1.3 Write and test migrations
- [ ] 1.4 Update database documentation

## 2. Backend Implementation

- [ ] 2.1 Install TOTP library (speakeasy)
- [ ] 2.2 Implement secret generation endpoint
- [ ] 2.3 Implement QR code generation
- [ ] 2.4 Implement TOTP verification
- [ ] 2.5 Implement backup code generation
- [ ] 2.6 Implement backup code validation
- [ ] 2.7 Update login endpoint for 2FA flow
- [ ] 2.8 Add rate limiting for verification attempts

## 3. Frontend Implementation

- [ ] 3.1 Create 2FA setup page (QR code display)
- [ ] 3.2 Create verification code input component
- [ ] 3.3 Create backup codes display/download
- [ ] 3.4 Update login flow to handle 2FA
- [ ] 3.5 Add 2FA management to user settings

## 4. Testing

- [ ] 4.1 Unit tests for TOTP generation/validation
- [ ] 4.2 Unit tests for backup codes
- [ ] 4.3 Integration tests for 2FA setup flow
- [ ] 4.4 Integration tests for 2FA login flow
- [ ] 4.5 E2E tests for complete user journey

## 5. Documentation & Validation

- [ ] 5.1 Run `tigs validate-specs --change add-two-factor-auth`
- [ ] 5.2 Write user guide for 2FA setup
- [ ] 5.3 Update API documentation
- [ ] 5.4 Create troubleshooting guide

## 6. Deployment

- [ ] 6.1 Archive: `tigs archive-change add-two-factor-auth`
- [ ] 6.2 Deploy to staging
- [ ] 6.3 QA testing in staging
- [ ] 6.4 Deploy to production
- [ ] 6.5 Monitor error rates and login success rates
```

7. **Write detailed delta specs** (see formats above for complete examples)

8. **Validate**: `tigs validate-specs --change add-two-factor-auth`

9. **Report**:
```
✓ Created change proposal: add-two-factor-auth

Files created:
  - specs/changes/add-two-factor-auth/proposal.md
  - specs/changes/add-two-factor-auth/tasks.md
  - specs/changes/add-two-factor-auth/capabilities/user-authentication/spec.md
  - specs/changes/add-two-factor-auth/data-models/user/schema.md
  - specs/changes/add-two-factor-auth/data-models/backup-codes/schema.md
  - specs/changes/add-two-factor-auth/api/auth/spec.md

Next steps:
1. Review the proposal and specifications
2. Start implementation following tasks.md
3. Archive when complete: tigs archive-change add-two-factor-auth
```

## Important Guidelines

### For All Specs

1. **Be comprehensive**: Include ALL details, not just changes
2. **Use concrete examples**: Real JSON, realistic field names, actual values
3. **Think end-to-end**: Cover the complete user journey
4. **Cross-reference**: Link related specs together
5. **Validate early**: Run validation after creating specs

### For Requirements (Capabilities)

- Use modal verbs consistently (SHALL/MUST/SHOULD/MAY)
- Every requirement needs at least one testable scenario
- Scenarios must have **WHEN** (condition) and **THEN** (result)
- Be specific enough that a developer knows exactly what to implement

### For Data Models

- Include ALL fields with complete type information
- Document constraints (NOT NULL, UNIQUE, etc.)
- Specify indexes for performance
- Document relationships between entities
- Add validation rules for business logic

### For APIs

- Document ALL request and response fields
- Include ALL possible response codes
- Provide realistic JSON examples
- Document authentication requirements
- Include error handling details
- Specify rate limits if applicable

### For Architecture

- Use concrete technology names and versions
- Document all dependencies and configuration
- Include scaling strategy
- Document design decisions with reasoning (ADRs)
- Provide performance requirements

## Tips

- **Start with proposal.md** to clarify scope before diving into specs
- **Keep changes focused** - aim for 1-2 weeks of work maximum
- **Break down large changes** - multiple small changes > one huge change
- **Write specs before code** - specs guide implementation
- **Validate early and often** - catch format errors before implementation
- **Use examples liberally** - concrete examples prevent ambiguity
