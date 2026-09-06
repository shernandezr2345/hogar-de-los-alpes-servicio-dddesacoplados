"""Pruebas unitarias de la API REST (Fase 5), contra la composicion en memoria."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from solicitudes_partner.api.app import crear_app
from solicitudes_partner.api.dependencias import obtener_consultas, obtener_relay, obtener_servicio
from solicitudes_partner.config.bootstrap import crear_servicio_y_consultas_solicitudes_partner

_PAYLOAD_BASE = {
    "solicitud_id": "sol-1",
    "partner_id": "partner-1",
    "referencia_externa": "REF-1",
    "tipo_servicio": "electricidad",
}


@pytest.fixture()
def cliente() -> TestClient:
    servicio, consultas = crear_servicio_y_consultas_solicitudes_partner()
    app = crear_app()
    app.dependency_overrides[obtener_servicio] = lambda: servicio
    app.dependency_overrides[obtener_consultas] = lambda: consultas
    app.dependency_overrides[obtener_relay] = lambda: None
    return TestClient(app)


def test_registrar_solicitud_devuelve_201_y_estado_final(cliente: TestClient) -> None:
    respuesta = cliente.post("/solicitudes-partner", json=_PAYLOAD_BASE)

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["solicitud_id"] == "sol-1"
    assert cuerpo["estado"] in {"LISTA_PARA_ATENCION", "RECHAZADA"}


def test_obtener_solicitud_por_id_devuelve_vista_completa(cliente: TestClient) -> None:
    cliente.post("/solicitudes-partner", json=_PAYLOAD_BASE)

    respuesta = cliente.get("/solicitudes-partner/sol-1")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["partner_id"] == "partner-1"
    assert cuerpo["referencia_externa"] == "REF-1"
    assert cuerpo["tipo_servicio"] == "electricidad"


def test_listar_por_partner_filtra_correctamente(cliente: TestClient) -> None:
    cliente.post("/solicitudes-partner", json=_PAYLOAD_BASE)
    cliente.post(
        "/solicitudes-partner",
        json={**_PAYLOAD_BASE, "solicitud_id": "sol-2", "partner_id": "partner-2"},
    )

    respuesta = cliente.get("/solicitudes-partner", params={"partner_id": "partner-1"})

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert len(cuerpo) == 1
    assert cuerpo[0]["solicitud_id"] == "sol-1"


def test_solicitud_duplicada_devuelve_409(cliente: TestClient) -> None:
    cliente.post("/solicitudes-partner", json=_PAYLOAD_BASE)

    respuesta = cliente.post("/solicitudes-partner", json=_PAYLOAD_BASE)

    assert respuesta.status_code == 409


def test_solicitud_no_encontrada_devuelve_404(cliente: TestClient) -> None:
    respuesta = cliente.get("/solicitudes-partner/no-existe")

    assert respuesta.status_code == 404


def test_value_object_invalido_devuelve_400(cliente: TestClient) -> None:
    respuesta = cliente.post("/solicitudes-partner", json={**_PAYLOAD_BASE, "partner_id": "  "})

    assert respuesta.status_code == 400


def test_endpoint_admin_outbox_devuelve_501_sin_relay(cliente: TestClient) -> None:
    respuesta = cliente.post("/admin/outbox/publicar-pendientes")

    assert respuesta.status_code == 501
