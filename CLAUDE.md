# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

CXAPP is a Python backend that wraps the **GoHighLevel (GHL) API V2** (LeadConnector, `services.leadconnectorhq.com`) behind a FastAPI server. It is organized as **vertical slices**: each GHL domain (calendar, contacts, and future conversaciones/etc.) is a self-contained module owning its router, schemas, and service.

The **calendar** and **contacts** slices are implemented; `src/modules/{Admin,User,Subaccount,Conversaciones}` are empty scaffolding. The contacts slice currently exposes `POST /contacts` (create) and a matching `create_contact` MCP tool.

## Commands

The active virtualenv with all deps installed is `./.venv` (the root one — **not** `src/.venv`, which is an empty leftover). Dependencies are declared in the **root `pyproject.toml`**; `src/pyproject.toml` is an empty workspace member.

```bash
# install / sync deps (uv-managed)
uv sync

# add a dependency
uv add <pkg>

# run the API server — MUST run from src/ so `core` and `modules` resolve as top-level packages
cd src && uvicorn server:app --reload      # docs at http://127.0.0.1:8000/docs

# lint / format (ruff, py313, line-length 88)
uv run ruff check .
uv run ruff format .
```

There is no test suite yet (`tests/` is empty). If adding tests, use `uv run pytest` and add `pytest` via `uv add --dev`.

## Import convention (important)

Modules import each other as **top-level packages** (`from core.client import GHLClient`, `from modules.calendar import router`). This only resolves when the process CWD is `src/`. Always run/import from `src/`, never from the repo root.

## Architecture

Request flow for a slice endpoint:

```
server.py (FastAPI app)
  └─ lifespan: creates ONE shared GHLClient → app.state.ghl_client
  └─ include_router(calendar_router)
       └─ modules/calendar/router.py
            get_client (core/deps.py) reads app.state.ghl_client
            → get_service builds CalendarService(client)
            → CalendarService (service.py) calls GHL via the shared client
```

Key points a new slice must respect:

- **Shared HTTP client.** `core/client.py:GHLClient` is a thin httpx wrapper that injects auth (`Authorization: Bearer`, `Version` header) and centralizes error handling. It is created once in `server.py`'s lifespan and reused across requests — do not instantiate per-request. Inject it via `Depends(get_client)`.
- **Auth/config.** `core/config.py:GHLConfig.from_env()` reads `GHL_TOKEN` (Private Integration token, `pit-...`) and `GHL_LOCATION_ID` from the environment, auto-loading a `.env` if `python-dotenv` is present. `GHLClient()` and `CalendarService()` both default to this when given no args.
- **Error translation.** `GHLClient` raises `GHLAPIError`/`GHLAuthError` (from `core/errors.py`) on non-2xx GHL responses. `server.py` has an exception handler that re-emits these as HTTP responses preserving the original GHL status code.
- **GHL naming boundary.** GHL's API uses camelCase (`calendarId`, `startTime`, `appointmentStatus`). Pydantic schemas in `schemas.py` map snake_case ↔ camelCase via field aliases (`populate_by_name=True`). The service layer speaks GHL's camelCase keys directly.
- **Date handling.** Free-slots queries take epoch **milliseconds**; `service.py:_to_epoch_ms` normalizes `date`/`datetime`/`int`.

### Adding a new vertical slice

1. Create `src/modules/<slice>/` with `service.py` (GHL calls via injected `GHLClient`), `schemas.py` (pydantic request/response with camelCase aliases), `router.py` (`APIRouter(prefix=...)` + `Depends(get_client)`).
2. Export `router` from the slice `__init__.py`.
3. `app.include_router(...)` in `server.py`.

## GHL API notes

- Targets **API V2**, not the deprecated V1 (`rest.gohighlevel.com`). Base URL and version live in `core/config.py`.
- Marketplace docs (`marketplace.gohighlevel.com/docs/ghl/...`) are JS-rendered — WebFetch returns only partial content; prefer WebSearch for endpoint shapes.

<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
at specs/001-contact-create/plan.md
<!-- SPECKIT END -->
