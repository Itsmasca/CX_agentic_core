"""Router del slice de booking."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from core.client import GHLClient
from core.deps import get_client

from .schemas import BookAppointmentRequest, ResolveContactRequest
from .service import BookingService

router = APIRouter(prefix="/booking", tags=["booking"])


def get_service(client: Annotated[GHLClient, Depends(get_client)]) -> BookingService:
    """Construye el BookingService sobre el cliente compartido."""
    return BookingService(client)


ServiceDep = Annotated[BookingService, Depends(get_service)]


@router.post("/resolve-contact")
def resolve_contact(body: ResolveContactRequest, service: ServiceDep):
    """Resuelve identificadores a un unico contacto (find-or-create).

    Devuelve `{contact, created}`. `created=false` = ya existia; `created=true`
    = recien creado. Requiere al menos email o telefono.
    """
    return service.resolve_contact(
        email=body.email,
        phone=body.phone,
        first_name=body.first_name,
        last_name=body.last_name,
        source=body.source,
    )


@router.post("/appointments")
def book_appointment(body: BookAppointmentRequest, service: ServiceDep):
    """Reserva una cita para un contacto en un solo paso.

    Resuelve el contacto (find-or-create), autoresuelve el calendario y crea la
    cita. Devuelve `status: booked` con la cita y el contacto, o
    `status: calendar_selection_required` con los calendarios disponibles si la
    eleccion es ambigua (sin crear nada).
    """
    return service.book_appointment(
        start_time=body.start_time,
        email=body.email,
        phone=body.phone,
        first_name=body.first_name,
        last_name=body.last_name,
        source=body.source,
        end_time=body.end_time,
        title=body.title,
        calendar_id=body.calendar_id,
    )
