"""Composition root para Fase 1 + Bloque 2.2 + Bloque 2.4 + Bloque 2.5 + Fase 4."""

from solicitudes_partner.aplicacion.consultas_lectura import ConsultasSolicitudesPartner
from solicitudes_partner.aplicacion.modulos.proyeccion_solicitudes import (
    ProyeccionSolicitudesPartner,
)
from solicitudes_partner.aplicacion.modulos.reglas_partner import HandlerReglasPartner
from solicitudes_partner.aplicacion.modulos.resultado_reglas import HandlerResultadoReglas
from solicitudes_partner.aplicacion.modulos.seguimiento import SeguimientoSolicitudes
from solicitudes_partner.aplicacion.puertos_lectura import RepositorioLecturaSolicitudesPartner
from solicitudes_partner.aplicacion.servicios import ServicioSolicitudesPartner
from solicitudes_partner.dominio.eventos import (
    ReglasDePartnerEvaluadas,
    SolicitudPartnerListaParaAtencion,
    SolicitudPartnerRechazada,
    SolicitudPartnerRegistrada,
)
from solicitudes_partner.dominio.repositorios import RepositorioSolicitudesPartner
from solicitudes_partner.infraestructura.event_bus_memoria import EventBusMemoria
from solicitudes_partner.infraestructura.repositorio_lectura_memoria import (
    RepositorioLecturaSolicitudesPartnerMemoria,
)
from solicitudes_partner.infraestructura.repositorio_memoria import (
    RepositorioSolicitudesPartnerMemoria,
)


def _suscribir_handlers_base(
    event_bus: EventBusMemoria, repositorio: RepositorioSolicitudesPartner
) -> None:
    handler_reglas = HandlerReglasPartner(event_bus=event_bus)
    handler_resultado = HandlerResultadoReglas(repositorio=repositorio, event_bus=event_bus)
    seguimiento = SeguimientoSolicitudes()

    event_bus.suscribir(SolicitudPartnerRegistrada, handler_reglas.manejar_solicitud_registrada)
    event_bus.suscribir(ReglasDePartnerEvaluadas, handler_resultado.manejar_reglas_evaluadas)

    event_bus.suscribir(SolicitudPartnerRegistrada, seguimiento.manejar_evento)
    event_bus.suscribir(ReglasDePartnerEvaluadas, seguimiento.manejar_evento)
    event_bus.suscribir(SolicitudPartnerListaParaAtencion, seguimiento.manejar_evento)
    event_bus.suscribir(SolicitudPartnerRechazada, seguimiento.manejar_evento)


def _construir_servicio(
    repositorio: RepositorioSolicitudesPartner,
    event_bus: EventBusMemoria | None = None,
) -> ServicioSolicitudesPartner:
    event_bus = event_bus if event_bus is not None else EventBusMemoria()
    _suscribir_handlers_base(event_bus, repositorio)
    return ServicioSolicitudesPartner(repositorio=repositorio, event_bus=event_bus)


def _construir_servicio_con_lectura(
    repositorio: RepositorioSolicitudesPartner,
    repositorio_lectura: RepositorioLecturaSolicitudesPartner,
    event_bus: EventBusMemoria | None = None,
) -> tuple[ServicioSolicitudesPartner, ConsultasSolicitudesPartner]:
    """Igual que _construir_servicio, sumando el proyector del Read Model (Fase 4)."""
    event_bus = event_bus if event_bus is not None else EventBusMemoria()
    _suscribir_handlers_base(event_bus, repositorio)

    proyeccion = ProyeccionSolicitudesPartner(
        repositorio_escritura=repositorio, repositorio_lectura=repositorio_lectura
    )
    event_bus.suscribir(SolicitudPartnerRegistrada, proyeccion.manejar_evento)
    event_bus.suscribir(SolicitudPartnerListaParaAtencion, proyeccion.manejar_evento)
    event_bus.suscribir(SolicitudPartnerRechazada, proyeccion.manejar_evento)

    servicio = ServicioSolicitudesPartner(repositorio=repositorio, event_bus=event_bus)
    consultas = ConsultasSolicitudesPartner(repositorio_lectura=repositorio_lectura)
    return servicio, consultas


def crear_servicio_solicitudes_partner() -> ServicioSolicitudesPartner:
    repositorio = RepositorioSolicitudesPartnerMemoria()
    return _construir_servicio(repositorio)


def crear_servicio_y_consultas_solicitudes_partner() -> tuple[
    ServicioSolicitudesPartner, ConsultasSolicitudesPartner
]:
    """Composicion en memoria con Read Model (Fase 4), para tests unitarios y desarrollo."""
    repositorio = RepositorioSolicitudesPartnerMemoria()
    repositorio_lectura = RepositorioLecturaSolicitudesPartnerMemoria()
    return _construir_servicio_con_lectura(repositorio, repositorio_lectura)


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


def crear_servicio_y_relay_outbox_postgres(conexion):
    """Composicion explicita PostgreSQL + RelayOutbox (Bloque 2.5).

    El repositorio persiste el agregado y sus eventos pendientes en `outbox_eventos` dentro de
    la misma transaccion (ver RepositorioSolicitudesPartnerPostgres.guardar). El RelayOutbox
    retornado permite drenar ese outbox explicitamente (relay.publicar_pendientes()); no se
    ejecuta automaticamente ni en segundo plano.

    El servicio usa un EventBus interno (Reglas/ResultadoReglas/Seguimiento, ya resueltos de
    forma sincrona en `registrar_solicitud`) y el RelayOutbox publica en un EventBus externo
    separado: así, drenar el outbox nunca vuelve a disparar el flujo de negocio interno.
    """
    from solicitudes_partner.infraestructura.relay_outbox import RelayOutbox
    from solicitudes_partner.infraestructura.repositorio_postgres import (
        RepositorioSolicitudesPartnerPostgres,
    )

    repositorio = RepositorioSolicitudesPartnerPostgres(conexion)
    servicio = _construir_servicio(repositorio, event_bus=EventBusMemoria())
    relay = RelayOutbox(conexion=conexion, event_bus=EventBusMemoria())
    return servicio, relay


def crear_servicio_consultas_y_relay_outbox_postgres(conexion):
    """Composicion PostgreSQL completa (Fase 4+5): comando + Read Model + Outbox.

    Retorna (servicio, consultas, relay). `consultas` solo lee de `solicitudes_partner_vista`,
    poblada por ProyeccionSolicitudesPartner al mismo tiempo que Reglas/Seguimiento reaccionan
    a los eventos (EventBus interno), y `relay` permite drenar el outbox de forma confiable
    (Bloque 2.5) publicando en un EventBus externo separado, para no re-disparar el flujo de
    negocio interno al drenar eventos ya procesados.
    """
    from solicitudes_partner.infraestructura.relay_outbox import RelayOutbox
    from solicitudes_partner.infraestructura.repositorio_lectura_postgres import (
        RepositorioLecturaSolicitudesPartnerPostgres,
    )
    from solicitudes_partner.infraestructura.repositorio_postgres import (
        RepositorioSolicitudesPartnerPostgres,
    )

    repositorio = RepositorioSolicitudesPartnerPostgres(conexion)
    repositorio_lectura = RepositorioLecturaSolicitudesPartnerPostgres(conexion)
    servicio, consultas = _construir_servicio_con_lectura(
        repositorio, repositorio_lectura, event_bus=EventBusMemoria()
    )
    relay = RelayOutbox(conexion=conexion, event_bus=EventBusMemoria())
    return servicio, consultas, relay

