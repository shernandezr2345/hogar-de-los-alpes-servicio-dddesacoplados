"""Puertos de aplicacion para publicacion y suscripcion de eventos."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, TypeAlias

from solicitudes_partner.dominio.eventos import EventoDominio

HandlerEvento: TypeAlias = Callable[[EventoDominio], None]


class EventBus(ABC):
    """Abstraccion del bus de eventos usada por la capa de aplicacion."""

    @abstractmethod
    def suscribir(self, tipo_evento: type[EventoDominio], handler: HandlerEvento) -> None:
        raise NotImplementedError

    @abstractmethod
    def publicar(self, evento: EventoDominio) -> None:
        raise NotImplementedError
