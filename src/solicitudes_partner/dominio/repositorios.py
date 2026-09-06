"""Puertos de salida del dominio para persistencia de solicitudes."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .entidades import SolicitudPartner
from .objetos_valor import PartnerId, ReferenciaExterna, SolicitudId


class RepositorioSolicitudesPartner(ABC):
    """Contrato de persistencia requerido por el dominio/aplicación."""

    @abstractmethod
    def guardar(self, solicitud: SolicitudPartner) -> None:
        raise NotImplementedError

    @abstractmethod
    def obtener_por_id(self, solicitud_id: SolicitudId) -> SolicitudPartner | None:
        raise NotImplementedError

    @abstractmethod
    def existe_por_partner_y_referencia(
        self,
        partner_id: PartnerId,
        referencia_externa: ReferenciaExterna,
    ) -> bool:
        raise NotImplementedError
