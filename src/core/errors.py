"""Errores del core de GHL."""

from __future__ import annotations


class GHLError(Exception):
    """Error base para cualquier fallo del core."""


class GHLAPIError(GHLError):
    """La API de GHL respondio con un status de error (4xx/5xx)."""

    def __init__(self, status_code: int, message: str, payload: object = None):
        self.status_code = status_code
        self.payload = payload
        super().__init__(f"[{status_code}] {message}")


class GHLAuthError(GHLAPIError):
    """Credenciales invalidas o sin permisos (401/403)."""
