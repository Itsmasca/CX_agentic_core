# Implementation Plan: Create Contact

**Branch**: `001-contact-create` | **Date**: 2026-06-15 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-contact-create/spec.md`

## Summary

Add a **Contacts** vertical slice whose first capability is creating a contact in
GoHighLevel for the configured location. Implementation mirrors the existing `calendar`
slice exactly: a `ContactsService` wrapping the shared `GHLClient`, snake_case↔camelCase
pydantic schemas, an `APIRouter` mounted in `server.py`, and (matching the project
pattern) an MCP tool exposing the same service method. The create call is `POST /contacts/`
on GHL API V2; the location is injected from config, never from the caller.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: FastAPI, httpx, pydantic v2, `mcp` (FastMCP) — all already present

**Storage**: None local; system of record is GoHighLevel (API V2, LeadConnector)

**Testing**: No suite yet. Manual validation via `/docs` and a `quickstart.md` script.
(If/when tests are added: `uv run pytest`, `uv add --dev pytest`.)

**Target Platform**: Linux/macOS server process (`uvicorn`), run from `src/`

**Project Type**: Single web-service backend (vertical slices over a third-party API)

**Performance Goals**: Single create returns within ~2s under normal upstream conditions
(SC-004); bounded by the GHL round-trip, not local compute.

**Constraints**: Must reuse the single shared `GHLClient`; must run with CWD=`src/`; ruff
clean (py313, line length 88); no secrets in code.

**Scale/Scope**: One new slice, one write endpoint + one MCP tool. Read/update/search/
delete and bulk creation are explicitly out of scope for v1.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Evaluated against `.specify/memory/constitution.md` v1.0.0:

| Principle | Compliance |
|-----------|------------|
| I. Vertical Slice Isolation | ✅ New `src/modules/contacts/` with own `router.py`/`schemas.py`/`service.py`; exports `router` from `__init__.py`; mounted in `server.py`. No import of any other slice. |
| II. Single Shared GHL Client | ✅ `ContactsService(client)` built via `get_service` → `Depends(get_client)`; no per-request client. MCP tool reuses the process-level `_client` like calendar does. |
| III. Explicit GHL Naming Boundary | ✅ `schemas.py` maps snake_case ↔ camelCase via `Field(alias=...)` + `populate_by_name=True`; service speaks GHL camelCase keys. No epoch dates involved here. |
| IV. Centralized Error Translation | ✅ All calls go through `GHLClient`, which raises `GHLAPIError`/`GHLAuthError`; `server.py`'s handler preserves upstream status. Slice adds no custom status mapping. |
| V. Environment-Sourced Config & Secrets | ✅ `location_id` read from `client.config.location_id`; no credentials introduced; nothing logged or hard-coded. |

**Result**: PASS — no violations. Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/001-contact-create/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── create-contact.md  # POST /contacts endpoint contract
├── checklists/
│   └── requirements.md  # Spec quality checklist (from /speckit-specify)
└── tasks.md             # /speckit-tasks output (NOT created here)
```

### Source Code (repository root)

```text
src/
├── core/                       # unchanged (client, config, deps, errors)
├── modules/
│   ├── calendar/               # reference implementation (unchanged)
│   └── contacts/               # NEW slice
│       ├── __init__.py         # exports `router`
│       ├── schemas.py          # CreateContactRequest (+ optional response model)
│       ├── service.py          # ContactsService.create_contact(...)
│       └── router.py           # APIRouter(prefix="/contacts"), POST ""
├── server.py                   # add: include_router(contacts_router)
└── mcp_server.py               # add: create_contact MCP tool over ContactsService
```

**Structure Decision**: Single project, vertical-slice layout (Option 1). The new
`contacts` package sits beside `calendar` under `src/modules/`. Note the empty
`src/modules/Conversaciones|Subaccount|User|Admin` scaffolds are untouched; this slice is
lowercase `contacts` to match the active `calendar` convention.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| Principle III — the created contact is returned as an unaliased camelCase GHL passthrough rather than re-mapped to snake_case in a public response model | The response is the system-of-record contact; passing it through keeps it faithful to GHL, matches the existing `calendar` slice exactly, and avoids maintaining a second contact representation. FR-008 is scoped to the request boundary. | Adding a snake_case response schema would duplicate GHL's contact shape, drift from upstream fields over time, and diverge from the established calendar pattern for no consumer-facing requirement (v1 only needs the created contact + its id). |

> Scope of exception: applies only to the **response** payload of the create endpoint. The
> **request** boundary, the request↔GHL mapping, error translation (IV), shared client (II),
> and slice isolation (I) all remain fully compliant.
