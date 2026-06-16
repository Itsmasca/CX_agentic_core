"""Servidor FastAPI del core de GHL.

Ensambla los routers de cada vertical slice y mantiene un GHLClient
compartido durante la vida de la app.
"""

from __future__ import annotations

import hmac
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from core.client import GHLClient
from core.errors import GHLAPIError
from mcp_server import mcp
from modules.booking import router as booking_router
from modules.calendar import router as calendar_router
from modules.contacts import router as contacts_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Un solo cliente HTTP para toda la app (lee credenciales del entorno/.env).
    app.state.ghl_client = GHLClient()
    # El session manager del MCP debe estar vivo mientras corre la app montada.
    async with mcp.session_manager.run():
        try:
            yield
        finally:
            app.state.ghl_client.close()


app = FastAPI(title="CXAPP - GHL Core", version="0.1.0", lifespan=lifespan)

# Auth del MCP: si MCP_AUTH_TOKEN esta definido, exige el token en el header
# `Authorization` de las rutas /mcp. Acepta tanto `Bearer <token>` como el
# token "pelon", porque distintos clientes (p.ej. ElevenLabs) lo mandan de una
# u otra forma. Sin la variable no aplica (uso interno/dev); imprescindible al
# exponer el MCP publicamente.
_MCP_AUTH_TOKEN = os.environ.get("MCP_AUTH_TOKEN")


@app.middleware("http")
async def mcp_auth_guard(request, call_next):
    if _MCP_AUTH_TOKEN and request.url.path.startswith("/mcp"):
        provided = request.headers.get("authorization", "")
        # Quita el prefijo "Bearer " (case-insensitive) si viene; si no, usa
        # el header tal cual. Asi toleramos ambos formatos.
        if provided[:7].lower() == "bearer ":
            provided = provided[7:]
        if not hmac.compare_digest(provided, _MCP_AUTH_TOKEN):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
    return await call_next(request)


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
app.include_router(contacts_router)
app.include_router(booking_router)

# --- MCP -----------------------------------------------------------------
# Server MCP (Streamable HTTP) montado en /mcp; comparte proceso con el REST.
app.mount("/mcp", mcp.streamable_http_app())
