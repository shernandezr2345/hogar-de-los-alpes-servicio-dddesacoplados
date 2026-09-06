"""Pruebas unitarias del servicio de consultas CQRS (Read Model, Fase 4)."""

from __future__ import annotations

import pytest

from solicitudes_partner.aplicacion.consultas_lectura import (
    ConsultarVistaSolicitudPartner,
    ConsultasSolicitudesPartner,
    ListarSolicitudesPartnerPorPartner,
)
from solicitudes_partner.aplicacion.vistas import VistaSolicitudPartner
from solicitudes_partner.dominio.excepciones import SolicitudNoEncontradaError
from solicitudes_partner.infraestructura.repositorio_lectura_memoria import (
    RepositorioLecturaSolicitudesPartnerMemoria,
)


def test_consultar_vista_retorna_la_vista_existente() -> None:
    repo_lectura = RepositorioLecturaSolicitudesPartnerMemoria()
    repo_lectura.actualizar(
        VistaSolicitudPartner(
            solicitud_id="sol-q-1",
            partner_id="partner-q-1",
            referencia_externa="ref-q-1",
            tipo_servicio="electricidad",
            estado="RECIBIDA",
        )
    )
    consultas = ConsultasSolicitudesPartner(repositorio_lectura=repo_lectura)

    vista = consultas.consultar_vista(ConsultarVistaSolicitudPartner(solicitud_id="sol-q-1"))

    assert vista.partner_id == "partner-q-1"
    assert vista.estado == "RECIBIDA"


def test_consultar_vista_lanza_error_si_no_existe() -> None:
    consultas = ConsultasSolicitudesPartner(
        repositorio_lectura=RepositorioLecturaSolicitudesPartnerMemoria()
    )

    with pytest.raises(SolicitudNoEncontradaError):
        consultas.consultar_vista(ConsultarVistaSolicitudPartner(solicitud_id="inexistente"))


def test_listar_por_partner_retorna_solo_las_del_partner() -> None:
    repo_lectura = RepositorioLecturaSolicitudesPartnerMemoria()
    repo_lectura.actualizar(
        VistaSolicitudPartner("sol-q-2a", "partner-q-2", "ref-2a", "electricidad", "RECIBIDA")
    )
    repo_lectura.actualizar(
        VistaSolicitudPartner("sol-q-2b", "partner-q-2", "ref-2b", "plomeria", "RECHAZADA")
    )
    repo_lectura.actualizar(
        VistaSolicitudPartner("sol-q-3", "partner-q-3", "ref-3", "electricidad", "RECIBIDA")
    )
    consultas = ConsultasSolicitudesPartner(repositorio_lectura=repo_lectura)

    vistas = consultas.listar_por_partner(
        ListarSolicitudesPartnerPorPartner(partner_id="partner-q-2")
    )

    assert {vista.solicitud_id for vista in vistas} == {"sol-q-2a", "sol-q-2b"}
