# Quickstart: Book Appointment for a Contact

Validates find-or-create resolve and one-step booking end-to-end against a real GHL location.

## Prerequisites

- `.env` with `GHL_TOKEN` and `GHL_LOCATION_ID`. Optionally `GHL_DEFAULT_CALENDAR_ID` (a
  calendar id from `GET /calendar/calendars`) to make ambiguous bookings deterministic.
- Deps synced (`uv sync`).
- Know one existing contact's email (e.g. `ada+quickstart@example.com` from feature 001) and
  at least one calendar id (from `GET /calendar/calendars`).

## Run the server

```bash
cd src && uvicorn server:app --reload   # docs at http://127.0.0.1:8000/docs
```

## Scenario 1 — Resolve an existing contact → matched (FR-003, SC-002)

```bash
curl -i -X POST http://127.0.0.1:8000/booking/resolve-contact \
  -H "Content-Type: application/json" -d '{ "email": "ada+quickstart@example.com" }'
```

**Expected**: `200`, `{ "contact": {...id...}, "created": false }`.

## Scenario 2 — Resolve a brand-new person → created (FR-004, SC-001)

```bash
curl -i -X POST http://127.0.0.1:8000/booking/resolve-contact \
  -H "Content-Type: application/json" \
  -d '{ "phone": "+15557770001", "first_name": "New", "last_name": "Person" }'
```

**Expected**: `200`, `{ "contact": {...id...}, "created": true }`.

## Scenario 3 — Resolve with no identifier → 422 (FR-002)

```bash
curl -i -X POST http://127.0.0.1:8000/booking/resolve-contact \
  -H "Content-Type: application/json" -d '{ "first_name": "NoId" }'
```

**Expected**: `422`.

## Scenario 4 — Book for an existing contact, explicit calendar (FR-008/010, SC-003)

Use a real `<CAL_ID>` from `GET /calendar/calendars` and a future `start_time`.

```bash
curl -i -X POST http://127.0.0.1:8000/booking/appointments \
  -H "Content-Type: application/json" \
  -d '{ "email": "ada+quickstart@example.com",
        "start_time": "2026-06-25T16:00:00-06:00",
        "title": "Quickstart booking",
        "calendar_id": "<CAL_ID>" }'
```

**Expected**: `200`, `{ "status": "booked", "appointment": {...}, "contact": {...}, "contact_created": false }`.

## Scenario 5 — Book for a new person (find-or-create + book) (FR-008, SC-003)

```bash
curl -i -X POST http://127.0.0.1:8000/booking/appointments \
  -H "Content-Type: application/json" \
  -d '{ "phone": "+15557770002", "first_name": "Walk", "last_name": "In",
        "start_time": "2026-06-25T17:00:00-06:00", "calendar_id": "<CAL_ID>" }'
```

**Expected**: `200`, `status: booked`, `contact_created: true`.

## Scenario 6 — Ambiguous calendar → selection required (FR-011, SC-005)

Run WITHOUT `GHL_DEFAULT_CALENDAR_ID` set and omit `calendar_id`, in a location with multiple
calendars.

```bash
curl -i -X POST http://127.0.0.1:8000/booking/appointments \
  -H "Content-Type: application/json" \
  -d '{ "email": "ada+quickstart@example.com", "start_time": "2026-06-25T18:00:00-06:00" }'
```

**Expected**: `200`, `{ "status": "calendar_selection_required", "calendars": [...] }`, no
appointment created.

## Scenario 7 — Missing start_time → 422 (FR-009, SC-006)

```bash
curl -i -X POST http://127.0.0.1:8000/booking/appointments \
  -H "Content-Type: application/json" -d '{ "email": "ada+quickstart@example.com" }'
```

**Expected**: `422`, nothing created.

## Done when

Scenarios 1–7 return the expected statuses; Scenario 4/5 produce real appointments visible in
GHL for the resolved contact; Scenario 6 surfaces the calendar list without booking.
