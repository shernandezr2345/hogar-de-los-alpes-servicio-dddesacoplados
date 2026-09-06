"""Consultas de lectura (Read Model) - Fase 4 CQRS."""

from __future__ import annotations

from dataclasses import dataclass

from solicitudes_partner.dominio.excepciones import SolicitudNoEncontradaError

from .puertos_lectura import RepositorioLecturaSolicitudesPartner
from .vistas import VistaSolicitudPartner


@dataclass(frozen=True)
class ConsultarVistaSolicitudPartner:
    solicitud_id: str


@dataclass(frozen=True)
class ListarSolicitudesPartnerPorPartner:
    partner_id: str


class ConsultasSolicitudesPartner:
    """Coordina consultas usando exclusivamente el Read Model (puerto de lectura)."""

    def __init__(self, repositorio_lectura: RepositorioLecturaSolicitudesPartner):
        self._repositorio_lectura = repositorio_lectura

    def consultar_vista(self, consulta: ConsultarVistaSolicitudPartner) -> VistaSolicitudPartner:
        vista = self._repositorio_lectura.obtener_por_id(consulta.solicitud_id)
        if vista is None:
            raise SolicitudNoEncontradaError("No existe solicitud para el id consultado")
        return vista

    def listar_por_partner(
        self, consulta: ListarSolicitudesPartnerPorPartner
    ) -> list[VistaSolicitudPartner]:
        return self._repositorio_lectura.listar_por_partner(consulta.partner_id)
