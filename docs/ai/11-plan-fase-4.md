# Plan Fase 4 - CQRS + Query + Read Model

## Estado
Plan propuesto. Pendiente de aprobacion. No se ha modificado codigo.

## 1. Objetivo
Introducir un modelo de lectura (Read Model) separado del modelo de escritura para
`SolicitudPartner`, alimentado por los eventos de dominio ya existentes, sin alterar el agregado,
el flujo de eventos, ni el Outbox aprobados en Fases 1-3.

## 2. Estado actual (verificado en el repositorio)
1. La unica consulta hoy es `ConsultarEstadoSolicitudPartner` (`aplicacion/consultas.py`), resuelta
   en `ServicioSolicitudesPartner.consultar_estado()` leyendo **directamente el repositorio de
   escritura** (`RepositorioSolicitudesPartner.obtener_por_id`). Esto no es CQRS real: comando y
   consulta comparten el mismo modelo/tabla (`solicitudes_partner`).
2. Los eventos del agregado (`SolicitudPartnerRegistrada`, `SolicitudPartnerListaParaAtencion`,
   `SolicitudPartnerRechazada`) ya se publican sincronamente en el `EventBus` desde
   `captura.py` y `resultado_reglas.py`, y ademas (Bloque 2.5) se persisten en `outbox_eventos`
   para entrega confiable.
3. `SeguimientoSolicitudes` ya demuestra el patron de "otro suscriptor mas" del mismo `EventBus`,
   sin tocar la orquestacion de comando existente.
4. No existe hoy ninguna tabla/estructura de lectura separada, ni puerto de consulta desacoplado
   del puerto de repositorio de escritura.

## 3. Problema que resuelve
Hoy toda consulta pasa por el mismo agregado/tabla que las escrituras, acoplando lectura y
escritura al mismo esquema y a las mismas reglas de invariantes. CQRS separa ambos modelos: el
lado de escritura sigue protegido por el Aggregate Root; el lado de lectura se optimiza para
consulta (proyeccion denormalizada), se actualiza de forma reactiva a partir de los eventos ya
emitidos, y podra evolucionar independientemente (por ejemplo, en Fase 5, servir directamente al
API REST sin pasar por el agregado).

## 4. Alcance
1. Nuevo Read Model: `VistaSolicitudPartner` (DTO de lectura) con los campos utiles para consulta:
   `solicitud_id`, `partner_id`, `referencia_externa`, `tipo_servicio`, `estado`.
2. Nuevo puerto de consulta en la capa de **aplicacion** (no en dominio, porque no protege
   invariantes, solo sirve lectura): `RepositorioLecturaSolicitudesPartner` con métodos
   `obtener_por_id(solicitud_id)` y `listar_por_partner(partner_id)`.
3. Dos adaptadores, simetricos a los del repositorio de escritura:
   - `RepositorioLecturaSolicitudesPartnerMemoria` (dict en memoria, para tests unitarios).
   - `RepositorioLecturaSolicitudesPartnerPostgres` (tabla de proyeccion `solicitudes_partner_vista`).
4. Nuevo proyector: `ProyeccionSolicitudesPartner`, handler que se suscribe a los mismos 3 eventos
   del agregado (igual que `SeguimientoSolicitudes`) y actualiza el Read Model (upsert) en cada
   evento. Se registra en `bootstrap.py` junto a los handlers existentes, sin modificar
   `captura.py` ni `resultado_reglas.py`.
5. Nuevo servicio de consulta: `ConsultasSolicitudesPartner` (aplicacion), que usa **unicamente**
   el puerto de lectura (nunca el repositorio de escritura). Se agrega una consulta nueva
   `ConsultarVistaSolicitudPartner` que retorna `VistaSolicitudPartner` completo (no solo el estado).
6. `ServicioSolicitudesPartner.consultar_estado()` **se mantiene tal cual** (no se elimina, no se
   modifica su comportamiento), para no romper contratos ni tests existentes; queda como consulta
   simple sobre el modelo de escritura, y `ConsultasSolicitudesPartner` como el nuevo camino CQRS.
7. Tabla de proyeccion en PostgreSQL: `solicitudes_partner_vista`, poblada solo por el proyector
   (nunca por el repositorio de escritura).
8. Pruebas unitarias del proyector y del servicio de consulta usando el Read Model en memoria.
9. Pruebas de integracion minimas contra PostgreSQL real (proyeccion se actualiza al publicar
   eventos, igual patron que `test_outbox.py`).

## 5. Fuera de alcance (explicito)
- Event Sourcing.
- API REST (Fase 5).
- Reconstruccion/replay de la proyeccion a partir del Outbox historico (se evaluara si hace falta
  en Fase 5; por ahora el proyector solo reacciona a eventos nuevos, igual que Seguimiento).
- Cambios en reglas o invariantes del dominio.
- Cambios en el Aggregate Root, en `RepositorioSolicitudesPartner` (puerto de escritura), ni en el
  Outbox/Relay del Bloque 2.5.
- Cache, paginacion avanzada o filtros complejos en la consulta.
- Eliminar o modificar `consultar_estado()` existente.

## 6. Arquitectura propuesta

```
Comando (sin cambios)
Aplicacion (Captura/ResultadoReglas) -> RepositorioSolicitudesPartner (PUERTO escritura)
                                      -> EventBus.publicar(evento)
                                             |
                                             +--> HandlerReglasPartner (sin cambios)
                                             +--> SeguimientoSolicitudes (sin cambios)
                                             +--> ProyeccionSolicitudesPartner (NUEVO)
                                                     |
                                                     v
                                     RepositorioLecturaSolicitudesPartner (PUERTO lectura, NUEVO)
                                                     |
                                                     v
                                   Memoria (tests) | Postgres: solicitudes_partner_vista

Consulta (nueva, CQRS real)
ConsultasSolicitudesPartner -> RepositorioLecturaSolicitudesPartner -> VistaSolicitudPartner
```

## 7. Modelo de datos propuesto
Tabla `solicitudes_partner_vista` (proyeccion, solo lectura desde el punto de vista del dominio):

| Columna              | Tipo         | Restriccion   |
|-----------------------|-------------|----------------|
| solicitud_id          | VARCHAR     | PRIMARY KEY    |
| partner_id            | VARCHAR     | NOT NULL       |
| referencia_externa    | VARCHAR     | NOT NULL       |
| tipo_servicio         | VARCHAR     | NOT NULL       |
| estado                | VARCHAR     | NOT NULL       |
| actualizado_en        | TIMESTAMPTZ | NOT NULL DEFAULT now() |

Se actualiza exclusivamente via upsert desde `ProyeccionSolicitudesPartner` (nunca desde el
repositorio de escritura).

## 8. Archivos que se crearian/modificarian (propuesta, sujeta a aprobacion)

Crear:
1. `src/solicitudes_partner/aplicacion/vistas.py` - DTO `VistaSolicitudPartner`.
2. `src/solicitudes_partner/aplicacion/puertos_lectura.py` - puerto `RepositorioLecturaSolicitudesPartner`.
3. `src/solicitudes_partner/aplicacion/modulos/proyeccion_solicitudes.py` - `ProyeccionSolicitudesPartner`.
4. `src/solicitudes_partner/aplicacion/consultas_lectura.py` (o ampliar `consultas.py`) -
   `ConsultarVistaSolicitudPartner` + servicio `ConsultasSolicitudesPartner`.
5. `src/solicitudes_partner/infraestructura/repositorio_lectura_memoria.py`.
6. `src/solicitudes_partner/infraestructura/repositorio_lectura_postgres.py`.
7. `tests/unit/solicitudes_partner/aplicacion/test_proyeccion_solicitudes.py` y
   `test_consultas_lectura.py`.
8. `tests/integration/solicitudes_partner/test_repositorio_lectura_postgres.py`.
9. Este documento y su `docs/ai/11-revision-fase-4.md` al cierre.

Modificar:
10. `db/schema.sql` - agregar tabla `solicitudes_partner_vista`.
11. `src/solicitudes_partner/config/bootstrap.py` - registrar `ProyeccionSolicitudesPartner` como
    suscriptor adicional y exponer `ConsultasSolicitudesPartner` en la composicion (memoria y
    Postgres).
12. `README.md` - documentar el Read Model y la consulta CQRS.

No se propone modificar:
- `src/solicitudes_partner/dominio/*`
- `src/solicitudes_partner/aplicacion/servicios.py` (se mantiene `consultar_estado()` igual)
- `src/solicitudes_partner/aplicacion/modulos/captura.py`, `reglas_partner.py`, `resultado_reglas.py`
- `src/solicitudes_partner/infraestructura/repositorio_memoria.py`,
  `repositorio_postgres.py`, `relay_outbox.py`, `event_bus_memoria.py`
- Tests existentes (deben seguir pasando sin cambios).

## 9. Dudas (mi recomendacion entre parentesis; avisame si prefieres otra cosa)
1. ¿El puerto de lectura va en `aplicacion/puertos_lectura.py` como propongo, o prefieres que viva
   junto al puerto de escritura en `dominio/repositorios.py`? (Recomiendo aplicacion: el read model
   no protege invariantes de negocio, es un detalle de consulta).
2. ¿La proyeccion reacciona solo a eventos nuevos via `EventBus` (igual que Seguimiento), o
   necesitas tambien un mecanismo de "reconstruir toda la vista desde cero" leyendo
   `solicitudes_partner` completa? (Recomiendo solo reaccion a eventos por ahora; reconstruccion
   completa la dejaria para si surge la necesidad real en Fase 5).
3. ¿Alcanza con `obtener_por_id` y `listar_por_partner` en el puerto de lectura, o necesitas alguna
   consulta adicional ya identificada (ej. listar por estado)? (Recomiendo esas dos por ahora, se
   pueden agregar mas sin romper nada).

Si no tienes objeciones a las recomendaciones, procedo a implementar tal como esta descrito.
