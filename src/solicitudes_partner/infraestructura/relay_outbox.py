"""Relay que drena la tabla outbox_eventos y publica en el EventBus."""

from __future__ import annotations

import psycopg

from solicitudes_partner.aplicacion.puertos_eventos import EventBus
from solicitudes_partner.dominio.eventos import (
    EventoDominio,
    SolicitudPartnerListaParaAtencion,
    SolicitudPartnerRechazada,
    SolicitudPartnerRegistrada,
)

_TIPOS_EVENTO: dict[str, type[EventoDominio]] = {
    "SolicitudPartnerRegistrada": SolicitudPartnerRegistrada,
    "SolicitudPartnerListaParaAtencion": SolicitudPartnerListaParaAtencion,
    "SolicitudPartnerRechazada": SolicitudPartnerRechazada,
}


def _reconstruir_evento(tipo_evento: str, payload: dict) -> EventoDominio:
    clase = _TIPOS_EVENTO.get(tipo_evento)
    if clase is None:
        raise ValueError(f"Tipo de evento desconocido en outbox: {tipo_evento}")

    campos = {clave: valor for clave, valor in payload.items() if clave != "ocurrido_en"}
    return clase(**campos)


class RelayOutbox:
    """Publica de forma confiable los eventos pendientes registrados en el outbox."""

    def __init__(self, conexion: psycopg.Connection, event_bus: EventBus):
        self._conexion = conexion
        self._event_bus = event_bus

    def publicar_pendientes(self) -> int:
        """Publica cada evento pendiente y lo marca como procesado. Retorna cuantos publico."""
        with self._conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, tipo_evento, payload
                FROM outbox_eventos
                WHERE procesado_en IS NULL
                ORDER BY id
                """
            )
            pendientes = cursor.fetchall()

        publicados = 0
        for id_evento, tipo_evento, payload in pendientes:
            evento = _reconstruir_evento(tipo_evento, payload)
            self._event_bus.publicar(evento)

            with self._conexion.cursor() as cursor:
                cursor.execute(
                    "UPDATE outbox_eventos SET procesado_en = now() WHERE id = %s",
                    (id_evento,),
                )
            publicados += 1

        return publicados
