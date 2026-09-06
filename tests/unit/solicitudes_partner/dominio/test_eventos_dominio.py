from solicitudes_partner.dominio.entidades import SolicitudPartner
from solicitudes_partner.dominio.eventos import (
    SolicitudPartnerListaParaAtencion,
    SolicitudPartnerRegistrada,
    SolicitudPartnerRechazada,
)
from solicitudes_partner.dominio.objetos_valor import PartnerId, ReferenciaExterna, SolicitudId, TipoServicio


def _crear_solicitud() -> SolicitudPartner:
    return SolicitudPartner.crear(
        solicitud_id=SolicitudId("sol-evt-1"),
        partner_id=PartnerId("partner-evt-1"),
        referencia_externa=ReferenciaExterna("ref-evt-1"),
        tipo_servicio=TipoServicio("electricidad"),
        existe_previa=False,
    )


def test_crear_solicitud_genera_evento_registrada() -> None:
    solicitud = _crear_solicitud()

    eventos = solicitud.pull_eventos_pendientes()

    assert len(eventos) == 1
    assert isinstance(eventos[0], SolicitudPartnerRegistrada)
    assert eventos[0].solicitud_id == "sol-evt-1"
    assert eventos[0].partner_id == "partner-evt-1"
    assert eventos[0].referencia_externa == "ref-evt-1"


def test_marcar_lista_para_atencion_genera_eventos_correspondientes() -> None:
    solicitud = _crear_solicitud()
    solicitud.pull_eventos_pendientes()

    solicitud.marcar_lista_para_atencion()

    eventos = solicitud.pull_eventos_pendientes()

    assert len(eventos) == 1
    assert isinstance(eventos[0], SolicitudPartnerListaParaAtencion)


def test_rechazar_genera_eventos_correspondientes() -> None:
    solicitud = _crear_solicitud()
    solicitud.pull_eventos_pendientes()

    solicitud.rechazar()

    eventos = solicitud.pull_eventos_pendientes()

    assert len(eventos) == 1
    assert isinstance(eventos[0], SolicitudPartnerRechazada)


def test_pull_eventos_pendientes_limpia_la_lista() -> None:
    solicitud = _crear_solicitud()

    eventos = solicitud.pull_eventos_pendientes()

    assert len(eventos) == 1
    assert solicitud.pull_eventos_pendientes() == []
