# Feature Specification: Create Contact

**Feature Branch**: `001-contact-create`

**Created**: 2026-06-15

**Status**: Draft

**Input**: User description: "Contacts slice: expose a 'create contact' endpoint that creates a new contact in GoHighLevel for the configured location, using the shared GHLClient. Accept the common contact fields (first name, last name, email, phone, optional tags and source), map snake_case request fields to GHL's camelCase, and return the created contact. Follow the existing calendar slice conventions (router/schemas/service, Depends(get_client), centralized GHL error translation)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create a contact with core details (Priority: P1)

An API consumer (an internal application or integration) submits a new contact's
details — at minimum an identifying piece of contact information such as an email or
phone — and the contact is created in the GoHighLevel account for the configured
location. The consumer receives back the stored contact, including the identifier
assigned by the system.

**Why this priority**: This is the entire purpose of the feature. Without it there is
no create-contact capability. It is the smallest slice that delivers value and is
independently shippable.

**Independent Test**: Submit a request containing valid contact details and confirm a
success response is returned containing the newly created contact and its assigned
identifier; then confirm the contact exists in the GoHighLevel account.

**Acceptance Scenarios**:

1. **Given** a valid contact with first name, last name, email, and phone, **When** the
   consumer requests creation, **Then** the contact is created for the configured
   location and the response contains the created contact with its assigned identifier.
2. **Given** a contact with only an email (no name/phone), **When** the consumer requests
   creation, **Then** the contact is created and returned successfully.
3. **Given** a contact with optional tags and a source value, **When** the consumer
   requests creation, **Then** the created contact reflects those tags and source.

---

### User Story 2 - Receive clear feedback on invalid or rejected input (Priority: P2)

When a consumer submits input that cannot produce a valid contact (e.g. no identifying
contact field at all, or a malformed email), or the underlying system rejects the
request (e.g. authentication failure or a duplicate), the consumer receives a clear,
faithful error that communicates what went wrong, rather than an opaque failure.

**Why this priority**: Robust error feedback makes the endpoint usable and debuggable in
real integrations, but the create path (P1) delivers value first.

**Independent Test**: Submit a request missing all identifying fields and confirm a
validation error is returned; submit a request that the upstream system rejects and
confirm the returned error preserves the upstream meaning and status.

**Acceptance Scenarios**:

1. **Given** a request with no identifying contact information, **When** the consumer
   requests creation, **Then** the request is rejected with a validation error explaining
   the missing requirement, and no contact is created.
2. **Given** valid input but invalid/expired credentials for the upstream account,
   **When** the consumer requests creation, **Then** an authentication error is returned
   that reflects the upstream rejection.
3. **Given** the upstream system rejects the create (e.g. duplicate contact), **When**
   the consumer requests creation, **Then** the returned error preserves the upstream
   status and reason.

---

### Edge Cases

- What happens when only an email is provided and no name or phone? → Contact is created
  with the available fields (assumption: email or phone alone is sufficient identity).
- What happens when neither email nor phone is provided? → Request is rejected with a
  validation error; no contact is created.
- What happens when the email is malformed? → Request is rejected with a validation error.
- What happens when tags is an empty list or omitted? → Treated as no tags; contact is
  created normally.
- What happens when the upstream account already has a matching contact? → The upstream
  system's response (acceptance or rejection) is surfaced faithfully to the consumer.
- What happens when the upstream service is unreachable or times out? → The consumer
  receives an error indicating the upstream failure rather than a silent success.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept a request to create a contact containing first name,
  last name, email, and phone fields.
- **FR-002**: System MUST accept optional tags (a list of labels) and an optional source
  value on the create request.
- **FR-003**: System MUST create the contact in the GoHighLevel account scoped to the
  configured location, without requiring the consumer to supply the location.
- **FR-004**: System MUST require at least one identifying contact field (email or phone)
  and reject requests that provide none with a validation error.
- **FR-005**: System MUST validate that a provided email is well-formed before attempting
  creation.
- **FR-006**: System MUST return the created contact, including the identifier assigned by
  the upstream system, on success.
- **FR-007**: System MUST surface upstream failures (authentication, rejection, duplicate,
  unreachable) as errors that preserve the upstream status and meaning, and MUST NOT
  report a created contact when none was created.
- **FR-008**: System MUST accept request fields in the consumer-facing snake_case naming.
  The created contact is returned as a faithful passthrough of the upstream system's
  representation (the system-of-record contact object) rather than re-mapped to
  snake_case; this keeps the response aligned with the source of truth. (Decision: see
  plan.md Complexity Tracking — documented exception to the response side of the naming
  boundary, consistent with the existing calendar slice.)

### Key Entities *(include if feature involves data)*

- **Contact**: A person record in the GoHighLevel account. Key attributes: first name,
  last name, email, phone, tags (zero or more labels), source (origin of the contact),
  and a system-assigned identifier returned on creation. Belongs to the configured
  location.
- **Create Contact Request**: The consumer-supplied set of contact details used to create
  a Contact. Carries the same descriptive attributes minus the system-assigned identifier.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A consumer can create a contact with valid details in a single request and
  receive the created contact (including its assigned identifier) in the response.
- **SC-002**: 100% of create requests that omit all identifying contact information are
  rejected with a validation error and result in no contact being created.
- **SC-003**: 100% of upstream rejections (auth failures, duplicates, other errors) are
  returned to the consumer with the upstream status preserved, with no false "created"
  responses.
- **SC-004**: A successful create request returns a response to the consumer within 2
  seconds under normal upstream conditions.

## Assumptions

- Either an email or a phone number alone is sufficient to identify a contact; a contact
  with neither is invalid. (No reasonable contact can be created without any identifier.)
- The target location is taken from existing configuration; the consumer does not and
  cannot specify a different location for this endpoint.
- Authentication/credentials for the upstream account are already configured and reused;
  this feature does not introduce its own credential management.
- Duplicate-handling policy is delegated to the upstream system — whatever GoHighLevel
  decides (accept or reject a duplicate) is surfaced faithfully; this feature does not add
  its own duplicate detection in v1.
- Only single-contact creation is in scope for v1; bulk creation is out of scope.
- Reading, updating, searching, and deleting contacts are out of scope for v1 (separate
  future operations of the Contacts slice).
