"""Pruebas de integracion del Transactional Outbox (Bloque 2.5).

Requieren PostgreSQL disponible y el extra opcional 'postgres' instalado, igual que
test_repositorio_postgres.py. Se omiten automaticamente si no se cumplen esas condiciones.
"""

from __future__ import annotations

from pathlib import Path

import pytest

psycopg = pytest.importorskip("psycopg")

from solicitudes_partner.dominio.entidades import SolicitudPartner  # noqa: E402
from solicitudes_partner.dominio.objetos_valor import (  # noqa: E402
    EstadoSolicitud,
    PartnerId,
    ReferenciaExterna,
    SolicitudId,
    TipoServicio,
)
from solicitudes_partner.infraestructura.db_conexion import crear_conexion  # noqa: E402
from solicitudes_partner.infraestructura.event_bus_memoria import EventBusMemoria  # noqa: E402
from solicitudes_partner.infraestructura.relay_outbox import RelayOutbox  # noqa: E402
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
        cursor.execute("TRUNCATE TABLE outbox_eventos")

    yield cnx

    with cnx.cursor() as cursor:
        cursor.execute("TRUNCATE TABLE solicitudes_partner")
        cursor.execute("TRUNCATE TABLE outbox_eventos")

    cnx.close()


@pytest.fixture()
def repositorio(conexion):
    return RepositorioSolicitudesPartnerPostgres(conexion)


def _crear_solicitud(solicitud_id: str, partner_id: str, referencia_externa: str) -> SolicitudPartner:
    return SolicitudPartner.crear(
        solicitud_id=SolicitudId(solicitud_id),
        partner_id=PartnerId(partner_id),
        referencia_externa=ReferenciaExterna(referencia_externa),
        tipo_servicio=TipoServicio("electricidad"),
        existe_previa=False,
    )


def _contar_outbox(conexion, procesado_en_es_null: bool) -> int:
    condicion = "IS NULL" if procesado_en_es_null else "IS NOT NULL"
    with conexion.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM outbox_eventos WHERE procesado_en {condicion}")
        (total,) = cursor.fetchone()
    return total


def test_guardar_persiste_evento_en_outbox_en_la_misma_transaccion(repositorio, conexion) -> None:
    solicitud = _crear_solicitud("sol-outbox-1", "partner-outbox-1", "ref-outbox-1")

    repositorio.guardar(solicitud)

    assert _contar_outbox(conexion, procesado_en_es_null=True) == 1


def test_relay_publica_evento_pendiente_y_lo_marca_procesado(repositorio, conexion) -> None:
    solicitud = _crear_solicitud("sol-outbox-2", "partner-outbox-2", "ref-outbox-2")
    repositorio.guardar(solicitud)

    event_bus = EventBusMemoria()
    eventos_recibidos = []
    event_bus.suscribir(
        type(solicitud.ver_eventos_pendientes()[0]),
        eventos_recibidos.append,
    )

    relay = RelayOutbox(conexion=conexion, event_bus=event_bus)
    publicados = relay.publicar_pendientes()

    assert publicados == 1
    assert len(eventos_recibidos) == 1
    assert eventos_recibidos[0].solicitud_id == "sol-outbox-2"
    assert _contar_outbox(conexion, procesado_en_es_null=False) == 1


def test_relay_no_vuelve_a_publicar_evento_ya_procesado(repositorio, conexion) -> None:
    solicitud = _crear_solicitud("sol-outbox-3", "partner-outbox-3", "ref-outbox-3")
    repositorio.guardar(solicitud)

    event_bus = EventBusMemoria()
    relay = RelayOutbox(conexion=conexion, event_bus=event_bus)

    primera_corrida = relay.publicar_pendientes()
    segunda_corrida = relay.publicar_pendientes()

    assert primera_corrida == 1
    assert segunda_corrida == 0


def test_transiciones_del_agregado_tambien_se_registran_en_outbox(repositorio, conexion) -> None:
    solicitud = _crear_solicitud("sol-outbox-4", "partner-outbox-4", "ref-outbox-4")
    repositorio.guardar(solicitud)

    solicitud.pull_eventos_pendientes()
    solicitud.marcar_lista_para_atencion()
    repositorio.guardar(solicitud)

    with conexion.cursor() as cursor:
        cursor.execute(
            "SELECT tipo_evento FROM outbox_eventos WHERE solicitud_id = %s ORDER BY id",
            ("sol-outbox-4",),
        )
        tipos = [fila[0] for fila in cursor.fetchall()]

    assert tipos == ["SolicitudPartnerRegistrada", "SolicitudPartnerListaParaAtencion"]
