# Quickstart: Create Contact

Validates the create-contact endpoint end-to-end against a real GoHighLevel location.

## Prerequisites

- `.env` (git-ignored) at repo root with `GHL_TOKEN` (a `pit-...` Private Integration
  token) and `GHL_LOCATION_ID` set. See `.env.example`.
- Deps synced: `uv sync` (and `email-validator` present for `EmailStr` — `uv add email-validator` if missing).

## Run the server

```bash
cd src && uvicorn server:app --reload   # docs at http://127.0.0.1:8000/docs
```

## Scenario 1 — Create a contact (happy path) → FR-001/002/003/006, SC-001

```bash
curl -i -X POST http://127.0.0.1:8000/contacts \
  -H "Content-Type: application/json" \
  -d '{
        "first_name": "Ada",
        "last_name": "Lovelace",
        "email": "ada+quickstart@example.com",
        "phone": "+15551234567",
        "tags": ["lead", "newsletter"],
        "source": "quickstart"
      }'
```

**Expected**: `201 Created`; body contains the created contact with a non-empty `id`.
Confirm the contact appears in the GHL account for the configured location.

## Scenario 2 — Email-only is sufficient → edge case / Assumptions

```bash
curl -i -X POST http://127.0.0.1:8000/contacts \
  -H "Content-Type: application/json" \
  -d '{ "email": "phone-less+quickstart@example.com" }'
```

**Expected**: `201 Created`.

## Scenario 3 — No identity → rejected → FR-004, SC-002

```bash
curl -i -X POST http://127.0.0.1:8000/contacts \
  -H "Content-Type: application/json" \
  -d '{ "first_name": "NoContactInfo" }'
```

**Expected**: `422 Unprocessable Entity`; no contact created.

## Scenario 4 — Malformed email → rejected → FR-005

```bash
curl -i -X POST http://127.0.0.1:8000/contacts \
  -H "Content-Type: application/json" \
  -d '{ "email": "not-an-email" }'
```

**Expected**: `422 Unprocessable Entity`.

## Scenario 5 — Upstream auth failure surfaced → FR-007, SC-003

Run the server with an invalid `GHL_TOKEN`, then repeat Scenario 1.

**Expected**: `401` (or `403`), body `{"error": "ghl_api_error", ...}` preserving the
upstream status — not a `500`, and no "created" response.

## MCP check (optional)

With the MCP server mounted at `/mcp`, the `create_contact` tool should appear in the tool
list and create a contact with the same arguments as Scenario 1.

## Done when

All scenarios return the expected status codes and Scenario 1 produces a contact visible in
the GoHighLevel location.
