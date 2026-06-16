"""Servicio del slice de booking.

`BookingService` es una capa de composicion: reusa el `GHLClient` compartido y
construye sobre el mismo cliente un `ContactsService` y un `CalendarService`.
No duplica llamadas a GHL; orquesta las que ya existen (Principio I: composicion
que depende hacia abajo de los dos dominios, no un peer importando a un peer).
"""

from __future__ import annotations

from typing import Any

from core.client import GHLClient
from core.errors import GHLAPIError
from modules.calendar.service import CalendarService
from modules.contacts.service import ContactsService


def _normalize_phone(phone: str | None) -> str:
    """Deja solo digitos para comparar telefonos de forma estable."""
    if not phone:
        return ""
    return "".join(ch for ch in phone if ch.isdigit())


class BookingService:
    """Resolver find-or-create + reserva de cita en un paso."""

    def __init__(self, client: GHLClient | None = None):
        self.client = client or GHLClient()
        # Mismo cliente compartido para ambos slices (Principio II).
        self._contacts = ContactsService(self.client)
        self._calendar = CalendarService(self.client)

    # --- find-or-create resolver (US1) -----------------------------------
    def resolve_contact(
        self,
        *,
        email: str | None = None,
        phone: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        source: str | None = None,
    ) -> dict[str, Any]:
        """Resuelve identificadores a un unico contacto (find-or-create).

        Busca por email (match exacto case-insensitive), luego por telefono
        (match exacto normalizado); si encuentra, es matched. Si no, crea el
        contacto. Devuelve `{"contact": {...}, "created": bool}`.

        Nota: la busqueda de GHL es eventualmente consistente, asi que el
        dedup es best-effort frente a creaciones muy recientes.
        """
        if not email and not phone:
            raise ValueError("Se requiere al menos 'email' o 'phone'.")

        if email:
            results = self._contacts.search_contacts(query=email).get("contacts", [])
            match = next(
                (c for c in results if (c.get("email") or "").lower() == email.lower()),
                None,
            )
            if match:
                return {"contact": match, "created": False}

        if phone:
            results = self._contacts.search_contacts(query=phone).get("contacts", [])
            target = _normalize_phone(phone)
            match = next(
                (c for c in results if _normalize_phone(c.get("phone")) == target),
                None,
            )
            if match:
                return {"contact": match, "created": False}

        created = self._contacts.create_contact(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            source=source,
        )
        # GHL envuelve el contacto creado en {"contact": {...}}; lo desenvolvemos
        # para devolver siempre el objeto contacto con su id en el nivel superior.
        contact = (
            created.get("contact", created) if isinstance(created, dict) else created
        )
        return {"contact": contact, "created": True}

    # --- calendar resolution (US2) ---------------------------------------
    def _resolve_calendar(
        self, explicit_calendar_id: str | None = None
    ) -> tuple[str | None, list[dict[str, Any]] | None]:
        """Resuelve que calendario usar.

        Precedencia: id explicito -> default configurado -> unico calendario.
        Devuelve `(calendar_id, None)` cuando se resuelve, o
        `(None, [candidatos])` cuando es ambiguo (no adivina, FR-011). Si no
        existe ningun calendario, lanza un error 409.
        """
        if explicit_calendar_id:
            return explicit_calendar_id, None

        default = self.client.config.default_calendar_id
        if default:
            return default, None

        calendars = self._calendar.list_calendars()
        if len(calendars) == 1:
            return calendars[0].get("id"), None
        if not calendars:
            raise GHLAPIError(409, "No hay calendario disponible en la location.")

        candidates = [{"id": c.get("id"), "name": c.get("name")} for c in calendars]
        return None, candidates

    # --- one-step booking (US2) ------------------------------------------
    def book_appointment(
        self,
        *,
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
        """Resuelve el contacto, resuelve el calendario y crea la cita.

        Si el calendario es ambiguo, devuelve `calendar_selection_required`
        sin crear nada. No es atomico: si el contacto se crea pero la cita
        falla, el contacto queda creado y el error se propaga (R5/FR-014).
        """
        resolved = self.resolve_contact(
            email=email,
            phone=phone,
            first_name=first_name,
            last_name=last_name,
            source=source,
        )
        contact = resolved["contact"]
        contact_created = resolved["created"]

        cal_id, candidates = self._resolve_calendar(calendar_id)
        if cal_id is None:
            return {
                "status": "calendar_selection_required",
                "calendars": candidates,
            }

        appointment = self._calendar.create_appointment(
            calendar_id=cal_id,
            contact_id=contact.get("id"),
            start_time=start_time,
            end_time=end_time,
            title=title,
        )
        return {
            "status": "booked",
            "appointment": appointment,
            "contact": contact,
            "contact_created": contact_created,
        }
