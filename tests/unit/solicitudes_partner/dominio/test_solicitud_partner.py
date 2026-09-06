import pytest

from solicitudes_partner.dominio.entidades import SolicitudPartner
from solicitudes_partner.dominio.excepciones import (
    SolicitudDuplicadaError,
    TransicionEstadoInvalidaError,
)
from solicitudes_partner.dominio.objetos_valor import (
    EstadoSolicitud,
    PartnerId,
    ReferenciaExterna,
    SolicitudId,
    TipoServicio,
)


def _crear_solicitud() -> SolicitudPartner:
    return SolicitudPartner.crear(
        solicitud_id=SolicitudId("sol-1"),
        partner_id=PartnerId("partner-1"),
        referencia_externa=ReferenciaExterna("ref-1"),
        tipo_servicio=TipoServicio("electricidad"),
        existe_previa=False,
    )


def test_crear_solicitud_inicia_en_recibida() -> None:
    solicitud = _crear_solicitud()
    assert solicitud.estado == EstadoSolicitud.RECIBIDA


def test_crear_solicitud_duplicada_lanza_error() -> None:
    with pytest.raises(SolicitudDuplicadaError):
        SolicitudPartner.crear(
            solicitud_id=SolicitudId("sol-2"),
            partner_id=PartnerId("partner-1"),
            referencia_externa=ReferenciaExterna("ref-1"),
            tipo_servicio=TipoServicio("electricidad"),
            existe_previa=True,
        )


def test_transicion_recibida_a_lista_para_atencion_es_valida() -> None:
    solicitud = _crear_solicitud()
    solicitud.marcar_lista_para_atencion()
    assert solicitud.estado == EstadoSolicitud.LISTA_PARA_ATENCION


def test_transicion_recibida_a_rechazada_es_valida() -> None:
    solicitud = _crear_solicitud()
    solicitud.rechazar()
    assert solicitud.estado == EstadoSolicitud.RECHAZADA


def test_transicion_rechazada_a_lista_para_atencion_no_es_valida() -> None:
    solicitud = _crear_solicitud()
    solicitud.rechazar()

    with pytest.raises(TransicionEstadoInvalidaError):
        solicitud.marcar_lista_para_atencion()
