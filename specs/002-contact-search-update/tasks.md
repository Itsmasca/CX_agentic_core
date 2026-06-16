---
description: "Task list for Search & Update Contacts feature implementation"
---

# Tasks: Search & Update Contacts

**Input**: Design documents from `specs/002-contact-search-update/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/{search-contacts,update-contact}.md, quickstart.md

**Tests**: NOT requested (no suite exists yet). No test tasks; validation is manual via `quickstart.md`.

**Organization**: Tasks grouped by user story (US1 = search/list, US2 = update). Extends the
existing `src/modules/contacts/` slice; no new package, and `server.py` needs no change
(`contacts_router` already mounted).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1 (search/list), US2 (update)
- Paths relative to repo root; runtime CWD is `src/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the existing slice and deps are ready — no new setup needed

- [X] T001 Confirm the `contacts` slice exists and is mounted (`src/modules/contacts/` with `router.py`/`service.py`/`schemas.py`; `contacts_router` included in `src/server.py`) and that `email-validator` is installed (from feature 001) — no edits, a readiness gate

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No new foundational code — reuses the shared core and existing `ContactsService`

- [X] T002 Verify `ContactsService.__init__` exposes `self.client` and `self.location_id` (added in feature 001) so new methods can reuse them — confirmation only, no edits

**Checkpoint**: Existing slice confirmed — story work can begin.

---

## Phase 3: User Story 1 - Find a contact to obtain its id (Priority: P1) 🎯 MVP

**Goal**: Search/list contacts in the configured location by email, phone, or free-text query (or list), returning each match with its id.

**Independent Test**: `GET /contacts?query=<known email>` returns the contact incl. `id`; `GET /contacts` (no query) lists contacts; a non-matching query returns `200` with an empty array (quickstart Scenarios 1–3).

### Implementation for User Story 1

- [X] T003 [US1] Add `search_contacts` to `ContactsService` in `src/modules/contacts/service.py`: signature `search_contacts(self, *, query: str | None = None, limit: int = 20) -> dict`; clamp `limit` to max 100; build body `{"locationId": self.location_id, "pageLimit": limit, "query": query}` and return `self.client.post("/contacts/search", json=body)` (None `query` is stripped by the client → list behavior)
- [X] T004 [US1] Add the search route in `src/modules/contacts/router.py`: `@router.get("")` `search_contacts(service: ServiceDep, query: str | None = None, limit: int = 20)` returning `service.search_contacts(query=query, limit=limit)` (GET on the same `/contacts` prefix; no collision with the existing POST create)
- [X] T005 [P] [US1] Add a `search_contacts` FastMCP tool in `src/mcp_server.py` over `_contacts`, signature `search_contacts(query: str | None = None, limit: int = 20)`, with a docstring noting its purpose is to resolve a `contact_id` (e.g. to then call `create_appointment`); returns the GHL search result

**Checkpoint**: Search/list works over REST and MCP; an agent can resolve a `contact_id`. MVP functional (quickstart 1–3).

---

## Phase 4: User Story 2 - Update an existing contact (Priority: P2)

**Goal**: Partially update a contact by id (first/last name, email, phone, source), sending only provided fields; validate ≥1 field and email format locally.

**Independent Test**: `PUT /contacts/{id}` with `{"first_name":"Augusta"}` changes only that field (others unchanged); empty body → `422`; malformed email → `422`; non-existent id → upstream `404` (quickstart Scenarios 4–7).

### Implementation for User Story 2

- [X] T006 [US2] Add `UpdateContactRequest` to `src/modules/contacts/schemas.py` per data-model.md: optional `first_name`→`firstName`, `last_name`→`lastName`, `email: EmailStr | None`, `phone`, `source`; `model_config = {"populate_by_name": True}`; add a `@model_validator(mode="after")` requiring at least one field present (raise `ValueError` → 422); add a `to_ghl_payload()` returning `self.model_dump(by_alias=True, exclude_none=True)` (mirrors calendar's `UpdateAppointmentRequest`)
- [X] T007 [US2] Add `update_contact` to `ContactsService` in `src/modules/contacts/service.py`: signature `update_contact(self, contact_id: str, **fields) -> dict` that returns `self.client.put(f"/contacts/{contact_id}", json=fields)` (fields are GHL camelCase keys; `None`s stripped by the client; do NOT include `locationId`)
- [X] T008 [US2] Add the update route in `src/modules/contacts/router.py`: `@router.put("/{contact_id}")` `update_contact(contact_id: str, body: UpdateContactRequest, service: ServiceDep)` returning `service.update_contact(contact_id, **body.to_ghl_payload())`
- [X] T009 [P] [US2] Add an `update_contact` FastMCP tool in `src/mcp_server.py` over `_contacts`, signature `update_contact(contact_id, first_name=None, last_name=None, email=None, phone=None, source=None)`; enforce ≥1 field (else raise `ValueError`); build the camelCase fields dict, strip `None`, and call `_contacts.update_contact(contact_id, **fields)` (mirrors the calendar `update_appointment` tool)

**Checkpoint**: Both stories functional independently — search (US1) and partial update (US2).

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Lint, docs, end-to-end validation

- [X] T010 [P] Run `uv run ruff check .` and `uv run ruff format .`; fix any findings in the changed files
- [X] T011 [P] Update `CLAUDE.md` contacts note to list the slice's operations (create, search/list, update)
- [X] T012 Run `quickstart.md` Scenarios 1–7 against a real GHL location, plus the SC-002 linkage check (use a searched `contact_id` to book an appointment)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)** + **Foundational (Phase 2)**: confirmation gates, no code; do first.
- **US1 (Phase 3)**: after gates. Delivers the MVP (search).
- **US2 (Phase 4)**: after gates. Independent of US1 in code (different additions), though
  in practice testing update is easier once search exists to find an id.
- **Polish (Phase 5)**: after the desired stories.

### User Story Dependencies

- **US1 (P1)**: independent — search/list. MVP.
- **US2 (P2)**: independent in code. Functionally complements US1 (search finds the id to
  update), but neither blocks the other's implementation.

### Within Each User Story

- US1: service `search_contacts` (T003) → route (T004); MCP tool (T005) needs only T003.
- US2: schema (T006) → route (T008); service `update_contact` (T007) is independent of the
  schema; MCP tool (T009) needs only T007.

### Parallel Opportunities

- T005 (MCP search) runs parallel to T004 once T003 exists (different files).
- T006 (schema) and T007 (service update) touch different files → parallel.
- T009 (MCP update) runs parallel to T008 once T007 exists.
- T010 and T011 (polish) run in parallel.
- US1 and US2 can be built in parallel by different people after the gates.

---

## Parallel Example: User Story 2

```bash
# Different files, no inter-dependency — can run together:
Task: "T006 Add UpdateContactRequest in src/modules/contacts/schemas.py"
Task: "T007 Add update_contact in src/modules/contacts/service.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + 2: confirmation gates (T001–T002)
2. Phase 3: search/list (T003–T005)
3. **STOP and VALIDATE**: quickstart Scenarios 1–3 — search returns ids; list works.
4. Demo/deploy if ready (the agent can now resolve contact ids).

### Incremental Delivery

1. Gates → ready.
2. US1 → search/list (MVP). Validate, demo.
3. US2 → partial update. Validate (Scenarios 4–7), demo.
4. Polish → lint, docs, full quickstart + SC-002 linkage.

---

## Notes

- No tests requested; validate via `quickstart.md`.
- Reuse the shared `GHLClient` and the existing `ContactsService` — no new client, no new
  package (Constitution I, II).
- Keep snake_case↔camelCase in `schemas.py`; service speaks GHL camelCase (Constitution III).
  Responses are passthrough per the documented exception (plan Complexity Tracking).
- No custom error mapping; rely on centralized translation — update to a non-existent id
  surfaces the upstream 404 automatically (Constitution IV).
- `server.py` is NOT modified; the router is already mounted.
- Commit after each task or logical group.
