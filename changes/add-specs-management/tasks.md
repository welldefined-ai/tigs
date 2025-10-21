# Implementation Tasks

## 1. Foundation

- [ ] 1.1 Create `python/src/specs_manager/` package structure
- [ ] 1.2 Define directory constants and configuration
- [ ] 1.3 Implement `SpecsDirectory` class for path management
- [ ] 1.4 Add utilities for file operations (create, read, copy)

## 2. Templates

- [ ] 2.1 Create template files in `python/src/specs_manager/templates/`:
  - [ ] 2.1.1 `capability_template.md`
  - [ ] 2.1.2 `data_model_template.md`
  - [ ] 2.1.3 `api_template.md`
  - [ ] 2.1.4 `architecture_template.md`
  - [ ] 2.1.5 `README_template.md`
  - [ ] 2.1.6 `proposal_template.md`
  - [ ] 2.1.7 `tasks_template.md`

- [ ] 2.2 Implement template rendering with variable substitution

## 3. CLI Commands - Basic

- [ ] 3.1 Add specs command group to `cli.py`
- [ ] 3.2 Implement `tig init-specs` command:
  - [ ] 3.2.1 Check if specs/ exists (warn if present)
  - [ ] 3.2.2 Create directory structure
  - [ ] 3.2.3 Generate README
  - [ ] 3.2.4 Support `--examples` flag
- [ ] 3.3 Implement `tig list-specs` command:
  - [ ] 3.3.1 Scan directories and discover specs
  - [ ] 3.3.2 Display grouped by type
  - [ ] 3.3.3 Support `--type` filter
  - [ ] 3.3.4 Support `--json` output
- [ ] 3.4 Implement `tig show-spec` command:
  - [ ] 3.4.1 Resolve spec name to file path
  - [ ] 3.4.2 Display formatted content
  - [ ] 3.4.3 Support `--type` disambiguation
  - [ ] 3.4.4 Support `--json` output

## 4. Validation Framework

- [ ] 4.1 Create `python/src/specs_manager/validators/` package
- [ ] 4.2 Implement base `SpecValidator` class
- [ ] 4.3 Implement `CapabilityValidator`:
  - [ ] 4.3.1 Check Purpose and Requirements sections
  - [ ] 4.3.2 Verify requirement format (### Requirement: + SHALL/MUST)
  - [ ] 4.3.3 Verify scenario format (#### Scenario:)
  - [ ] 4.3.4 Validate WHEN/THEN/AND keywords
- [ ] 4.4 Implement `DataModelValidator`:
  - [ ] 4.4.1 Check Purpose and Schema sections
  - [ ] 4.4.2 Verify table definition
  - [ ] 4.4.3 Validate field table format
  - [ ] 4.4.4 Check validation rules section
- [ ] 4.5 Implement `ApiValidator`:
  - [ ] 4.5.1 Check Purpose and Endpoints sections
  - [ ] 4.5.2 Verify endpoint format (METHOD /path)
  - [ ] 4.5.3 Check request/response schemas
  - [ ] 4.5.4 Validate status codes
- [ ] 4.6 Implement `ArchitectureValidator`:
  - [ ] 4.6.1 Check Purpose and Components sections
  - [ ] 4.6.2 Verify component definitions
  - [ ] 4.6.3 Validate ADR format (if present)
- [ ] 4.7 Implement cross-reference validation
- [ ] 4.8 Implement validation reporter with error levels

## 5. CLI Commands - Validation

- [ ] 5.1 Implement `tig validate-specs` command:
  - [ ] 5.1.1 Support `--all` flag
  - [ ] 5.1.2 Support type filters (--capabilities, --data-models, etc.)
  - [ ] 5.1.3 Support `--strict` mode
  - [ ] 5.1.4 Display validation report
  - [ ] 5.1.5 Exit with appropriate code

## 6. Change Management - Parsing

- [ ] 6.1 Implement `DeltaParser` for capabilities (OpenSpec format):
  - [ ] 6.1.1 Parse ADDED requirements
  - [ ] 6.1.2 Parse MODIFIED requirements
  - [ ] 6.1.3 Parse REMOVED requirements
  - [ ] 6.1.4 Parse RENAMED requirements
- [ ] 6.2 Implement `DataModelDeltaParser`:
  - [ ] 6.2.1 Parse ADDED models
  - [ ] 6.2.2 Parse MODIFIED models with field changes
- [ ] 6.3 Implement `ApiDeltaParser`:
  - [ ] 6.3.1 Parse ADDED endpoints
  - [ ] 6.3.2 Parse MODIFIED endpoints
- [ ] 6.4 Implement change validation:
  - [ ] 6.4.1 Verify proposal.md exists
  - [ ] 6.4.2 Verify at least one delta spec
  - [ ] 6.4.3 Validate delta operations reference existing specs

## 7. Change Management - Merging

- [ ] 7.1 Implement `CapabilityMerger`:
  - [ ] 7.1.1 Apply RENAMED operations
  - [ ] 7.1.2 Apply REMOVED operations
  - [ ] 7.1.3 Apply MODIFIED operations (replace blocks)
  - [ ] 7.1.4 Apply ADDED operations (append)
  - [ ] 7.1.5 Preserve requirement ordering
- [ ] 7.2 Implement `DataModelMerger`:
  - [ ] 7.2.1 Create new models (ADDED)
  - [ ] 7.2.2 Update existing models (MODIFIED)
  - [ ] 7.2.3 Update migrations.md
- [ ] 7.3 Implement `ApiMerger`:
  - [ ] 7.3.1 Add new endpoints
  - [ ] 7.3.2 Update existing endpoints
  - [ ] 7.3.3 Maintain endpoint ordering

## 8. CLI Commands - Archive

- [ ] 8.1 Implement `tig archive-change` command:
  - [ ] 8.1.1 Discover change directory
  - [ ] 8.1.2 Validate change completeness
  - [ ] 8.1.3 Parse all delta specs
  - [ ] 8.1.4 Display summary and prompt for confirmation
  - [ ] 8.1.5 Apply merges to main specs
  - [ ] 8.1.6 Move to archive with date prefix
  - [ ] 8.1.7 Support `--yes` and `--skip-specs` flags

## 9. Template Generation via /change Slash Command

- [ ] 9.1 Implement `/change` slash command:
  - [ ] 9.1.1 Guide user through change proposal creation
  - [ ] 9.1.2 Identify affected spec types
  - [ ] 9.1.3 Generate delta specs in changes directory
  - [ ] 9.1.4 Create proposal.md and tasks.md
  - [ ] 9.1.5 Validate all generated specs

## 10. Testing

- [ ] 10.1 Unit tests for validators:
  - [ ] 10.1.1 Test valid specs pass
  - [ ] 10.1.2 Test invalid specs fail with correct errors
  - [ ] 10.1.3 Test edge cases
- [ ] 10.2 Unit tests for delta parsers:
  - [ ] 10.2.1 Test parsing all operation types
  - [ ] 10.2.2 Test malformed deltas
- [ ] 10.3 Unit tests for mergers:
  - [ ] 10.3.1 Test each operation type
  - [ ] 10.3.2 Test operation ordering
  - [ ] 10.3.3 Test conflict detection
- [ ] 10.4 Integration tests:
  - [ ] 10.4.1 Test full init → create → validate → archive flow
  - [ ] 10.4.2 Test with real-world spec examples
- [ ] 10.5 CLI tests:
  - [ ] 10.5.1 Test all commands with various options
  - [ ] 10.5.2 Test error handling

## 11. Documentation

- [ ] 11.1 Update README with specs management section
- [ ] 11.2 Create user guide for each spec type
- [ ] 11.3 Add CLI command reference
- [ ] 11.4 Create tutorial with examples
- [ ] 11.5 Document format specifications

## 12. Dogfooding

- [ ] 12.1 Use specs system to document tig's existing features:
  - [ ] 12.1.1 Create `capabilities/chat-storage/spec.md`
  - [ ] 12.1.2 Create `capabilities/tui-interface/spec.md`
  - [ ] 12.1.3 Create `data-models/git-notes/schema.md`
  - [ ] 12.1.4 Create `architecture/tig-system/spec.md`
- [ ] 12.2 Validate all tig specs pass validation
- [ ] 12.3 Verify specs serve as useful documentation
