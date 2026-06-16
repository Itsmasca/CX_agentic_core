# Contract: Update Contact

## REST endpoint

`PUT /contacts/{contact_id}`

Partially updates an existing contact. Only provided fields change.

### Path

- `contact_id` — the id of the contact to update.

### Request body (application/json)

Public boundary is snake_case (camelCase aliases accepted too). All fields optional, but at
least one MUST be present.

```json
{
  "first_name": "Augusta",
  "source": "manual-edit"
}
```

- At least one of `first_name`, `last_name`, `email`, `phone`, `source` is required.
- `email`, if present, must be a valid email address.
- `location` is NOT accepted (the contact already belongs to its location).

### Responses

| Status | When | Body |
|--------|------|------|
| `200 OK` | Contact updated | `{ "contact": { "id": "...", ... } }` (updated contact) |
| `422 Unprocessable Entity` | No changeable field provided, or malformed email | FastAPI validation error |
| `404` (passthrough) | `contact_id` does not exist upstream | `{ "error": "ghl_api_error", "detail": "[404] ...", ... }` |
| `401 / 403` | Upstream auth failure | Error envelope, status preserved |

### Acceptance mapping

- 200, only provided fields changed, others unchanged → FR-009/010/011/014, SC-003
- 422 on no-field or malformed email → FR-012/013, SC-004
- 404 passthrough on non-existent id (no change) → FR-015, SC-004

## MCP tool

`update_contact(contact_id: str, first_name=None, last_name=None, email=None, phone=None, source=None) -> dict`

Sends only the provided fields; returns the updated contact. Enforces the "≥1 field" rule.

## Upstream call (informative)

`PUT https://services.leadconnectorhq.com/contacts/{contactId}`
Body: only the changed camelCase fields (`firstName`, `lastName`, `email`, `phone`,
`source`); `None`s stripped by the shared `GHLClient`. No `locationId` in the body.
