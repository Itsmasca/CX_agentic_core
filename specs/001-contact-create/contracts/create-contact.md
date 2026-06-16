# Contract: Create Contact

## REST endpoint

`POST /contacts`

Creates a contact in GoHighLevel for the configured location.

### Request body (application/json)

Public boundary is snake_case (aliases accept camelCase too).

```json
{
  "first_name": "Ada",
  "last_name": "Lovelace",
  "email": "ada@example.com",
  "phone": "+15551234567",
  "tags": ["lead", "newsletter"],
  "source": "website-form"
}
```

- All fields optional individually, BUT at least one of `email` or `phone` MUST be present.
- `email`, if present, must be a valid email address.
- The location is taken from server config and MUST NOT be supplied by the caller.

### Responses

| Status | When | Body |
|--------|------|------|
| `201 Created` | Contact created | The created contact, e.g. `{ "contact": { "id": "...", "firstName": "Ada", ... } }` |
| `422 Unprocessable Entity` | Neither email nor phone provided, or malformed email | FastAPI validation error detail |
| `401 / 403` | Upstream auth failure (invalid/expired token or no permission) | `{ "error": "ghl_api_error", "detail": "[401] ...", "payload": ... }` |
| `4xx / 5xx` (passthrough) | GHL rejected the create (e.g. duplicate) or upstream error | Same error envelope, original GHL status preserved |

Success status code is `201` (matches the calendar create endpoint convention).

### Acceptance mapping

- 201 with a `contact.id` → FR-001, FR-002, FR-003, FR-006, SC-001
- 422 on identity-less / malformed input → FR-004, FR-005, SC-002
- Passthrough of upstream status → FR-007, SC-003
- snake_case request accepted → FR-008

## MCP tool

`create_contact(first_name=None, last_name=None, email=None, phone=None, tags=None, source=None) -> dict`

Same semantics as the REST endpoint (identity rule enforced in the service/schema path),
returning the created contact dict. Mirrors the calendar MCP tools and reuses the shared
process-level client.

## Upstream call (informative)

`POST https://services.leadconnectorhq.com/contacts/`
Headers: `Authorization: Bearer <pit-token>`, `Version: 2021-04-15`, `Accept: application/json`
Body: camelCase fields + injected `locationId`. (Handled by the shared `GHLClient`.)
