"""Repositorio en memoria temporal para desarrollo y pruebas de FASE 1."""

from __future__ import annotations

from solicitudes_partner.dominio.entidades import SolicitudPartner
from solicitudes_partner.dominio.objetos_valor import PartnerId, ReferenciaExterna, SolicitudId
from solicitudes_partner.dominio.repositorios import RepositorioSolicitudesPartner


class RepositorioSolicitudesPartnerMemoria(RepositorioSolicitudesPartner):
    """Implementación temporal; será reemplazada por PostgreSQL en fases siguientes."""

    def __init__(self) -> None:
        self._solicitudes_por_id: dict[str, SolicitudPartner] = {}
        self._indice_partner_referencia: set[tuple[str, str]] = set()

    def guardar(self, solicitud: SolicitudPartner) -> None:
        self._solicitudes_por_id[solicitud.solicitud_id.valor] = solicitud
        self._indice_partner_referencia.add(
            (solicitud.partner_id.valor, solicitud.referencia_externa.valor)
        )

    def obtener_por_id(self, solicitud_id: SolicitudId) -> SolicitudPartner | None:
        return self._solicitudes_por_id.get(solicitud_id.valor)

    def existe_por_partner_y_referencia(
        self,
        partner_id: PartnerId,
        referencia_externa: ReferenciaExterna,
    ) -> bool:
        return (partner_id.valor, referencia_externa.valor) in self._indice_partner_referencia
