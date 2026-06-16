# Contract: Resolve Contact (find-or-create)

## REST endpoint

`POST /booking/resolve-contact`

Resolves contact identifiers to a single contact, creating it only if none exists.

### Request body (application/json)

```json
{
  "email": "ada@example.com",
  "phone": "+15551234567",
  "first_name": "Ada",
  "last_name": "Lovelace",
  "source": "voice-agent"
}
```

- At least one of `email` / `phone` required.
- `first_name`/`last_name`/`source` are used only when creating.

### Responses

| Status | When | Body |
|--------|------|------|
| `200 OK` | Resolved | `{ "contact": { "id": "...", ... }, "created": <bool> }` |
| `422 Unprocessable Entity` | Neither email nor phone, or malformed email | Validation error |
| `401 / 403 / 4xx / 5xx` (passthrough) | Upstream error | `{ "error": "ghl_api_error", ... }`, status preserved |

`created: false` = matched an existing contact; `created: true` = newly created.

### Acceptance mapping

- 200 matched on existing email → FR-003/006, SC-002
- 200 created on new identifiers → FR-004/005/006, SC-001
- 422 when no identifier → FR-002
- deterministic single result on multiple matches → FR-007

## MCP tool

`resolve_contact(email=None, phone=None, first_name=None, last_name=None, source=None) -> dict`

Returns `{contact, created}`. Reusable "smart resolver"; the agent uses it to get a
`contact_id`.

## Notes

- Find-or-create dedup is best-effort against very-recent creations (GHL search is eventually
  consistent).
