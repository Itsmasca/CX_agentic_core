"""Dependencias compartidas para FastAPI.

El `GHLClient` vive en `app.state` (creado una vez en el lifespan) para
reutilizar la conexion httpx entre requests.
"""

from __future__ import annotations

from fastapi import Request

from .client import GHLClient


def get_client(request: Request) -> GHLClient:
    """Devuelve el GHLClient compartido de la app."""
    return request.app.state.ghl_client
