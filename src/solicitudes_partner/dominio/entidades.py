"""Aggregate Root SolicitudPartner y sus invariantes."""

from __future__ import annotations

from dataclasses import dataclass, field

from .eventos import (
    EventoDominio,
    SolicitudPartnerListaParaAtencion,
    SolicitudPartnerRegistrada,
    SolicitudPartnerRechazada,
)
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
    _eventos_pendientes: list[EventoDominio] = field(default_factory=list, init=False, repr=False)

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

        solicitud = cls(
            solicitud_id=solicitud_id,
            partner_id=partner_id,
            referencia_externa=referencia_externa,
            tipo_servicio=tipo_servicio,
            estado=EstadoSolicitud.RECIBIDA,
        )

        solicitud._registrar_evento(
            SolicitudPartnerRegistrada(
                solicitud_id=solicitud.solicitud_id.valor,
                partner_id=solicitud.partner_id.valor,
                referencia_externa=solicitud.referencia_externa.valor,
            )
        )

        return solicitud

    def marcar_lista_para_atencion(self) -> None:
        self._cambiar_estado(EstadoSolicitud.LISTA_PARA_ATENCION)
        self._registrar_evento(
            SolicitudPartnerListaParaAtencion(
                solicitud_id=self.solicitud_id.valor,
            )
        )

    def rechazar(self) -> None:
        self._cambiar_estado(EstadoSolicitud.RECHAZADA)
        self._registrar_evento(
            SolicitudPartnerRechazada(
                solicitud_id=self.solicitud_id.valor,
            )
        )

    def ver_eventos_pendientes(self) -> tuple[EventoDominio, ...]:
        return tuple(self._eventos_pendientes)

    def pull_eventos_pendientes(self) -> list[EventoDominio]:
        eventos = list(self._eventos_pendientes)
        self._eventos_pendientes.clear()
        return eventos

    def _registrar_evento(self, evento: EventoDominio) -> None:
        self._eventos_pendientes.append(evento)

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
