"""DTO de lectura (Read Model) para SolicitudPartner - Fase 4 CQRS."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VistaSolicitudPartner:
    """Proyeccion de solo lectura de una SolicitudPartner."""

    solicitud_id: str
    partner_id: str
    referencia_externa: str
    tipo_servicio: str
    estado: str
