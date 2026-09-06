"""Pruebas de integracion del adaptador RepositorioSolicitudesPartnerPostgres.

Estas pruebas requieren:
- el extra opcional 'postgres' instalado (pip install -e ".[postgres]");
- una instancia de PostgreSQL disponible (ver docker-compose.yml).

Si psycopg no esta instalado, el modulo completo se omite en la coleccion.
Si no hay conexion disponible a PostgreSQL, cada prueba se omite explicitamente.
"""

from __future__ import annotations

from pathlib import Path

import pytest

psycopg = pytest.importorskip("psycopg")

from solicitudes_partner.dominio.entidades import SolicitudPartner  # noqa: E402
from solicitudes_partner.dominio.excepciones import SolicitudDuplicadaError  # noqa: E402
from solicitudes_partner.dominio.objetos_valor import (  # noqa: E402
    EstadoSolicitud,
    PartnerId,
    ReferenciaExterna,
    SolicitudId,
    TipoServicio,
)
from solicitudes_partner.infraestructura.db_conexion import crear_conexion  # noqa: E402
from solicitudes_partner.infraestructura.repositorio_postgres import (  # noqa: E402
    RepositorioSolicitudesPartnerPostgres,
)

_RUTA_ESQUEMA = Path(__file__).resolve().parents[3] / "db" / "schema.sql"


@pytest.fixture()
def conexion():
    try:
        cnx = crear_conexion()
    except psycopg.OperationalError as error:
        pytest.skip(f"PostgreSQL no disponible: {error}")

    with cnx.cursor() as cursor:
        cursor.execute(_RUTA_ESQUEMA.read_text(encoding="utf-8"))
        cursor.execute("TRUNCATE TABLE solicitudes_partner")

    yield cnx

    with cnx.cursor() as cursor:
        cursor.execute("TRUNCATE TABLE solicitudes_partner")

    cnx.close()


@pytest.fixture()
def repositorio(conexion):
    return RepositorioSolicitudesPartnerPostgres(conexion)


def _crear_solicitud(
    solicitud_id: str,
    partner_id: str,
    referencia_externa: str,
    tipo_servicio: str = "electricidad",
    estado: EstadoSolicitud = EstadoSolicitud.RECIBIDA,
) -> SolicitudPartner:
    return SolicitudPartner(
        solicitud_id=SolicitudId(solicitud_id),
        partner_id=PartnerId(partner_id),
        referencia_externa=ReferenciaExterna(referencia_externa),
        tipo_servicio=TipoServicio(tipo_servicio),
        estado=estado,
    )


def test_guardar_una_solicitud_partner(repositorio) -> None:
    solicitud = _crear_solicitud("sol-int-1", "partner-int-1", "ref-int-1")

    repositorio.guardar(solicitud)

    encontrada = repositorio.obtener_por_id(SolicitudId("sol-int-1"))
    assert encontrada is not None


def test_recuperar_por_solicitud_id(repositorio) -> None:
    solicitud = _crear_solicitud("sol-int-2", "partner-int-2", "ref-int-2")
    repositorio.guardar(solicitud)

    encontrada = repositorio.obtener_por_id(SolicitudId("sol-int-2"))

    assert encontrada is not None
    assert encontrada.solicitud_id.valor == "sol-int-2"
    assert encontrada.partner_id.valor == "partner-int-2"
    assert encontrada.referencia_externa.valor == "ref-int-2"


def test_existe_por_partner_y_referencia(repositorio) -> None:
    solicitud = _crear_solicitud("sol-int-3", "partner-int-3", "ref-int-3")
    repositorio.guardar(solicitud)

    assert repositorio.existe_por_partner_y_referencia(
        PartnerId("partner-int-3"), ReferenciaExterna("ref-int-3")
    ) is True
    assert repositorio.existe_por_partner_y_referencia(
        PartnerId("partner-int-3"), ReferenciaExterna("ref-inexistente")
    ) is False


def test_restriccion_unique_partner_referencia(repositorio) -> None:
    primera = _crear_solicitud("sol-int-4a", "partner-int-4", "ref-int-4")
    repositorio.guardar(primera)

    segunda = _crear_solicitud("sol-int-4b", "partner-int-4", "ref-int-4")

    with pytest.raises(SolicitudDuplicadaError):
        repositorio.guardar(segunda)


def test_mapeo_entre_postgres_y_aggregate_value_objects(repositorio) -> None:
    solicitud = _crear_solicitud(
        "sol-int-5",
        "partner-int-5",
        "ref-int-5",
        tipo_servicio="plomeria",
        estado=EstadoSolicitud.LISTA_PARA_ATENCION,
    )
    repositorio.guardar(solicitud)

    encontrada = repositorio.obtener_por_id(SolicitudId("sol-int-5"))

    assert encontrada is not None
    assert isinstance(encontrada.solicitud_id, SolicitudId)
    assert isinstance(encontrada.partner_id, PartnerId)
    assert isinstance(encontrada.referencia_externa, ReferenciaExterna)
    assert isinstance(encontrada.tipo_servicio, TipoServicio)
    assert isinstance(encontrada.estado, EstadoSolicitud)
    assert encontrada.tipo_servicio.valor == "plomeria"
    assert encontrada.estado == EstadoSolicitud.LISTA_PARA_ATENCION
