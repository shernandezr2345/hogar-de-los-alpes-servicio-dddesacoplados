"""Repositorio de lectura en memoria (Read Model) - Fase 4 CQRS, para tests unitarios."""

from __future__ import annotations

from solicitudes_partner.aplicacion.puertos_lectura import RepositorioLecturaSolicitudesPartner
from solicitudes_partner.aplicacion.vistas import VistaSolicitudPartner


class RepositorioLecturaSolicitudesPartnerMemoria(RepositorioLecturaSolicitudesPartner):
    """Proyeccion en memoria; espejo del RepositorioSolicitudesPartnerMemoria."""

    def __init__(self) -> None:
        self._vistas: dict[str, VistaSolicitudPartner] = {}

    def obtener_por_id(self, solicitud_id: str) -> VistaSolicitudPartner | None:
        return self._vistas.get(solicitud_id)

    def listar_por_partner(self, partner_id: str) -> list[VistaSolicitudPartner]:
        return [vista for vista in self._vistas.values() if vista.partner_id == partner_id]

    def actualizar(self, vista: VistaSolicitudPartner) -> None:
        self._vistas[vista.solicitud_id] = vista
