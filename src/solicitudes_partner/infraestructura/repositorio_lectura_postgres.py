"""Adaptador PostgreSQL del puerto de lectura (Read Model) - Fase 4 CQRS."""

from __future__ import annotations

import psycopg

from solicitudes_partner.aplicacion.puertos_lectura import RepositorioLecturaSolicitudesPartner
from solicitudes_partner.aplicacion.vistas import VistaSolicitudPartner


class RepositorioLecturaSolicitudesPartnerPostgres(RepositorioLecturaSolicitudesPartner):
    """Consulta y actualiza la proyeccion solicitudes_partner_vista."""

    def __init__(self, conexion: psycopg.Connection):
        self._conexion = conexion

    def obtener_por_id(self, solicitud_id: str) -> VistaSolicitudPartner | None:
        with self._conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT solicitud_id, partner_id, referencia_externa, tipo_servicio, estado
                FROM solicitudes_partner_vista
                WHERE solicitud_id = %s
                """,
                (solicitud_id,),
            )
            fila = cursor.fetchone()

        return self._fila_a_vista(fila) if fila is not None else None

    def listar_por_partner(self, partner_id: str) -> list[VistaSolicitudPartner]:
        with self._conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT solicitud_id, partner_id, referencia_externa, tipo_servicio, estado
                FROM solicitudes_partner_vista
                WHERE partner_id = %s
                ORDER BY solicitud_id
                """,
                (partner_id,),
            )
            filas = cursor.fetchall()

        return [self._fila_a_vista(fila) for fila in filas]

    def actualizar(self, vista: VistaSolicitudPartner) -> None:
        with self._conexion.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO solicitudes_partner_vista
                    (solicitud_id, partner_id, referencia_externa, tipo_servicio, estado)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (solicitud_id) DO UPDATE SET
                    partner_id = EXCLUDED.partner_id,
                    referencia_externa = EXCLUDED.referencia_externa,
                    tipo_servicio = EXCLUDED.tipo_servicio,
                    estado = EXCLUDED.estado,
                    actualizado_en = now()
                """,
                (
                    vista.solicitud_id,
                    vista.partner_id,
                    vista.referencia_externa,
                    vista.tipo_servicio,
                    vista.estado,
                ),
            )

    @staticmethod
    def _fila_a_vista(fila: tuple) -> VistaSolicitudPartner:
        solicitud_id, partner_id, referencia_externa, tipo_servicio, estado = fila
        return VistaSolicitudPartner(
            solicitud_id=solicitud_id,
            partner_id=partner_id,
            referencia_externa=referencia_externa,
            tipo_servicio=tipo_servicio,
            estado=estado,
        )
