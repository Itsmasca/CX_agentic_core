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
from modules.booking.service import BookingService
from modules.calendar.service import CalendarService
from modules.contacts.service import ContactsService

# streamable_http_path="/" para que, al montarlo en FastAPI bajo "/mcp",
# el endpoint quede exactamente en /mcp (sin duplicar el segmento).
# host/port solo aplican al modo standalone (__main__).
mcp = FastMCP(
    "CXAPP - GHL Core",
    host=os.environ.get("MCP_HOST", "0.0.0.0"),
    port=int(os.environ.get("MCP_PORT", "8000")),
    streamable_http_path="/",
)

# Un solo cliente HTTP para todo el proceso (lee credenciales del entorno/.env).
_client = GHLClient()
_calendar = CalendarService(_client)
_contacts = ContactsService(_client)
_booking = BookingService(_client)


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
    start_date: int | None = None,
    end_date: int | None = None,
    timezone: str | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Devuelve los slots libres de un calendario.

    start_date y end_date van en epoch milisegundos y son OPCIONALES: lo
    recomendado es OMITIRLOS, y entonces consulta desde ahora hasta +30 dias
    (evita errores al calcular fechas). La respuesta viene mapeada por dia
    (YYYY-MM-DD) con su lista de slots; ofrece al usuario los mas proximos.
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


# --- contacts slice ------------------------------------------------------
@mcp.tool()
def create_contact(
    first_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    tags: list[str] | None = None,
    source: str | None = None,
) -> dict[str, Any]:
    """Crea un contacto en la subcuenta de GHL.

    Requiere al menos email o telefono para identificar al contacto. El
    location se toma de la config; devuelve el contacto creado con su id.
    """
    if not email and not phone:
        raise ValueError("Se requiere al menos 'email' o 'phone'.")
    return _contacts.create_contact(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        tags=tags,
        source=source,
    )


@mcp.tool()
def search_contacts(query: str | None = None, limit: int = 20) -> dict[str, Any]:
    """Busca/lista contactos de la subcuenta de GHL.

    Usa esta tool para encontrar el contact_id de un contacto (por ejemplo,
    para luego agendar una cita con create_appointment). `query` es texto libre
    que matchea nombre/email/telefono; omitelo para listar. `limit` por defecto
    20, maximo 100. Devuelve {"contacts": [...], "total": n}.
    """
    return _contacts.search_contacts(query=query, limit=limit)


@mcp.tool()
def update_contact(
    contact_id: str,
    first_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    source: str | None = None,
) -> dict[str, Any]:
    """Actualiza un contacto existente (update parcial). Solo se mandan los
    campos no vacios; debe venir al menos uno."""
    fields = {
        "firstName": first_name,
        "lastName": last_name,
        "email": email,
        "phone": phone,
        "source": source,
    }
    fields = {k: v for k, v in fields.items() if v is not None}
    if not fields:
        raise ValueError("Se requiere al menos un campo para actualizar.")
    return _contacts.update_contact(contact_id, **fields)


# --- booking slice -------------------------------------------------------
@mcp.tool()
def resolve_contact(
    email: str | None = None,
    phone: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    source: str | None = None,
) -> dict[str, Any]:
    """Resuelve identificadores a un unico contacto (find-or-create).

    Busca el contacto por email/telefono y, si existe, lo devuelve (matched);
    si no, lo crea. Requiere al menos email o telefono. Devuelve
    {"contact": {...}, "created": bool}. Util para obtener el contact_id de una
    persona, creandola solo si hace falta.
    """
    if not email and not phone:
        raise ValueError("Se requiere al menos 'email' o 'phone'.")
    return _booking.resolve_contact(
        email=email,
        phone=phone,
        first_name=first_name,
        last_name=last_name,
        source=source,
    )


@mcp.tool()
def book_appointment(
    start_time: str,
    email: str | None = None,
    phone: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    source: str | None = None,
    end_time: str | None = None,
    title: str | None = None,
    calendar_id: str | None = None,
) -> dict[str, Any]:
    """Reserva una cita para una persona en un solo paso.

    Resuelve el contacto (find-or-create), autoresuelve el calendario y crea la
    cita. start_time va en ISO 8601 con offset (ej. 2026-06-20T15:00:00-06:00).
    Requiere start_time y al menos email o telefono. Devuelve status "booked"
    con la cita y el contacto, o status "calendar_selection_required" con los
    calendarios disponibles si hay que elegir: en ese caso, vuelve a llamar
    pasando un calendar_id.
    """
    if not email and not phone:
        raise ValueError("Se requiere al menos 'email' o 'phone'.")
    return _booking.book_appointment(
        start_time=start_time,
        email=email,
        phone=phone,
        first_name=first_name,
        last_name=last_name,
        source=source,
        end_time=end_time,
        title=title,
        calendar_id=calendar_id,
    )


if __name__ == "__main__":
    # Modo standalone (dev). Con streamable_http_path="/" el endpoint queda en
    # http://<host>:<port>/ . En produccion se sirve montado en /mcp via server.py.
    # Para stdio (Claude Desktop local), usa: mcp.run()
    mcp.run(transport="streamable-http")
