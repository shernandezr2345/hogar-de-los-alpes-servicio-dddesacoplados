"""Modulo de resultado de reglas para completar el flujo de eventos."""

from __future__ import annotations

from solicitudes_partner.aplicacion.puertos_eventos import EventBus
from solicitudes_partner.dominio.eventos import EventoDominio, ReglasDePartnerEvaluadas
from solicitudes_partner.dominio.excepciones import SolicitudNoEncontradaError
from solicitudes_partner.dominio.objetos_valor import SolicitudId
from solicitudes_partner.dominio.repositorios import RepositorioSolicitudesPartner


class HandlerResultadoReglas:
    """Aplica resultado de reglas sobre el agregado y publica eventos finales."""

    def __init__(self, repositorio: RepositorioSolicitudesPartner, event_bus: EventBus):
        self._repositorio = repositorio
        self._event_bus = event_bus

    def manejar_reglas_evaluadas(self, evento: EventoDominio) -> None:
        if not isinstance(evento, ReglasDePartnerEvaluadas):
            return

        solicitud = self._repositorio.obtener_por_id(SolicitudId(evento.solicitud_id))
        if solicitud is None:
            raise SolicitudNoEncontradaError("No existe solicitud para el id del evento evaluado")

        if evento.fue_aprobada:
            solicitud.marcar_lista_para_atencion()
        else:
            solicitud.rechazar()

        self._repositorio.guardar(solicitud)

        for evento_final in solicitud.pull_eventos_pendientes():
            self._event_bus.publicar(evento_final)
