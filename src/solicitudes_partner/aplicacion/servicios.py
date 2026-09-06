"""Servicios de aplicación para orquestar casos de uso sin lógica técnica."""

from __future__ import annotations

from solicitudes_partner.aplicacion.modulos.captura import CapturaSolicitudes
from solicitudes_partner.aplicacion.puertos_eventos import EventBus
from solicitudes_partner.dominio.entidades import SolicitudPartner
from solicitudes_partner.dominio.excepciones import SolicitudNoEncontradaError
from solicitudes_partner.dominio.objetos_valor import (
    EstadoSolicitud,
    SolicitudId,
)
from solicitudes_partner.dominio.repositorios import RepositorioSolicitudesPartner

from .comandos import RegistrarSolicitudPartner
from .consultas import ConsultarEstadoSolicitudPartner


class ServicioSolicitudesPartner:
    """Coordina comando y consulta usando puertos del dominio."""

    def __init__(self, repositorio: RepositorioSolicitudesPartner, event_bus: EventBus):
        self._repositorio = repositorio
        self._captura = CapturaSolicitudes(repositorio=repositorio, event_bus=event_bus)

    def registrar_solicitud(self, comando: RegistrarSolicitudPartner) -> SolicitudPartner:
        return self._captura.registrar_solicitud(comando)

    def consultar_estado(self, consulta: ConsultarEstadoSolicitudPartner) -> EstadoSolicitud:
        solicitud = self._repositorio.obtener_por_id(SolicitudId(consulta.solicitud_id))
        if solicitud is None:
            raise SolicitudNoEncontradaError("No existe solicitud para el id consultado")
        return solicitud.estado
