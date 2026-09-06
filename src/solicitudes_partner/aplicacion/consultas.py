"""Consulta de FASE 1 para obtener estado actual de una solicitud."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ConsultarEstadoSolicitudPartner:
    solicitud_id: str
