"""Proyector que mantiene el Read Model de SolicitudPartner - Fase 4 CQRS."""

from __future__ import annotations

from solicitudes_partner.aplicacion.puertos_lectura import RepositorioLecturaSolicitudesPartner
from solicitudes_partner.aplicacion.vistas import VistaSolicitudPartner
from solicitudes_partner.dominio.eventos import (
    EventoDominio,
    SolicitudPartnerListaParaAtencion,
    SolicitudPartnerRechazada,
    SolicitudPartnerRegistrada,
)
from solicitudes_partner.dominio.objetos_valor import SolicitudId
from solicitudes_partner.dominio.repositorios import RepositorioSolicitudesPartner

_EVENTOS_RELEVANTES = (
    SolicitudPartnerRegistrada,
    SolicitudPartnerListaParaAtencion,
    SolicitudPartnerRechazada,
)


class ProyeccionSolicitudesPartner:
    """Actualiza el Read Model a partir de los eventos del agregado.

    Lee el estado ya persistido en el repositorio de escritura (nunca lo modifica) porque los
    eventos de transicion (Lista/Rechazada) no cargan todos los campos de la vista; esto evita
    cambiar el contrato de los eventos de dominio.
    """

    def __init__(
        self,
        repositorio_escritura: RepositorioSolicitudesPartner,
        repositorio_lectura: RepositorioLecturaSolicitudesPartner,
    ):
        self._repositorio_escritura = repositorio_escritura
        self._repositorio_lectura = repositorio_lectura

    def manejar_evento(self, evento: EventoDominio) -> None:
        if not isinstance(evento, _EVENTOS_RELEVANTES):
            return

        solicitud = self._repositorio_escritura.obtener_por_id(SolicitudId(evento.solicitud_id))
        if solicitud is None:
            return

        self._repositorio_lectura.actualizar(
            VistaSolicitudPartner(
                solicitud_id=solicitud.solicitud_id.valor,
                partner_id=solicitud.partner_id.valor,
                referencia_externa=solicitud.referencia_externa.valor,
                tipo_servicio=solicitud.tipo_servicio.valor,
                estado=solicitud.estado.value,
            )
        )
