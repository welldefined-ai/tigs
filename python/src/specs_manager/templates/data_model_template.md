# {{model_name}} Model

## Purpose

{{purpose}}

## Schema

### Entity: {{entity_name}}

{{description}}

**Table**: `{{table_name}}`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, NOT NULL | Unique identifier |
| `{{field_name}}` | {{field_type}} | {{constraints}} | {{field_description}} |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Record creation time |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last update time |

**Indexes**:
- `idx_{{index_name}}` ON `{{field_name}}`

**Relationships**:
```typescript
{{entity_name}} {
  hasMany: []
  belongsTo: []
}
```

## Validation Rules

### Rule: {{rule_name}}

- **MUST** {{constraint}}
- **MUST NOT** {{restriction}}

## Related Specs

- **Capabilities**: `capabilities/{{related_capability}}/spec.md`
- **APIs**: `api/{{related_api}}/spec.md`
