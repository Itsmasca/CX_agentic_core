# Phase 0 Research: Book Appointment for a Contact

The endpoint shapes are already known from features 001/002 and the calendar slice; the open
questions here are orchestration/design choices, resolved below. No `NEEDS CLARIFICATION`
remained (spec Assumptions cover the defaults).

## R1 — Where the orchestration lives

- **Decision**: New `src/modules/booking/` slice with a `BookingService(client)` that
  internally constructs `ContactsService(client)` and `CalendarService(client)` over the
  **same shared** `GHLClient`.
- **Rationale**: Booking is a composition of two domains; it belongs in a layer above them,
  not inside either. Reusing the existing services avoids duplicating GHL calls and keeps the
  single-client guarantee (Principle II). Documented Principle-I layering exception (plan
  Complexity Tracking).
- **Alternatives considered**: extend `contacts`/`calendar` (forces a peer cross-import —
  worse); put orchestration in `core/` (pollutes the shared layer); duplicate GHL calls in
  booking (DRY violation, drift).

## R2 — Find-or-create matching strategy (avoid false positives)

- **Decision**: `resolve_contact(email?, phone?, first_name?, last_name?, source?)`:
  1. Require email or phone (reuse the identity rule), else 422.
  2. If `email`: `search_contacts(query=email)`, then look for a result whose `email` equals
     the provided email case-insensitively → if found, **matched**.
  3. Else/if not found and `phone`: `search_contacts(query=phone)`, look for a result whose
     `phone` equals the provided phone (normalized) → if found, **matched**.
  4. Otherwise `create_contact(...)` → **created**.
  Return `{contact, created: bool}`.
- **Rationale**: GHL `query` is fuzzy; requiring an **exact** field match among results
  prevents matching the wrong person (FR-003/FR-007 deterministic rule). Email preferred over
  phone. Satisfies SC-001/SC-002.
- **Alternatives considered**: trust the first fuzzy result → risks false matches; upstream
  upsert endpoint → out of scope (tags/upsert excluded) and changes semantics.

## R3 — Calendar auto-resolution

- **Decision**: `_resolve_calendar(explicit_calendar_id=None)` precedence:
  1. `explicit_calendar_id` if provided → use it.
  2. else `config.default_calendar_id` (new `GHL_DEFAULT_CALENDAR_ID`) if set → use it.
  3. else `list_calendars()`: exactly one → use it; zero → error ("no calendar available");
     multiple → **ambiguous**: do not guess, return the calendar list for the caller.
- **Rationale**: FR-010/FR-011. Keeps the common single-calendar case zero-config while never
  guessing when ambiguous.
- **Alternatives considered**: always require an explicit calendar (worse UX for the agent);
  pick the first of many (violates "do not guess", FR-011).

## R4 — Representing the "ambiguous calendar" outcome

- **Decision**: Booking returns HTTP `200` with a discriminated body:
  `{"status": "calendar_selection_required", "calendars": [ {id, name}... ]}` and creates no
  appointment. The success body is `{"status": "booked", "appointment": {...}, "contact":
  {...}, "contact_created": bool}`.
- **Rationale**: For the MCP/agent surface a structured 200 is easier to act on than an error
  code; the agent reads `status` and re-calls with a chosen `calendar_id`. FR-011/FR-012.
- **Alternatives considered**: `409 Conflict` — valid but turns a normal guided step into an
  "error" for the agent; rejected for ergonomics. Documented either way.

## R5 — Non-atomic create-then-book

- **Decision**: Resolve the contact first, then create the appointment. If appointment
  creation fails, the contact remains created (no rollback); the upstream error is surfaced.
- **Rationale**: GHL offers no cross-resource transaction; rollback (deleting a just-created
  contact) is riskier than leaving it. Documented in spec Assumptions; caller can retry
  booking with the now-existing contact. FR-014.
- **Alternatives considered**: delete the contact on booking failure → destructive and racy;
  rejected.

## R6 — Default-calendar configuration

- **Decision**: Add optional `default_calendar_id: str | None` to `GHLConfig`, read from
  `GHL_DEFAULT_CALENDAR_ID` in `from_env()`. Additive; absent = no default.
- **Rationale**: Principle V (env-sourced config). Smallest change; consistent with how
  `location_id` is sourced.
- **Alternatives considered**: a per-request default (no persistence) — doesn't help the
  zero-config agent case; a separate config file — unnecessary.

## R7 — REST & MCP surfaces

- **Decision**: REST `POST /booking/resolve-contact` and `POST /booking/appointments`; MCP
  tools `resolve_contact` and `book_appointment`. New `booking_router` mounted in
  `server.py`; tools added over a process-level `BookingService(_client)` in `mcp_server.py`.
- **Rationale**: POST for both (resolve may create; booking creates). Parity REST↔MCP
  (FR-016). The MCP `book_appointment` is the headline tool for a voice agent.
- **Alternatives considered**: GET for resolve — rejected, resolve has create side effects.
