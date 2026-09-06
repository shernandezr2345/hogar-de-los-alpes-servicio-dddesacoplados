# Plan Fase 5 - API REST + Integracion

## Estado
Plan propuesto. Pendiente de aprobacion. No se ha modificado codigo.

## 1. Objetivo
Exponer el servicio de Solicitudes de Partner via una API REST (adaptador primario/driving),
reutilizando exactamente los mismos puertos y composiciones (comando + Read Model CQRS + Outbox)
ya implementados en Fases 1-4, sin tocar dominio, aplicacion (excepto DTOs de entrada/salida HTTP)
ni infraestructura existente.

## 2. Estado actual (verificado en el repositorio)
1. No existe ningun adaptador HTTP/API hoy. El unico punto de entrada es codigo Python que llama
   directamente a `ServicioSolicitudesPartner` / `ConsultasSolicitudesPartner` via `bootstrap.py`.
2. Comando disponible: `RegistrarSolicitudPartner` (`solicitud_id, partner_id, referencia_externa,
   tipo_servicio`) -> `ServicioSolicitudesPartner.registrar_solicitud()`.
3. Consultas disponibles:
   - `ServicioSolicitudesPartner.consultar_estado()` (Fase 1, modelo de escritura).
   - `ConsultasSolicitudesPartner.consultar_vista()` / `.listar_por_partner()` (Fase 4, Read Model).
4. Excepciones de dominio ya definidas: `ValueObjectInvalidoError`, `SolicitudDuplicadaError`,
   `TransicionEstadoInvalidaError`, `SolicitudNoEncontradaError` (`dominio/excepciones.py`).
5. Composiciones disponibles en `bootstrap.py`: memoria (`crear_servicio_y_consultas_solicitudes_partner`)
   y PostgreSQL completa con Outbox (`crear_servicio_consultas_y_relay_outbox_postgres(conexion)`).
6. `pyproject.toml` no declara ningun framework web (no FastAPI, no Flask, no Django).

## 3. Problema que resuelve
El servicio hoy solo es invocable desde Python. Para que otros sistemas (frontend, partners, otros
microservicios) puedan registrar y consultar solicitudes, se necesita un adaptador HTTP que traduzca
peticiones REST a comandos/consultas de la capa de aplicacion, sin filtrar detalles de dominio ni de
infraestructura hacia el exterior (y viceversa).

## 4. Alcance
1. Nuevo paquete `src/solicitudes_partner/api/` (adaptador primario, al mismo nivel que
   `dominio/aplicacion/infraestructura/config`):
   - `app.py`: factory de la aplicacion FastAPI (`crear_app()`).
   - `esquemas.py`: modelos Pydantic de request/response (DTOs HTTP, separados de los DTOs de
     aplicacion).
   - `dependencias.py`: construye la composicion (servicio/consultas/relay) una vez al iniciar la
     app y la expone via `Depends()`.
   - `rutas_solicitudes_partner.py`: router con los endpoints.
   - `manejo_errores.py`: exception handlers que traducen excepciones de dominio a codigos HTTP.
2. Endpoints propuestos:
   - `POST /solicitudes-partner` -> registra una solicitud (comando). Responde 201 con
     `solicitud_id`, `estado` (post-reglas, ya resuelto sincronamente).
   - `GET /solicitudes-partner/{solicitud_id}` -> `ConsultasSolicitudesPartner.consultar_vista()`
     (Read Model). Responde 200 con la vista completa o 404 si no existe.
   - `GET /solicitudes-partner?partner_id=...` -> `listar_por_partner()`. Responde 200 con lista
     (vacia si no hay resultados).
3. Mapeo de errores de dominio a HTTP:
   - `ValueObjectInvalidoError` -> 400 Bad Request
   - `SolicitudDuplicadaError` -> 409 Conflict
   - `SolicitudNoEncontradaError` -> 404 Not Found
   - `TransicionEstadoInvalidaError` -> 409 Conflict
   - Cualquier otro error no controlado -> 500 (sin exponer detalles internos en el body)
4. Composicion usada en tiempo de ejecucion: PostgreSQL completa (comando + Read Model + Outbox),
   via `crear_servicio_consultas_y_relay_outbox_postgres(crear_conexion())`, construida una sola
   vez al levantar la app (no por request). Ver Duda 2 sobre configurabilidad memoria/Postgres.
5. Dependencia nueva: `fastapi` + `uvicorn` como extra opcional `api` en `pyproject.toml` (no se
   agregan a las dependencias base, igual criterio que el extra `postgres`).
6. Pruebas con `TestClient` (FastAPI) contra la composicion en memoria (rapidas, sin PostgreSQL):
   registrar + consultar + listar + duplicado (409) + no encontrado (404) + payload invalido (400).
7. Pruebas de integracion opcionales contra la composicion PostgreSQL real (mismo patron
   skip-si-no-hay-DB que el resto de `tests/integration`).
8. Documentacion en `README.md`: como levantar la API (`uvicorn`) y ejemplos de uso con `curl`.

## 5. Fuera de alcance (explicito)
- Autenticacion/autorizacion (API keys, OAuth, JWT).
- Versionado de API (`/v1/...`), rate limiting, CORS especifico.
- Endpoint HTTP para disparar `RelayOutbox.publicar_pendientes()` manualmente (ver Duda 3: puede
  agregarse como endpoint administrativo simple si lo quieres, pero no es obligatorio para "API
  REST" del servicio de negocio).
- Despliegue (Dockerfile de la API, orquestacion, Nginx, etc.).
- Cambios en dominio, aplicacion (comandos/consultas/servicios existentes), infraestructura de
  persistencia u Outbox.
- Documentacion OpenAPI custom mas alla de la que FastAPI genera automaticamente.
- Websockets, GraphQL, gRPC u otro protocolo distinto a REST/HTTP.

## 6. Arquitectura propuesta

```
Cliente HTTP
    |
    v
api/rutas_solicitudes_partner.py (adaptador primario)
    |
    +--> ServicioSolicitudesPartner.registrar_solicitud(RegistrarSolicitudPartner)
    |        -> Captura -> guardar (+ outbox si Postgres) -> Reglas -> ResultadoReglas -> Seguimiento
    |                                                                -> ProyeccionSolicitudesPartner
    |
    +--> ConsultasSolicitudesPartner.consultar_vista() / listar_por_partner()
             -> RepositorioLecturaSolicitudesPartner (Read Model, Fase 4)

api/manejo_errores.py: traduce excepciones de dominio -> respuestas HTTP
api/esquemas.py: Pydantic <-> comandos/consultas/vistas de aplicacion (sin logica de negocio)
```

## 7. Contrato HTTP propuesto (resumen)

### POST /solicitudes-partner
Request:
```json
{
  "solicitud_id": "sol-1",
  "partner_id": "partner-1",
  "referencia_externa": "REF-1",
  "tipo_servicio": "electricidad"
}
```
Response 201:
```json
{ "solicitud_id": "sol-1", "estado": "LISTA_PARA_ATENCION" }
```

### GET /solicitudes-partner/{solicitud_id}
Response 200:
```json
{
  "solicitud_id": "sol-1",
  "partner_id": "partner-1",
  "referencia_externa": "REF-1",
  "tipo_servicio": "electricidad",
  "estado": "LISTA_PARA_ATENCION"
}
```
Response 404: `{ "detalle": "No existe solicitud para el id consultado" }`

### GET /solicitudes-partner?partner_id=partner-1
Response 200: lista de objetos con el mismo shape que el GET por id (puede ser vacia `[]`).

## 8. Archivos que se crearian/modificarian (propuesta, sujeta a aprobacion)

Crear:
1. `src/solicitudes_partner/api/__init__.py`
2. `src/solicitudes_partner/api/app.py`
3. `src/solicitudes_partner/api/esquemas.py`
4. `src/solicitudes_partner/api/dependencias.py`
5. `src/solicitudes_partner/api/rutas_solicitudes_partner.py`
6. `src/solicitudes_partner/api/manejo_errores.py`
7. `tests/unit/api/test_rutas_solicitudes_partner.py`
8. `tests/integration/api/test_api_postgres.py` (opcional, skip-si-no-hay-DB)
9. Este documento y su `docs/ai/12-revision-fase-5.md` al cierre.

Modificar:
10. `pyproject.toml` - extra opcional `api` con `fastapi` + `uvicorn`.
11. `README.md` - como levantar y usar la API.

No se propone modificar:
- `src/solicitudes_partner/dominio/*`
- `src/solicitudes_partner/aplicacion/*` (ningun archivo existente)
- `src/solicitudes_partner/infraestructura/*`
- `src/solicitudes_partner/config/bootstrap.py`
- Tests existentes (deben seguir pasando sin cambios).

## 9. Dudas (mi recomendacion entre parentesis)
1. ¿FastAPI + Uvicorn te parece bien, o prefieres otro framework (Flask, Django REST)?
   (Recomiendo FastAPI: tipado con Pydantic, valida requests automaticamente, genera OpenAPI/Swagger
   gratis, encaja natural con el estilo de puertos/DTOs ya usado en el proyecto).
2. ¿La API corre siempre contra PostgreSQL (composicion completa de Fase 4), o quieres poder
   levantarla tambien contra la composicion en memoria (por ejemplo via una variable de entorno
   `SOLICITUDES_PARTNER_BACKEND=memoria|postgres`)? (Recomiendo: por defecto Postgres para uso real,
   ya que docker-compose ya lo provee; agregar el flag de entorno es trivial y util para demos sin
   Docker, lo incluyo si te sirve).
3. ¿Agrego un endpoint administrativo `POST /admin/outbox/publicar-pendientes` que invoque
   `RelayOutbox.publicar_pendientes()`? (Opcional; sin el, seguirias invocandolo solo desde Python
   como hasta ahora. Recomiendo agregarlo, es minimo y da una forma real de "integracion" del
   Outbox via HTTP).
4. ¿Necesitas algun endpoint adicional ya identificado (ej. cambiar estado manualmente, cancelar,
   etc.), o con Crear + Consultar + Listar alcanza para esta fase?

Si no tienes objeciones a las recomendaciones, procedo a implementar tal como esta descrito
(FastAPI, Postgres por defecto + flag de entorno para memoria, endpoint admin de outbox incluido).
