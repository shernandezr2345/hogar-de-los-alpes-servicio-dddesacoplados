# Revision Bloque 2.4

## Objetivo
Validar el cierre formal del Bloque 2.4: incorporacion de persistencia real con PostgreSQL para el Aggregate Root SolicitudPartner, manteniendo DDD, arquitectura hexagonal y el flujo de eventos ya aprobado en el Bloque 2.3.

## Arquitectura implementada
Se mantuvo el modelo por capas ya usado en el proyecto y se agrego un adaptador nuevo sin tocar el puerto:

- Dominio: sin cambios. Aggregate SolicitudPartner, Value Objects, Domain Events y el puerto `RepositorioSolicitudesPartner` permanecen exactamente igual que en Bloque 2.3.
- Aplicacion: sin cambios de comportamiento. Sigue dependiendo unicamente del puerto de repositorio, no de una implementacion concreta.
- Infraestructura: se agrego `RepositorioSolicitudesPartnerPostgres` (adaptador PostgreSQL) junto a `db_conexion.py` (construccion de conexion via variables de entorno). `RepositorioSolicitudesPartnerMemoria` y `EventBusMemoria` no se modificaron.
- Configuracion: `bootstrap.py` se refactorizo internamente (`_construir_servicio`) sin cambiar la firma ni el comportamiento de `crear_servicio_solicitudes_partner()`. Se agrego `crear_servicio_solicitudes_partner_postgres(conexion)` como composicion explicita y separada; no hay seleccion automatica por variables de entorno.

Diagrama conceptual cumplido:

Aplicacion -> RepositorioSolicitudesPartner (PUERTO) -> RepositorioSolicitudesPartnerPostgres (ADAPTADOR) -> psycopg -> PostgreSQL

## Flujo de eventos
El flujo de eventos del Bloque 2.3 no fue alterado:

RegistrarSolicitudPartner -> Captura -> SolicitudPartnerRegistrada -> Reglas de Partner -> ReglasDePartnerEvaluadas -> HandlerResultadoReglas -> Aggregate -> SolicitudPartnerListaParaAtencion / SolicitudPartnerRechazada -> Seguimiento.

La unica diferencia posible en este flujo es la implementacion concreta del repositorio inyectada en `_construir_servicio` (memoria o PostgreSQL); la logica de negocio y el encadenamiento de eventos permanecen identicos.

## Desacoplamiento
- El dominio no importa `psycopg` ni conoce PostgreSQL.
- La aplicacion sigue dependiendo exclusivamente de `RepositorioSolicitudesPartner` (puerto).
- El adaptador PostgreSQL traduce entre Aggregate/Value Objects y filas de la tabla `solicitudes_partner`.
- Unicamente `psycopg.errors.UniqueViolation` se traduce a `SolicitudDuplicadaError` (excepcion de dominio ya existente); otros errores tecnicos no se ocultan ni se traducen artificialmente.
- `bootstrap.py` mantiene ambas composiciones (memoria y PostgreSQL) totalmente separadas; no existe activacion implicita por presencia/ausencia de variables de entorno.

## Pruebas

### Suite unitaria (sin PostgreSQL)
Comando:

python -m pytest -q

Resultado:

sssss.....................                                               [100%]
21 passed, 5 skipped in 0.92s

Los 21 tests unitarios de Fase 1, Bloque 2.1, Bloque 2.2 y Bloque 2.3 continuan pasando sin requerir PostgreSQL. Los 5 tests de integracion se omiten automaticamente (skip) cuando no hay conexion disponible, sin generar fallos.

### Pruebas de integracion (con PostgreSQL disponible)
Ejecutadas previamente contra un contenedor PostgreSQL real, con resultado:

.....                                                                    [100%]
5 passed in 0.89s

Cobertura validada:
1. Guardar una SolicitudPartner.
2. Recuperar por solicitud_id.
3. Verificar existe_por_partner_y_referencia.
4. Verificar la restriccion UNIQUE (partner_id, referencia_externa).
5. Validar el mapeo entre PostgreSQL y el Aggregate/Value Objects.

### Verificacion de la restriccion UNIQUE
Confirmada directamente en el catalogo de PostgreSQL:

Indexes:
    "solicitudes_partner_pkey" PRIMARY KEY, btree (solicitud_id)
    "solicitudes_partner_partner_id_referencia_externa_key" UNIQUE CONSTRAINT, btree (partner_id, referencia_externa)

## Decisiones
1. Se uso psycopg (driver directo) en lugar de ORM, segun aprobacion explicita, para mantener el adaptador simple y minimo.
2. El esquema se definio mediante un script SQL simple (`db/schema.sql`), sin herramienta de migraciones, segun aprobacion.
3. `guardar` implementa upsert por `solicitud_id` (`INSERT ... ON CONFLICT (solicitud_id) DO UPDATE`), cubriendo tanto creacion como transiciones de estado con una unica operacion, sin duplicar reglas de negocio en el adaptador.
4. Solo se traduce `UniqueViolation` a `SolicitudDuplicadaError`; otros errores tecnicos de psycopg se dejan propagar, evitando inventar abstracciones de error no solicitadas.
5. La conexion se crea con `autocommit=True` para mantener el adaptador simple, sin gestion manual de transacciones.
6. El bootstrap para PostgreSQL usa import perezoso de `repositorio_postgres`, de modo que el flujo por defecto (memoria) no requiere `psycopg` instalado.
7. Se agrego Docker Compose minimo, exclusivamente para levantar PostgreSQL local, sin contenedores adicionales de aplicacion, workers ni brokers.
8. Se ajusto `.gitignore` para no ignorar `.env.example`, permitiendo que quede versionable como plantilla sin exponer secretos reales.

## Alcance deliberadamente excluido
No implementado en este bloque, segun lo aprobado:
- Transactional Outbox
- Kafka
- RabbitMQ
- CQRS
- Read Model persistente
- Event Sourcing
- Docker complejo/orquestacion productiva (solo PostgreSQL minimo para desarrollo/pruebas)
- nuevos microservicios
- Saga
- funcionalidades adicionales de negocio
- cambios en reglas o invariantes del dominio
- cambios en el flujo de eventos aprobado en Bloque 2.3
- reemplazo de EventBusMemoria
- columnas de auditoria (created_at/updated_at) en la tabla solicitudes_partner
- seleccion automatica de repositorio por variables de entorno en el bootstrap usado por los tests

## Resultado
**APROBADO**
