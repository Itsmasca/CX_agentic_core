"""Servidor FastAPI del core de GHL.

Ensambla los routers de cada vertical slice y mantiene un GHLClient
compartido durante la vida de la app.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from core.client import GHLClient
from core.errors import GHLAPIError
from modules.calendar import router as calendar_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Un solo cliente HTTP para toda la app (lee credenciales del entorno/.env).
    app.state.ghl_client = GHLClient()
    try:
        yield
    finally:
        app.state.ghl_client.close()


app = FastAPI(title="CXAPP - GHL Core", version="0.1.0", lifespan=lifespan)


@app.exception_handler(GHLAPIError)
async def ghl_api_error_handler(request, exc: GHLAPIError):
    """Traduce errores de la API de GHL a respuestas HTTP limpias."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "ghl_api_error", "detail": str(exc), "payload": exc.payload},
    )


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}


# --- vertical slices -----------------------------------------------------
app.include_router(calendar_router)
