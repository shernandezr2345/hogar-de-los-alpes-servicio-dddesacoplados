# Revision Bloque 2.5 - Transactional Outbox (cierre de Fase 3)

## Estado
Implementado y **APROBADO** por el usuario (2026-09-06). Fase 3 (PostgreSQL + Repository + Outbox) queda cerrada.

## Decisiones tomadas (respuesta a las Dudas del plan)
1. **Puerto de outbox**: no se agrego puerto nuevo en `dominio/repositorios.py`. El outbox es un
   detalle de entrega confiable (infraestructura), no una regla de negocio. `RepositorioSolicitudesPartner`
   no cambio de contrato.
2. **Evitar publicacion duplicada**: se ajusto el enfoque original del plan. En vez de que la
   aplicacion deje de publicar directo al event bus, el **repositorio Postgres** ademas persiste
   los eventos del agregado en `outbox_eventos` (transaccionalmente, via lectura no destructiva
   `solicitud.ver_eventos_pendientes()`), sin tocar `captura.py` ni `resultado_reglas.py`. El flujo
   interno sincrono (Reglas -> ResultadoReglas -> Seguimiento) sigue igual que en 2.3/2.4, porque
   `ReglasDePartnerEvaluadas` no proviene del agregado (lo emite `HandlerReglasPartner` directamente)
   y por lo tanto nunca entra al outbox; solo los eventos "de hecho durable" del agregado
   (`SolicitudPartnerRegistrada`, `SolicitudPartnerListaParaAtencion`, `SolicitudPartnerRechazada`)
   se registran ahi. Esto evita duplicidad sin alterar el flujo aprobado.
3. **Marcar procesado**: confirmado. `outbox_eventos.procesado_en` se setea con `now()` al publicar;
   no se borran filas (trazabilidad).
4. **Migraciones**: se amplio `db/schema.sql` (mismo archivo, `CREATE TABLE IF NOT EXISTS`), sin
   introducir carpeta de migraciones ni herramienta adicional, consistente con Bloque 2.4.
5. **Disparo del relay**: metodo Python explicito `RelayOutbox.publicar_pendientes()`, invocado
   manualmente (sin CLI, cron ni proceso en segundo plano).

## Arquitectura implementada
- Dominio: sin cambios.
- Aplicacion: sin cambios (`captura.py`, `resultado_reglas.py` identicos).
- Infraestructura:
  - `repositorio_postgres.py`: `guardar()` ahora envuelve el upsert de `solicitudes_partner` y el
    insert de `outbox_eventos` en `with self._conexion.transaction():` (funciona sobre una conexion
    `autocommit=True` sin necesidad de tocar `db_conexion.py`, segun documentacion oficial de psycopg3).
  - `relay_outbox.py` (nuevo): `RelayOutbox.publicar_pendientes()` lee filas pendientes
    (`procesado_en IS NULL`), reconstruye el evento de dominio desde `tipo_evento` + `payload`,
    lo publica en el `EventBus` recibido, y marca la fila como procesada. Retorna cuantos eventos publico.
  - `db/schema.sql`: se agrego la tabla `outbox_eventos` (id, solicitud_id, tipo_evento, payload
    JSONB, creado_en, procesado_en) + indice parcial sobre pendientes.
- Configuracion: `bootstrap.py` agrega `crear_servicio_y_relay_outbox_postgres(conexion)`, que
  construye el servicio y un `RelayOutbox` compartiendo el mismo `EventBusMemoria`. No se modifico
  `crear_servicio_solicitudes_partner()` ni `crear_servicio_solicitudes_partner_postgres()`.

Diagrama conceptual:

```
Aplicacion -> RepositorioSolicitudesPartner (PUERTO, sin cambios)
                 -> RepositorioSolicitudesPartnerPostgres.guardar()
                        - 1 transaccion: UPSERT solicitudes_partner + INSERT outbox_eventos
RelayOutbox.publicar_pendientes() (invocacion explicita)
    -> SELECT outbox_eventos WHERE procesado_en IS NULL
    -> EventBus.publicar(evento_reconstruido)
    -> UPDATE outbox_eventos SET procesado_en = now()
```

## Archivos afectados
Creados:
- `src/solicitudes_partner/infraestructura/relay_outbox.py`
- `tests/integration/solicitudes_partner/test_outbox.py`
- `docs/ai/10-plan-bloque-2.5-outbox.md`
- `docs/ai/10-revision-bloque-2.5-outbox.md` (este documento)

Modificados:
- `db/schema.sql` (tabla `outbox_eventos` + indice)
- `src/solicitudes_partner/infraestructura/repositorio_postgres.py` (transaccion + escritura outbox)
- `src/solicitudes_partner/config/bootstrap.py` (`_construir_servicio` acepta `event_bus` opcional;
  nueva `crear_servicio_y_relay_outbox_postgres`)
- `README.md` (documentacion del outbox y del relay)

No modificados (confirmado):
- `src/solicitudes_partner/dominio/*`
- `src/solicitudes_partner/aplicacion/*` (ningun archivo)
- `src/solicitudes_partner/infraestructura/repositorio_memoria.py`
- `src/solicitudes_partner/infraestructura/event_bus_memoria.py`
- `src/solicitudes_partner/infraestructura/db_conexion.py`

## Pruebas

### Suite unitaria (sin PostgreSQL)
```
21 passed, 2 skipped
```
Los 21 tests de Fase 1/2.2/2.3/2.4 continuan pasando sin cambios de comportamiento.

### Suite completa con PostgreSQL disponible (`docker compose up -d`, extra `.[postgres]` instalado)
```
30 passed
```
Cobertura nueva (`test_outbox.py`, 4 pruebas):
1. `guardar()` persiste el evento pendiente en `outbox_eventos` en la misma transaccion.
2. `RelayOutbox.publicar_pendientes()` publica el evento en el `EventBus` y marca `procesado_en`.
3. Una segunda corrida del relay no vuelve a publicar eventos ya procesados (idempotencia basica).
4. Las transiciones del agregado (`RECIBIDA` -> `LISTA_PARA_ATENCION`) generan una segunda fila en
   el outbox, sin duplicar la primera.

Las 5 pruebas de integracion existentes de `test_repositorio_postgres.py` siguen pasando sin cambios.

## Alcance deliberadamente excluido (igual que en el plan)
- Kafka, RabbitMQ o broker externo real.
- CQRS, Read Model persistente, Event Sourcing (quedan para Fase 4).
- API REST (Fase 5).
- Reintentos/backoff, dead-letter queue, scheduler/cron para el relay.
- Cambios en reglas del dominio o en el flujo de eventos aprobado en 2.3/2.4.

## Resultado
**APROBADO**. Fase 3 (PostgreSQL + Repository + Outbox) completa. Siguiente: Fase 4 (CQRS + Query + Read Model).
