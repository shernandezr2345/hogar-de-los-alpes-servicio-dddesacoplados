# Revision Fase 4 - CQRS + Query + Read Model

## Estado
Implementado y **APROBADO** por el usuario (2026-09-06). Fase 4 (CQRS + Query + Read Model) queda cerrada.

## Decisiones tomadas (segun aprobacion del plan, sin objeciones)
1. Puerto de lectura en `aplicacion/puertos_lectura.py` (no en `dominio`).
2. `ProyeccionSolicitudesPartner` reacciona solo a eventos nuevos via `EventBus` (sin reconstruccion
   completa de la vista).
3. Puerto de lectura con `obtener_por_id`, `listar_por_partner` y `actualizar` (este ultimo no
   estaba explicito en las dudas, pero es necesario para que el proyector escriba en el Read Model).

## Arquitectura implementada
- Dominio: sin cambios.
- Aplicacion (nuevo, sin tocar lo existente):
  - `vistas.py`: DTO `VistaSolicitudPartner`.
  - `puertos_lectura.py`: puerto `RepositorioLecturaSolicitudesPartner`.
  - `modulos/proyeccion_solicitudes.py`: `ProyeccionSolicitudesPartner`, suscrita a
    `SolicitudPartnerRegistrada`, `SolicitudPartnerListaParaAtencion` y `SolicitudPartnerRechazada`.
  - `consultas_lectura.py`: `ConsultarVistaSolicitudPartner`, `ListarSolicitudesPartnerPorPartner`
    y el servicio `ConsultasSolicitudesPartner` (solo usa el puerto de lectura).
- Infraestructura (nuevo):
  - `repositorio_lectura_memoria.py` / `repositorio_lectura_postgres.py`.
- Configuracion:
  - `bootstrap.py` se refactorizo internamente (`_suscribir_handlers_base` compartido por
    `_construir_servicio` y la nueva `_construir_servicio_con_lectura`), sin cambiar el
    comportamiento de `crear_servicio_solicitudes_partner()` ni de
    `crear_servicio_solicitudes_partner_postgres()`.
  - Nuevas funciones: `crear_servicio_y_consultas_solicitudes_partner()` (memoria) y
    `crear_servicio_consultas_y_relay_outbox_postgres(conexion)` (Postgres completo:
    comando + Read Model + Outbox, un solo `EventBus`).
- Base de datos: tabla `solicitudes_partner_vista` agregada a `db/schema.sql`, poblada
  exclusivamente por `ProyeccionSolicitudesPartner` (nunca por el repositorio de escritura).

## Punto de diseno relevante: por que la proyeccion lee el repositorio de escritura
Los eventos `SolicitudPartnerListaParaAtencion` y `SolicitudPartnerRechazada` solo cargan
`solicitud_id` (no `tipo_servicio`, `partner_id`, etc.), y `SolicitudPartnerRegistrada` tampoco
incluye `tipo_servicio`. Modificar los eventos de dominio estaba fuera de alcance. Por eso,
`ProyeccionSolicitudesPartner` lee el estado ya persistido (`repositorio_escritura.obtener_por_id`)
al recibir cualquiera de los 3 eventos, y con eso arma la vista completa. Es una lectura, nunca una
escritura, sobre el modelo de comando; el Read Model solo se escribe via el puerto de lectura.

## Flujo de eventos (sin cambios respecto a Bloque 2.3/2.4/2.5)
```
RegistrarSolicitudPartner -> Captura -> guardar() [+ outbox si Postgres] -> publica evento
    -> Reglas de Partner -> ReglasDePartnerEvaluadas
    -> HandlerResultadoReglas -> Aggregate -> SolicitudPartnerListaParaAtencion/Rechazada
    -> Seguimiento (sin cambios)
    -> ProyeccionSolicitudesPartner (NUEVO) -> actualiza solicitudes_partner_vista
```

## Archivos afectados
Creados:
- `src/solicitudes_partner/aplicacion/vistas.py`
- `src/solicitudes_partner/aplicacion/puertos_lectura.py`
- `src/solicitudes_partner/aplicacion/consultas_lectura.py`
- `src/solicitudes_partner/aplicacion/modulos/proyeccion_solicitudes.py`
- `src/solicitudes_partner/infraestructura/repositorio_lectura_memoria.py`
- `src/solicitudes_partner/infraestructura/repositorio_lectura_postgres.py`
- `tests/unit/solicitudes_partner/aplicacion/test_proyeccion_solicitudes.py`
- `tests/unit/solicitudes_partner/aplicacion/test_consultas_lectura.py`
- `tests/unit/solicitudes_partner/aplicacion/test_cqrs_flujo_completo.py`
- `tests/integration/solicitudes_partner/test_repositorio_lectura_postgres.py`
- `docs/ai/11-plan-fase-4.md`, `docs/ai/11-revision-fase-4.md` (este documento)

Modificados:
- `db/schema.sql` (tabla `solicitudes_partner_vista` + indice)
- `src/solicitudes_partner/config/bootstrap.py` (refactor interno + 2 funciones nuevas)
- `README.md` (documentacion CQRS/Read Model)

No modificados (confirmado):
- `src/solicitudes_partner/dominio/*`
- `src/solicitudes_partner/aplicacion/servicios.py`, `comandos.py`, `consultas.py`
- `src/solicitudes_partner/aplicacion/modulos/captura.py`, `reglas_partner.py`, `resultado_reglas.py`, `seguimiento.py`
- `src/solicitudes_partner/infraestructura/repositorio_memoria.py`, `repositorio_postgres.py`,
  `relay_outbox.py`, `event_bus_memoria.py`, `db_conexion.py`

## Pruebas

### Suite unitaria (sin PostgreSQL)
Nuevas: 8 pruebas (proyeccion x3, consultas_lectura x3, flujo CQRS completo x2). Las existentes
(21 previas) no cambian de comportamiento.

### Suite completa con PostgreSQL disponible
```
40 passed
```
(21 unit Fase1-2.4 + 5 integracion Postgres repo escritura + 4 integracion Outbox + 8 unit CQRS +
2 integracion Read Model Postgres = 40).

Cobertura nueva de integracion (`test_repositorio_lectura_postgres.py`):
1. La proyeccion puebla `solicitudes_partner_vista` correctamente contra Postgres real.
2. `ConsultasSolicitudesPartner` lee correctamente desde esa tabla (`consultar_vista` y
   `listar_por_partner`).

## Alcance deliberadamente excluido (igual que en el plan)
- Event Sourcing.
- API REST (Fase 5, siguiente).
- Reconstruccion/replay completo de la proyeccion desde el Outbox historico.
- Cambios en reglas del dominio, en el Aggregate, en el puerto/adaptadores de escritura, ni en el
  Outbox/Relay del Bloque 2.5.
- Cache, paginacion o filtros avanzados en la consulta.

## Resultado
**APROBADO**. Fase 4 (CQRS + Query + Read Model) completa. Siguiente: Fase 5 (API REST + integracion).
