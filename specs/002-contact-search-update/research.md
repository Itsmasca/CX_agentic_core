# Phase 0 Research: Search & Update Contacts

Unknowns were the GHL V2 endpoint shapes for search and update. Resolved below; the spec
carried no open `NEEDS CLARIFICATION` (defaults are in its Assumptions).

## R1 — Search endpoint: `POST /contacts/search` vs deprecated `GET /contacts/`

- **Decision**: Use `POST /contacts/search` with a body of `{"locationId": <cfg>,
  "pageLimit": <limit>, "query": <text?>}`. When no `query` is given, the same call with
  just `locationId` + `pageLimit` returns the location's contacts (the "list" case).
- **Rationale**: GHL has **deprecated `GET /contacts/`** and recommends the search
  endpoint. Its top-level `query` string matches across name/email/phone, so the spec's
  three criteria (email, phone, free-text) collapse into one mechanism — the service picks
  the most specific provided value (email → phone → query) and passes it as `query`,
  satisfying FR-001/002/003/004 with a single call. Response is `{"contacts": [...],
  "total": <n>}`.
- **Alternatives considered**:
  - `GET /contacts/?locationId=&query=&limit=` — simpler but **deprecated**; rejected as the
    primary path. Kept as a documented fallback (R5) if the search body is rejected.
  - Advanced `filters`/`sort` DSL on `POST /contacts/search` — more powerful but the filter
    schema is complex and overkill for "find by email/phone/name"; rejected for v1.
- **Risk/Fallback** (R5): if a bare top-level `query` is not honored by the account's API
  version, fall back to `GET /contacts/` with `query`/`limit`, or to a minimal `filters`
  payload. The service isolates this in one method so the switch is localized.

## R2 — Update endpoint: `PUT /contacts/{contactId}`

- **Decision**: Use `PUT /contacts/{contactId}` with a camelCase body containing only the
  changed fields (`firstName`, `lastName`, `email`, `phone`, `source`); omit `None`s (the
  `GHLClient` already strips them). Do **not** send `locationId` in the update body — the
  contact already belongs to a location. Response is `{"contact": {...}}`.
- **Rationale**: Satisfies FR-009/010/011/014. Partial update = send only present fields,
  which the existing client-side None-stripping makes natural. Mirrors how the calendar
  slice's `update_appointment` forwards only non-empty fields.
- **Alternatives considered**: A full-replace PUT requiring all fields — rejected; the spec
  mandates partial update (FR-010) and replacing would risk clearing data.

## R3 — Partial-update validation (≥1 changeable field, email format)

- **Decision**: An `UpdateContactRequest` schema with all fields optional, `email` typed as
  `EmailStr | None` (FR-012), and a model validator requiring at least one changeable field
  present (FR-013) → 422 before any upstream call.
- **Rationale**: Local 422 avoids a wasted/again-destructive round-trip and gives a precise
  error. Reuses the exact pattern from the create feature's identity validator.
- **Alternatives considered**: Letting GHL reject empty updates — rejected; weaker, costs a
  round-trip, less precise error.

## R4 — REST verb/path mapping

- **Decision**: `GET /contacts` (search/list, query params `query`, `limit`) and
  `PUT /contacts/{contact_id}` (update). `POST /contacts` (create) already exists.
- **Rationale**: Clean REST semantics, no route collisions on the shared `/contacts`
  prefix. GET for a read/search is idiomatic even though the upstream call is a POST search
  — the service hides that.
- **Alternatives considered**: `POST /contacts/search` at our boundary too — rejected;
  exposes an upstream implementation detail and is less idiomatic for a read.

## R5 — Default and maximum result limit

- **Decision**: Default `limit = 20`; allow the consumer to override; cap effective limit at
  the GHL maximum of **100** per page.
- **Rationale**: Matches GHL's documented defaults (20 default, 100 max per request).
  Satisfies FR-008. Exhaustive pagination across pages is out of scope (spec Assumptions).
- **Alternatives considered**: Auto-paginate to fetch all — rejected; out of scope and
  unbounded latency/cost for v1.

## R6 — MCP exposure & error handling

- **Decision**: Add `search_contacts` and `update_contact` FastMCP tools over the existing
  process-level `_contacts` service. No slice-specific error handling — `GHLClient` raises
  `GHLAPIError`/`GHLAuthError` and `server.py`'s handler preserves upstream status (FR-015;
  e.g. update to a non-existent id surfaces the upstream 404).
- **Rationale**: Parity with calendar + create-contact (Constitution II, IV); the MCP
  search tool is what makes the agent able to resolve a `contact_id` before booking.
- **Alternatives considered**: REST-only — rejected; the agent (MCP) surface is the primary
  motivation for search (obtaining an id to book an appointment).

## Sources

- GHL deprecates `GET /contacts/` in favor of Search Contacts:
  https://marketplace.gohighlevel.com/docs/ghl/contacts/get-contacts/index.html
- Search Contacts (advanced), `POST /contacts/search` (locationId, page, pageLimit,
  filters, sort): https://marketplace.gohighlevel.com/docs/ghl/contacts/search-contacts-advanced/index.html
- Pagination/limits (default 20, max 100 per request):
  https://medium.com/@tuguidragos/fetch-all-gohighlevel-contacts-with-n8n-api-pagination-explained-25621d6e6976
