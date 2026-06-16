# Quickstart: Search & Update Contacts

Validates search/list and partial update end-to-end against a real GoHighLevel location.

## Prerequisites

- `.env` with `GHL_TOKEN` and `GHL_LOCATION_ID` (see feature 001).
- Deps synced (`uv sync`); `email-validator` present.
- At least one known contact in the location (e.g. create one via feature 001 first, and
  note its `id` and `email`).

## Run the server

```bash
cd src && uvicorn server:app --reload   # docs at http://127.0.0.1:8000/docs
```

## Scenario 1 — Search by email → FR-001/006, SC-001

```bash
curl -i "http://127.0.0.1:8000/contacts?query=ada+quickstart@example.com"
```

**Expected**: `200`; `contacts` array contains the contact with that email and a non-empty
`id`. (Note the `id` for Scenario 4 / appointment linkage.)

## Scenario 2 — List (no query) → FR-004, FR-008

```bash
curl -i "http://127.0.0.1:8000/contacts?limit=5"
```

**Expected**: `200`; up to 5 contacts for the location.

## Scenario 3 — Search with no match → FR-007, SC-005

```bash
curl -i "http://127.0.0.1:8000/contacts?query=zzz-no-such-contact-zzz"
```

**Expected**: `200` with `{"contacts": [], "total": 0}` — NOT an error.

## Scenario 4 — Partial update → FR-009/010/011/014, SC-003

Use a real `<CONTACT_ID>` from Scenario 1.

```bash
curl -i -X PUT http://127.0.0.1:8000/contacts/<CONTACT_ID> \
  -H "Content-Type: application/json" \
  -d '{ "first_name": "Augusta", "source": "quickstart-edit" }'
```

**Expected**: `200`; returned contact shows `firstName: "Augusta"` and the new source, while
`lastName`, `email`, `phone` are unchanged. Re-run Scenario 1 to confirm persistence.

## Scenario 5 — Update with no changeable field → FR-013, SC-004

```bash
curl -i -X PUT http://127.0.0.1:8000/contacts/<CONTACT_ID> \
  -H "Content-Type: application/json" -d '{}'
```

**Expected**: `422`; nothing changed.

## Scenario 6 — Update with malformed email → FR-012, SC-004

```bash
curl -i -X PUT http://127.0.0.1:8000/contacts/<CONTACT_ID> \
  -H "Content-Type: application/json" -d '{ "email": "not-an-email" }'
```

**Expected**: `422`; nothing changed.

## Scenario 7 — Update non-existent id → FR-015, SC-004

```bash
curl -i -X PUT http://127.0.0.1:8000/contacts/does-not-exist-id \
  -H "Content-Type: application/json" -d '{ "first_name": "Ghost" }'
```

**Expected**: upstream `404` envelope `{"error": "ghl_api_error", ...}` — not a `500`, no
change.

## Linkage check (SC-002)

Take a `contact_id` from Scenario 1 and use it as `contact_id` in the calendar slice's
`POST /calendar/appointments` — confirms search→book works end-to-end.

## Done when

Scenarios 1–7 return the expected statuses and the partial update is verified to change only
the provided fields.
