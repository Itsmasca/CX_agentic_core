# Implementation Plan: Book Appointment for a Contact (find-or-create)

**Branch**: `003-book-appointment-for-contact` | **Date**: 2026-06-16 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/003-book-appointment-for-contact/spec.md`

## Summary

Add a **booking** composition slice that ties the existing `contacts` and `calendar` slices
together. It exposes (1) a find-or-create contact **resolver** and (2) a one-step **book
appointment for a contact** operation. A new `BookingService` reuses the shared `GHLClient`
and composes `ContactsService` + `CalendarService` (no GHL logic duplicated). Calendar is
auto-resolved (single calendar, configured default, or explicit id; ambiguous → surface the
list). Both capabilities are exposed over REST (`/booking/...`) and MCP. A small additive
config field carries an optional default calendar.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: FastAPI, httpx, pydantic v2, `mcp` (FastMCP), `email-validator` —
all present

**Storage**: None local; system of record is GoHighLevel (API V2)

**Testing**: No suite yet. Manual validation via `/docs` and `quickstart.md`.

**Target Platform**: Linux/macOS server (`uvicorn`), run from `src/`

**Project Type**: Single web-service backend (vertical slices over a third-party API)

**Performance Goals**: Resolve and one-step booking each within ~4s under normal upstream
conditions (SC-007); booking makes multiple upstream calls (resolve → maybe list calendars →
create appointment).

**Constraints**: Reuse the single shared `GHLClient`; run with CWD=`src/`; ruff clean; no
secrets in code. GHL contact search is eventually consistent → find-or-create dedup is
best-effort against very-recent creations.

**Scale/Scope**: One new composition slice; two operations on REST + MCP; one additive config
field. Reschedule/cancel, free-slot auto-selection, UI, tags/upsert are out of scope.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Evaluated against `.specify/memory/constitution.md` v1.0.0:

| Principle | Compliance |
|-----------|------------|
| I. Vertical Slice Isolation | ⚠️ **Documented exception.** The booking slice composes `ContactsService` and `CalendarService`, i.e. it imports two other slices' services. Principle I prohibits *peer* cross-slice imports. Booking is a deliberate higher-level **composition** that depends *downward* on the two domains (not a peer importing a peer). Justified in Complexity Tracking; the alternative (duplicating contact/calendar GHL calls, or putting orchestration in `core/`) is worse. The composed slices remain unmodified and independent. |
| II. Single Shared GHL Client | ✅ `BookingService` is built from the shared client (`Depends(get_client)`); it constructs `ContactsService(client)`/`CalendarService(client)` over that **same** client — no new HTTP client. MCP reuses the process-level client. |
| III. Explicit GHL Naming Boundary | ✅ Booking request schemas map snake_case↔camelCase; the service delegates GHL calls to the composed services. Responses are passthrough (FR-015), same documented exception as 001/002. |
| IV. Centralized Error Translation | ✅ All GHL calls flow through the composed services → `GHLClient` → `server.py` handler preserving upstream status. The non-atomic create-then-book path surfaces the booking error without inventing status (FR-014). |
| V. Environment-Sourced Config & Secrets | ✅ Location from config; new optional `GHL_DEFAULT_CALENDAR_ID` read via `GHLConfig.from_env()` — additive, no secret, no hard-coding. |

**Result**: PASS with one documented exception (Principle I — composition layering). See
Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/003-book-appointment-for-contact/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── resolve-contact.md
│   └── book-appointment.md
├── checklists/requirements.md
└── tasks.md            # /speckit-tasks output (NOT created here)
```

### Source Code (repository root)

```text
src/
├── core/
│   └── config.py               # + optional default_calendar_id (GHL_DEFAULT_CALENDAR_ID)
├── modules/
│   ├── calendar/               # unchanged (composed)
│   ├── contacts/               # unchanged (composed)
│   └── booking/                # NEW composition slice
│       ├── __init__.py         # exports `router`
│       ├── schemas.py          # ResolveContactRequest, BookAppointmentRequest (+ response shapes)
│       ├── service.py          # BookingService: resolve_contact(), book_appointment(), _resolve_calendar()
│       └── router.py           # POST /booking/resolve-contact, POST /booking/appointments
├── server.py                   # + include_router(booking_router)
└── mcp_server.py               # + resolve_contact + book_appointment MCP tools
```

**Structure Decision**: A new `booking` slice rather than extending `contacts` or `calendar`
— putting the orchestration in either domain would make that domain import the other
(worse). `BookingService` composes the two existing services over the shared client. The
one core touch is an **additive** optional config field for the default calendar.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| Principle I — `booking` imports `ContactsService` and `CalendarService` (cross-slice) | The feature's entire purpose is to compose the two domains into one operation. Reusing their services keeps GHL logic in one place (DRY) and over the shared client (Principle II). Booking is a layer *above* the domains, depending downward — not two peers entangling. | (a) Duplicating contact-search/create and appointment-create GHL calls inside booking → drift and double maintenance. (b) Moving orchestration into `core/` → pollutes the shared HTTP/config layer with domain business logic. (c) Forcing it into `contacts` or `calendar` → that domain then imports the other, a true peer cross-import, exactly what Principle I guards against. |
| Principle III — booking responses are unaliased camelCase GHL passthrough (contact, appointment) | Consistency with 001/002 and the calendar slice; avoids re-mapping composite payloads. FR-015 scopes snake_case to the request boundary. | A snake_case response model would duplicate both GHL contact and appointment shapes and drift over time, for no v1 consumer requirement. |

> Both exceptions are deliberate and bounded; all other principles remain fully satisfied.
> The composed `contacts`/`calendar` slices are not modified.
