"""Modulo de Calendar de GHL (API V2).

Cubre lo basico funcional: listar calendarios, consultar slots libres y
crear / leer / editar / cancelar citas. Cada metodo es un wrapper tipado
sobre el `GHLClient` del core.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from core.client import GHLClient


def _to_epoch_ms(value: int | datetime | date) -> int:
    """Normaliza fechas a epoch en milisegundos, como espera GHL."""
    if isinstance(value, int):
        return value
    if isinstance(value, datetime):
        return int(value.timestamp() * 1000)
    if isinstance(value, date):
        return int(datetime(value.year, value.month, value.day).timestamp() * 1000)
    raise TypeError(f"Fecha no soportada: {type(value)!r}")


class CalendarService:
    """Operaciones de calendario sobre una subcuenta de GHL."""

    def __init__(self, client: GHLClient | None = None):
        self.client = client or GHLClient()
        # location_id por defecto, tomado de la config del cliente.
        self.location_id = self.client.config.location_id

    # --- calendarios -----------------------------------------------------
    def list_calendars(self, location_id: str | None = None) -> list[dict[str, Any]]:
        """Lista los calendarios de la subcuenta."""
        data = self.client.get(
            "/calendars/",
            params={"locationId": location_id or self.location_id},
        )
        return data.get("calendars", []) if isinstance(data, dict) else []

    # --- disponibilidad --------------------------------------------------
    def get_free_slots(
        self,
        calendar_id: str,
        start: int | datetime | date,
        end: int | datetime | date,
        *,
        timezone: str | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """Devuelve los slots libres de un calendario en un rango de fechas.

        La respuesta viene mapeada por dia (`YYYY-MM-DD`) con su lista de
        slots disponibles.
        """
        return self.client.get(
            f"/calendars/{calendar_id}/free-slots",
            params={
                "startDate": _to_epoch_ms(start),
                "endDate": _to_epoch_ms(end),
                "timezone": timezone,
                "userId": user_id,
            },
        )

    # --- citas -----------------------------------------------------------
    def create_appointment(
        self,
        *,
        calendar_id: str,
        contact_id: str,
        start_time: str,
        end_time: str | None = None,
        title: str | None = None,
        assigned_user_id: str | None = None,
        appointment_status: str = "confirmed",
        location_id: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Crea una cita.

        `start_time` / `end_time` van en ISO 8601 con offset, por ejemplo
        `2026-06-15T09:00:00-06:00`.
        """
        body: dict[str, Any] = {
            "calendarId": calendar_id,
            "locationId": location_id or self.location_id,
            "contactId": contact_id,
            "startTime": start_time,
            "endTime": end_time,
            "title": title,
            "assignedUserId": assigned_user_id,
            "appointmentStatus": appointment_status,
        }
        if extra:
            body.update(extra)
        return self.client.post("/calendars/events/appointments", json=body)

    def get_appointment(self, event_id: str) -> dict[str, Any]:
        """Obtiene una cita por su id de evento."""
        return self.client.get(f"/calendars/events/appointments/{event_id}")

    def update_appointment(self, event_id: str, **fields: Any) -> dict[str, Any]:
        """Actualiza campos de una cita (start_time, status, etc.).

        Acepta las mismas claves camelCase de la API V2, por ejemplo
        `startTime`, `appointmentStatus`, `title`.
        """
        return self.client.put(
            f"/calendars/events/appointments/{event_id}", json=fields
        )

    def cancel_appointment(self, event_id: str) -> dict[str, Any]:
        """Cancela una cita marcandola como `cancelled`."""
        return self.update_appointment(event_id, appointmentStatus="cancelled")

    def delete_appointment(self, event_id: str) -> Any:
        """Elimina un evento de calendario."""
        return self.client.delete(f"/calendars/events/{event_id}")
