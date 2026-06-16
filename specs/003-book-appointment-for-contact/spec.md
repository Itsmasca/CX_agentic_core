# Feature Specification: Book Appointment for a Contact (find-or-create)

**Feature Branch**: `003-book-appointment-for-contact`

**Created**: 2026-06-16

**Status**: Draft

**Input**: User description: "Appointment booking for a contact, with intelligent find-or-create contact resolution. (1) Find-or-create contact resolver: given identifiers (email and/or phone, optional name/source), determine whether the contact exists; if matched return it, else create it; result indicates matched-vs-created and includes the id. (2) Book appointment for a contact in one step: resolve the contact via find-or-create, auto-resolve the calendar (single calendar, or configured default; if ambiguous surface the options), and create the appointment. Reuse shared GHLClient and existing ContactsService/CalendarService. Out of scope: reschedule/cancel, automatic free-slot selection, UI, tags/upsert beyond create."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Resolve a contact intelligently (find-or-create) (Priority: P1)

A consumer (an integration or an AI/voice agent over the MCP surface) provides a person's
identifying data (email and/or phone, optionally name and source) and asks the system to
resolve it to a single contact. The system intelligently determines whether that person is
already known: if an existing contact matches, it returns that contact; if none matches, it
creates a new contact from the provided data. The response makes clear whether the contact
was already known (matched) or newly created, and always includes the contact id.

**Why this priority**: This "smart resolver" is the reusable core that the booking flow
depends on and is independently valuable — any flow needing "get me the id for this person,
creating them if necessary" uses it. It is the smallest shippable increment.

**Independent Test**: Call resolve with the email of a contact that already exists and
confirm it returns that contact marked as matched (not created); call resolve with brand-new
identifiers and confirm a new contact is created and marked as created, with an id.

**Acceptance Scenarios**:

1. **Given** a contact already exists with a known email, **When** the consumer resolves by
   that email, **Then** the existing contact is returned, flagged as matched (not created),
   with its id.
2. **Given** no contact exists for a given phone, **When** the consumer resolves by that
   phone plus a name, **Then** a new contact is created from the data and returned, flagged
   as created, with its id.
3. **Given** neither email nor phone is provided, **When** the consumer attempts to resolve,
   **Then** a validation error is returned (cannot identify or create a contact without at
   least one identifier).
4. **Given** a contact was just created moments ago, **When** the consumer resolves by the
   same identifier again, **Then** the system should return the same contact rather than a
   duplicate, to the extent the upstream data is consistent (see Edge Cases / Assumptions on
   eventual consistency).

---

### User Story 2 - Book an appointment for a contact in one step (Priority: P1)

A consumer provides a person's identifying data plus appointment details (start time, and
optionally end time and title) and asks the system to book an appointment. In a single
request the system resolves the contact (find-or-create), determines which calendar to use,
and creates the appointment. It returns the created appointment together with the resolved
contact and whether that contact was newly created.

**Why this priority**: This is the end-to-end value the whole feature exists for — turning
"a person wants an appointment" into a booked appointment without the caller juggling
contact lookup, contact creation, and calendar selection. For a voice agent it collapses
several steps into one.

**Independent Test**: Book an appointment by supplying a known contact's email plus a start
time, and confirm an appointment is created for that contact on the resolved calendar and
returned; repeat with a brand-new person and confirm the contact is created and the
appointment booked.

**Acceptance Scenarios**:

1. **Given** a known contact and a valid start time, **When** the consumer books, **Then**
   an appointment is created for that contact on the resolved calendar and returned, along
   with the resolved contact marked as matched.
2. **Given** an unknown person (new identifiers) and a valid start time, **When** the
   consumer books, **Then** the contact is created, the appointment is booked for it, and
   the response shows the contact as newly created.
3. **Given** the location has exactly one calendar, **When** the consumer books without
   specifying a calendar, **Then** that single calendar is used automatically.
4. **Given** the location has multiple calendars and no default is configured and none is
   specified, **When** the consumer books, **Then** the system does not guess — it returns a
   response listing the available calendars so the caller can choose.
5. **Given** a configured default calendar (or an explicitly supplied calendar), **When** the
   consumer books, **Then** that calendar is used.
6. **Given** no identifying contact data, or no start time, **When** the consumer attempts to
   book, **Then** a validation error is returned and no appointment is created.

---

### Edge Cases

- **Eventual consistency**: GHL contact search lags right after a create. If find-or-create
  searches immediately after the same contact was just created, the search may not yet
  return it, risking a duplicate. The system MUST minimize this within its control but
  cannot fully guarantee dedup against very-recent creations (documented limitation).
- **Multiple matches**: a search by identifier returns more than one contact → the system
  selects the best/most exact match (e.g. exact email match) deterministically; if still
  ambiguous, it uses the first and the behavior is documented.
- **Ambiguous calendar**: multiple calendars, no default, none supplied → surface the list,
  do not guess (Scenario 2.4).
- **No calendars exist** in the location → booking returns an error explaining no calendar is
  available.
- **Appointment creation fails** after a contact was just created (e.g. invalid start time) →
  the contact remains created (no rollback); the error is surfaced. (Documented; see
  Assumptions.)
- **Upstream failures** (auth, not found, unreachable) → surfaced faithfully with the
  upstream status; no false success.
- **Booking in the past / invalid time** → the upstream rejection is surfaced faithfully
  (the system does not add its own calendar business rules in this feature).

## Requirements *(mandatory)*

### Functional Requirements

#### Find-or-create resolver (US1)

- **FR-001**: System MUST accept contact identifiers — email and/or phone, plus optional
  first name, last name, and source — and resolve them to a single contact.
- **FR-002**: System MUST require at least one of email or phone, rejecting requests with
  neither (a contact can be neither found nor created without an identifier).
- **FR-003**: System MUST search for an existing contact by the provided identifying data and
  return the matching contact when one is found, without creating a duplicate.
- **FR-004**: System MUST create a new contact from the provided data when no existing match
  is found, and return it.
- **FR-005**: System MUST indicate in the result whether the contact was matched (already
  existed) or newly created.
- **FR-006**: System MUST return the resolved contact including its identifier.
- **FR-007**: When multiple contacts match, System MUST select a single contact
  deterministically (preferring an exact identifier match) and document the rule.

#### One-step booking (US2)

- **FR-008**: System MUST accept contact identifiers plus appointment details (start time,
  optional end time, optional title) and, in one operation, resolve the contact and create
  the appointment for it.
- **FR-009**: System MUST require a start time and at least one contact identifier for
  booking; missing either is a validation error with no appointment created.
- **FR-010**: System MUST resolve the calendar automatically: if the location has exactly one
  calendar, use it; if a default calendar is configured, use it; if an explicit calendar is
  supplied, use it.
- **FR-011**: When the calendar is ambiguous (multiple calendars, no default, none supplied),
  System MUST NOT guess — it MUST return the list of available calendars for the caller to
  choose from, without creating an appointment.
- **FR-012**: System MUST return the created appointment together with the resolved contact
  and whether that contact was newly created.

#### Cross-cutting

- **FR-013**: System MUST scope all operations to the configured location without the caller
  supplying it.
- **FR-014**: System MUST surface upstream failures (validation, not found, auth, unreachable)
  with the upstream status preserved, never reporting a false booking or false resolution.
- **FR-015**: System MUST accept request inputs in the consumer-facing snake_case naming;
  returned contacts/appointments are a faithful passthrough of the upstream representation
  (consistent with prior contacts/calendar features).
- **FR-016**: Both capabilities MUST be available over the same surfaces as existing
  operations (the HTTP API and the agent/MCP tool surface).

### Key Entities *(include if feature involves data)*

- **Contact** — a person record in the configured location (id, first/last name, email,
  phone, source). Same entity as the contacts features.
- **Resolve Request** — identifying inputs (email and/or phone, optional first/last name,
  source) used to find-or-create a Contact.
- **Resolve Result** — the resolved Contact plus a flag indicating matched vs. created.
- **Appointment** — a calendar event for a contact (calendar, contact, start/end time,
  title, status). Same entity as the calendar feature.
- **Booking Request** — Resolve Request inputs plus appointment details (start time, optional
  end time, optional title, optional explicit calendar).
- **Calendar** — a bookable calendar within the location; the booking flow resolves which one
  to use.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A consumer can obtain a single contact id for a person in one request, with the
  system creating the contact only when none already exists.
- **SC-002**: For a person who already exists, the resolver returns the existing contact
  (matched, not created) in 100% of cases where the upstream data is consistent.
- **SC-003**: A consumer can book an appointment for a person in one request without
  separately calling contact lookup, contact creation, and calendar selection.
- **SC-004**: When the location has a single calendar (or a configured default), 100% of
  bookings that omit a calendar succeed using the resolved calendar.
- **SC-005**: When the calendar is ambiguous, 0% of bookings guess; 100% return the available
  calendars instead, with no appointment created.
- **SC-006**: 100% of booking attempts missing a start time or any contact identifier are
  rejected with no appointment created.
- **SC-007**: Resolve and one-step booking each return within 4 seconds under normal upstream
  conditions (booking may make multiple upstream calls).

## Assumptions

- **Matching strategy**: a contact is considered "existing" when the search by its email (or,
  failing that, phone) returns a contact; an exact email match is preferred over other
  matches. This is the documented deterministic rule for FR-003/FR-007.
- **Eventual consistency**: because GHL contact search lags after a create, find-or-create
  dedup is best-effort against very-recent creations; a duplicate created within the search
  indexing window is a known, accepted limitation for this feature.
- **No rollback / not transactional**: if the contact is created but the appointment creation
  then fails, the contact is left created (the operation is not atomic). The error is
  surfaced so the caller can retry the booking with the now-existing contact.
- **Calendar default**: an optional configured default calendar may be provided via existing
  configuration; when present it is used for otherwise-ambiguous bookings. Absent that and
  with multiple calendars, the flow surfaces the choices rather than guessing.
- **Free-slot selection is out of scope**: the caller supplies the start time; the system does
  not pick a free slot (the existing free-slots operation remains separate).
- **Appointment status / timezone** default to the existing calendar feature's behavior; this
  feature adds no new calendar business rules.
- **Out of scope**: rescheduling, cancellation, free-slot auto-selection, any UI, and
  tags/upsert beyond what create-contact already supports.
- Authentication/credentials are reused from existing configuration; no new credential
  management is introduced.
