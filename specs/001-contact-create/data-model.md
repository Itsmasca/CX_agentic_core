# Phase 1 Data Model: Create Contact

The slice has no local persistence; these are the request/response shapes at the public
boundary and the payload sent to GHL. Naming boundary (Constitution III): public =
snake_case, GHL = camelCase, bridged by pydantic aliases.

## Entity: Create Contact Request (`CreateContactRequest`)

Consumer-facing input. `populate_by_name=True` so both snake_case and camelCase are
accepted on input; output/serialization uses aliases.

| Public field (snake_case) | GHL alias (camelCase) | Type             | Required | Notes |
|---------------------------|-----------------------|------------------|----------|-------|
| `first_name`              | `firstName`           | `str \| None`    | No       | |
| `last_name`               | `lastName`            | `str \| None`    | No       | |
| `email`                   | `email`               | `EmailStr \| None` | No*    | Validated format (FR-005) |
| `phone`                   | `phone`               | `str \| None`    | No*      | E.164 recommended; not strictly validated in v1 |
| `tags`                    | `tags`                | `list[str] \| None` | No    | Omitted/empty → no tags |
| `source`                  | `source`              | `str \| None`    | No       | Free-form origin label |

\* **Identity rule (FR-004)**: at least one of `email` or `phone` MUST be present. Enforced
by a model validator → 422 if both are absent. This is the only cross-field rule.

### Validation rules

- **V1 (identity)**: `email` or `phone` required; else 422 (FR-004, SC-002).
- **V2 (email format)**: if `email` present, must be a well-formed address (FR-005).
- **V3 (location)**: `location_id` is NOT accepted from the consumer; it is injected from
  config (FR-003). The request schema does not expose it.

## Payload sent to GHL (`POST /contacts/`)

Built by the service from the validated request plus injected location. `None`/empty values
are stripped by `GHLClient._request` before sending.

```jsonc
{
  "firstName": "Ada",
  "lastName": "Lovelace",
  "email": "ada@example.com",
  "phone": "+15551234567",
  "tags": ["lead", "newsletter"],
  "source": "website-form",
  "locationId": "<from config>"   // injected, never from caller
}
```

## Entity: Contact (response)

Returned by GHL on success; passed through to the consumer (FR-006). Shape is GHL's; key
attributes the consumer relies on:

| Field        | Type        | Notes |
|--------------|-------------|-------|
| `id`         | `str`       | System-assigned identifier (proves creation) |
| `firstName`  | `str \| null` | Echoes input |
| `lastName`   | `str \| null` | Echoes input |
| `email`      | `str \| null` | Echoes input |
| `phone`      | `str \| null` | Echoes input |
| `tags`       | `string[]`  | Echoes input |
| `source`     | `str \| null` | Echoes input |
| `locationId` | `str`       | The configured location |
| …            | …           | Additional GHL fields passed through unmodified |

GHL wraps this as `{"contact": { ... }}`; the service returns that result as-is (parity
with the calendar create endpoint).

## State

No state machine — a single create transition: *(no contact)* → *contact created with id*.
On any upstream rejection, no contact is created and an error is surfaced (FR-007).
