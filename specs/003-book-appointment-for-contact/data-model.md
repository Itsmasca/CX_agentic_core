# Phase 1 Data Model: Book Appointment for a Contact

No local persistence. Request boundary is snake_case; payloads to GHL are camelCase (handled
by the composed `ContactsService`/`CalendarService`). Responses are passthrough (FR-015).

## Resolve (find-or-create)

### Input: Resolve Contact Request (`ResolveContactRequest`)

| Public field (snake_case) | Type | Required | Notes |
|---------------------------|------|----------|-------|
| `email` | `EmailStr \| None` | No* | Validated if present |
| `phone` | `str \| None` | No* | |
| `first_name` | `str \| None` | No | Used only when creating |
| `last_name` | `str \| None` | No | Used only when creating |
| `source` | `str \| None` | No | Used only when creating |

\* At least one of `email`/`phone` required (FR-002) → else 422.

### Output: Resolve Result

```jsonc
{ "contact": { "id": "...", ... }, "created": false }   // matched existing
{ "contact": { "id": "...", ... }, "created": true }    // newly created
```

### Resolution rules

- **V1 identity (FR-002)**: email or phone required.
- **Match (FR-003/FR-007)**: search by email → exact case-insensitive email match among
  results = matched; else search by phone → exact phone match = matched; else create.
- **Create (FR-004)**: uses email/phone/first_name/last_name/source via `create_contact`.

## Book (one-step)

### Input: Book Appointment Request (`BookAppointmentRequest`)

| Public field | Type | Required | Notes |
|--------------|------|----------|-------|
| `email` | `EmailStr \| None` | No* | Contact identifier |
| `phone` | `str \| None` | No* | Contact identifier |
| `first_name` | `str \| None` | No | For create |
| `last_name` | `str \| None` | No | For create |
| `source` | `str \| None` | No | For create |
| `start_time` | `str` | **Yes** | ISO 8601 w/ offset (FR-009) |
| `end_time` | `str \| None` | No | |
| `title` | `str \| None` | No | |
| `calendar_id` | `str \| None` | No | Explicit calendar override |

\* email or phone required (FR-009).

### Output: Booking Result (discriminated)

```jsonc
// success
{ "status": "booked",
  "appointment": { "id": "...", ... },
  "contact": { "id": "...", ... },
  "contact_created": true }

// ambiguous calendar — no appointment created (FR-011)
{ "status": "calendar_selection_required",
  "calendars": [ { "id": "...", "name": "..." }, ... ] }
```

### Booking rules

- **V1 (FR-009)**: `start_time` AND (email or phone) required → else 422, nothing created.
- **Calendar resolution (FR-010/FR-011)**: explicit `calendar_id` → `config.default_calendar_id`
  → single calendar → else ambiguous (return list, no booking) / zero calendars → error.
- **Compose**: resolve contact (find-or-create) → resolve calendar → `create_appointment`.
- **Non-atomic (R5)**: contact may exist even if the appointment step fails (no rollback).

## Entities (reused)

- **Contact** — id, first/last name, email, phone, source (contacts feature).
- **Appointment** — calendar event for a contact (calendar feature): calendar, contact, start/
  end, title, status.
- **Calendar** — bookable calendar in the location; `{id, name}` surfaced when ambiguous.

## State

- Resolve: read-or-create; transition *(unknown)* → *(matched | created contact)*.
- Book: *(no appointment)* → *(appointment created)* on success; on ambiguity, no transition
  (selection required); on post-resolve failure, contact created but no appointment (R5).

## Config addition

- `GHLConfig.default_calendar_id: str | None` from `GHL_DEFAULT_CALENDAR_ID` (optional).
