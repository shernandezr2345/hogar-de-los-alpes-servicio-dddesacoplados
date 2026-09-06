"""Composicion y cableado de dependencias para la API (FastAPI ``Depends``).

El backend (memoria|postgres) se decide una sola vez, en el primer request que lo necesite,
via la variable de entorno ``SOLICITUDES_PARTNER_BACKEND`` (por defecto ``postgres``). En tests,
las funciones ``obtener_servicio``/``obtener_consultas``/``obtener_relay`` se sobreescriben con
``app.dependency_overrides`` y esta composicion nunca se construye.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from solicitudes_partner.aplicacion.consultas_lectura import ConsultasSolicitudesPartner
from solicitudes_partner.aplicacion.servicios import ServicioSolicitudesPartner
from solicitudes_partner.config.bootstrap import (
    crear_servicio_consultas_y_relay_outbox_postgres,
    crear_servicio_y_consultas_solicitudes_partner,
)


@dataclass
class _ContenedorServicios:
    servicio: ServicioSolicitudesPartner
    consultas: ConsultasSolicitudesPartner
    relay: Any | None


@lru_cache(maxsize=1)
def _contenedor() -> _ContenedorServicios:
    backend = os.environ.get("SOLICITUDES_PARTNER_BACKEND", "postgres").strip().lower()

    if backend == "memoria":
        servicio, consultas = crear_servicio_y_consultas_solicitudes_partner()
        return _ContenedorServicios(servicio=servicio, consultas=consultas, relay=None)

    from solicitudes_partner.infraestructura.db_conexion import crear_conexion

    servicio, consultas, relay = crear_servicio_consultas_y_relay_outbox_postgres(crear_conexion())
    return _ContenedorServicios(servicio=servicio, consultas=consultas, relay=relay)


def obtener_servicio() -> ServicioSolicitudesPartner:
    return _contenedor().servicio


def obtener_consultas() -> ConsultasSolicitudesPartner:
    return _contenedor().consultas


def obtener_relay() -> Any | None:
    return _contenedor().relay
