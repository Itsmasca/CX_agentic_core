# Contract: Search / List Contacts

## REST endpoint

`GET /contacts`

Searches or lists contacts in the configured location.

### Query parameters

| Param | Type | Default | Notes |
|-------|------|---------|-------|
| `query` | string | — | Free text; matches name/email/phone. Omit to list. |
| `limit` | int | 20 | Capped at 100. |

Location is taken from server config; not a parameter.

### Responses

| Status | When | Body |
|--------|------|------|
| `200 OK` | Search/list succeeded (incl. zero matches) | `{ "contacts": [ {contact}... ], "total": <n> }` |
| `401 / 403` | Upstream auth failure | `{ "error": "ghl_api_error", "detail": "[401] ...", "payload": ... }` |
| `4xx / 5xx` (passthrough) | Other upstream error | Same envelope, original GHL status preserved |

Zero matches returns `200` with an empty `contacts` array — NOT an error (FR-007).

### Acceptance mapping

- 200 with matching contact incl. `id` (by email/phone/query) → FR-001/002/003/006, SC-001
- 200 list when no `query` → FR-004
- 200 empty array on no match → FR-007, SC-005
- Result bounded by `limit` (default 20, max 100) → FR-008
- Upstream status preserved → FR-015

## MCP tool

`search_contacts(query: str | None = None, limit: int = 20) -> dict`

Returns the GHL search result (`contacts` + `total`). Primary use: resolve a `contact_id`
to pass to `create_appointment`.

## Upstream call (informative)

`POST https://services.leadconnectorhq.com/contacts/search`
Body: `{ "locationId": "<config>", "pageLimit": <limit>, "query": "<text?>" }`
Headers handled by the shared `GHLClient`.
