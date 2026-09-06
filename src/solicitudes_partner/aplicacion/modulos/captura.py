"""Modulo de Captura de Solicitudes."""

from __future__ import annotations

from solicitudes_partner.aplicacion.comandos import RegistrarSolicitudPartner
from solicitudes_partner.aplicacion.puertos_eventos import EventBus
from solicitudes_partner.dominio.entidades import SolicitudPartner
from solicitudes_partner.dominio.objetos_valor import (
    PartnerId,
    ReferenciaExterna,
    SolicitudId,
    TipoServicio,
)
from solicitudes_partner.dominio.repositorios import RepositorioSolicitudesPartner


class CapturaSolicitudes:
    """Registra solicitudes y publica eventos del agregado sin acoplarse a Reglas."""

    def __init__(self, repositorio: RepositorioSolicitudesPartner, event_bus: EventBus):
        self._repositorio = repositorio
        self._event_bus = event_bus

    def registrar_solicitud(self, comando: RegistrarSolicitudPartner) -> SolicitudPartner:
        solicitud_id = SolicitudId(comando.solicitud_id)
        partner_id = PartnerId(comando.partner_id)
        referencia = ReferenciaExterna(comando.referencia_externa)
        tipo_servicio = TipoServicio(comando.tipo_servicio)

        existe_previa = self._repositorio.existe_por_partner_y_referencia(partner_id, referencia)

        solicitud = SolicitudPartner.crear(
            solicitud_id=solicitud_id,
            partner_id=partner_id,
            referencia_externa=referencia,
            tipo_servicio=tipo_servicio,
            existe_previa=existe_previa,
        )

        self._repositorio.guardar(solicitud)

        for evento in solicitud.pull_eventos_pendientes():
            self._event_bus.publicar(evento)

        return solicitud
