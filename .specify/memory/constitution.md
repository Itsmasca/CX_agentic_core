<!--
Sync Impact Report
==================
Version change: (template, unversioned) → 1.0.0
Rationale: Initial ratification — first concrete fill of the constitution template.

Modified principles: none (initial adoption)
Added principles:
  - I. Vertical Slice Isolation
  - II. Single Shared GHL Client
  - III. Explicit GHL Naming Boundary
  - IV. Centralized Error Translation
  - V. Environment-Sourced Configuration & Secrets
Added sections:
  - Technology & Code Standards (Section 2)
  - Development Workflow (Section 3)
Removed sections: none

Templates requiring updates:
  ✅ .specify/templates/plan-template.md — Constitution Check is generic ("Gates
     determined based on constitution file"); no hardcoded principles to revise.
  ✅ .specify/templates/spec-template.md — no constitution-specific constraints; aligned.
  ✅ .specify/templates/tasks-template.md — task categories compatible with new
     principles (slice structure, linting, error handling); no edits required.
  ✅ CLAUDE.md — already documents these architectural rules; constitution codifies them.

Follow-up TODOs: none. RATIFICATION_DATE set to first adoption date (2026-06-15).
-->

# CXAPP Constitution

CXAPP is a FastAPI backend that wraps the GoHighLevel (GHL) API V2 behind vertical
slices. These principles are the non-negotiable rules every slice and contribution
MUST satisfy.

## Core Principles

### I. Vertical Slice Isolation

Each GHL domain (calendar, contacts, conversaciones, etc.) MUST be a self-contained
module under `src/modules/<slice>/` owning its own `router.py`, `schemas.py`, and
`service.py`. A slice MUST expose its `router` from the slice `__init__.py`, and
`server.py` MUST mount it via `app.include_router(...)`. Cross-slice imports of one
slice's service or schemas by another are PROHIBITED; shared behavior MUST live in
`core/`. Rationale: isolation keeps domains independently understandable and lets new
GHL domains be added without destabilizing existing ones.

### II. Single Shared GHL Client

There MUST be exactly one `core/client.py:GHLClient` instance per process, created in
`server.py`'s lifespan and stored on `app.state.ghl_client`. Slices MUST obtain it via
`Depends(get_client)` and MUST NOT instantiate a `GHLClient` (or a raw `httpx` client)
per request. Rationale: a shared client reuses connections, centralizes auth-header
injection, and gives one place for HTTP-level concerns.

### III. Explicit GHL Naming Boundary

GHL speaks camelCase (`calendarId`, `startTime`, `appointmentStatus`); CXAPP's public
boundary speaks snake_case. Pydantic schemas in `schemas.py` MUST bridge the two with
field aliases and `populate_by_name=True`. The service layer MAY speak GHL's camelCase
keys directly when calling the client, but camelCase MUST NOT leak into a slice's
public response model unaliased. Date/time inputs destined for GHL epoch-millisecond
parameters MUST be normalized through a single helper (e.g. `service._to_epoch_ms`).
Rationale: one explicit translation layer prevents naming drift and silent contract
breaks.

### IV. Centralized Error Translation

All non-2xx GHL responses MUST surface as `GHLAPIError`/`GHLAuthError` raised from
`GHLClient`, never as raw `httpx` exceptions escaping a slice. `server.py`'s exception
handler MUST re-emit these as HTTP responses that preserve the original GHL status
code. Slices MUST NOT swallow these errors into generic 500s or invent their own
status mapping. Rationale: callers receive faithful, consistent error semantics that
mirror the upstream API.

### V. Environment-Sourced Configuration & Secrets

Configuration MUST be read through `core/config.py:GHLConfig.from_env()`, which sources
`GHL_TOKEN` (Private Integration token) and `GHL_LOCATION_ID` from the environment.
Secrets MUST NOT be hard-coded in source, committed to the repo, or logged; `.env`
files hold local secrets and MUST remain git-ignored, with `.env.example` documenting
required keys. `GHLClient()` and service constructors MUST default to this config when
given no arguments. Rationale: keeping credentials out of code and in the environment
is the baseline for safe deployment.

## Technology & Code Standards

- **Runtime**: Python 3.13, FastAPI + httpx, served with `uvicorn`.
- **Dependency management**: `uv`. Dependencies are declared in the **root**
  `pyproject.toml`; `uv add <pkg>` to add, `uv sync` to install. The active
  virtualenv is the root `./.venv`.
- **Import & run convention**: modules import each other as top-level packages
  (`from core.client import GHLClient`, `from modules.calendar import router`), which
  only resolves with CWD = `src/`. The server MUST be run from `src/`
  (`cd src && uvicorn server:app --reload`).
- **Lint & format**: `ruff` (target py313, line length 88). `uv run ruff check .` and
  `uv run ruff format .` MUST pass before code is considered done.

## Development Workflow

- New slices MUST follow the "Adding a new vertical slice" steps in `CLAUDE.md`
  (service → schemas → router → export → include).
- Changes MUST be lint-clean (`ruff check`) and formatted (`ruff format`) before merge.
- When a test suite exists, tests run via `uv run pytest`; `pytest` is added with
  `uv add --dev pytest`. Until then, new behavior SHOULD be manually verified against
  the `/docs` endpoint.
- Code review MUST verify the change upholds every Core Principle; any deviation MUST
  be justified in the PR description (see Governance).

## Governance

This constitution supersedes ad-hoc practices for CXAPP. Amendments MUST be made by
editing `.specify/memory/constitution.md`, accompanied by an updated Sync Impact
Report and a version bump per the policy below.

- **Versioning policy** (semantic):
  - MAJOR — backward-incompatible governance changes or principle removals/redefinitions.
  - MINOR — a new principle or section, or materially expanded guidance.
  - PATCH — clarifications, wording, or non-semantic refinements.
- **Compliance review**: every PR/review MUST confirm compliance with the Core
  Principles. A justified, documented exception MAY be recorded in the plan's
  Complexity Tracking table; unjustified violations MUST block merge.
- **Runtime guidance**: `CLAUDE.md` is the authoritative day-to-day development guide
  and MUST stay consistent with this constitution.

**Version**: 1.0.0 | **Ratified**: 2026-06-15 | **Last Amended**: 2026-06-15
