"""Modulo de Reglas de Partner para reaccionar a eventos de captura."""

from __future__ import annotations

from solicitudes_partner.aplicacion.puertos_eventos import EventBus
from solicitudes_partner.dominio.eventos import (
    EventoDominio,
    ReglasDePartnerEvaluadas,
    SolicitudPartnerRegistrada,
)


class EvaluadorReglasPartner:
    """Evaluador minimo de reglas para esta fase in-process."""

    def evaluar(self, evento: SolicitudPartnerRegistrada) -> bool:
        return bool(evento.referencia_externa.strip())


class HandlerReglasPartner:
    """Handler que transforma SolicitudPartnerRegistrada en ReglasDePartnerEvaluadas."""

    def __init__(self, event_bus: EventBus, evaluador: EvaluadorReglasPartner | None = None):
        self._event_bus = event_bus
        self._evaluador = evaluador or EvaluadorReglasPartner()

    def manejar_solicitud_registrada(self, evento: EventoDominio) -> None:
        if not isinstance(evento, SolicitudPartnerRegistrada):
            return

        fue_aprobada = self._evaluador.evaluar(evento)
        self._event_bus.publicar(
            ReglasDePartnerEvaluadas(
                solicitud_id=evento.solicitud_id,
                fue_aprobada=fue_aprobada,
            )
        )
