"""Schemas (request/response) del slice de booking.

El borde publico habla snake_case (FR-015). Las respuestas son passthrough de
GHL (contacto/cita en camelCase, tal cual las devuelven los slices compuestos).
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, EmailStr, model_validator


class ResolveContactRequest(BaseModel):
    """Identificadores para el resolver find-or-create (US1).

    Se exige al menos email o telefono (FR-002): sin un identificador no se
    puede ni buscar ni crear un contacto. first_name/last_name/source solo se
    usan al crear.
    """

    email: EmailStr | None = None
    phone: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    source: str | None = None

    @model_validator(mode="after")
    def _require_email_or_phone(self) -> ResolveContactRequest:
        if not self.email and not self.phone:
            raise ValueError("Se requiere al menos 'email' o 'phone'.")
        return self


class ResolveResult(BaseModel):
    """Resultado del resolver: el contacto y si fue creado o ya existia."""

    contact: dict[str, Any]
    created: bool


class BookAppointmentRequest(BaseModel):
    """Identificadores del contacto + datos de la cita (US2).

    Requiere `start_time` y al menos un identificador (FR-009). `calendar_id`
    es un override opcional; si se omite, el calendario se autoresuelve.
    """

    email: EmailStr | None = None
    phone: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    source: str | None = None
    start_time: str
    end_time: str | None = None
    title: str | None = None
    calendar_id: str | None = None

    @model_validator(mode="after")
    def _require_identifier(self) -> BookAppointmentRequest:
        if not self.email and not self.phone:
            raise ValueError("Se requiere al menos 'email' o 'phone'.")
        return self


class BookedResult(BaseModel):
    """Reserva exitosa: cita creada + contacto resuelto (FR-012)."""

    status: Literal["booked"] = "booked"
    appointment: dict[str, Any]
    contact: dict[str, Any]
    contact_created: bool


class CalendarOption(BaseModel):
    """Calendario candidato que se ofrece cuando la eleccion es ambigua."""

    id: str
    name: str | None = None


class CalendarSelectionRequired(BaseModel):
    """Calendario ambiguo: no se reserva nada, se devuelven las opciones (FR-011)."""

    status: Literal["calendar_selection_required"] = "calendar_selection_required"
    calendars: list[CalendarOption]
