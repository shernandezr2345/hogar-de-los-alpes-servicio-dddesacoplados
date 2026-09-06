"""Prueba de integracion de la API contra la composicion PostgreSQL completa (Fase 5).

Requiere PostgreSQL disponible y el extra opcional 'postgres' instalado, igual que los demas
modulos de tests/integration. Se omite automaticamente si no se cumplen esas condiciones.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

psycopg = pytest.importorskip("psycopg")

from fastapi.testclient import TestClient  # noqa: E402

from solicitudes_partner.api.app import crear_app  # noqa: E402
from solicitudes_partner.api.dependencias import (  # noqa: E402
    obtener_consultas,
    obtener_relay,
    obtener_servicio,
)
from solicitudes_partner.config.bootstrap import (  # noqa: E402
    crear_servicio_consultas_y_relay_outbox_postgres,
)
from solicitudes_partner.infraestructura.db_conexion import crear_conexion  # noqa: E402

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


@pytest.fixture()
def cliente(conexion) -> TestClient:
    servicio, consultas, relay = crear_servicio_consultas_y_relay_outbox_postgres(conexion)
    app = crear_app()
    app.dependency_overrides[obtener_servicio] = lambda: servicio
    app.dependency_overrides[obtener_consultas] = lambda: consultas
    app.dependency_overrides[obtener_relay] = lambda: relay
    return TestClient(app)


def test_registrar_y_consultar_contra_postgres(cliente: TestClient) -> None:
    respuesta = cliente.post(
        "/solicitudes-partner",
        json={
            "solicitud_id": "sol-api-1",
            "partner_id": "partner-api-1",
            "referencia_externa": "REF-API-1",
            "tipo_servicio": "electricidad",
        },
    )
    assert respuesta.status_code == 201

    respuesta_get = cliente.get("/solicitudes-partner/sol-api-1")
    assert respuesta_get.status_code == 200
    assert respuesta_get.json()["partner_id"] == "partner-api-1"


def test_endpoint_admin_outbox_publica_pendientes(cliente: TestClient) -> None:
    cliente.post(
        "/solicitudes-partner",
        json={
            "solicitud_id": "sol-api-2",
            "partner_id": "partner-api-2",
            "referencia_externa": "REF-API-2",
            "tipo_servicio": "electricidad",
        },
    )

    respuesta = cliente.post("/admin/outbox/publicar-pendientes")

    assert respuesta.status_code == 200
    assert respuesta.json()["publicados"] >= 1
