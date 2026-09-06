"""Eventos de dominio para el agregado SolicitudPartner."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class EventoDominio:
    """Abstracción mínima para representar hechos de negocio."""

    solicitud_id: str
    ocurrido_en: datetime = field(default_factory=lambda: datetime.now(timezone.utc), init=False)


@dataclass(frozen=True)
class SolicitudPartnerRegistrada(EventoDominio):
    partner_id: str
    referencia_externa: str


@dataclass(frozen=True)
class ReglasDePartnerEvaluadas(EventoDominio):
    fue_aprobada: bool


@dataclass(frozen=True)
class SolicitudPartnerListaParaAtencion(EventoDominio):
    pass


@dataclass(frozen=True)
class SolicitudPartnerRechazada(EventoDominio):
    pass
