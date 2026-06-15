"""Cliente HTTP base para la API V2 de GHL.

Centraliza auth, headers obligatorios y manejo de errores. Cada modulo
(calendar, contacts, etc.) recibe una instancia de `GHLClient` y solo se
preocupa por sus endpoints.
"""

from __future__ import annotations

from typing import Any

import httpx

from .config import GHLConfig
from .errors import GHLAPIError, GHLAuthError


class GHLClient:
    """Wrapper delgado sobre httpx con la auth de GHL ya resuelta."""

    def __init__(self, config: GHLConfig | None = None):
        self.config = config or GHLConfig.from_env()
        self._http = httpx.Client(
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            headers={
                "Authorization": f"Bearer {self.config.token}",
                "Version": self.config.api_version,
                "Accept": "application/json",
            },
        )

    # --- ciclo de vida ---------------------------------------------------
    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> GHLClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # --- verbos ----------------------------------------------------------
    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return self._request("GET", path, params=params)

    def post(self, path: str, json: dict[str, Any] | None = None) -> Any:
        return self._request("POST", path, json=json)

    def put(self, path: str, json: dict[str, Any] | None = None) -> Any:
        return self._request("PUT", path, json=json)

    def delete(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return self._request("DELETE", path, params=params)

    # --- nucleo ----------------------------------------------------------
    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        # Limpia params/body de valores None para no mandar basura a la API.
        if params is not None:
            params = {k: v for k, v in params.items() if v is not None}
        if json is not None:
            json = {k: v for k, v in json.items() if v is not None}

        response = self._http.request(method, path, params=params, json=json)
        return self._handle(response)

    def _handle(self, response: httpx.Response) -> Any:
        if response.is_success:
            if not response.content:
                return None
            try:
                return response.json()
            except ValueError:
                return response.text

        # Intenta extraer el mensaje de error que manda GHL.
        try:
            payload = response.json()
            message = payload.get("message") or payload.get("error") or response.text
        except ValueError:
            payload = response.text
            message = response.text

        if response.status_code in (401, 403):
            raise GHLAuthError(response.status_code, message, payload)
        raise GHLAPIError(response.status_code, message, payload)
