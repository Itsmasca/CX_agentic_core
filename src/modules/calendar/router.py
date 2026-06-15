"""Router del slice de calendar."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from core.client import GHLClient
from core.deps import get_client

from .schemas import CreateAppointmentRequest, UpdateAppointmentRequest
from .service import CalendarService

router = APIRouter(prefix="/calendar", tags=["calendar"])


def get_service(client: Annotated[GHLClient, Depends(get_client)]) -> CalendarService:
    """Construye el CalendarService sobre el cliente compartido."""
    return CalendarService(client)


ServiceDep = Annotated[CalendarService, Depends(get_service)]


@router.get("/calendars")
def list_calendars(service: ServiceDep, location_id: str | None = None):
    """Lista los calendarios de la subcuenta."""
    return service.list_calendars(location_id)


@router.get("/calendars/{calendar_id}/free-slots")
def get_free_slots(
    calendar_id: str,
    service: ServiceDep,
    start_date: Annotated[int, Query(description="epoch ms")],
    end_date: Annotated[int, Query(description="epoch ms")],
    timezone: str | None = None,
    user_id: str | None = None,
):
    """Slots libres de un calendario en un rango (fechas en epoch ms)."""
    return service.get_free_slots(
        calendar_id, start_date, end_date, timezone=timezone, user_id=user_id
    )


@router.post("/appointments", status_code=201)
def create_appointment(body: CreateAppointmentRequest, service: ServiceDep):
    """Crea una cita."""
    return service.create_appointment(
        calendar_id=body.calendar_id,
        contact_id=body.contact_id,
        start_time=body.start_time,
        end_time=body.end_time,
        title=body.title,
        assigned_user_id=body.assigned_user_id,
        appointment_status=body.appointment_status,
        location_id=body.location_id,
    )


@router.get("/appointments/{event_id}")
def get_appointment(event_id: str, service: ServiceDep):
    """Obtiene una cita por id de evento."""
    return service.get_appointment(event_id)


@router.patch("/appointments/{event_id}")
def update_appointment(
    event_id: str, body: UpdateAppointmentRequest, service: ServiceDep
):
    """Edita campos de una cita."""
    return service.update_appointment(event_id, **body.to_ghl_payload())


@router.post("/appointments/{event_id}/cancel")
def cancel_appointment(event_id: str, service: ServiceDep):
    """Cancela una cita."""
    return service.cancel_appointment(event_id)


@router.delete("/appointments/{event_id}", status_code=204)
def delete_appointment(event_id: str, service: ServiceDep):
    """Elimina un evento de calendario."""
    service.delete_appointment(event_id)
