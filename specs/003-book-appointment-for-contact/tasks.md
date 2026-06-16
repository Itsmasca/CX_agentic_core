---
description: "Task list for Book Appointment for a Contact (find-or-create)"
---

# Tasks: Book Appointment for a Contact (find-or-create)

**Input**: Design documents from `/specs/003-book-appointment-for-contact/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: No automated test suite exists for this project (plan.md: "No suite yet. Manual
validation via `/docs` and `quickstart.md`"). Test tasks are therefore **omitted**; validation
is the `quickstart.md` scenarios in the Polish phase.

**Organization**: Tasks are grouped by user story. Both stories are P1; US1 (resolve) is the
reusable core US2 (booking) composes, so US1 ships first as the MVP.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1 = find-or-create resolver; US2 = one-step booking
- All paths are relative to the repo root; the process runs from `src/` (import convention).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the new `booking` slice skeleton so subsequent files have a home.

- [X] T001 Create the booking slice package directory `src/modules/booking/` with empty
  `service.py`, `schemas.py`, `router.py`, and an `__init__.py` that will export `router`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Additive config field that calendar resolution (US2) depends on, and which must
exist before the service is wired. Safe for US1 too (US1 ignores it).

**⚠️ CRITICAL**: Must complete before user story phases.

- [X] T002 Add optional `default_calendar_id: str | None = None` field to `GHLConfig` and read
  it from `GHL_DEFAULT_CALENDAR_ID` in `GHLConfig.from_env()` in `src/core/config.py` (additive,
  no secret; absent = no default). Per research R6 / data-model "Config addition".

**Checkpoint**: Config carries the optional default calendar; slice package exists.

---

## Phase 3: User Story 1 - Resolve a contact intelligently (find-or-create) (Priority: P1) 🎯 MVP

**Goal**: Given email and/or phone (+ optional name/source), return a single contact flagged
`created: true|false`, creating it only when no exact match exists.

**Independent Test**: `POST /booking/resolve-contact` with an existing contact's email returns
`{contact, created: false}`; with brand-new identifiers returns `{contact, created: true}`;
with neither email nor phone returns `422` (quickstart Scenarios 1–3).

### Implementation for User Story 1

- [X] T003 [US1] Define `ResolveContactRequest` (snake_case: `email: EmailStr | None`,
  `phone`, `first_name`, `last_name`, `source`) and `ResolveResult` (`contact: dict`,
  `created: bool`) pydantic models in `src/modules/booking/schemas.py`, with a model validator
  enforcing "at least one of email/phone" (FR-002 → 422). Mirror the snake↔camel conventions
  used in `src/modules/contacts/schemas.py`.
- [X] T004 [US1] Implement `BookingService.__init__(self, client: GHLClient | None = None)` in
  `src/modules/booking/service.py` constructing `ContactsService(client)` and
  `CalendarService(client)` over the **same** shared client (no new HTTP client; Principle II).
- [X] T005 [US1] Implement `BookingService.resolve_contact(email, phone, first_name, last_name,
  source) -> dict` in `src/modules/booking/service.py` per research R2 / data-model: search by
  email then exact case-insensitive email match → matched; else search by phone then exact
  (normalized) phone match → matched; else `create_contact(...)` → created. Return
  `{"contact": ..., "created": bool}`. Reuse `self._contacts.search_contacts`/`create_contact`.
- [X] T006 [US1] Create `booking_router = APIRouter(prefix="/booking", tags=["booking"])` with
  `POST /booking/resolve-contact` in `src/modules/booking/router.py`, using
  `Depends(get_client)` → a `get_service` building `BookingService(client)` (pattern from
  `src/modules/contacts/router.py`); maps the request model to `resolve_contact(...)`.
- [X] T007 [US1] Export `router` from `src/modules/booking/__init__.py` and
  `app.include_router(booking_router)` in `src/server.py`.
- [X] T008 [US1] Add the `resolve_contact(email=None, phone=None, first_name=None,
  last_name=None, source=None) -> dict` MCP tool in `src/mcp_server.py`, delegating to the
  process-level `BookingService(_client)` (parity with existing contacts tools; FR-016).

**Checkpoint**: US1 fully functional — resolve works over REST and MCP, independently of US2.

---

## Phase 4: User Story 2 - Book an appointment for a contact in one step (Priority: P1)

**Goal**: From identifiers + `start_time` (+ optional end/title/calendar), resolve the contact,
auto-resolve the calendar, and create the appointment in one request — or, when the calendar is
ambiguous, return the calendar list without booking.

**Independent Test**: `POST /booking/appointments` with a known email + future `start_time` +
explicit `calendar_id` returns `{status:"booked", appointment, contact, contact_created:false}`;
with a new person returns `contact_created:true`; with multiple calendars and no default/explicit
returns `{status:"calendar_selection_required", calendars:[...]}` and creates nothing; missing
`start_time` returns `422` (quickstart Scenarios 4–7).

### Implementation for User Story 2

- [X] T009 [US2] Add `BookAppointmentRequest` (US1 identifier fields + `start_time: str`
  (required), `end_time`, `title`, `calendar_id` all optional) and the discriminated booking
  response shapes (`booked` and `calendar_selection_required`) to
  `src/modules/booking/schemas.py`, validating `start_time` present AND (email or phone) present
  (FR-009 → 422). Per data-model "Book (one-step)".
- [X] T010 [US2] Implement `BookingService._resolve_calendar(explicit_calendar_id=None)` in
  `src/modules/booking/service.py` per research R3: explicit id → `config.default_calendar_id`
  → `list_calendars()` (exactly one → use; zero → error "no calendar available"; multiple →
  signal ambiguous with the `[{id,name}]` list). Reuse `self._calendar.list_calendars`.
- [X] T011 [US2] Implement `BookingService.book_appointment(start_time, email, phone,
  first_name, last_name, source, end_time, title, calendar_id) -> dict` in
  `src/modules/booking/service.py`: resolve contact (reuse `resolve_contact`, T005) → resolve
  calendar (T010); if ambiguous return `{"status":"calendar_selection_required","calendars":...}`
  with no appointment (FR-011); else `create_appointment(...)` and return
  `{"status":"booked","appointment":...,"contact":...,"contact_created":bool}`. Non-atomic: on
  appointment failure the contact remains, surface the upstream error (research R5, FR-014).
- [X] T012 [US2] Add `POST /booking/appointments` to `src/modules/booking/router.py` mapping
  `BookAppointmentRequest` → `book_appointment(...)` and returning the discriminated body
  (HTTP 200 for both `booked` and `calendar_selection_required`; research R4).
- [X] T013 [US2] Add the `book_appointment(start_time, email=None, phone=None, first_name=None,
  last_name=None, source=None, end_time=None, title=None, calendar_id=None) -> dict` MCP tool in
  `src/mcp_server.py`, delegating to the process-level `BookingService(_client)` (FR-016; the
  headline voice-agent tool, research R7).

**Checkpoint**: US1 AND US2 both work over REST and MCP.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Verify, lint, and confirm the slice end-to-end.

- [X] T014 [P] Run `uv run ruff check .` and `uv run ruff format .` from the repo root; fix any
  findings in the new `src/modules/booking/` files, `src/core/config.py`, `src/server.py`, and
  `src/mcp_server.py`.
- [ ] T015 Run the `quickstart.md` Scenarios 1–7 against a real GHL location (server from
  `src/`); confirm resolve matched/created/422 and booking booked/selection-required/422 behave
  as documented, and that Scenarios 4/5 produce appointments visible in GHL.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: none — start immediately.
- **Foundational (Phase 2 / T002)**: after Setup; required by US2 calendar resolution.
- **US1 (Phase 3)**: after Setup. Does not depend on T002. The MVP.
- **US2 (Phase 4)**: after Foundational (T002) and US1 (reuses `resolve_contact` from T005 and
  the slice scaffolding T004/T006/T007 from US1).
- **Polish (Phase 5)**: after the user stories you intend to ship.

### User Story Dependencies

- **US1 (P1)**: independent — the reusable resolver. Shippable alone.
- **US2 (P1)**: builds on US1 (calls `resolve_contact`) and on T002; still independently
  testable via its own endpoint/tool.

### Within Each User Story

- schemas → service → router → `__init__`/server wiring → MCP tool.
- US1's `BookingService.__init__` (T004) must precede US1's service method (T005) and all US2
  service methods (T010, T011).

### Parallel Opportunities

- T014 (ruff) is the only [P] task; most tasks touch the same three files
  (`service.py`, `schemas.py`, `router.py`) and are therefore sequential within a story.
- Across stories: once T004/T005 exist, US2's schema task (T009) could be drafted alongside US1
  wiring, but to avoid edit conflicts in shared files, run US1 → US2 sequentially as listed.

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1 Setup (T001) → Phase 2 Foundational (T002) → Phase 3 US1 (T003–T008).
2. **STOP and VALIDATE**: quickstart Scenarios 1–3 (resolve matched/created/422).
3. Ship the resolver — any flow needing "get me the id for this person" can use it.

### Incremental Delivery

1. Setup + Foundational + US1 → resolve over REST + MCP (MVP).
2. Add US2 (T009–T013) → one-step booking over REST + MCP.
3. Polish (T014–T015) → ruff clean + full quickstart pass.

---

## Notes

- [P] = different files, no dependencies. [Story] maps tasks to US1/US2 for traceability.
- The composed `contacts`/`calendar` slices are NOT modified (plan Complexity Tracking).
- Responses are GHL passthrough (camelCase) per FR-015; only request inputs are snake_case.
- Find-or-create dedup is best-effort against very-recent creations (GHL search eventual
  consistency) — documented limitation, not a bug.
- Commit after each task or logical group; run from `src/` per the import convention.
