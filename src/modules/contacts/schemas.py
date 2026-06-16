"""Schemas (request/response) del slice de contacts."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, model_validator


class CreateContactRequest(BaseModel):
    """Body para crear un contacto.

    El borde publico habla snake_case; los alias mapean a las claves
    camelCase que espera la API V2 de GHL. Se exige al menos un dato de
    contacto identificable (email o telefono).
    """

    first_name: str | None = Field(None, alias="firstName")
    last_name: str | None = Field(None, alias="lastName")
    email: EmailStr | None = None
    phone: str | None = None
    tags: list[str] | None = None
    source: str | None = None

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def _require_email_or_phone(self) -> CreateContactRequest:
        """Un contacto necesita al menos email o telefono para identificarse."""
        if not self.email and not self.phone:
            raise ValueError("Se requiere al menos 'email' o 'phone'.")
        return self
