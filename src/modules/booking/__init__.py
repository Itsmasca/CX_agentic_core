"""Slice de booking: composicion de contacts + calendar.

Expone (1) un resolver find-or-create de contactos y (2) la reserva de cita en
un paso. No duplica logica de GHL: compone los servicios existentes sobre el
mismo `GHLClient` compartido.
"""

from .router import router

__all__ = ["router"]
