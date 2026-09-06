"""Prueba de integracion (in-process) del flujo completo con Read Model - Fase 4."""

from __future__ import annotations

from solicitudes_partner.aplicacion.comandos import RegistrarSolicitudPartner
from solicitudes_partner.aplicacion.consultas_lectura import ConsultarVistaSolicitudPartner
from solicitudes_partner.config.bootstrap import crear_servicio_y_consultas_solicitudes_partner


def test_flujo_completo_actualiza_el_read_model() -> None:
    servicio, consultas = crear_servicio_y_consultas_solicitudes_partner()

    servicio.registrar_solicitud(
        RegistrarSolicitudPartner(
            solicitud_id="sol-cqrs-1",
            partner_id="partner-cqrs-1",
            referencia_externa="REF-CQRS-1",
            tipo_servicio="electricidad",
        )
    )

    vista = consultas.consultar_vista(ConsultarVistaSolicitudPartner(solicitud_id="sol-cqrs-1"))

    assert vista.estado == "LISTA_PARA_ATENCION"
    assert vista.partner_id == "partner-cqrs-1"
    assert vista.tipo_servicio == "electricidad"


def test_flujo_rechazado_actualiza_el_read_model() -> None:
    servicio, consultas = crear_servicio_y_consultas_solicitudes_partner()

    servicio.registrar_solicitud(
        RegistrarSolicitudPartner(
            solicitud_id="sol-cqrs-2",
            partner_id="partner-cqrs-2",
            referencia_externa="RECHAZAR-CQRS-2",
            tipo_servicio="plomeria",
        )
    )

    vista = consultas.consultar_vista(ConsultarVistaSolicitudPartner(solicitud_id="sol-cqrs-2"))

    assert vista.estado == "RECHAZADA"
