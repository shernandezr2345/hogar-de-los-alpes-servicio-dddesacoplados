import inspect

from solicitudes_partner.aplicacion.comandos import RegistrarSolicitudPartner
from solicitudes_partner.aplicacion.modulos.captura import CapturaSolicitudes
from solicitudes_partner.aplicacion.modulos.reglas_partner import HandlerReglasPartner
from solicitudes_partner.aplicacion.servicios import ServicioSolicitudesPartner
from solicitudes_partner.dominio.eventos import ReglasDePartnerEvaluadas, SolicitudPartnerRegistrada
from solicitudes_partner.infraestructura.event_bus_memoria import EventBusMemoria
from solicitudes_partner.infraestructura.repositorio_memoria import RepositorioSolicitudesPartnerMemoria


def test_solicitud_registrada_llega_a_reglas_por_event_bus() -> None:
    repo = RepositorioSolicitudesPartnerMemoria()
    bus = EventBusMemoria()
    reglas = HandlerReglasPartner(event_bus=bus)
    evaluadas: list[ReglasDePartnerEvaluadas] = []

    def capturar_evaluada(evento):
        if isinstance(evento, ReglasDePartnerEvaluadas):
            evaluadas.append(evento)

    bus.suscribir(SolicitudPartnerRegistrada, reglas.manejar_solicitud_registrada)
    bus.suscribir(ReglasDePartnerEvaluadas, capturar_evaluada)

    servicio = ServicioSolicitudesPartner(repositorio=repo, event_bus=bus)
    servicio.registrar_solicitud(
        RegistrarSolicitudPartner(
            solicitud_id="sol-flujo-1",
            partner_id="partner-flujo-1",
            referencia_externa="ref-flujo-1",
            tipo_servicio="electricidad",
        )
    )

    assert len(evaluadas) == 1
    assert evaluadas[0].solicitud_id == "sol-flujo-1"
    assert evaluadas[0].fue_aprobada is True


def test_sin_suscripcion_de_reglas_no_se_publica_evaluacion() -> None:
    repo = RepositorioSolicitudesPartnerMemoria()
    bus = EventBusMemoria()
    evaluadas: list[ReglasDePartnerEvaluadas] = []

    def capturar_evaluada(evento):
        if isinstance(evento, ReglasDePartnerEvaluadas):
            evaluadas.append(evento)

    bus.suscribir(ReglasDePartnerEvaluadas, capturar_evaluada)

    servicio = ServicioSolicitudesPartner(repositorio=repo, event_bus=bus)
    servicio.registrar_solicitud(
        RegistrarSolicitudPartner(
            solicitud_id="sol-flujo-2",
            partner_id="partner-flujo-2",
            referencia_externa="ref-flujo-2",
            tipo_servicio="plomeria",
        )
    )

    assert evaluadas == []


def test_captura_no_tiene_dependencia_directa_de_reglas_partner() -> None:
    source = inspect.getsource(CapturaSolicitudes)
    assert "reglas_partner" not in source
    assert "HandlerReglasPartner" not in source
