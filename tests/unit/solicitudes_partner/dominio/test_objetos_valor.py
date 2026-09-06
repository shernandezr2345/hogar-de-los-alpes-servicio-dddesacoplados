from solicitudes_partner.dominio.excepciones import ValueObjectInvalidoError
from solicitudes_partner.dominio.objetos_valor import (
    EstadoSolicitud,
    PartnerId,
    ReferenciaExterna,
    SolicitudId,
    TipoServicio,
)


def test_estados_son_los_aprobados_para_fase_1() -> None:
    assert [estado.value for estado in EstadoSolicitud] == [
        "RECIBIDA",
        "LISTA_PARA_ATENCION",
        "RECHAZADA",
    ]


def test_value_objects_aceptan_texto_no_vacio() -> None:
    assert SolicitudId("sol-1").valor == "sol-1"
    assert PartnerId("partner-1").valor == "partner-1"
    assert ReferenciaExterna("ref-externa").valor == "ref-externa"
    assert TipoServicio("plomeria").valor == "plomeria"


def test_partner_id_vacio_lanza_error() -> None:
    try:
        PartnerId("   ")
        assert False, "Se esperaba ValueObjectInvalidoError"
    except ValueObjectInvalidoError:
        assert True
