"""Adaptador PostgreSQL del puerto RepositorioSolicitudesPartner."""

from __future__ import annotations

import dataclasses

import psycopg
from psycopg.types.json import Jsonb

from solicitudes_partner.dominio.entidades import SolicitudPartner
from solicitudes_partner.dominio.eventos import EventoDominio
from solicitudes_partner.dominio.excepciones import SolicitudDuplicadaError
from solicitudes_partner.dominio.objetos_valor import (
    EstadoSolicitud,
    PartnerId,
    ReferenciaExterna,
    SolicitudId,
    TipoServicio,
)
from solicitudes_partner.dominio.repositorios import RepositorioSolicitudesPartner


def _evento_a_payload(evento: EventoDominio) -> dict:
    datos = dataclasses.asdict(evento)
    datos["ocurrido_en"] = evento.ocurrido_en.isoformat()
    return datos


class RepositorioSolicitudesPartnerPostgres(RepositorioSolicitudesPartner):
    """Traduce entre el Aggregate SolicitudPartner y filas de PostgreSQL."""

    def __init__(self, conexion: psycopg.Connection):
        self._conexion = conexion

    def guardar(self, solicitud: SolicitudPartner) -> None:
        # Eventos aun pendientes en el agregado (lectura, no los consume): se
        # persisten en el outbox en la misma transaccion que el upsert, para
        # publicacion confiable posterior via RelayOutbox. La app sigue
        # pudiendo hacer pull_eventos_pendientes() despues para su flujo interno.
        eventos = solicitud.ver_eventos_pendientes()
        try:
            with self._conexion.transaction(), self._conexion.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO solicitudes_partner
                        (solicitud_id, partner_id, referencia_externa, tipo_servicio, estado)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (solicitud_id) DO UPDATE SET
                        partner_id = EXCLUDED.partner_id,
                        referencia_externa = EXCLUDED.referencia_externa,
                        tipo_servicio = EXCLUDED.tipo_servicio,
                        estado = EXCLUDED.estado
                    """,
                    (
                        solicitud.solicitud_id.valor,
                        solicitud.partner_id.valor,
                        solicitud.referencia_externa.valor,
                        solicitud.tipo_servicio.valor,
                        solicitud.estado.value,
                    ),
                )

                for evento in eventos:
                    cursor.execute(
                        """
                        INSERT INTO outbox_eventos (solicitud_id, tipo_evento, payload)
                        VALUES (%s, %s, %s)
                        """,
                        (
                            evento.solicitud_id,
                            type(evento).__name__,
                            Jsonb(_evento_a_payload(evento)),
                        ),
                    )
        except psycopg.errors.UniqueViolation as error:
            raise SolicitudDuplicadaError(
                "Ya existe una solicitud para el partner y referencia externa"
            ) from error

    def obtener_por_id(self, solicitud_id: SolicitudId) -> SolicitudPartner | None:
        with self._conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT solicitud_id, partner_id, referencia_externa, tipo_servicio, estado
                FROM solicitudes_partner
                WHERE solicitud_id = %s
                """,
                (solicitud_id.valor,),
            )
            fila = cursor.fetchone()

        if fila is None:
            return None

        return self._fila_a_solicitud(fila)

    def existe_por_partner_y_referencia(
        self,
        partner_id: PartnerId,
        referencia_externa: ReferenciaExterna,
    ) -> bool:
        with self._conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM solicitudes_partner
                WHERE partner_id = %s AND referencia_externa = %s
                LIMIT 1
                """,
                (partner_id.valor, referencia_externa.valor),
            )
            return cursor.fetchone() is not None

    @staticmethod
    def _fila_a_solicitud(fila: tuple) -> SolicitudPartner:
        solicitud_id, partner_id, referencia_externa, tipo_servicio, estado = fila
        return SolicitudPartner(
            solicitud_id=SolicitudId(solicitud_id),
            partner_id=PartnerId(partner_id),
            referencia_externa=ReferenciaExterna(referencia_externa),
            tipo_servicio=TipoServicio(tipo_servicio),
            estado=EstadoSolicitud(estado),
        )
