# /archive - Archive Change Proposal

Archive a completed change proposal by merging delta specifications into the main specs directory.

## Your Task

1. **Validate** the change before archiving
2. **Run archive command** to merge changes
3. **Verify** the merge results
4. **Report** what was archived

## When to Archive

Archive a change when:
- ✅ All tasks in `tasks.md` are completed
- ✅ Implementation is done and tested
- ✅ Specs pass validation
- ✅ Code is deployed (or ready to deploy)

## Pre-Archive Checklist

Before archiving, ensure:
1. **Implementation complete**: All code changes are done
2. **Tests passing**: Unit and integration tests pass
3. **Validation passing**: `tigs validate-specs --change <change-id>` succeeds
4. **Documentation updated**: README, API docs, etc.
5. **Code reviewed**: PR approved and merged

## Workflow

### Step 1: Validate the Change

Always validate before archiving to catch any issues:

```bash
tigs validate-specs --change <change-id>
```

If validation fails:
- Fix the errors in the delta specs
- Re-validate
- Don't proceed until all errors are resolved

### Step 2: Review the Change

Check what will be archived:

```bash
# List all specs in the change
tigs list-specs --change <change-id>

# Show specific specs to review
tigs show-spec capabilities/<name> --change <change-id>
```

Verify:
- Delta operations are correct (ADDED/MODIFIED/REMOVED/RENAMED)
- Content is accurate and complete
- Cross-references are valid

### Step 3: Archive the Change

Run the archive command:

```bash
tigs archive-change <change-id>
```

This will:
1. Parse all delta specs in `specs/changes/<change-id>/`
2. Merge changes into `specs/` (main directory)
3. Move the change directory to `specs/archive/<change-id>/`
4. Preserve the original change for reference

### Step 4: Verify the Merge

After archiving, verify the results:

```bash
# Check that specs were updated in main directory
tigs show-spec capabilities/<name>

# Validate the main specs
tigs validate-specs --type capabilities
```

Confirm:
- New requirements were added to main specs
- Modified requirements were updated
- Removed requirements were deleted
- Cross-references still work

## Archive Behavior by Spec Type

### Capabilities (spec.md)

**ADDED Requirements**:
- Appended to `## Requirements` section in main spec
- Scenario blocks included

**MODIFIED Requirements**:
- Existing requirement completely replaced with new content
- Match by requirement name

**REMOVED Requirements**:
- Requirement and all scenarios deleted from main spec
- Removal reason not preserved (documented in archived change)

**RENAMED Requirements**:
- Requirement name updated in main spec
- Content unchanged

### Data Models (schema.md)

**ADDED Entities**:
- New entity block appended to `## Schema` section

**MODIFIED Entities**:
- Existing entity replaced with updated schema
- Match by entity name

**REMOVED Entities**:
- Entity block deleted from main spec

### API (spec.md)

**ADDED Endpoints**:
- New endpoint appended to `## Endpoints` section

**MODIFIED Endpoints**:
- Existing endpoint replaced with updated definition
- Match by METHOD and path

**REMOVED Endpoints**:
- Endpoint block deleted from main spec

### Architecture (spec.md)

**ADDED Components**:
- New component appended to `## Components` section

**MODIFIED Components**:
- Existing component replaced with updated definition
- Match by component name

**REMOVED Components**:
- Component block deleted from main spec

## Example Interaction

User: "Archive the add-two-factor-auth change"

You:
1. **Validate first**:
```bash
tigs validate-specs --change add-two-factor-auth
```

2. **If validation passes**:
```
✓ Validation passed!

All 3 specification(s) validated successfully:
  - capabilities/user-authentication/spec.md
  - data-models/user/schema.md
  - api/auth/spec.md

Ready to archive.
```

3. **Review what will be archived**:
```bash
tigs list-specs --change add-two-factor-auth
```

4. **Archive**:
```bash
tigs archive-change add-two-factor-auth
```

5. **Report results**:
```
✓ Successfully archived change: add-two-factor-auth

Merged specifications:
  - capabilities/user-authentication/spec.md
    • Added 3 requirements
    • Modified 1 requirement
  - data-models/user/schema.md
    • Modified 1 entity (added 2FA fields)
  - api/auth/spec.md
    • Added 3 endpoints

Archived to: specs/archive/add-two-factor-auth/

Next steps:
1. Verify merged specs: tigs show-spec capabilities/user-authentication
2. Validate: tigs validate-specs --type capabilities
```

## Common Issues

### Issue: Validation Fails

```
✗ Validation failed with 2 errors
```

**Solution**:
- Fix errors in delta specs
- Re-validate
- Don't archive until validation passes

### Issue: Merge Conflict

```
[ERROR] Cannot modify requirement 'User Login' - not found in main spec
```

**Solution**:
- Check that the requirement name matches exactly
- If renaming, use RENAMED operation first
- If requirement doesn't exist, use ADDED instead

### Issue: Missing Cross-References

```
[WARNING] Reference to 'data-models/user/schema.md' not found
```

**Solution**:
- Ensure referenced specs exist or will be created
- Check the path is correct
- If referencing a new spec, make sure it's in the same change

### Issue: Accidental Archive

If you archived by mistake:
1. The original is in `specs/archive/<change-id>/`
2. Manually revert changes in `specs/`
3. Move the change back: `mv specs/archive/<change-id> specs/changes/`

## Tips

- **Validate always**: Never skip validation before archiving
- **Review diffs**: Check what will change before archiving
- **Test thoroughly**: Archive only after testing is complete
- **Atomic changes**: Keep changes focused and small
- **Document well**: Good proposal.md helps future understanding
- **Preserve history**: Archived changes are valuable documentation

## Important Notes

1. **Archiving is semi-permanent**: Changes go to `specs/archive/` but manual reversion is possible
2. **No automatic rollback**: Plan carefully before archiving
3. **Cross-change dependencies**: Archive changes in dependency order
4. **Breaking changes**: Document migration path in proposal.md
5. **Validation is mandatory**: The command will fail if validation doesn't pass

## Validation Before Archive

The archive command automatically runs validation first. These must pass:

**For all specs**:
- Required sections present
- Proper formatting
- Valid delta operations

**For capabilities**:
- Requirement format: `### Requirement: <Name>`
- Modal verbs: SHALL/MUST/SHOULD/MAY
- Scenario format: `#### Scenario: <Description>`
- Keywords: **WHEN**/**THEN**/**AND**

**For data-models**:
- Entity format: `### Entity: <Name>`
- Table definition: `**Table**: \`name\``
- Field table structure

**For API**:
- Endpoint format: `### METHOD /path`
- Valid HTTP methods
- Response codes: `#### 200 OK`, etc.

**For architecture**:
- Component format: `### Component: <Name>`
- Component metadata: **Type**, **Responsibility**
- ADR format (if present)

## After Archiving

Once archived:
1. ✅ Main specs are updated with the changes
2. ✅ Change directory moved to `specs/archive/`
3. ✅ Original delta specs preserved for reference
4. ✅ Ready to start next change

Continue the development cycle:
- Identify next feature/change
- Create new change proposal
- Implement → Validate → Archive
