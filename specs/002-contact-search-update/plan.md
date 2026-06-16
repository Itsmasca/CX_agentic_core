# Implementation Plan: Search & Update Contacts

**Branch**: `002-contact-search-update` | **Date**: 2026-06-15 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/002-contact-search-update/spec.md`

## Summary

Extend the existing `contacts` slice with two operations: **search/list** and **partial
update**. Search uses GHL V2 `POST /contacts/search` (the recommended, non-deprecated
endpoint) with a simple `query` string that matches across name/email/phone — so the
spec's email/phone/query criteria collapse to one mechanism (precedence email→phone→query
resolved in the service). Update uses `PUT /contacts/{contactId}` sending only the changed
fields. Both are exposed as REST endpoints (`GET /contacts`, `PUT /contacts/{id}`) and MCP
tools, reusing the shared `GHLClient` and the patterns established by create-contact.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: FastAPI, httpx, pydantic v2, `mcp` (FastMCP) — all present;
`email-validator` (added in feature 001) for `EmailStr`

**Storage**: None local; system of record is GoHighLevel (API V2, LeadConnector)

**Testing**: No suite yet. Manual validation via `/docs` and `quickstart.md`.

**Target Platform**: Linux/macOS server process (`uvicorn`), run from `src/`

**Project Type**: Single web-service backend (vertical slices over a third-party API)

**Performance Goals**: Search/list and update each return within ~2s under normal upstream
conditions (SC-006); bounded by the GHL round-trip.

**Constraints**: Reuse the single shared `GHLClient`; run with CWD=`src/`; ruff clean
(py313, line length 88); no secrets in code.

**Scale/Scope**: Two operations added to an existing slice (search + update), each on REST
and MCP. Default single-page results; tags/upsert/get-by-id/delete are out of scope.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Evaluated against `.specify/memory/constitution.md` v1.0.0:

| Principle | Compliance |
|-----------|------------|
| I. Vertical Slice Isolation | ✅ All changes stay in `src/modules/contacts/`; `server.py`/`mcp_server.py` only add routes/tools. No cross-slice import (the calendar linkage is via returned ids, not code coupling). |
| II. Single Shared GHL Client | ✅ New service methods on the existing `ContactsService`, called through the shared client via `Depends(get_client)`; MCP reuses `_contacts`. |
| III. Explicit GHL Naming Boundary | ✅ New request schema(s) map snake_case↔camelCase; service speaks GHL camelCase. Response is a documented passthrough (same exception recorded for create, FR-016). |
| IV. Centralized Error Translation | ✅ Upstream errors (404 not-found on update, 401/403) flow through `GHLClient` → `server.py` handler preserving status. No custom mapping. |
| V. Environment-Sourced Config & Secrets | ✅ `locationId` injected from `client.config.location_id`; no new credentials; nothing logged/hard-coded. |

**Result**: PASS — no violations. Complexity Tracking carries forward only the create
feature's documented response-passthrough exception (Principle III), which this feature
reuses for consistency.

## Project Structure

### Documentation (this feature)

```text
specs/002-contact-search-update/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── search-contacts.md
│   └── update-contact.md
├── checklists/requirements.md
└── tasks.md            # /speckit-tasks output (NOT created here)
```

### Source Code (repository root)

```text
src/
├── modules/
│   └── contacts/               # EXISTING slice — extended
│       ├── schemas.py          # + UpdateContactRequest (partial, ≥1 field)
│       ├── service.py          # + search_contacts(...) + update_contact(...)
│       └── router.py           # + GET /contacts (search/list) + PUT /contacts/{id}
├── server.py                   # unchanged (router already mounted)
└── mcp_server.py               # + search_contacts + update_contact MCP tools
```

**Structure Decision**: Extend the existing `contacts` slice in place (no new package).
`server.py` needs no change — `contacts_router` is already mounted; new routes attach to it.
REST verbs are split cleanly: `POST /contacts` (create, feature 001), `GET /contacts`
(search/list), `PUT /contacts/{id}` (update) — no collisions.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| Principle III — returned contacts are unaliased camelCase GHL passthrough (search results and updated contact), not re-mapped to snake_case | Consistency with the create-contact feature (same slice, same entity) and with the `calendar` slice; avoids maintaining a second contact representation that would drift from upstream. FR-016 scopes snake_case to the request boundary. | A snake_case response model would duplicate GHL's contact shape for every result in a list, drift over time, and diverge from the slice's established pattern for no consumer-facing v1 requirement. |

> Scope of exception: response payloads only. Request boundaries, request↔GHL mapping,
> error translation, shared client, and slice isolation remain fully compliant.
