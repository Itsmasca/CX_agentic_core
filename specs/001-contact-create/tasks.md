---
description: "Task list for Create Contact feature implementation"
---

# Tasks: Create Contact

**Input**: Design documents from `specs/001-contact-create/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/create-contact.md, quickstart.md

**Tests**: NOT requested in the spec (no suite exists yet). No test tasks are generated;
validation is manual via `quickstart.md`.

**Organization**: Tasks grouped by user story (US1 = create happy path, US2 = invalid/rejected feedback).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1, US2 (maps to spec.md user stories)
- All paths are relative to repo root; runtime CWD is `src/` per the import convention.

## Path Conventions

Single project, vertical-slice layout. New slice lives in `src/modules/contacts/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the slice package and ensure dependencies are present

- [X] T001 Create the contacts slice package directory `src/modules/contacts/` with an empty `src/modules/contacts/__init__.py` (router export added in T009)
- [X] T002 [P] Ensure `email-validator` is installed for pydantic `EmailStr`: run `uv add email-validator` if not already present (verify with `uv run python -c "import email_validator"`)
- [X] T003 [P] Confirm `.env` / `.env.example` document `GHL_TOKEN` and `GHL_LOCATION_ID` (no code change; prerequisite for running the slice)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Confirm shared core is in place — no new foundational code is required

**⚠️ CRITICAL**: This slice reuses existing core infrastructure; nothing new blocks the stories.

- [X] T004 Verify the shared `GHLClient` is reachable via `Depends(get_client)` (already provided by `src/core/deps.py`, `src/core/client.py`) and that `client.config.location_id` is available — no edits expected, this is a confirmation gate before story work

**Checkpoint**: Core (client, config, deps, errors, exception handler) confirmed — story implementation can begin.

---

## Phase 3: User Story 1 - Create a contact with core details (Priority: P1) 🎯 MVP

**Goal**: A consumer submits contact details and a contact is created in GHL for the configured location, returning the created contact with its assigned id.

**Independent Test**: `POST /contacts` with valid details returns `201` and a body containing `contact.id`; the contact appears in the GHL location (quickstart Scenario 1).

### Implementation for User Story 1

- [X] T005 [US1] Create `CreateContactRequest` schema in `src/modules/contacts/schemas.py` with snake_case fields and camelCase aliases per data-model.md: `first_name`→`firstName`, `last_name`→`lastName`, `email`, `phone`, `tags: list[str] | None`, `source`; set `model_config = {"populate_by_name": True}`. (Email type/identity validator added in US2 — start with `str | None` for email here.)
- [X] T006 [US1] Implement `ContactsService` in `src/modules/contacts/service.py`: constructor `__init__(self, client: GHLClient | None = None)` defaulting to `GHLClient()` and setting `self.location_id = self.client.config.location_id`; method `create_contact(*, first_name=None, last_name=None, email=None, phone=None, tags=None, source=None, location_id=None) -> dict` that builds a camelCase body (`firstName`, `lastName`, `email`, `phone`, `tags`, `source`, `locationId=location_id or self.location_id`) and returns `self.client.post("/contacts/", json=body)` (mirrors `CalendarService.create_appointment`)
- [X] T007 [US1] Implement the router in `src/modules/contacts/router.py`: `APIRouter(prefix="/contacts", tags=["contacts"])`, a `get_service` dependency over `Depends(get_client)`, a `ServiceDep` alias, and `@router.post("", status_code=201)` `create_contact(body: CreateContactRequest, service: ServiceDep)` mapping request fields to `service.create_contact(...)` (mirrors calendar's `create_appointment` route)
- [X] T008 [US1] Export `router` from `src/modules/contacts/__init__.py` (`from .router import router`)
- [X] T009 [US1] Register the slice in `src/server.py`: add `from modules.contacts import router as contacts_router` and `app.include_router(contacts_router)` next to the calendar registration
- [X] T010 [P] [US1] Add a `create_contact` FastMCP tool in `src/mcp_server.py` over a process-level `ContactsService(_client)` (instantiate `_contacts = ContactsService(_client)` alongside `_calendar`), accepting `first_name, last_name, email, phone, tags, source` and returning the created contact dict (mirrors calendar MCP tools)

**Checkpoint**: `POST /contacts` and the MCP tool create a contact and return it with an id. MVP is functional (quickstart Scenarios 1 & 2).

---

## Phase 4: User Story 2 - Clear feedback on invalid or rejected input (Priority: P2)

**Goal**: Identity-less or malformed input is rejected with a 422 before any GHL call; upstream rejections (auth, duplicate, errors) surface faithfully with the original status.

**Independent Test**: `POST /contacts` with no email/phone → `422`; with malformed email → `422`; with an invalid token → upstream `401/403` envelope, not `500` (quickstart Scenarios 3, 4, 5).

### Implementation for User Story 2

- [X] T011 [US2] In `src/modules/contacts/schemas.py`, change `email` to `EmailStr | None` (enforces FR-005 malformed-email rejection) — import `EmailStr` from pydantic
- [X] T012 [US2] In `src/modules/contacts/schemas.py`, add a `@model_validator(mode="after")` to `CreateContactRequest` enforcing that at least one of `email` or `phone` is present, raising a `ValueError` (→ 422) when both are missing (FR-004)
- [X] T013 [US2] Verify centralized upstream error translation requires no slice code: confirm `GHLClient` raises `GHLAPIError`/`GHLAuthError` and `server.py`'s `@app.exception_handler(GHLAPIError)` preserves the upstream status (no edits; document the confirmation in the PR per Constitution IV)

**Checkpoint**: Both stories work independently — happy path (US1) and validation/error feedback (US2).

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Lint, docs, and end-to-end validation

- [X] T014 [P] Run `uv run ruff check .` and `uv run ruff format .`; fix any findings in the new files
- [X] T015 [P] Update `CLAUDE.md` "What this is" note to reflect that `contacts` is now an implemented slice (no longer empty scaffolding)
- [X] T016 Run `quickstart.md` Scenarios 1–5 against a real GHL location and confirm expected status codes (covers SC-001…SC-004)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: After Setup; a confirmation gate (no new code).
- **US1 (Phase 3)**: After Foundational. Delivers the MVP.
- **US2 (Phase 4)**: After Foundational. Edits the same `schemas.py` US1 created, so in practice runs after T005; the rest is independent.
- **Polish (Phase 5)**: After the desired stories are complete.

### User Story Dependencies

- **US1 (P1)**: Independent — the create path. This is the MVP.
- **US2 (P2)**: Builds on the `CreateContactRequest` schema from US1 (T005). Logically separable (validation feedback) but touches the same file, so not file-parallel with T005.

### Within Each User Story

- US1: schema (T005) → service (T006) → router (T007) → export (T008) → register (T009); MCP tool (T010) only needs the service (T006).
- US2: schema edits (T011, T012) are sequential on the same file; T013 is a no-code confirmation.

### Parallel Opportunities

- T002 and T003 (Setup) run in parallel.
- T010 (MCP tool) can proceed in parallel with T007–T009 once the service (T006) exists (different file).
- T014 and T015 (Polish) run in parallel.

---

## Parallel Example: User Story 1

```bash
# After T006 (service) is done, these touch different files and can run together:
Task: "T007 Implement router in src/modules/contacts/router.py"
Task: "T010 Add create_contact MCP tool in src/mcp_server.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: Setup (T001–T003)
2. Phase 2: Foundational gate (T004)
3. Phase 3: User Story 1 (T005–T010)
4. **STOP and VALIDATE**: quickstart Scenarios 1 & 2 — a contact is created and returned.
5. Demo/deploy if ready.

### Incremental Delivery

1. Setup + Foundational → ready.
2. US1 → create works (MVP). Validate, demo.
3. US2 → validation + faithful error feedback. Validate (Scenarios 3–5), demo.
4. Polish → lint, docs, full quickstart run.

---

## Notes

- [P] = different files, no dependency on an incomplete task.
- [Story] label maps each task to its spec.md user story for traceability.
- No tests were requested; verify behavior via `quickstart.md`.
- Reuse the shared `GHLClient` — do NOT instantiate a client per request (Constitution II).
- Keep the snake_case↔camelCase mapping in `schemas.py`; the service speaks GHL camelCase (Constitution III).
- Add no custom error mapping in the slice; rely on centralized translation (Constitution IV).
- Commit after each task or logical group.
