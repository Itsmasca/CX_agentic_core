# Phase 0 Research: Create Contact

All Technical Context items resolved against the existing codebase and GHL API V2. No
open `NEEDS CLARIFICATION` remained from the spec (defaults were captured in its
Assumptions section).

## R1 — GHL "create contact" endpoint shape

- **Decision**: Call `POST /contacts/` on GHL API V2 (base `services.leadconnectorhq.com`,
  `Version: 2021-04-15` header), with a JSON body in camelCase:
  `firstName`, `lastName`, `email`, `phone`, `locationId`, `tags` (array of strings),
  `source`. Expect a `2xx` response whose body is `{"contact": { "id": ..., ... }}`.
- **Rationale**: Matches the V2 contacts contract and the same auth/version headers the
  shared `GHLClient` already injects. `locationId` is required by GHL and is supplied from
  config, satisfying FR-003.
- **Alternatives considered**:
  - V1 `rest.gohighlevel.com` — rejected; constitution and CLAUDE.md target V2 only.
  - "Upsert" endpoint (`POST /contacts/upsert`) — rejected for v1; spec delegates duplicate
    handling to GHL's default create behavior (Assumptions), and upsert changes semantics.

## R2 — Identity validation (email-or-phone)

- **Decision**: Enforce "at least one of email or phone" at the schema boundary with a
  pydantic model validator, returning a 422 validation error before any GHL call. Validate
  email format with pydantic's `EmailStr`.
- **Rationale**: Satisfies FR-004/FR-005 and SC-002 (100% of identity-less requests
  rejected, no contact created) without a wasted upstream round-trip. Keeps the rule
  explicit and testable at the public boundary.
- **Alternatives considered**:
  - Let GHL reject identity-less payloads — rejected; weaker guarantee, costs a round-trip,
    and yields a less precise error than a local 422.
  - Free-form `str` email — rejected; misses malformed-email validation (FR-005).
- **Dependency note**: `EmailStr` requires `email-validator`. Confirm it is installed; if
  not, `uv add email-validator`. (Captured as a task in `/speckit-tasks`.)

## R3 — Mirroring the calendar slice conventions

- **Decision**: Reproduce the calendar slice's exact structure: `schemas.py` with
  `Field(alias=...)` + `model_config = {"populate_by_name": True}`; `service.py` with
  `ContactsService(client=None)` defaulting to `GHLClient()` and reading
  `self.location_id = self.client.config.location_id`; `router.py` with a `get_service`
  dependency over `Depends(get_client)` and a `ServiceDep` alias.
- **Rationale**: Constitution Principles I–III; consistency makes the slice reviewable
  against a known-good reference and keeps the naming boundary in one place.
- **Alternatives considered**: A bespoke structure — rejected; violates slice-isolation
  conventions and adds review friction for no benefit.

## R4 — Error handling

- **Decision**: Do nothing slice-specific. `GHLClient._handle` already raises
  `GHLAuthError` (401/403) and `GHLAPIError` (other non-2xx); `server.py`'s
  `@app.exception_handler(GHLAPIError)` re-emits them preserving the upstream status code.
- **Rationale**: Constitution Principle IV and FR-007/SC-003 — upstream rejections
  (auth, duplicate, unreachable) surface faithfully with no false "created" response.
- **Alternatives considered**: Custom try/except in the service mapping GHL errors to local
  codes — rejected; duplicates centralized logic and risks divergent status semantics.

## R5 — MCP exposure

- **Decision**: Add a `create_contact` FastMCP tool in `mcp_server.py` that calls a
  process-level `ContactsService(_client)`, mirroring the calendar tools (same shared
  `_client`).
- **Rationale**: The project exposes every calendar capability over both REST and MCP;
  parity keeps the agent surface consistent. Reuses the single client (Principle II).
- **Alternatives considered**: REST-only for v1 — viable, but diverges from the established
  pattern; included to keep surfaces aligned. Low cost (thin wrapper).

## R6 — Response model

- **Decision**: Return the created contact as returned by GHL (the `contact` object),
  passed through. Optionally define a lightweight response schema later; for v1 return the
  service result directly like the calendar create endpoint does.
- **Rationale**: FR-006 only requires returning the created contact incl. its identifier;
  the calendar slice returns the raw GHL dict, so parity is simplest and sufficient.
- **Alternatives considered**: A strict typed response model — deferred; adds maintenance
  with no v1 requirement. Public *request* naming is already snake_case (FR-008); the
  returned GHL object is the system-of-record representation.
