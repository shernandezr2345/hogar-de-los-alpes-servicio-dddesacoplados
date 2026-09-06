"""Pruebas de integracion del Read Model contra PostgreSQL (Fase 4).

Requieren PostgreSQL disponible y el extra opcional 'postgres' instalado, igual que los demas
modulos de tests/integration. Se omiten automaticamente si no se cumplen esas condiciones.
"""

from __future__ import annotations

from pathlib import Path

import pytest

psycopg = pytest.importorskip("psycopg")

from solicitudes_partner.aplicacion.consultas_lectura import (  # noqa: E402
    ConsultarVistaSolicitudPartner,
    ConsultasSolicitudesPartner,
    ListarSolicitudesPartnerPorPartner,
)
from solicitudes_partner.aplicacion.modulos.proyeccion_solicitudes import (  # noqa: E402
    ProyeccionSolicitudesPartner,
)
from solicitudes_partner.dominio.entidades import SolicitudPartner  # noqa: E402
from solicitudes_partner.dominio.objetos_valor import (  # noqa: E402
    PartnerId,
    ReferenciaExterna,
    SolicitudId,
    TipoServicio,
)
from solicitudes_partner.infraestructura.db_conexion import crear_conexion  # noqa: E402
from solicitudes_partner.infraestructura.repositorio_lectura_postgres import (  # noqa: E402
    RepositorioLecturaSolicitudesPartnerPostgres,
)
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
        cursor.execute("TRUNCATE TABLE solicitudes_partner_vista")

    yield cnx

    with cnx.cursor() as cursor:
        cursor.execute("TRUNCATE TABLE solicitudes_partner")
        cursor.execute("TRUNCATE TABLE outbox_eventos")
        cursor.execute("TRUNCATE TABLE solicitudes_partner_vista")

    cnx.close()


def _crear_y_guardar(conexion, solicitud_id: str, partner_id: str, referencia_externa: str):
    repo_escritura = RepositorioSolicitudesPartnerPostgres(conexion)
    solicitud = SolicitudPartner.crear(
        solicitud_id=SolicitudId(solicitud_id),
        partner_id=PartnerId(partner_id),
        referencia_externa=ReferenciaExterna(referencia_externa),
        tipo_servicio=TipoServicio("electricidad"),
        existe_previa=False,
    )
    repo_escritura.guardar(solicitud)
    return repo_escritura, solicitud


def test_proyeccion_puebla_la_vista_postgres(conexion) -> None:
    repo_escritura, solicitud = _crear_y_guardar(
        conexion, "sol-vista-pg-1", "partner-vista-pg-1", "ref-vista-pg-1"
    )
    repo_lectura = RepositorioLecturaSolicitudesPartnerPostgres(conexion)
    proyeccion = ProyeccionSolicitudesPartner(
        repositorio_escritura=repo_escritura, repositorio_lectura=repo_lectura
    )

    for evento in solicitud.pull_eventos_pendientes():
        proyeccion.manejar_evento(evento)

    vista = repo_lectura.obtener_por_id("sol-vista-pg-1")
    assert vista is not None
    assert vista.partner_id == "partner-vista-pg-1"
    assert vista.estado == "RECIBIDA"


def test_consultas_solicitudes_partner_lee_desde_la_vista_postgres(conexion) -> None:
    repo_escritura, solicitud = _crear_y_guardar(
        conexion, "sol-vista-pg-2", "partner-vista-pg-2", "ref-vista-pg-2"
    )
    repo_lectura = RepositorioLecturaSolicitudesPartnerPostgres(conexion)
    proyeccion = ProyeccionSolicitudesPartner(
        repositorio_escritura=repo_escritura, repositorio_lectura=repo_lectura
    )
    for evento in solicitud.pull_eventos_pendientes():
        proyeccion.manejar_evento(evento)

    consultas = ConsultasSolicitudesPartner(repositorio_lectura=repo_lectura)
    vista = consultas.consultar_vista(ConsultarVistaSolicitudPartner(solicitud_id="sol-vista-pg-2"))
    listado = consultas.listar_por_partner(
        ListarSolicitudesPartnerPorPartner(partner_id="partner-vista-pg-2")
    )

    assert vista.solicitud_id == "sol-vista-pg-2"
    assert len(listado) == 1
