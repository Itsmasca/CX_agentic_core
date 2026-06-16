"""Modulo de Contacts de GHL (API V2).

Cubre crear, buscar/listar y actualizar contactos. Cada metodo es un wrapper
tipado sobre el `GHLClient` del core, que centraliza auth y manejo de errores.
"""

from __future__ import annotations

from typing import Any

from core.client import GHLClient


class ContactsService:
    """Operaciones de contactos sobre una subcuenta de GHL."""

    def __init__(self, client: GHLClient | None = None):
        self.client = client or GHLClient()
        # location_id por defecto, tomado de la config del cliente.
        self.location_id = self.client.config.location_id

    def create_contact(
        self,
        *,
        first_name: str | None = None,
        last_name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        tags: list[str] | None = None,
        source: str | None = None,
        location_id: str | None = None,
    ) -> dict[str, Any]:
        """Crea un contacto en la subcuenta configurada.

        El `locationId` se inyecta desde la config; el consumidor no lo
        especifica. Los campos vacios (None) los limpia el `GHLClient`.
        """
        body: dict[str, Any] = {
            "firstName": first_name,
            "lastName": last_name,
            "email": email,
            "phone": phone,
            "tags": tags,
            "source": source,
            "locationId": location_id or self.location_id,
        }
        return self.client.post("/contacts/", json=body)

    def search_contacts(
        self,
        *,
        query: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Busca/lista contactos de la subcuenta configurada.

        `query` es texto libre que GHL matchea contra nombre/email/telefono;
        omitelo para listar. `limit` se acota al maximo de 100 por pagina que
        admite GHL. Devuelve `{"contacts": [...], "total": n}`.
        """
        limit = max(1, min(limit, 100))
        body: dict[str, Any] = {
            "locationId": self.location_id,
            "pageLimit": limit,
            "query": query,
        }
        return self.client.post("/contacts/search", json=body)

    def update_contact(self, contact_id: str, **fields: Any) -> dict[str, Any]:
        """Actualiza un contacto existente (update parcial).

        `fields` van en las claves camelCase de la API V2 (por ejemplo
        `firstName`, `source`). Solo se mandan los presentes; el `GHLClient`
        limpia los None. No se envia `locationId` (el contacto ya pertenece a
        su location).
        """
        return self.client.put(f"/contacts/{contact_id}", json=fields)
