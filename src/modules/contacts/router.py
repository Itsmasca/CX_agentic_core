"""Router del slice de contacts."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from core.client import GHLClient
from core.deps import get_client

from .schemas import CreateContactRequest, UpdateContactRequest
from .service import ContactsService

router = APIRouter(prefix="/contacts", tags=["contacts"])


def get_service(client: Annotated[GHLClient, Depends(get_client)]) -> ContactsService:
    """Construye el ContactsService sobre el cliente compartido."""
    return ContactsService(client)


ServiceDep = Annotated[ContactsService, Depends(get_service)]


@router.post("", status_code=201)
def create_contact(body: CreateContactRequest, service: ServiceDep):
    """Crea un contacto en la subcuenta configurada."""
    return service.create_contact(
        first_name=body.first_name,
        last_name=body.last_name,
        email=body.email,
        phone=body.phone,
        tags=body.tags,
        source=body.source,
    )


@router.get("")
def search_contacts(
    service: ServiceDep,
    query: str | None = None,
    limit: int = 20,
):
    """Busca/lista contactos. `query` es texto libre (nombre/email/telefono);
    omitelo para listar. `limit` por defecto 20, maximo 100."""
    return service.search_contacts(query=query, limit=limit)


@router.put("/{contact_id}")
def update_contact(contact_id: str, body: UpdateContactRequest, service: ServiceDep):
    """Actualiza campos de un contacto existente (update parcial)."""
    return service.update_contact(contact_id, **body.to_ghl_payload())
