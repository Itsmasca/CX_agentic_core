# Contract: Book Appointment for a Contact (one-step)

## REST endpoint

`POST /booking/appointments`

Resolves the contact (find-or-create), resolves the calendar, and creates the appointment —
in one request.

### Request body (application/json)

```json
{
  "email": "ada@example.com",
  "phone": "+15551234567",
  "first_name": "Ada",
  "last_name": "Lovelace",
  "source": "voice-agent",
  "start_time": "2026-06-20T15:00:00-06:00",
  "end_time": "2026-06-20T15:30:00-06:00",
  "title": "Intro call",
  "calendar_id": null
}
```

- `start_time` required; at least one of `email`/`phone` required.
- `calendar_id` optional override; otherwise the calendar is auto-resolved.

### Responses

| Status | When | Body |
|--------|------|------|
| `200 OK` (booked) | Contact resolved + appointment created | `{ "status": "booked", "appointment": {...}, "contact": {...}, "contact_created": <bool> }` |
| `200 OK` (selection) | Calendar ambiguous, nothing created | `{ "status": "calendar_selection_required", "calendars": [ {"id","name"}... ] }` |
| `422` | Missing `start_time` or any contact identifier, or malformed email | Validation error, nothing created |
| `4xx / 5xx` (passthrough) | Upstream error (incl. no calendar available, invalid time) | `{ "error": "ghl_api_error", ... }`, status preserved |

### Acceptance mapping

- 200 booked for known contact → FR-008/012, SC-003
- 200 booked + `contact_created: true` for new person → FR-008, SC-003
- single calendar / default used automatically → FR-010, SC-004
- ambiguous → `calendar_selection_required`, no appointment → FR-011, SC-005
- 422 missing start_time or identifier → FR-009, SC-006
- upstream errors preserved → FR-014

## MCP tool

`book_appointment(start_time, email=None, phone=None, first_name=None, last_name=None, source=None, end_time=None, title=None, calendar_id=None) -> dict`

Headline tool for a voice agent: turns "this person wants an appointment" into a booking. On
`calendar_selection_required`, the agent re-calls with a chosen `calendar_id`.

## Notes

- Non-atomic: if the contact is created but appointment creation fails, the contact remains;
  the error is surfaced for retry.
- Free-slot selection is out of scope — the caller supplies `start_time`.
