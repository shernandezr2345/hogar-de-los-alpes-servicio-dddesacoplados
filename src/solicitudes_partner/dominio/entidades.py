"""Aggregate Root SolicitudPartner y sus invariantes."""

from __future__ import annotations

from dataclasses import dataclass

from .excepciones import SolicitudDuplicadaError, TransicionEstadoInvalidaError
from .objetos_valor import EstadoSolicitud, PartnerId, ReferenciaExterna, SolicitudId, TipoServicio


@dataclass
class SolicitudPartner:
    """Aggregate Root de FASE 1 para Entrada de Solicitudes de Partner."""

    solicitud_id: SolicitudId
    partner_id: PartnerId
    referencia_externa: ReferenciaExterna
    tipo_servicio: TipoServicio
    estado: EstadoSolicitud

    @classmethod
    def crear(
        cls,
        solicitud_id: SolicitudId,
        partner_id: PartnerId,
        referencia_externa: ReferenciaExterna,
        tipo_servicio: TipoServicio,
        existe_previa: bool,
    ) -> "SolicitudPartner":
        if existe_previa:
            raise SolicitudDuplicadaError(
                "Ya existe una solicitud para el partner y referencia externa"
            )

        return cls(
            solicitud_id=solicitud_id,
            partner_id=partner_id,
            referencia_externa=referencia_externa,
            tipo_servicio=tipo_servicio,
            estado=EstadoSolicitud.RECIBIDA,
        )

    def marcar_lista_para_atencion(self) -> None:
        self._cambiar_estado(EstadoSolicitud.LISTA_PARA_ATENCION)

    def rechazar(self) -> None:
        self._cambiar_estado(EstadoSolicitud.RECHAZADA)

    def _cambiar_estado(self, nuevo_estado: EstadoSolicitud) -> None:
        transiciones_validas = {
            EstadoSolicitud.RECIBIDA: {
                EstadoSolicitud.LISTA_PARA_ATENCION,
                EstadoSolicitud.RECHAZADA,
            },
            EstadoSolicitud.LISTA_PARA_ATENCION: set(),
            EstadoSolicitud.RECHAZADA: set(),
        }

        if nuevo_estado not in transiciones_validas[self.estado]:
            raise TransicionEstadoInvalidaError(
                f"No se permite transición {self.estado.value} -> {nuevo_estado.value}"
            )

        self.estado = nuevo_estado
