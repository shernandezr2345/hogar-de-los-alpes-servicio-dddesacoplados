"""Servicios de aplicación para orquestar casos de uso sin lógica técnica."""

from __future__ import annotations

from solicitudes_partner.dominio.entidades import SolicitudPartner
from solicitudes_partner.dominio.excepciones import SolicitudNoEncontradaError
from solicitudes_partner.dominio.objetos_valor import (
    EstadoSolicitud,
    PartnerId,
    ReferenciaExterna,
    SolicitudId,
    TipoServicio,
)
from solicitudes_partner.dominio.repositorios import RepositorioSolicitudesPartner

from .comandos import RegistrarSolicitudPartner
from .consultas import ConsultarEstadoSolicitudPartner


class ServicioSolicitudesPartner:
    """Coordina comando y consulta usando puertos del dominio."""

    def __init__(self, repositorio: RepositorioSolicitudesPartner):
        self._repositorio = repositorio

    def registrar_solicitud(self, comando: RegistrarSolicitudPartner) -> SolicitudPartner:
        solicitud_id = SolicitudId(comando.solicitud_id)
        partner_id = PartnerId(comando.partner_id)
        referencia = ReferenciaExterna(comando.referencia_externa)
        tipo_servicio = TipoServicio(comando.tipo_servicio)

        existe_previa = self._repositorio.existe_por_partner_y_referencia(partner_id, referencia)

        solicitud = SolicitudPartner.crear(
            solicitud_id=solicitud_id,
            partner_id=partner_id,
            referencia_externa=referencia,
            tipo_servicio=tipo_servicio,
            existe_previa=existe_previa,
        )

        self._repositorio.guardar(solicitud)
        return solicitud

    def consultar_estado(self, consulta: ConsultarEstadoSolicitudPartner) -> EstadoSolicitud:
        solicitud = self._repositorio.obtener_por_id(SolicitudId(consulta.solicitud_id))
        if solicitud is None:
            raise SolicitudNoEncontradaError("No existe solicitud para el id consultado")
        return solicitud.estado
