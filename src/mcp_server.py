"""Servidor MCP del core de GHL.

Expone el `CalendarService` como tools MCP para que un LLM (Claude Desktop,
Claude Code, o la API via mcp_servers) pueda operar la subcuenta de GHL.

Es una capa delgada sobre la misma logica que usa el server REST: comparte
un unico `GHLClient` durante la vida del proceso.

Arranque (Streamable HTTP, por defecto en este modulo):

    uv run python -m mcp_server          # expone en http://0.0.0.0:8000/mcp

Para uso local con stdio (Claude Desktop), cambia el transport en __main__.
"""

from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from core.client import GHLClient
from modules.calendar.service import CalendarService

# host/port configurables por entorno; /mcp es el path del transporte HTTP.
mcp = FastMCP(
    "CXAPP - GHL Core",
    host=os.environ.get("MCP_HOST", "0.0.0.0"),
    port=int(os.environ.get("MCP_PORT", "8000")),
)

# Un solo cliente HTTP para todo el proceso (lee credenciales del entorno/.env).
_client = GHLClient()
_calendar = CalendarService(_client)


# --- calendar slice ------------------------------------------------------
@mcp.tool()
def list_calendars(location_id: str | None = None) -> list[dict[str, Any]]:
    """Lista los calendarios de la subcuenta de GHL.

    Usa esta tool cuando el usuario pregunte que calendarios existen o
    necesite un calendar_id para agendar.
    """
    return _calendar.list_calendars(location_id)


@mcp.tool()
def get_free_slots(
    calendar_id: str,
    start_date: int,
    end_date: int,
    timezone: str | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Devuelve los slots libres de un calendario en un rango de fechas.

    start_date y end_date van en epoch milisegundos. La respuesta viene
    mapeada por dia (YYYY-MM-DD) con su lista de slots disponibles.
    """
    return _calendar.get_free_slots(
        calendar_id, start_date, end_date, timezone=timezone, user_id=user_id
    )


@mcp.tool()
def create_appointment(
    calendar_id: str,
    contact_id: str,
    start_time: str,
    end_time: str | None = None,
    title: str | None = None,
    assigned_user_id: str | None = None,
    appointment_status: str = "confirmed",
    location_id: str | None = None,
) -> dict[str, Any]:
    """Crea una cita en un calendario.

    start_time / end_time van en ISO 8601 con offset, por ejemplo
    2026-06-15T09:00:00-06:00.
    """
    return _calendar.create_appointment(
        calendar_id=calendar_id,
        contact_id=contact_id,
        start_time=start_time,
        end_time=end_time,
        title=title,
        assigned_user_id=assigned_user_id,
        appointment_status=appointment_status,
        location_id=location_id,
    )


@mcp.tool()
def get_appointment(event_id: str) -> dict[str, Any]:
    """Obtiene una cita por su id de evento."""
    return _calendar.get_appointment(event_id)


@mcp.tool()
def update_appointment(
    event_id: str,
    start_time: str | None = None,
    end_time: str | None = None,
    title: str | None = None,
    appointment_status: str | None = None,
    assigned_user_id: str | None = None,
) -> dict[str, Any]:
    """Edita campos de una cita. Solo se mandan los campos no vacios.

    appointment_status acepta valores de la API V2 (confirmed, cancelled, etc).
    """
    fields = {
        "startTime": start_time,
        "endTime": end_time,
        "title": title,
        "appointmentStatus": appointment_status,
        "assignedUserId": assigned_user_id,
    }
    fields = {k: v for k, v in fields.items() if v is not None}
    return _calendar.update_appointment(event_id, **fields)


@mcp.tool()
def cancel_appointment(event_id: str) -> dict[str, Any]:
    """Cancela una cita marcandola como cancelled."""
    return _calendar.cancel_appointment(event_id)


@mcp.tool()
def delete_appointment(event_id: str) -> str:
    """Elimina un evento de calendario. Accion no reversible."""
    _calendar.delete_appointment(event_id)
    return f"Evento {event_id} eliminado."


if __name__ == "__main__":
    # Streamable HTTP: clientes remotos se conectan a http://<host>:<port>/mcp
    # Para stdio (Claude Desktop local), usa: mcp.run()
    mcp.run(transport="streamable-http")
