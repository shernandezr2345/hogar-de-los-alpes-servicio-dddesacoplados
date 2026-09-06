# Plan Bloque 2.5 - Transactional Outbox (cierre de Fase 3)

## Estado
Plan propuesto. Pendiente de aprobacion. No se ha modificado codigo.

## 1. Objetivo
Cerrar la Fase 3 (PostgreSQL + Repository + Outbox) incorporando el patron Transactional Outbox
para el Aggregate Root `SolicitudPartner`, garantizando que la persistencia del agregado y el
registro de sus eventos de dominio ocurran de forma atomica, sin alterar el dominio ni el flujo
de eventos ya aprobado en el Bloque 2.3/2.4.

## 2. Estado actual (verificado en el repositorio)
1. `RepositorioSolicitudesPartnerPostgres.guardar()` hace upsert por `solicitud_id` sobre una
   conexion con `autocommit=True` (sin transaccion explicita).
2. Los eventos de dominio se publican de forma sincrona e inmediata contra `EventBusMemoria`,
   justo despues de `repositorio.guardar()`, en:
   - `aplicacion/modulos/captura.py` (`CapturaSolicitudes.registrar_solicitud`)
   - `aplicacion/modulos/resultado_reglas.py` (`HandlerResultadoReglas.manejar_reglas_evaluadas`)
3. No existe tabla ni mecanismo de outbox. Si el proceso cae entre `guardar()` y `publicar()`,
   el evento se pierde (no hay garantia de entrega).
4. `EventBusMemoria` y el puerto `RepositorioSolicitudesPartner` no tienen relacion con outbox hoy.
5. Bloque 2.4 dejo explicitamente Outbox fuera de alcance (ver `docs/ai/09-revision-bloque-2.4.md`).

## 3. Problema que resuelve
Publicar eventos en el mismo paso que se guarda el agregado, sin una transaccion que cubra ambas
escrituras, no garantiza consistencia: puede persistirse el estado sin publicar el evento, o
publicarse el evento sin que la escritura del agregado se confirme. El patron Outbox resuelve esto
escribiendo el evento en la misma transaccion de base de datos que el agregado, y publicandolo
despues mediante un proceso separado (relay) que lee la tabla outbox y marca cada evento como
procesado solo tras publicarlo exitosamente.

## 4. Alcance
1. Tabla `outbox_eventos` en PostgreSQL para persistir eventos pendientes de publicacion.
2. Puerto de dominio/aplicacion para escribir en el outbox (ver Duda 1 sobre su ubicacion).
3. Adaptador PostgreSQL que, en una unica transaccion, persista el agregado (upsert en
   `solicitudes_partner`) y los eventos generados (insert en `outbox_eventos`).
4. Cambio en la conexion PostgreSQL: pasar de `autocommit=True` a manejo explicito de transaccion
   (commit al final del caso de uso, rollback ante error) solo para la ruta Postgres. El
   repositorio en memoria no cambia.
5. Relay/publicador: componente que lee eventos pendientes de `outbox_eventos` en orden, los
   publica en `EventBusMemoria` (o el bus vigente) y los marca como procesados. Se ejecuta de
   forma explicita (metodo/CLI), sin scheduler ni proceso en segundo plano en este bloque.
6. Adaptar `CapturaSolicitudes` y `HandlerResultadoReglas` para que, cuando se use el repositorio
   Postgres, los eventos se escriban en el outbox en lugar de publicarse de forma sincrona e
   inmediata. El comportamiento con el repositorio en memoria (usado por tests unitarios) se
   mantiene igual (publicacion sincrona), para no romper la suite existente.
7. Pruebas de integracion minimas: outbox se llena junto con el agregado en la misma transaccion;
   el relay publica y marca como procesado; un evento ya procesado no se vuelve a publicar.

## 5. Fuera de alcance (explicito)
- Kafka, RabbitMQ o cualquier broker externo real.
- CQRS, Read Model persistente, Event Sourcing (Fase 4).
- API REST (Fase 5).
- Reintentos con backoff, dead-letter queue, o scheduler/cron para el relay.
- Idempotencia del lado del consumidor mas alla de marcar el evento como procesado.
- Cambios en reglas o invariantes del dominio, ni en el flujo de eventos aprobado en 2.3/2.4.
- Cambios en `RepositorioSolicitudesPartnerMemoria` o en el comportamiento de los tests unitarios.

## 6. Arquitectura propuesta
Se mantiene el modelo por capas:

```
Aplicacion (Captura / ResultadoReglas)
    |
    v
RepositorioSolicitudesPartner (PUERTO, sin cambios de firma)
    |
    v
RepositorioSolicitudesPartnerPostgres
    - guardar(solicitud) + eventos -> 1 transaccion
        - UPSERT solicitudes_partner
        - INSERT outbox_eventos (uno por evento pendiente del agregado)
    |
    v
PostgreSQL

RelayOutbox (nuevo, infraestructura)
    - lee outbox_eventos WHERE procesado = false ORDER BY creado_en
    - publica cada evento en EventBus
    - marca procesado = true (o borra la fila, a decidir - ver Duda 3)
```

## 7. Modelo de datos propuesto
Tabla `outbox_eventos`:

| Columna       | Tipo             | Restriccion                     |
|---------------|------------------|----------------------------------|
| id            | BIGSERIAL        | PRIMARY KEY                      |
| solicitud_id  | VARCHAR          | NOT NULL                         |
| tipo_evento   | VARCHAR          | NOT NULL                         |
| payload       | JSONB            | NOT NULL                         |
| creado_en     | TIMESTAMPTZ      | NOT NULL DEFAULT now()           |
| procesado_en  | TIMESTAMPTZ      | NULL (NULL = pendiente)          |

## 8. Archivos que se crearian/modificarian (propuesta, sujeta a aprobacion)

Crear:
1. `db/migrations/002_outbox_eventos.sql` (o ampliar `db/schema.sql`, ver Duda 4).
2. `src/solicitudes_partner/infraestructura/outbox_postgres.py` - escritura/lectura del outbox.
3. `src/solicitudes_partner/infraestructura/relay_outbox.py` - publicador que drena el outbox.
4. `tests/integration/solicitudes_partner/test_outbox.py`.
5. Este documento y su correspondiente `docs/ai/10-revision-bloque-2.5.md` al cierre.

Modificar:
6. `src/solicitudes_partner/infraestructura/repositorio_postgres.py` - transaccion explicita +
   insercion de eventos del agregado en `outbox_eventos` dentro del mismo `guardar()`.
7. `src/solicitudes_partner/infraestructura/db_conexion.py` - quitar `autocommit=True` (o exponer
   ambos modos) para permitir transacciones explicitas.
8. `src/solicitudes_partner/aplicacion/modulos/captura.py` y `resultado_reglas.py` - dejar de
   publicar directo al event bus cuando el repositorio ya persistio los eventos via outbox (a
   definir mecanismo exacto, ver Duda 2).
9. `src/solicitudes_partner/config/bootstrap.py` - conectar el relay en la composicion Postgres.
10. `README.md` - documentar el flujo de outbox y como ejecutar el relay.

No se propone modificar:
- `src/solicitudes_partner/dominio/*`
- `src/solicitudes_partner/infraestructura/repositorio_memoria.py`
- `crear_servicio_solicitudes_partner()` (ruta memoria, usada por tests unitarios)

## 9. Dudas (requieren tu decision antes de implementar)
1. **Donde vive el puerto de outbox**: lo agrego como puerto en `dominio/repositorios.py`
   (ej. `RepositorioOutbox`) o lo trato como detalle interno de infraestructura sin puerto en el
   dominio (ya que el outbox es un detalle tecnico de entrega confiable, no una regla de negocio)?
2. **Como evitar publicacion duplicada** entre el flujo actual (sincrono) y el nuevo outbox: la
   capa de aplicacion deja de llamar a `event_bus.publicar()` directamente cuando el repositorio es
   Postgres (el propio adaptador o un wrapper se encarga de escribir al outbox), y el relay es quien
   efectivamente llama a `event_bus.publicar()`. Estas de acuerdo con este enfoque?
3. **Marcar vs borrar**: al publicar un evento del outbox, prefieres marcarlo `procesado_en`
   (se conserva historial/auditoria) o borrar la fila (tabla se mantiene pequena)? Propongo marcar,
   por trazabilidad, dado que ya se evito agregar columnas de auditoria en `solicitudes_partner`
   pero aqui el outbox si necesita ese registro para su proposito.
4. **Migraciones**: seguimos con script SQL plano (ampliar `db/schema.sql` o agregar un segundo
   archivo `db/migrations/002_outbox_eventos.sql`), igual que en Bloque 2.4, sin herramienta de
   migraciones?
5. **Disparo del relay**: por ahora, ¿alcanza con un metodo Python invocable manualmente o desde un
   test (`RelayOutbox.publicar_pendientes()`), sin CLI ni proceso en segundo plano? (Broker real y
   automatizacion quedarian para una fase posterior, fuera de alcance aqui).

## 10. Impacto en pruebas existentes
- Suite unitaria (repositorio en memoria): sin cambios de comportamiento, deben seguir pasando los
  21 tests actuales.
- Suite de integracion Postgres: se agregan pruebas nuevas para outbox; las 5 pruebas existentes de
  `test_repositorio_postgres.py` deben seguir pasando (ajustando si cambia el manejo de conexion de
  autocommit a transaccion explicita).

## 11. Siguientes fases (solo referencia, no incluidas en este bloque)
- Fase 4: CQRS + Query + Read Model (modelo de lectura separado, posiblemente alimentado por los
  eventos que hoy publica el relay del outbox).
- Fase 5: API REST + integracion (exponer comandos/consultas via HTTP).
