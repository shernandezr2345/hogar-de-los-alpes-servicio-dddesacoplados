"""Implementacion in-memory/in-process del Event Bus."""

from __future__ import annotations

from collections import defaultdict

from solicitudes_partner.aplicacion.puertos_eventos import EventBus, HandlerEvento
from solicitudes_partner.dominio.eventos import EventoDominio


class EventBusMemoria(EventBus):
    """Despacha eventos a todos los handlers suscritos por tipo de evento."""

    def __init__(self) -> None:
        self._handlers: dict[type[EventoDominio], list[HandlerEvento]] = defaultdict(list)

    def suscribir(self, tipo_evento: type[EventoDominio], handler: HandlerEvento) -> None:
        self._handlers[tipo_evento].append(handler)

    def publicar(self, evento: EventoDominio) -> None:
        for handler in self._handlers.get(type(evento), []):
            handler(evento)
