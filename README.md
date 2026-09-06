# hogar-de-los-alpes-servicio-dddesacoplados

Servicio de **Entrada de Solicitudes de Partner**, implementado con DDD tactico (Aggregate,
Value Objects, Domain Events) y arquitectura hexagonal (dominio/aplicacion/infraestructura/config),
sobre un flujo interno guiado por eventos (`EventBus`). Fases implementadas:

1. **Fase 1-2**: Aggregate `SolicitudPartner`, comando de registro, reglas de partner y
   seguimiento, comunicados por eventos de dominio.
2. **Fase 3 (Bloque 2.4/2.5)**: Persistencia PostgreSQL + Transactional Outbox para entrega
   confiable de eventos.
3. **Fase 4**: CQRS + Read Model (`solicitudes_partner_vista`) proyectado por eventos.
4. **Fase 5**: API REST (FastAPI) sobre las fases anteriores, sin logica de negocio propia.

## Instalacion

1. Crear y activar un entorno virtual.
2. Instalar el proyecto en modo editable:

```bash
pip install -e .
```

## Ejecutar pruebas

```bash
python -m pytest -q
```

## Persistencia PostgreSQL (Bloque 2.4)

El puerto `RepositorioSolicitudesPartner` tiene dos implementaciones:
- `RepositorioSolicitudesPartnerMemoria` (usada por `crear_servicio_solicitudes_partner()`, sin dependencias externas, para tests unitarios).
- `RepositorioSolicitudesPartnerPostgres` (adaptador real, usado explicitamente via `crear_servicio_solicitudes_partner_postgres(conexion)`).

### Variables de entorno

```
DB_HOST
DB_PORT
DB_NAME
DB_USER
DB_PASSWORD
```

Ver ejemplo en `.env.example`.

### Levantar PostgreSQL localmente

```bash
docker compose up -d
```

Esto expone PostgreSQL en el puerto configurado (por defecto 5432) y crea la tabla `solicitudes_partner` a partir de `db/schema.sql`.

### Instalar dependencias para PostgreSQL

```bash
pip install -e ".[postgres]"
```

### Ejecutar pruebas de integracion

Con PostgreSQL levantado (`docker compose up -d`) y las variables de entorno exportadas:

```bash
python -m pytest tests/integration -q
```

Si `psycopg` no esta instalado o PostgreSQL no esta disponible, estas pruebas se omiten (skip) de forma explicita y no afectan la suite unitaria.

## Transactional Outbox (Bloque 2.5)

`RepositorioSolicitudesPartnerPostgres.guardar()` persiste el agregado y sus eventos de dominio
pendientes (`SolicitudPartnerRegistrada`, `SolicitudPartnerListaParaAtencion`, `SolicitudPartnerRechazada`)
en una unica transaccion PostgreSQL: upsert en `solicitudes_partner` + insert en `outbox_eventos`.
Esto garantiza que nunca se pierda un evento por una caida entre "guardar" y "publicar".

El flujo interno de eventos (Reglas -> ResultadoReglas -> Seguimiento) no cambia: sigue siendo
sincrono via `EventBusMemoria`, tal como en el Bloque 2.3/2.4.

Para publicar de forma confiable los eventos ya persistidos en el outbox (por ejemplo hacia un
futuro broker externo), se usa `RelayOutbox`:

```python
from solicitudes_partner.config.bootstrap import crear_servicio_y_relay_outbox_postgres
from solicitudes_partner.infraestructura.db_conexion import crear_conexion

servicio, relay = crear_servicio_y_relay_outbox_postgres(crear_conexion())
servicio.registrar_solicitud(...)

relay.publicar_pendientes()  # drena outbox_eventos, publica y marca procesado_en
```

`relay.publicar_pendientes()` es invocado explicitamente (no hay scheduler ni proceso en segundo
plano en este bloque); retorna cuantos eventos publico. Los eventos ya marcados con `procesado_en`
no se vuelven a publicar.

`RelayOutbox` publica en un `EventBus` **externo**, separado del `EventBus` **interno** que usa
`ServicioSolicitudesPartner` para Reglas/ResultadoReglas/Seguimiento/Proyeccion. Esto evita que
drenar el outbox vuelva a disparar el flujo de negocio interno sobre una solicitud que ya lo
completo de forma sincrona al registrarse.

## CQRS + Read Model (Fase 4)

Se agrego un modelo de lectura separado del modelo de escritura, siguiendo CQRS:

- Puerto `RepositorioLecturaSolicitudesPartner` (`aplicacion/puertos_lectura.py`), con adaptadores
  `RepositorioLecturaSolicitudesPartnerMemoria` (tests) y `RepositorioLecturaSolicitudesPartnerPostgres`
  (tabla `solicitudes_partner_vista`).
- `ProyeccionSolicitudesPartner` (aplicacion): se suscribe a los mismos eventos del agregado que
  `SeguimientoSolicitudes` y actualiza el Read Model. Como los eventos de transicion no cargan todos
  los campos, lee el estado ya persistido del repositorio de escritura (sin modificarlo) para armar
  la vista completa; esto no cambia el contrato de los eventos de dominio.
- `ConsultasSolicitudesPartner` (aplicacion): servicio de consulta que **solo** usa el puerto de
  lectura, nunca el repositorio de escritura. `ServicioSolicitudesPartner.consultar_estado()` se
  mantiene sin cambios como via alternativa simple sobre el modelo de escritura.

Composicion en memoria (para tests/desarrollo):

```python
from solicitudes_partner.config.bootstrap import crear_servicio_y_consultas_solicitudes_partner

servicio, consultas = crear_servicio_y_consultas_solicitudes_partner()
```

Composicion PostgreSQL completa (comando + Read Model + Outbox):

```python
from solicitudes_partner.config.bootstrap import crear_servicio_consultas_y_relay_outbox_postgres
from solicitudes_partner.infraestructura.db_conexion import crear_conexion

servicio, consultas, relay = crear_servicio_consultas_y_relay_outbox_postgres(crear_conexion())
```

## API REST (Fase 5)

Adaptador primario HTTP (`src/solicitudes_partner/api/`), construido con FastAPI. Reutiliza tal
cual el comando y las consultas de las fases anteriores; no agrega logica de negocio.

Instalacion del extra:

```bash
pip install -e ".[postgres,api]"
```

Levantar la API (por defecto usa la composicion PostgreSQL completa, requiere PostgreSQL
disponible via las variables de entorno de `DB_HOST`/`DB_PORT`/`DB_NAME`/`DB_USER`/`DB_PASSWORD`):

```bash
uvicorn solicitudes_partner.api.app:app --reload
```

Para levantarla contra la composicion en memoria (sin PostgreSQL, util para demos rapidas):

```bash
# PowerShell
$env:SOLICITUDES_PARTNER_BACKEND = "memoria"
uvicorn solicitudes_partner.api.app:app --reload
```

Endpoints:

- `POST /solicitudes-partner` - registra una solicitud. Responde 201 con `solicitud_id` y `estado`
  (ya resuelto, tras Reglas/ResultadoReglas sincronos).
- `GET /solicitudes-partner/{solicitud_id}` - consulta la vista completa (Read Model). 404 si no
  existe.
- `GET /solicitudes-partner?partner_id=...` - lista las vistas de un partner (lista vacia si no
  hay resultados).
- `POST /admin/outbox/publicar-pendientes` - drena el Outbox pendiente via `RelayOutbox`. 501 si
  la composicion activa es la de memoria (no tiene Outbox).

Ejemplo:

```bash
curl -X POST http://localhost:8000/solicitudes-partner \
  -H "Content-Type: application/json" \
  -d '{"solicitud_id": "sol-1", "partner_id": "partner-1", "referencia_externa": "REF-1", "tipo_servicio": "electricidad"}'

curl http://localhost:8000/solicitudes-partner/sol-1
```

Errores de dominio mapeados a HTTP: `ValueObjectInvalidoError` -> 400,
`SolicitudDuplicadaError`/`TransicionEstadoInvalidaError` -> 409, `SolicitudNoEncontradaError` -> 404.

Documentacion interactiva autogenerada por FastAPI disponible en `/docs` (Swagger UI) y
`/redoc` una vez levantada la API.

### Coleccion de Postman

En `postman/` hay una coleccion (`hogar-de-los-alpes-solicitudes-partner.postman_collection.json`)
y un environment (`hogar-de-los-alpes-local.postman_environment.json`) listos para importar, con
pruebas para los 6 casos principales (201, 200 consulta, 200 lista, 409 duplicada, 404 no
encontrada, 400 invalida) y el endpoint admin del Outbox.

