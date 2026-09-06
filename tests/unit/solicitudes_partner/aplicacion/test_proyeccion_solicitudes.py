"""Pruebas unitarias del proyector del Read Model (Fase 4 CQRS)."""

from __future__ import annotations

from solicitudes_partner.aplicacion.modulos.proyeccion_solicitudes import (
    ProyeccionSolicitudesPartner,
)
from solicitudes_partner.dominio.entidades import SolicitudPartner
from solicitudes_partner.dominio.objetos_valor import (
    PartnerId,
    ReferenciaExterna,
    SolicitudId,
    TipoServicio,
)
from solicitudes_partner.infraestructura.repositorio_lectura_memoria import (
    RepositorioLecturaSolicitudesPartnerMemoria,
)
from solicitudes_partner.infraestructura.repositorio_memoria import (
    RepositorioSolicitudesPartnerMemoria,
)


def _armar_proyeccion():
    repo_escritura = RepositorioSolicitudesPartnerMemoria()
    repo_lectura = RepositorioLecturaSolicitudesPartnerMemoria()
    proyeccion = ProyeccionSolicitudesPartner(
        repositorio_escritura=repo_escritura, repositorio_lectura=repo_lectura
    )
    return proyeccion, repo_escritura, repo_lectura


def test_proyeccion_actualiza_vista_al_registrar() -> None:
    proyeccion, repo_escritura, repo_lectura = _armar_proyeccion()

    solicitud = SolicitudPartner.crear(
        solicitud_id=SolicitudId("sol-vista-1"),
        partner_id=PartnerId("partner-vista-1"),
        referencia_externa=ReferenciaExterna("ref-vista-1"),
        tipo_servicio=TipoServicio("electricidad"),
        existe_previa=False,
    )
    repo_escritura.guardar(solicitud)

    for evento in solicitud.pull_eventos_pendientes():
        proyeccion.manejar_evento(evento)

    vista = repo_lectura.obtener_por_id("sol-vista-1")
    assert vista is not None
    assert vista.partner_id == "partner-vista-1"
    assert vista.referencia_externa == "ref-vista-1"
    assert vista.tipo_servicio == "electricidad"
    assert vista.estado == "RECIBIDA"


def test_proyeccion_actualiza_vista_al_cambiar_estado() -> None:
    proyeccion, repo_escritura, repo_lectura = _armar_proyeccion()

    solicitud = SolicitudPartner.crear(
        solicitud_id=SolicitudId("sol-vista-2"),
        partner_id=PartnerId("partner-vista-2"),
        referencia_externa=ReferenciaExterna("ref-vista-2"),
        tipo_servicio=TipoServicio("plomeria"),
        existe_previa=False,
    )
    repo_escritura.guardar(solicitud)
    for evento in solicitud.pull_eventos_pendientes():
        proyeccion.manejar_evento(evento)

    solicitud.marcar_lista_para_atencion()
    repo_escritura.guardar(solicitud)
    for evento in solicitud.pull_eventos_pendientes():
        proyeccion.manejar_evento(evento)

    vista = repo_lectura.obtener_por_id("sol-vista-2")
    assert vista is not None
    assert vista.estado == "LISTA_PARA_ATENCION"


def test_proyeccion_ignora_eventos_no_relevantes() -> None:
    proyeccion, _repo_escritura, repo_lectura = _armar_proyeccion()

    from solicitudes_partner.dominio.eventos import ReglasDePartnerEvaluadas

    proyeccion.manejar_evento(ReglasDePartnerEvaluadas(solicitud_id="sol-x", fue_aprobada=True))

    assert repo_lectura.obtener_por_id("sol-x") is None
