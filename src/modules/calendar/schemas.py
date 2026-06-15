"""Schemas (request/response) del slice de calendar."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CreateAppointmentRequest(BaseModel):
    """Body para crear una cita."""

    calendar_id: str = Field(..., alias="calendarId")
    contact_id: str = Field(..., alias="contactId")
    start_time: str = Field(..., alias="startTime")
    end_time: str | None = Field(None, alias="endTime")
    title: str | None = None
    assigned_user_id: str | None = Field(None, alias="assignedUserId")
    appointment_status: str = Field("confirmed", alias="appointmentStatus")
    location_id: str | None = Field(None, alias="locationId")

    model_config = {"populate_by_name": True}


class UpdateAppointmentRequest(BaseModel):
    """Body para editar una cita. Solo se mandan los campos presentes."""

    start_time: str | None = Field(None, alias="startTime")
    end_time: str | None = Field(None, alias="endTime")
    title: str | None = None
    appointment_status: str | None = Field(None, alias="appointmentStatus")
    assigned_user_id: str | None = Field(None, alias="assignedUserId")

    model_config = {"populate_by_name": True}

    def to_ghl_payload(self) -> dict:
        """Campos en camelCase, omitiendo los que vienen vacios."""
        return self.model_dump(by_alias=True, exclude_none=True)
