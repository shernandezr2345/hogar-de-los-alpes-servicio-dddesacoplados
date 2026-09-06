from solicitudes_partner.dominio.eventos import SolicitudPartnerRegistrada
from solicitudes_partner.infraestructura.event_bus_memoria import EventBusMemoria


def _evento_registrada() -> SolicitudPartnerRegistrada:
    return SolicitudPartnerRegistrada(
        solicitud_id="sol-1",
        partner_id="partner-1",
        referencia_externa="ref-1",
    )


def test_handler_puede_suscribirse_a_un_tipo_evento() -> None:
    bus = EventBusMemoria()
    recibidos: list[str] = []

    def handler(evento):
        recibidos.append(evento.solicitud_id)

    bus.suscribir(SolicitudPartnerRegistrada, handler)
    bus.publicar(_evento_registrada())

    assert recibidos == ["sol-1"]


def test_publicar_evento_ejecuta_handler_correspondiente() -> None:
    bus = EventBusMemoria()
    ejecutado = {"valor": False}

    def handler(_evento):
        ejecutado["valor"] = True

    bus.suscribir(SolicitudPartnerRegistrada, handler)
    bus.publicar(_evento_registrada())

    assert ejecutado["valor"] is True


def test_multiples_handlers_reciben_el_mismo_evento() -> None:
    bus = EventBusMemoria()
    recibidos: list[str] = []

    def handler_a(_evento):
        recibidos.append("a")

    def handler_b(_evento):
        recibidos.append("b")

    bus.suscribir(SolicitudPartnerRegistrada, handler_a)
    bus.suscribir(SolicitudPartnerRegistrada, handler_b)
    bus.publicar(_evento_registrada())

    assert recibidos == ["a", "b"]
