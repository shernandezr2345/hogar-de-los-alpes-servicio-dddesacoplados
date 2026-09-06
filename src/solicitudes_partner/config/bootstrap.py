"""Composition root para Fase 1 + Bloque 2.2."""

from solicitudes_partner.aplicacion.modulos.reglas_partner import HandlerReglasPartner
from solicitudes_partner.aplicacion.modulos.seguimiento import SeguimientoSolicitudes
from solicitudes_partner.aplicacion.servicios import ServicioSolicitudesPartner
from solicitudes_partner.dominio.eventos import ReglasDePartnerEvaluadas, SolicitudPartnerRegistrada
from solicitudes_partner.infraestructura.event_bus_memoria import EventBusMemoria
from solicitudes_partner.infraestructura.repositorio_memoria import (
    RepositorioSolicitudesPartnerMemoria,
)


def crear_servicio_solicitudes_partner() -> ServicioSolicitudesPartner:
    repositorio = RepositorioSolicitudesPartnerMemoria()
    event_bus = EventBusMemoria()

    handler_reglas = HandlerReglasPartner(event_bus=event_bus)
    seguimiento = SeguimientoSolicitudes()

    event_bus.suscribir(SolicitudPartnerRegistrada, handler_reglas.manejar_solicitud_registrada)
    event_bus.suscribir(SolicitudPartnerRegistrada, seguimiento.manejar_evento)
    event_bus.suscribir(ReglasDePartnerEvaluadas, seguimiento.manejar_evento)

    return ServicioSolicitudesPartner(repositorio=repositorio, event_bus=event_bus)
