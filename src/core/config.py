"""Configuracion del core de GHL (API V2 / LeadConnector)."""

from __future__ import annotations

import os
from dataclasses import dataclass

# Base de la API V2 de GoHighLevel (LeadConnector).
BASE_URL = "https://services.leadconnectorhq.com"

# Version del contrato de la API V2. GHL la exige en cada request.
API_VERSION = "2021-04-15"


@dataclass(frozen=True)
class GHLConfig:
    """Credenciales y parametros para hablar con la API de GHL.

    El `token` es el Private Integration token de la subcuenta (empieza con
    `pit-...`). El `location_id` es el id de la subcuenta sobre la que operas.
    """

    token: str
    location_id: str
    base_url: str = BASE_URL
    api_version: str = API_VERSION
    timeout: float = 30.0

    @classmethod
    def from_env(cls) -> GHLConfig:
        """Construye la config desde variables de entorno.

        Requiere `GHL_TOKEN` y `GHL_LOCATION_ID`. Carga un archivo `.env`
        automaticamente si python-dotenv esta disponible.
        """
        try:
            from dotenv import load_dotenv

            load_dotenv()
        except ImportError:
            pass

        token = os.environ.get("GHL_TOKEN")
        location_id = os.environ.get("GHL_LOCATION_ID")
        if not token:
            raise ValueError("Falta la variable de entorno GHL_TOKEN")
        if not location_id:
            raise ValueError("Falta la variable de entorno GHL_LOCATION_ID")
        return cls(
            token=token,
            location_id=location_id,
            base_url=os.environ.get("GHL_BASE_URL", BASE_URL),
            api_version=os.environ.get("GHL_API_VERSION", API_VERSION),
        )
