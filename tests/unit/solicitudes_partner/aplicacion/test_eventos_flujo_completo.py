import inspect
from collections import Counter

from solicitudes_partner.aplicacion.comandos import RegistrarSolicitudPartner
from solicitudes_partner.aplicacion.modulos.reglas_partner import HandlerReglasPartner
from solicitudes_partner.aplicacion.modulos.resultado_reglas import HandlerResultadoReglas
from solicitudes_partner.aplicacion.modulos.seguimiento import SeguimientoSolicitudes
from solicitudes_partner.aplicacion.servicios import ServicioSolicitudesPartner
from solicitudes_partner.dominio.eventos import (
    ReglasDePartnerEvaluadas,
    SolicitudPartnerListaParaAtencion,
    SolicitudPartnerRechazada,
    SolicitudPartnerRegistrada,
)
from solicitudes_partner.dominio.objetos_valor import EstadoSolicitud, SolicitudId
from solicitudes_partner.infraestructura.event_bus_memoria import EventBusMemoria
from solicitudes_partner.infraestructura.repositorio_memoria import RepositorioSolicitudesPartnerMemoria


def _armar_escenario():
    repo = RepositorioSolicitudesPartnerMemoria()
    bus = EventBusMemoria()

    reglas = HandlerReglasPartner(event_bus=bus)
    resultado = HandlerResultadoReglas(repositorio=repo, event_bus=bus)
    seguimiento = SeguimientoSolicitudes()

    bus.suscribir(SolicitudPartnerRegistrada, reglas.manejar_solicitud_registrada)
    bus.suscribir(ReglasDePartnerEvaluadas, resultado.manejar_reglas_evaluadas)

    bus.suscribir(SolicitudPartnerRegistrada, seguimiento.manejar_evento)
    bus.suscribir(ReglasDePartnerEvaluadas, seguimiento.manejar_evento)
    bus.suscribir(SolicitudPartnerListaParaAtencion, seguimiento.manejar_evento)
    bus.suscribir(SolicitudPartnerRechazada, seguimiento.manejar_evento)

    servicio = ServicioSolicitudesPartner(repositorio=repo, event_bus=bus)
    return servicio, repo, seguimiento


def test_flujo_completo_aprobado() -> None:
    servicio, repo, seguimiento = _armar_escenario()

    servicio.registrar_solicitud(
        RegistrarSolicitudPartner(
            solicitud_id="sol-completa-ok",
            partner_id="partner-1",
            referencia_externa="REF-OK-1",
            tipo_servicio="electricidad",
        )
    )

    solicitud = repo.obtener_por_id(SolicitudId("sol-completa-ok"))
    assert solicitud is not None
    assert solicitud.estado == EstadoSolicitud.LISTA_PARA_ATENCION

    tipos = Counter(type(e) for e in seguimiento.eventos_recibidos)
    assert tipos[SolicitudPartnerRegistrada] == 1
    assert tipos[ReglasDePartnerEvaluadas] == 1
    assert tipos[SolicitudPartnerListaParaAtencion] == 1


def test_flujo_completo_rechazado() -> None:
    servicio, repo, seguimiento = _armar_escenario()

    servicio.registrar_solicitud(
        RegistrarSolicitudPartner(
            solicitud_id="sol-completa-no",
            partner_id="partner-2",
            referencia_externa="RECHAZAR-001",
            tipo_servicio="plomeria",
        )
    )

    solicitud = repo.obtener_por_id(SolicitudId("sol-completa-no"))
    assert solicitud is not None
    assert solicitud.estado == EstadoSolicitud.RECHAZADA

    tipos = Counter(type(e) for e in seguimiento.eventos_recibidos)
    assert tipos[SolicitudPartnerRegistrada] == 1
    assert tipos[ReglasDePartnerEvaluadas] == 1
    assert tipos[SolicitudPartnerRechazada] == 1


def test_no_hay_llamadas_directas_entre_modulos_para_continuar_flujo() -> None:
    source_reglas = inspect.getsource(HandlerReglasPartner)
    assert "resultado_reglas" not in source_reglas
    assert "seguimiento" not in source_reglas
