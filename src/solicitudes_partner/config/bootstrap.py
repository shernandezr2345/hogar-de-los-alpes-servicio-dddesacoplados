"""Composition root mínimo de FASE 1."""

from solicitudes_partner.aplicacion.servicios import ServicioSolicitudesPartner
from solicitudes_partner.infraestructura.repositorio_memoria import (
    RepositorioSolicitudesPartnerMemoria,
)


def crear_servicio_solicitudes_partner() -> ServicioSolicitudesPartner:
    repositorio = RepositorioSolicitudesPartnerMemoria()
    return ServicioSolicitudesPartner(repositorio=repositorio)
