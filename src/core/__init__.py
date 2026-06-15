"""Core de GHL: config, cliente HTTP y errores compartidos."""

from .client import GHLClient
from .config import GHLConfig
from .errors import GHLAPIError, GHLAuthError, GHLError

__all__ = [
    "GHLClient",
    "GHLConfig",
    "GHLError",
    "GHLAPIError",
    "GHLAuthError",
]
