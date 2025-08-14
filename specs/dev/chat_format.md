# Tigs Chat Format Specification

**Schema version:** `tigs.chat/v1`

Each chat represents **one complete, independent conversation** (sequence of messages in order).  
Stored in **UTF-8 YAML** for human readability and easy parsing.  

---

## Top-Level Structure

| Field      | Type   | Required | Description                                                         |
|------------|--------|----------|---------------------------------------------------------------------|
| `schema`   | string | **Yes**  | Schema identifier (`"tigs.chat/v1"`).                               |
| `summary`  | string | No       | Short one-line description of the chat. Useful for search/skimming. |
| `messages` | list   | **Yes**  | Ordered list of message objects (see below).                        |

## Message Object

| Field       | Type                   | Required | Description                                                             |
|-------------|------------------------|----------|-------------------------------------------------------------------------|
| `role`      | string                 | **Yes**  | Who sent the message: `user`, `assistant`, or `system`.                 |
| `content`   | string (multi-line)    | **Yes**  | Message text in any format. Stored as a YAML block scalar (`\|`).       |
| `model`     | string                 | No       | AI Model name/identifier used to generate this message (e.g., `gpt-5`). |
| `timestamp` | string (ISO 8601, UTC) | **Yes**  | When the message was created. Format: `YYYY-MM-DDThh:mm:ssZ`.           |

## Rules

- Timestamps must be UTC with Z suffix; precision to seconds is recommended.
- Content fidelity:
  - Use YAML block scalars (`|`) to keep Markdown/code/JSON/... unchanged.
  - Do not fold or rewrap lines.

---

## Example

```yaml
schema: "tigs.chat/v1"
summary: "LangFuse optional integration discussion"

messages:
  - role: user
    content: |-
      I want LangFuse tracing but optional.
      Env var to enable.
    timestamp: "2025-07-19T15:28:57Z"

  - role: assistant
    content: |-
      **Plan:**
      - Use extras / soft dependency
      - Guard imports
      - Enable via `LANGFUSE_ENABLED`
      - Provide `docker-compose` for local stack
    model: "claude-opus-4-20250514"
    timestamp: "2025-07-19T15:33:40Z"
```
