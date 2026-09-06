"""Puerto de lectura (Read Model) para consultas CQRS de SolicitudPartner - Fase 4."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .vistas import VistaSolicitudPartner


class RepositorioLecturaSolicitudesPartner(ABC):
    """Contrato de consulta sobre la proyeccion de lectura, independiente del modelo de escritura."""

    @abstractmethod
    def obtener_por_id(self, solicitud_id: str) -> VistaSolicitudPartner | None:
        raise NotImplementedError

    @abstractmethod
    def listar_por_partner(self, partner_id: str) -> list[VistaSolicitudPartner]:
        raise NotImplementedError

    @abstractmethod
    def actualizar(self, vista: VistaSolicitudPartner) -> None:
        raise NotImplementedError
