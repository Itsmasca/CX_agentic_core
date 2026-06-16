# Feature Specification: Search & Update Contacts

**Feature Branch**: `002-contact-search-update`

**Created**: 2026-06-15

**Status**: Draft

**Input**: User description: "Contacts slice continuation (builds on the existing create-contact feature): add Search/list contacts and Update an existing contact. Search lets a caller find contacts by email, phone, or free-text query, and/or list contacts for the configured location; the primary motivation is obtaining a contact's id (e.g. to then book an appointment in the calendar slice). Update modifies an existing contact's fields (first name, last name, email, phone, source) identified by its id, sending only the provided fields. Expose both as REST endpoints and as MCP tools, mirroring the calendar slice conventions and the existing contacts create implementation. Out of scope: tags-specific add/remove operations, upsert/duplicate handling, a dedicated get-by-id endpoint, and delete."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find a contact to obtain its id (Priority: P1)

An API consumer (an internal application, an integration, or an AI agent over the MCP
surface) looks up contacts in the configured location by email, phone, or a free-text
query — or lists the location's contacts — primarily to obtain a contact's identifier so
it can be used elsewhere (for example, to book an appointment in the calendar slice).

**Why this priority**: Search is the linchpin that makes the rest of the system usable —
the calendar's create-appointment needs a `contact_id`, and create-contact returns one
only at creation time. Without search there is no way to retrieve an existing contact's
id. It is independently shippable and delivers immediate value.

**Independent Test**: Issue a search by a known contact's email (or phone, or query) and
confirm the matching contact — including its id — is returned; issue a list request and
confirm contacts for the location are returned.

**Acceptance Scenarios**:

1. **Given** a contact exists with a known email, **When** the consumer searches by that
   email, **Then** the matching contact (including its id) is returned.
2. **Given** a contact exists with a known phone, **When** the consumer searches by that
   phone, **Then** the matching contact (including its id) is returned.
3. **Given** several contacts exist, **When** the consumer searches by a free-text query
   matching a name, **Then** the contacts matching the query are returned.
4. **Given** no search criteria are provided, **When** the consumer requests a list,
   **Then** contacts for the configured location are returned (bounded by a result limit).
5. **Given** no contact matches the criteria, **When** the consumer searches, **Then** an
   empty result set is returned (not an error).

---

### User Story 2 - Update an existing contact (Priority: P2)

An API consumer updates fields of an existing contact (first name, last name, email,
phone, source) identified by its id, sending only the fields it wants to change; other
fields are left untouched.

**Why this priority**: Keeping contact data correct is valuable, but it depends on first
being able to identify the contact (US1). It is independently testable once an id is
known.

**Independent Test**: Update a known contact's first name by id and confirm the change is
reflected; confirm fields not included in the request are unchanged.

**Acceptance Scenarios**:

1. **Given** a contact id, **When** the consumer updates its first name only, **Then** the
   first name changes and other fields (last name, email, phone, source) are unchanged.
2. **Given** a contact id, **When** the consumer updates several fields at once, **Then**
   all provided fields are changed and the updated contact is returned.
3. **Given** a non-existent contact id, **When** the consumer attempts an update, **Then**
   an error reflecting the upstream "not found" is returned, and nothing is changed.
4. **Given** a contact id but a malformed email in the update, **When** the consumer
   attempts the update, **Then** a validation error is returned and nothing is changed.

---

### Edge Cases

- What happens when a search matches many contacts? → Results are bounded by a default
  limit; the caller can request a larger/smaller page via a limit parameter.
- What happens when search criteria are combined (e.g. email + query)? → The most specific
  provided criterion is used; behavior is documented and deterministic (see Assumptions).
- What happens when an update request contains no changeable fields? → Treated as a no-op
  request and rejected with a validation error (nothing to update).
- What happens when the update email is malformed? → Rejected with a validation error
  before any upstream call.
- What happens when the contact id does not exist? → The upstream "not found" status is
  surfaced faithfully; nothing is changed.
- What happens when the upstream service is unreachable or times out? → An error
  indicating the upstream failure is returned, not a silent success/empty result.

## Requirements *(mandatory)*

### Functional Requirements

#### Search / List (US1)

- **FR-001**: System MUST allow searching contacts within the configured location by email.
- **FR-002**: System MUST allow searching contacts within the configured location by phone.
- **FR-003**: System MUST allow searching contacts within the configured location by a
  free-text query (e.g. matching name).
- **FR-004**: System MUST allow listing contacts for the configured location when no search
  criterion is provided.
- **FR-005**: System MUST scope every search/list to the configured location without the
  consumer supplying the location.
- **FR-006**: System MUST return each matching contact including its identifier.
- **FR-007**: System MUST return an empty result set (not an error) when nothing matches.
- **FR-008**: System MUST bound results by a default maximum count and allow the consumer to
  request a different limit.

#### Update (US2)

- **FR-009**: System MUST allow updating an existing contact identified by its id.
- **FR-010**: System MUST update only the fields provided in the request, leaving omitted
  fields unchanged (partial update).
- **FR-011**: System MUST support updating first name, last name, email, phone, and source.
- **FR-012**: System MUST validate that a provided email is well-formed before attempting
  the update.
- **FR-013**: System MUST reject an update request that contains no changeable fields with a
  validation error, making no upstream change.
- **FR-014**: System MUST return the updated contact on success.

#### Cross-cutting

- **FR-015**: System MUST surface upstream failures (not found, authentication, unreachable)
  as errors that preserve the upstream status and meaning, never reporting a false success
  or a misleading empty result.
- **FR-016**: System MUST accept request inputs in the consumer-facing snake_case naming.
  Returned contacts are a faithful passthrough of the upstream representation (consistent
  with the create-contact feature; see Assumptions).
- **FR-017**: Both operations MUST be available over the same surfaces as the existing
  contacts capability (the HTTP API and the agent/MCP tool surface).

### Key Entities *(include if feature involves data)*

- **Contact**: A person record in the configured location. Relevant attributes: identifier,
  first name, last name, email, phone, source. (Same entity as the create-contact feature.)
- **Contact Search Criteria**: The consumer-supplied lookup inputs — email, phone, or
  free-text query — plus an optional result limit. Absence of all criteria means "list".
- **Contact Update Request**: A contact id plus the subset of fields to change (first name,
  last name, email, phone, source); at least one changeable field required.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A consumer can retrieve an existing contact's id by searching with that
  contact's email, phone, or a matching query, in a single request.
- **SC-002**: A consumer can obtain a contact id via search and successfully use it to book
  an appointment in the calendar slice (end-to-end linkage works).
- **SC-003**: A partial update changes exactly the provided fields and leaves all other
  fields unchanged, verifiable by reading the contact back.
- **SC-004**: 100% of updates to a non-existent id, and 100% of malformed-email or
  no-changeable-field updates, are rejected/ surfaced as errors with no data change.
- **SC-005**: A search returning no matches yields an empty result set (not an error) in
  100% of such cases.
- **SC-006**: Search/list and update each return a response within 2 seconds under normal
  upstream conditions.

## Assumptions

- Returned contacts are a faithful passthrough of the upstream (system-of-record)
  representation rather than re-mapped to snake_case, consistent with the create-contact
  feature's documented decision (request boundary is snake_case; response is passthrough).
- The configured location scopes all operations; the consumer cannot target another
  location (same as create-contact).
- When multiple search criteria are supplied, the system uses the most specific identifying
  criterion (email, then phone, then free-text query) to keep behavior deterministic; this
  is a reasonable default that can be revisited.
- A sensible default result limit applies to list/search (e.g. a single page of results);
  exhaustive pagination/cursoring across all pages is out of scope for this feature.
- "Update" is a partial update: only provided fields change. Replacing/clearing a field to
  empty is out of scope for this feature (no explicit null-clear semantics in v1).
- Tags-specific add/remove operations, upsert/duplicate handling, a dedicated get-by-id
  endpoint, and delete are explicitly OUT OF SCOPE for this feature.
- Authentication/credentials for the upstream account are already configured and reused;
  this feature introduces no new credential management.
