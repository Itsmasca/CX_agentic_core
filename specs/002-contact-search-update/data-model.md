# Phase 1 Data Model: Search & Update Contacts

No local persistence. Shapes below cover the request boundary (snake_case) and the payloads
sent to GHL (camelCase). Returned contacts are a GHL passthrough (FR-016).

## Search / List

### Input: Contact Search Criteria (query params on `GET /contacts`)

| Public param | Type | Required | Notes |
|--------------|------|----------|-------|
| `query` | `str \| None` | No | Free text; matches name/email/phone upstream. Absence → list. |
| `limit` | `int` | No | Default 20; capped at 100 (GHL max per page). |

- The service accepts the most specific identifying value as `query`. Callers searching by
  email or phone simply pass that value as `query` (precedence email→phone→query is applied
  by callers/MCP tool args; at the HTTP boundary it is a single `query`).
- No `location` param — injected from config (FR-005).

### Payload sent to GHL (`POST /contacts/search`)

```jsonc
{
  "locationId": "<from config>",
  "pageLimit": 20,
  "query": "ada@example.com"   // omitted entirely when listing
}
```

### Response (passthrough)

```jsonc
{ "contacts": [ { "id": "...", "firstName": "Ada", "email": "...", ... } ], "total": 1 }
```

Returned to the consumer as-is. Empty match → `{"contacts": [], "total": 0}` (FR-007, not an
error).

## Update

### Entity: Contact Update Request (`UpdateContactRequest`)

Body of `PUT /contacts/{contact_id}`. All fields optional; `populate_by_name=True`.

| Public field (snake_case) | GHL alias | Type | Notes |
|---------------------------|-----------|------|-------|
| `first_name` | `firstName` | `str \| None` | |
| `last_name` | `lastName` | `str \| None` | |
| `email` | `email` | `EmailStr \| None` | Validated if present (FR-012) |
| `phone` | `phone` | `str \| None` | |
| `source` | `source` | `str \| None` | |

The contact id comes from the path, not the body.

### Validation rules

- **V1 (at least one field, FR-013)**: at least one of the five fields MUST be present; else
  422, no upstream call.
- **V2 (email format, FR-012)**: if `email` present, must be well-formed.
- **V3 (no location)**: `locationId` is NOT sent in the update body (contact already belongs
  to its location).

### Payload sent to GHL (`PUT /contacts/{contactId}`)

```jsonc
{ "firstName": "Augusta", "source": "manual-edit" }   // only the provided fields; None stripped
```

### Response (passthrough)

```jsonc
{ "contact": { "id": "...", "firstName": "Augusta", ... } }
```

## State

- Search/list: read-only; no state change.
- Update: single transition — *(existing contact)* → *(contact with provided fields
  changed)*; omitted fields unchanged (FR-010). Non-existent id → upstream not-found, no
  change (FR-015).

## Relationship to other slices

A `Contact.id` obtained from search is the `contact_id` input to the calendar slice's
create-appointment — this is the linkage targeted by SC-002. Coupling is by value (the id),
not by code (Constitution I preserved).
