"""Modulo de Seguimiento de Solicitudes para consumo desacoplado de eventos."""

from __future__ import annotations

from solicitudes_partner.dominio.eventos import EventoDominio


class SeguimientoSolicitudes:
    """Consumidor in-memory de eventos para trazabilidad interna."""

    def __init__(self) -> None:
        self.eventos_recibidos: list[EventoDominio] = []

    def manejar_evento(self, evento: EventoDominio) -> None:
        self.eventos_recibidos.append(evento)
