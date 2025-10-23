# /validate - Validate Specifications

Validate specification format and structure to ensure compliance with defined rules.

## Your Task

Run validation and report results in a clear, actionable format.

## Usage

```bash
# Validate all specs
tigs validate-specs --all

# Validate specific type
tigs validate-specs --type capabilities

# Validate a change before archiving
tigs validate-specs --change <change-id>

# Strict mode (warnings as errors)
tigs validate-specs --all --strict
```

## What Gets Validated

### Capabilities
- ✅ Required sections: `## Purpose`, `## Requirements`
- ✅ Requirement format: `### Requirement: <Name>`
- ⚠️ Modal verbs: SHALL/MUST/SHOULD/MAY
- ✅ Scenario format: `#### Scenario: <Description>`
- ⚠️ Keywords: **WHEN**/**THEN**/**AND**

### Data Models
- ✅ Required sections: `## Purpose`, `## Schema`
- ✅ Entity format: `### Entity: <Name>`
- ⚠️ Table definition: `**Table**: `name``
- ⚠️ Field table structure

### API
- ✅ Required sections: `## Purpose`, `## Endpoints`
- ✅ Endpoint format: `### METHOD /path`
- ⚠️ Response codes: `#### 200 OK`, etc.

### Architecture
- ✅ Required sections: `## Purpose`, `## Components`
- ✅ Component format: `### Component: <Name>`
- ⚠️ Component metadata: **Type**, **Responsibility**
- ⚠️ ADR format (if Design Decisions section exists)

## Workflow

1. **Identify what to validate**
   - All specs: `--all`
   - Specific type: `--type <type>`
   - Change only: `--change <change-id>`

2. **Run validation**
   ```bash
   tigs validate-specs <options>
   ```

3. **Review results**
   - ✅ No issues: Ready to archive
   - ⚠️ Warnings only: Consider fixing but not blocking
   - ❌ Errors: Must fix before archiving

4. **Fix issues**
   - Read error messages carefully (include line numbers)
   - Edit the spec files
   - Re-validate

5. **Report**
   - Summarize validation results
   - List any errors or warnings
   - Suggest fixes if errors found

## Common Issues and Fixes

### Missing Required Section
```
[ERROR] Missing required section: ## Requirements
```
**Fix**: Add the missing section to the spec file

### Wrong Requirement Format
```
[ERROR] Line 25: Requirement must follow format: '### Requirement: <Name>'
```
**Fix**: Change `### User Login` to `### Requirement: User Login`

### Missing Modal Verb
```
[WARNING] Line 30: Requirement should include SHALL/MUST statement
```
**Fix**: Add "The system SHALL..." to the requirement description

### Wrong Scenario Format
```
[ERROR] Line 42: Scenario must follow format: '#### Scenario: <Description>'
```
**Fix**: Use 4 hashtags: `#### Scenario: Successful login`

### Missing WHEN/THEN
```
[WARNING] Line 45: Scenario should include **WHEN** and **THEN** keywords
```
**Fix**: Add bullets with **WHEN** and **THEN**

## Example Interaction

User: "Validate the specs I just created"

You:
1. Determine the scope (all specs or specific change)
2. Run: `tigs validate-specs --change <change-id>` (or appropriate command)
3. Report results:

**If successful:**
```
✓ Validation passed!

All 3 specification(s) validated successfully:
  - capabilities/user-auth/spec.md
  - data-models/user/schema.md
  - api/auth/spec.md

Ready to archive: tigs archive-change <change-id>
```

**If errors found:**
```
✗ Validation failed with 2 errors:

capabilities/user-auth/spec.md:
  [ERROR] Line 25: Requirement must follow format: '### Requirement: <Name>'
  [WARNING] Line 42: Scenario should include **WHEN** and **THEN** keywords

Please fix the errors and run validation again.
```

## Tips

- Always validate before archiving
- Use `--strict` in CI/CD pipelines
- Fix errors first, warnings can be deferred
- Re-validate after fixing issues
