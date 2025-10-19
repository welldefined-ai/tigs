# /change - Create Change Proposal

Create a structured change proposal for adding, modifying, or removing specifications.

## Your Task

Guide the user through creating a complete change proposal with:
- proposal.md (why, what, impact)
- tasks.md (implementation checklist)
- Delta specifications (what's changing)

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

### Step 1: Choose Change ID
- Use kebab-case
- Verb-led: `add-`, `update-`, `remove-`, `refactor-`
- Examples: `add-user-auth`, `update-payment-api`, `remove-legacy-endpoints`

### Step 2: Create Directory Structure
```
specs/changes/<change-id>/
├── proposal.md
├── tasks.md
└── <type>/
    └── <spec-name>/
        └── spec.md (or schema.md for data-models)
```

### Step 3: Write proposal.md
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

### Step 4: Write tasks.md
```markdown
## 1. Implementation

- [ ] 1.1 Create/update database schema
- [ ] 1.2 Implement business logic
- [ ] 1.3 Add API endpoints
- [ ] 1.4 Update frontend
- [ ] 1.5 Write tests
- [ ] 1.6 Update documentation

## 2. Validation

- [ ] 2.1 Run `tigs validate-specs --change <change-id>`
- [ ] 2.2 Review all delta specs
- [ ] 2.3 Verify cross-references

## 3. Deployment

- [ ] 3.1 Archive change: `tigs archive-change <change-id>`
- [ ] 3.2 Deploy to staging
- [ ] 3.3 Run integration tests
- [ ] 3.4 Deploy to production
```

### Step 5: Write Delta Specs

Use delta operations in the spec files:

**For New Requirements** (## ADDED):
```markdown
## ADDED Requirements

### Requirement: <New Requirement>
The system SHALL <requirement>

#### Scenario: <Description>
- **WHEN** <condition>
- **THEN** <result>
```

**For Modified Requirements** (## MODIFIED):
```markdown
## MODIFIED Requirements

### Requirement: <Existing Requirement>
<Complete updated requirement text including all scenarios>
```

**For Removed Requirements** (## REMOVED):
```markdown
## REMOVED Requirements

### Requirement: <Requirement to Remove>

**Reason**: <Why removing>
**Migration**: <How users should adapt>
```

**For Renamed Requirements** (## RENAMED):
```markdown
## RENAMED Requirements

### Requirement: <Old Name> → <New Name>
```

### Step 6: Validate
```bash
tigs validate-specs --change <change-id>
```

## Example Interaction

User: "I want to add two-factor authentication"

You:
1. **Clarify**: "Will this be optional or required? Which 2FA methods (SMS, TOTP, email)?"
2. **Choose ID**: `add-two-factor-auth`
3. **Create structure**:
```
specs/changes/add-two-factor-auth/
├── proposal.md
├── tasks.md
├── capabilities/user-authentication/spec.md (MODIFIED)
├── data-models/user/schema.md (MODIFIED - add 2FA fields)
└── api/auth/spec.md (ADDED - 2FA endpoints)
```

4. **Write files**:

proposal.md:
```markdown
## Why

Users need additional security beyond passwords. Industry best practice
requires multi-factor authentication for sensitive operations.

## What Changes

- Add 2FA setup flow (TOTP-based)
- Require 2FA verification at login
- Add backup codes generation
- **BREAKING**: Login flow now requires additional step

## Impact

- **Affected specs**: capabilities/user-authentication, data-models/user, api/auth
- **Affected code**: auth-service, frontend login flow

## Success Criteria

- Users can enable/disable 2FA
- Login validates 2FA when enabled
- Backup codes work if TOTP unavailable
```

tasks.md:
```markdown
## 1. Database Schema

- [ ] 1.1 Add `two_factor_enabled` field to users table
- [ ] 1.2 Create `two_factor_secrets` table
- [ ] 1.3 Create `backup_codes` table
- [ ] 1.4 Run migrations

## 2. Backend Implementation

- [ ] 2.1 TOTP secret generation
- [ ] 2.2 QR code generation endpoint
- [ ] 2.3 TOTP verification logic
- [ ] 2.4 Backup code generation/validation
- [ ] 2.5 Update login flow

## 3. Frontend Implementation

- [ ] 3.1 2FA setup page
- [ ] 3.2 QR code display
- [ ] 3.3 Verification code input
- [ ] 3.4 Backup codes display
- [ ] 3.5 Update login form

## 4. Testing & Documentation

- [ ] 4.1 Unit tests
- [ ] 4.2 Integration tests
- [ ] 4.3 User documentation
- [ ] 4.4 API documentation
```

5. **Validate**: `tigs validate-specs --change add-two-factor-auth`

6. **Report**:
```
Created change proposal: add-two-factor-auth

Files created:
  - specs/changes/add-two-factor-auth/proposal.md
  - specs/changes/add-two-factor-auth/tasks.md
  - specs/changes/add-two-factor-auth/capabilities/user-authentication/spec.md
  - specs/changes/add-two-factor-auth/data-models/user/schema.md
  - specs/changes/add-two-factor-auth/api/auth/spec.md

Next steps:
1. Review the proposal and tasks
2. Validate: tigs validate-specs --change add-two-factor-auth
3. Start implementation following tasks.md
4. Archive when done: tigs archive-change add-two-factor-auth
```

## Tips

- Start with proposal.md to clarify scope
- tasks.md should be actionable checklist
- Delta specs focus on what's changing, not everything
- Validate early and often
- Keep change scope reasonable (1-2 weeks max)
