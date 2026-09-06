"""Comando de FASE 1 para registrar solicitudes de partner."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RegistrarSolicitudPartner:
    solicitud_id: str
    partner_id: str
    referencia_externa: str
    tipo_servicio: str
