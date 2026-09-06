# Revision Fase 5 - API REST + Integracion

## Estado
Implementado segun `docs/ai/12-plan-fase-5.md`. Pendiente de aprobacion final del usuario.

## Decisiones tomadas (segun tu aprobacion)
1. Framework: FastAPI + Uvicorn.
2. Flag de entorno `SOLICITUDES_PARTNER_BACKEND=memoria|postgres` (por defecto `postgres`) para
   elegir la composicion sin tocar codigo.
3. Endpoint administrativo `POST /admin/outbox/publicar-pendientes` agregado.
4. Alcance de endpoints: Crear (`POST /solicitudes-partner`), Consultar por id
   (`GET /solicitudes-partner/{id}`) y Listar por partner (`GET /solicitudes-partner?partner_id=`).

## Arquitectura implementada
Nuevo paquete `src/solicitudes_partner/api/` (adaptador primario), sin tocar dominio ni
aplicacion existentes:
- `app.py`: factory `crear_app()` + instancia `app` para `uvicorn solicitudes_partner.api.app:app`.
- `esquemas.py`: DTOs Pydantic de request/response, separados de los DTOs de aplicacion.
- `dependencias.py`: construye la composicion una sola vez (via `SOLICITUDES_PARTNER_BACKEND`,
  memoria|postgres) y la expone via `Depends()`; en tests se sobreescribe completamente con
  `app.dependency_overrides`, sin tocar el flag ni el `lru_cache`.
- `rutas_solicitudes_partner.py`: los 3 endpoints de negocio.
- `rutas_admin.py`: endpoint para drenar el Outbox (`RelayOutbox.publicar_pendientes()`).
- `manejo_errores.py`: traduce excepciones de dominio a respuestas HTTP (400/404/409).

### Detalle: por que `POST /solicitudes-partner` relee del Read Model antes de responder
`ServicioSolicitudesPartner.registrar_solicitud()` retorna la instancia del agregado devuelta por
`CapturaSolicitudes`, pero `HandlerResultadoReglas` opera sobre una instancia distinta obtenida via
`repositorio.obtener_por_id()`. El estado final (`LISTA_PARA_ATENCION`/`RECHAZADA`) no es confiable
leyendo el objeto retornado. Por eso el endpoint llama a `consultas.consultar_vista()` inmediatamente
despues de `registrar_solicitud()`: como todo el flujo (Reglas -> ResultadoReglas -> Proyeccion) es
sincrono, el Read Model ya esta actualizado en ese punto.

## Bug encontrado y corregido (fuera del alcance original, pero bloqueante)
Al escribir la prueba de integracion del endpoint admin (`test_endpoint_admin_outbox_publica_pendientes`)
se detecto que `crear_servicio_y_relay_outbox_postgres` y
`crear_servicio_consultas_y_relay_outbox_postgres` (Bloque 2.5 / Fase 4, ya aprobados) construian
`ServicioSolicitudesPartner` y `RelayOutbox` **compartiendo el mismo `EventBusMemoria`**. Esto nunca
se detecto antes porque las pruebas de `test_outbox.py` usan un `EventBusMemoria()` nuevo y aislado
para el relay (no la composicion real de bootstrap).

Al llamar `relay.publicar_pendientes()` sobre la composicion real despues de un registro real, el
evento `SolicitudPartnerRegistrada` se re-publicaba en el mismo bus y volvia a disparar
`HandlerReglasPartner` -> `HandlerResultadoReglas`, que intentaba transicionar de nuevo un agregado
que ya estaba en un estado terminal (`LISTA_PARA_ATENCION`/`RECHAZADA`), lanzando
`TransicionEstadoInvalidaError` (409) en vez de simplemente confirmar la entrega del evento.

**Correccion aplicada**: `bootstrap.py` ahora construye dos `EventBusMemoria` independientes en
ambas funciones: uno **interno** (Reglas/ResultadoReglas/Seguimiento/Proyeccion, usado por
`ServicioSolicitudesPartner`) y uno **externo** (usado por `RelayOutbox`, hoy sin suscriptores,
preparado para un futuro adaptador de mensajeria externa). Drenar el outbox ya no vuelve a disparar
el flujo de negocio interno. No cambia la firma publica de ninguna funcion de `bootstrap.py`, solo
su implementacion interna; `test_outbox.py` (30 tests previos) sigue pasando sin cambios.

## Archivos afectados

Creados:
- `src/solicitudes_partner/api/__init__.py`
- `src/solicitudes_partner/api/app.py`
- `src/solicitudes_partner/api/esquemas.py`
- `src/solicitudes_partner/api/dependencias.py`
- `src/solicitudes_partner/api/rutas_solicitudes_partner.py`
- `src/solicitudes_partner/api/rutas_admin.py`
- `src/solicitudes_partner/api/manejo_errores.py`
- `tests/unit/api/__init__.py`, `tests/unit/api/test_rutas_solicitudes_partner.py` (7 pruebas)
- `tests/integration/api/__init__.py`, `tests/integration/api/test_api_postgres.py` (2 pruebas)
- `docs/ai/12-plan-fase-5.md`, `docs/ai/12-revision-fase-5.md` (este documento)

Modificados:
- `pyproject.toml` - extra opcional `api` (`fastapi`, `uvicorn`, `httpx`).
- `README.md` - seccion "API REST (Fase 5)" + nota de EventBus interno/externo en Outbox.
- `src/solicitudes_partner/config/bootstrap.py` - fix de EventBus interno/externo descrito arriba
  (unico cambio a codigo de fases previas).

No modificados:
- `src/solicitudes_partner/dominio/*`
- `src/solicitudes_partner/aplicacion/*` (ningun archivo existente)
- `src/solicitudes_partner/infraestructura/*` (ningun archivo existente)
- Tests existentes de Fases 1-4 (siguen pasando sin cambios).

## Pruebas

### Unitarias de la API (memoria, sin PostgreSQL)
7 pruebas: registrar (201 + estado final), consultar por id, listar por partner, duplicada (409),
no encontrada (404), value object invalido (400), admin outbox sin relay (501).

### Integracion contra PostgreSQL real
2 pruebas: registrar+consultar contra Postgres real, y publicar pendientes via el endpoint admin
(valida el fix del EventBus interno/externo).

### Suite completa
```
49 passed
```
(40 previos de Fases 1-4 + 7 unit API + 2 integracion API).

## Alcance deliberadamente excluido (segun el plan)
- Autenticacion/autorizacion.
- Versionado de API, rate limiting, CORS.
- Dockerfile/despliegue de la API.
- Cambios en dominio, comandos/consultas/servicios existentes, persistencia u Outbox (mas alla
  del fix puntual de EventBus interno/externo).
- OpenAPI custom (se usa el autogenerado por FastAPI).
- Otro protocolo distinto a REST/HTTP.

## Resultado
Fase 5 (API REST + integracion) queda **completa** con este bloque, sujeta a tu confirmacion
final. Con esto se cierran las 5 fases planificadas del roadmap.
