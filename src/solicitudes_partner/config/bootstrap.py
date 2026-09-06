"""Composition root para Fase 1 + Bloque 2.2 + Bloque 2.4."""

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
from solicitudes_partner.dominio.repositorios import RepositorioSolicitudesPartner
from solicitudes_partner.infraestructura.event_bus_memoria import EventBusMemoria
from solicitudes_partner.infraestructura.repositorio_memoria import (
    RepositorioSolicitudesPartnerMemoria,
)


def _construir_servicio(repositorio: RepositorioSolicitudesPartner) -> ServicioSolicitudesPartner:
    event_bus = EventBusMemoria()

    handler_reglas = HandlerReglasPartner(event_bus=event_bus)
    handler_resultado = HandlerResultadoReglas(repositorio=repositorio, event_bus=event_bus)
    seguimiento = SeguimientoSolicitudes()

    event_bus.suscribir(SolicitudPartnerRegistrada, handler_reglas.manejar_solicitud_registrada)
    event_bus.suscribir(ReglasDePartnerEvaluadas, handler_resultado.manejar_reglas_evaluadas)

    event_bus.suscribir(SolicitudPartnerRegistrada, seguimiento.manejar_evento)
    event_bus.suscribir(ReglasDePartnerEvaluadas, seguimiento.manejar_evento)
    event_bus.suscribir(SolicitudPartnerListaParaAtencion, seguimiento.manejar_evento)
    event_bus.suscribir(SolicitudPartnerRechazada, seguimiento.manejar_evento)

    return ServicioSolicitudesPartner(repositorio=repositorio, event_bus=event_bus)


def crear_servicio_solicitudes_partner() -> ServicioSolicitudesPartner:
    repositorio = RepositorioSolicitudesPartnerMemoria()
    return _construir_servicio(repositorio)


def crear_servicio_solicitudes_partner_postgres(conexion) -> ServicioSolicitudesPartner:
    """Composicion explicita para PostgreSQL; no se activa por variables de entorno.

    Requiere el extra opcional 'postgres' (psycopg) y una conexion ya creada,
    por ejemplo mediante solicitudes_partner.infraestructura.db_conexion.crear_conexion().
    """
    from solicitudes_partner.infraestructura.repositorio_postgres import (
        RepositorioSolicitudesPartnerPostgres,
    )

    repositorio = RepositorioSolicitudesPartnerPostgres(conexion)
    return _construir_servicio(repositorio)

