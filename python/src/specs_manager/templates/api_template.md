# {{api_name}} API

## Purpose

{{purpose}}

## Base Configuration

**Base URL**: `/api/v1/{{resource}}`
**Authentication**: {{auth_method}}

## Endpoints

### {{method}} /{{path}}

{{description}}

**Authentication**: {{auth_required}}

**Request**:
```json
{
  "{{field}}": "{{value}}"
}
```

**Request Schema**:

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `{{field}}` | {{type}} | {{required}} | {{validation}} |

**Responses**:

#### 200 OK - Success

```json
{
  "{{response_field}}": "{{response_value}}"
}
```

#### 400 Bad Request - Validation Error

```json
{
  "error": "ERROR_CODE",
  "message": "Human readable message"
}
```

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `ERROR_CODE` | 400 | {{error_description}} |

## Related Specs

- **Capabilities**: `capabilities/{{related_capability}}/spec.md`
- **Data Models**: `data-models/{{related_model}}/schema.md`
