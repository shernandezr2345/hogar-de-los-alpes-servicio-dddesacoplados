# Plan Bloque 2.4 - Persistencia real con PostgreSQL

## Estado
Plan propuesto. Pendiente de aprobacion. No se ha modificado codigo.

## 1. Objetivo
Incorporar persistencia real con PostgreSQL para el Aggregate Root SolicitudPartner, manteniendo DDD y arquitectura hexagonal, sin alterar el flujo de eventos ya aprobado en Bloque 2.3.

## 2. Estado actual (verificado en el repositorio)
Revision directa de archivos existentes:

1. Puerto de dominio ya definido:
   - src/solicitudes_partner/dominio/repositorios.py
   - Clase RepositorioSolicitudesPartner (ABC) con:
     - guardar(solicitud)
     - obtener_por_id(solicitud_id)
     - existe_por_partner_y_referencia(partner_id, referencia_externa)

2. Adaptador en memoria ya implementado:
   - src/solicitudes_partner/infraestructura/repositorio_memoria.py
   - Clase RepositorioSolicitudesPartnerMemoria
   - Usa diccionario en memoria y set de indice (partner_id, referencia_externa)

3. Composition root actual:
   - src/solicitudes_partner/config/bootstrap.py
   - Instancia RepositorioSolicitudesPartnerMemoria + EventBusMemoria
   - Registra handlers de Reglas, Resultado y Seguimiento (Bloque 2.3)

4. Empaquetado del proyecto:
   - pyproject.toml
   - Usa setuptools, layout src/, pytest con testpaths=["tests"]
   - No existen dependencias de PostgreSQL declaradas (no hay psycopg2, no hay SQLAlchemy)

5. No existe:
   - requirements.txt en la raiz del servicio
   - Dockerfile ni docker-compose
   - Cualquier adaptador PostgreSQL previo

6. Tests existentes:
   - tests/unit/solicitudes_partner/dominio
   - tests/unit/solicitudes_partner/aplicacion
   - tests/unit/solicitudes_partner/infraestructura
   - Suite actual: 21 pruebas pasando (segun ultima ejecucion registrada)

7. Bloque 2.3 aprobado y documentado en:
   - docs/ai/08-plan-bloque-2.3.md
   - docs/ai/09-revision-bloque-2.3.md

## 3. Problema que resuelve el bloque
El curso exige un motor de base de datos real (PostgreSQL). Actualmente la unica persistencia es en memoria, valida para pruebas pero no aceptable como entrega final. Se requiere una implementacion concreta que:
- persista el agregado de forma durable;
- refuerce en base de datos la regla de no duplicidad partner_id + referencia_externa;
- mantenga el dominio libre de detalles de infraestructura.

## 4. Alcance
Incluye:
1. Mantener RepositorioSolicitudesPartner como puerto (sin cambios de contrato).
2. Crear adaptador concreto RepositorioSolicitudesPartnerPostgres en infraestructura.
3. Definir tabla solicitudes_partner con columnas minimas:
   - solicitud_id
   - partner_id
   - referencia_externa
   - tipo_servicio
   - estado
4. Restriccion UNIQUE sobre (partner_id, referencia_externa).
5. Mantener RepositorioSolicitudesPartnerMemoria para pruebas unitarias sin cambios de comportamiento.
6. Permitir que bootstrap real use PostgreSQL mediante configuracion (variables de entorno), sin romper el bootstrap usado por tests unitarios.
7. Definir estrategia de conexion via variables de entorno.
8. Definir como levantar PostgreSQL local para desarrollo/pruebas.
9. Definir pruebas de integracion minimas contra PostgreSQL (marcadas para no ejecutarse en la suite unitaria por defecto).
10. Mantener separacion dominio/aplicacion/infraestructura/configuracion.
11. Mantener Dependency Inversion: aplicacion y dominio dependen del puerto; infraestructura implementa.

## 5. Fuera de alcance (explicito)
No se implementa en este bloque:
- Transactional Outbox
- Kafka
- RabbitMQ
- CQRS
- Read Model persistente
- Event Sourcing
- Docker complejo (solo lo minimo para levantar PostgreSQL local, si se aprueba)
- nuevos microservicios
- Saga
- funcionalidades adicionales de negocio
- cambios en reglas o invariantes del dominio
- cambios en el flujo de eventos de Bloque 2.3
- reemplazo de EventBusMemoria (se mantiene)

## 6. Arquitectura propuesta
Se mantiene el modelo por capas ya usado en el proyecto:

Dominio
- Aggregate SolicitudPartner
- Value Objects
- Domain Events
- Puerto RepositorioSolicitudesPartner (sin cambios)

Aplicacion
- Casos de uso actuales (Captura, Reglas, ResultadoReglas, Seguimiento)
- Depende del puerto de repositorio, no de su implementacion

Infraestructura
- EventBusMemoria (sin cambios)
- RepositorioSolicitudesPartnerMemoria (sin cambios, para tests)
- RepositorioSolicitudesPartnerPostgres (nuevo adaptador)
- Acceso a datos (driver/DBAPI o SQLAlchemy Core, a decidir con el usuario)

Configuracion
- bootstrap.py ampliado para seleccionar implementacion segun entorno (memoria vs PostgreSQL)

Diagrama conceptual (igual al solicitado):

Aplicacion
    |
    v
RepositorioSolicitudesPartner (PUERTO)
    |
    v
RepositorioSolicitudesPartnerPostgres (ADAPTADOR)
    |
    v
PostgreSQL

## 7. Archivos que se crearian/modificarian (propuesta, sujeta a aprobacion)

Crear:
1. src/solicitudes_partner/infraestructura/repositorio_postgres.py
   - Adaptador concreto que implementa RepositorioSolicitudesPartner contra PostgreSQL.

2. src/solicitudes_partner/infraestructura/db_conexion.py
   - Modulo responsable de construir la conexion/engine a partir de variables de entorno.

3. src/solicitudes_partner/infraestructura/esquema_sql.py o migrations/001_solicitudes_partner.sql
   - Definicion de la tabla solicitudes_partner y restriccion UNIQUE.
   - A decidir: script SQL plano vs migraciones con herramienta (ver Dudas).

4. docs/ai/09-plan-bloque-2.4.md
   - Este documento.

5. tests/integration/solicitudes_partner/test_repositorio_postgres.py
   - Pruebas de integracion minimas contra PostgreSQL real, ejecutables solo si hay conexion disponible (marcadas/omitidas por defecto).

6. .env.example (en la raiz del servicio)
   - Ejemplo de variables de entorno requeridas para conexion a PostgreSQL, sin valores sensibles reales.

Modificar:
7. src/solicitudes_partner/config/bootstrap.py
   - Agregar funcion o parametro para seleccionar repositorio (memoria vs PostgreSQL) segun configuracion/entorno.
   - No romper la funcion actual usada por los tests.

8. pyproject.toml
   - Agregar dependencia de driver/libreria de PostgreSQL (a definir, ver Dudas).

9. README.md
   - Documentar variables de entorno y como levantar PostgreSQL local para desarrollo.

No se propone modificar:
- src/solicitudes_partner/dominio/* (ningun archivo)
- src/solicitudes_partner/aplicacion/modulos/* (sin cambios de comportamiento)
- src/solicitudes_partner/infraestructura/repositorio_memoria.py
- src/solicitudes_partner/infraestructura/event_bus_memoria.py
- tests/unit/* (deben seguir pasando sin PostgreSQL)

## 8. Modelo de datos
Tabla propuesta: solicitudes_partner

| Columna              | Tipo sugerido      | Restriccion                              |
|----------------------|--------------------|-------------------------------------------|
| solicitud_id         | TEXT / VARCHAR     | PRIMARY KEY                               |
| partner_id           | TEXT / VARCHAR     | NOT NULL                                  |
| referencia_externa   | TEXT / VARCHAR     | NOT NULL                                  |
| tipo_servicio        | TEXT / VARCHAR     | NOT NULL                                  |
| estado               | TEXT / VARCHAR     | NOT NULL                                  |

Restriccion adicional:
- UNIQUE (partner_id, referencia_externa)

Esta restriccion refuerza en base de datos la regla de dominio de no duplicidad ya validada en el agregado y en el servicio de aplicacion.

## 9. Puerto y adaptador de persistencia
Puerto (sin cambios):
- RepositorioSolicitudesPartner en src/solicitudes_partner/dominio/repositorios.py

Adaptador nuevo (propuesto):
- RepositorioSolicitudesPartnerPostgres en src/solicitudes_partner/infraestructura/repositorio_postgres.py
- Debe implementar exactamente los 3 metodos del puerto:
  - guardar
  - obtener_por_id
  - existe_por_partner_y_referencia
- Debe traducir entre Value Objects/Aggregate del dominio y filas de la tabla solicitudes_partner.
- No debe filtrar tipos de infraestructura (por ejemplo, excepciones especificas del driver) hacia el dominio; deben traducirse a excepciones de dominio existentes cuando aplique (por ejemplo, violacion de UNIQUE -> SolicitudDuplicadaError si corresponde a esa ruta de uso).

## 10. Configuracion de PostgreSQL
Estrategia propuesta:
1. Variables de entorno para conexion:
   - DB_HOST
   - DB_PORT
   - DB_NAME
   - DB_USER
   - DB_PASSWORD
2. Estas variables se leen en db_conexion.py para construir la cadena de conexion.
3. Para desarrollo local se documentaria en README.md el comando para levantar PostgreSQL (por ejemplo, un contenedor simple), pero sin introducir orquestacion compleja (fuera de alcance segun restricciones).
4. El bootstrap de ejecucion real usaria estas variables para instanciar RepositorioSolicitudesPartnerPostgres; el bootstrap de tests unitarios seguiria usando RepositorioSolicitudesPartnerMemoria sin requerir configuracion de entorno.

## 11. Estrategia de pruebas
1. Tests unitarios (no cambian):
   - Siguen usando RepositorioSolicitudesPartnerMemoria.
   - No requieren PostgreSQL ni variables de entorno.
2. Tests de integracion (nuevos, minimos):
   - Verifican que RepositorioSolicitudesPartnerPostgres cumple el contrato del puerto:
     - guardar y obtener_por_id devuelven el mismo agregado (por campos).
     - existe_por_partner_y_referencia refleja el estado real de la tabla.
     - intentar violar la restriccion UNIQUE resulta en el comportamiento esperado.
   - Se ejecutan solo si hay PostgreSQL disponible (por variable de entorno o marcador de pytest), para no romper el pipeline sin base de datos.

## 12. Impacto sobre los tests existentes
- No se espera impacto funcional sobre los 21 tests actuales.
- Bootstrap actual usado por tests (si se usa directamente) no cambia su comportamiento por defecto.
- Se debe verificar, al implementar, que ningun test unitario importe o dependa transitivamente del modulo de conexion PostgreSQL de forma obligatoria.

## 13. Decisiones arquitectonicas
1. El puerto RepositorioSolicitudesPartner no cambia; solo se agrega un adaptador nuevo.
2. La restriccion de duplicidad se refuerza en dos niveles: dominio/aplicacion (ya existente) y base de datos (nueva), sin duplicar logica de negocio en el adaptador.
3. El bootstrap decide la implementacion concreta (memoria o PostgreSQL) segun contexto de ejecucion, manteniendo Dependency Inversion.
4. No se introduce ORM salvo que el usuario lo apruebe explicitamente (ver Dudas); por defecto se plantea uso de un driver/DBAPI directo para mantener el bloque minimo.

## 14. Trade-offs

Decision: Agregar UNIQUE (partner_id, referencia_externa) en PostgreSQL
- Punto de sensibilidad: la regla de duplicidad ya existe en aplicacion/dominio.
- Trade-off: se duplica la proteccion (aplicacion + base de datos), lo cual agrega una capa extra de validacion.
- Riesgo: si el adaptador no traduce bien el error de violacion UNIQUE, podria filtrarse una excepcion tecnica hacia capas superiores.
- Justificacion: el curso exige persistencia real; una restriccion a nivel de base de datos previene inconsistencia en escenarios de concurrencia que la validacion en memoria de aplicacion no cubre completamente.

Decision: Mantener RepositorioSolicitudesPartnerMemoria para tests unitarios
- Punto de sensibilidad: riesgo de tener dos implementaciones que diverjan en comportamiento.
- Trade-off: mayor cobertura de pruebas rapidas sin infraestructura, a cambio de mantener dos adaptadores.
- Riesgo: comportamiento no identico entre memoria y PostgreSQL si no se prueban con la misma bateria de casos.
- Justificacion: aporta a Mantenibilidad (tests rapidos, sin dependencias externas) y Resiliencia (aislar pruebas de fallos de infraestructura), consistente con los atributos de calidad de Entrega 2.

Decision: No introducir ORM en este bloque (a definir con el usuario)
- Punto de sensibilidad: elegir approach de acceso a datos.
- Trade-off: driver/DBAPI directo es mas simple y con menos dependencias, pero implica mas codigo manual de mapeo.
- Riesgo: mayor esfuerzo manual comparado con un ORM, aunque menor superficie de dependencia.
- Justificacion: mantiene el bloque minimo y evita introducir patrones/tecnologia no solicitada explicitamente; aporta a Mantenibilidad al mantener el adaptador simple y explicito.

Decision: Pruebas de integracion condicionadas a disponibilidad de PostgreSQL
- Punto de sensibilidad: no se quiere romper la suite si no hay base de datos disponible en el entorno de ejecucion.
- Trade-off: menor automatizacion continua de estas pruebas versus mantener estabilidad de la suite principal.
- Riesgo: posible falta de ejecucion regular de las pruebas de integracion si no se define un proceso claro.
- Justificacion: aporta a Mantenibilidad (tests unitarios estables) y prepara base para Escalabilidad/Resiliencia al validar la integracion real sin acoplar toda la suite a infraestructura externa.

## 15. Riesgos
1. Riesgo de fuga de excepciones tecnicas del driver hacia capas superiores si no se traduce correctamente.
2. Riesgo de divergencia de comportamiento entre RepositorioSolicitudesPartnerMemoria y RepositorioSolicitudesPartnerPostgres si no se ejecuta la misma bateria de pruebas de contrato sobre ambos.
3. Riesgo de acoplar bootstrap a detalles de PostgreSQL si no se aisla correctamente la construccion de conexion en un modulo dedicado.
4. Riesgo de bloquear la suite de CI si las pruebas de integracion no estan claramente separadas de las unitarias.

## 16. Criterios de aceptacion
1. El dominio no depende de PostgreSQL.
2. La aplicacion utiliza el puerto RepositorioSolicitudesPartner.
3. PostgreSQL implementa dicho puerto mediante un adaptador (RepositorioSolicitudesPartnerPostgres).
4. SolicitudPartner puede persistirse y recuperarse correctamente vía dicho adaptador.
5. La restriccion partner_id + referencia_externa existe en la base de datos.
6. Los tests unitarios existentes siguen pasando sin requerir PostgreSQL.
7. Existen pruebas de integracion minimas que validan el adaptador PostgreSQL.
8. El bootstrap puede utilizar PostgreSQL cuando corresponda, sin romper el bootstrap usado en pruebas.
9. No se incorporan Outbox, CQRS, brokers ni Event Sourcing en este bloque.
10. No se altera el flujo de eventos ya aprobado en el Bloque 2.3.

## 17. Estrategia de implementacion por pasos (para cuando se apruebe)
1. Confirmar decisiones pendientes (ver seccion de Dudas).
2. Agregar dependencia de acceso a PostgreSQL en pyproject.toml.
3. Crear modulo de conexion basado en variables de entorno.
4. Crear script/definicion de tabla solicitudes_partner con restriccion UNIQUE.
5. Implementar RepositorioSolicitudesPartnerPostgres cumpliendo el contrato del puerto.
6. Traducir errores tecnicos relevantes (por ejemplo, violacion UNIQUE) a excepciones de dominio ya existentes, donde aplique.
7. Ajustar bootstrap para permitir seleccion de implementacion (memoria o PostgreSQL) sin romper el bootstrap actual usado por tests.
8. Documentar en README variables de entorno y forma de levantar PostgreSQL local.
9. Escribir pruebas de integracion minimas, condicionadas a disponibilidad de PostgreSQL.
10. Ejecutar validaciones (ver seccion de comandos).

## 18. Comandos de validacion que posteriormente deberia ejecutar el agente
1. python -m pytest -q
   - Debe seguir mostrando el total de pruebas unitarias actuales en verde.
2. Comando para levantar PostgreSQL local (a definir exactamente con el usuario; por ejemplo, un contenedor con imagen oficial de PostgreSQL) antes de correr integracion.
3. Comando especifico para ejecutar solo pruebas de integracion (por ejemplo, seleccionando la carpeta tests/integration o un marcador de pytest dedicado).
4. Verificacion manual o automatizada de que la restriccion UNIQUE en partner_id + referencia_externa existe en la base de datos (por ejemplo, consultando el catalogo de restricciones de PostgreSQL).

## 19. Relacion con los atributos de calidad de la Entrega 2/Entrega 3
1. Mantenibilidad:
   - Persistencia real y explicita en un adaptador aislado facilita cambios futuros sin tocar dominio ni aplicacion.
   - Mantener el repositorio en memoria para pruebas preserva velocidad y simplicidad de feedback durante desarrollo.
2. Escalabilidad:
   - Usar PostgreSQL real es la base necesaria para futuros escenarios de mayor volumen de solicitudes, sin comprometerse todavia con patrones adicionales (Outbox, CQRS) que se evaluaran en bloques futuros.
3. Resiliencia:
   - Reforzar la restriccion de unicidad a nivel de base de datos reduce el riesgo de inconsistencias ante escrituras concurrentes, complementando la validacion ya existente en aplicacion/dominio.

No se inventan nuevos escenarios de calidad ni metricas; se referencian unicamente los atributos ya trabajados en Entrega 2 (Mantenibilidad, Escalabilidad, Resiliencia) como justificacion cualitativa de esta decision.

## 20. Dudas y decisiones que requieren aprobacion antes de implementar
1. Libreria de acceso a PostgreSQL: se propone usar un driver directo (por ejemplo, psycopg) en lugar de un ORM, para mantener el bloque minimo. ¿Se aprueba esta eleccion o prefieren usar SQLAlchemy u otra libreria especifica?
2. Manejo del esquema de base de datos: ¿se aprueba un script SQL simple ejecutado manualmente/una vez, o se requiere una herramienta de migraciones (por ejemplo, Alembic)? El plan por defecto propone un script SQL simple para mantener el alcance minimo.
3. Estrategia para pruebas de integracion: ¿deben ejecutarse automaticamente en CI si hay PostgreSQL disponible, o unicamente de forma manual/local por ahora?
4. Alcance de "levantar PostgreSQL localmente": ¿se autoriza incluir un docker-compose minimo solo para desarrollo/pruebas (no productivo), o se prefiere que el usuario administre su propia instancia de PostgreSQL sin que el agente proponga Docker en absoluto?
5. Nombre y ubicacion exacta de las variables de entorno (por ejemplo, prefijo especifico como HOGAR_DB_* en lugar de DB_*) si el proyecto ya tiene una convencion definida en otro lugar no revisado.
6. Confirmar si el timestamp/fecha de auditoria (creacion/actualizacion) debe agregarse a la tabla en este bloque o se deja fuera de alcance por ahora, dado que el enunciado solo pide los 5 campos minimos listados.

---

## Resumen del plan generado
Se genero el documento docs/ai/09-plan-bloque-2.4.md con el plan completo para incorporar persistencia real con PostgreSQL para el Aggregate Root SolicitudPartner, manteniendo el puerto de dominio sin cambios, agregando un adaptador concreto en infraestructura, definiendo la tabla solicitudes_partner con restriccion UNIQUE (partner_id, referencia_externa), preservando el repositorio en memoria para tests unitarios, y dejando fuera de alcance Outbox, CQRS, brokers, Event Sourcing, Docker complejo, Saga y cambios al flujo de eventos del Bloque 2.3.

## Archivos que se proponen crear/modificar
Crear:
- src/solicitudes_partner/infraestructura/repositorio_postgres.py
- src/solicitudes_partner/infraestructura/db_conexion.py
- definicion de esquema SQL para la tabla solicitudes_partner (archivo a nombrar segun decision de migraciones vs script simple)
- tests/integration/solicitudes_partner/test_repositorio_postgres.py
- .env.example

Modificar:
- src/solicitudes_partner/config/bootstrap.py
- pyproject.toml
- README.md

## Lista explicita de cosas que NO se van a implementar en este bloque
- Transactional Outbox
- Kafka
- RabbitMQ
- CQRS
- Read Model persistente
- Event Sourcing
- Docker complejo/orquestacion productiva
- nuevos microservicios
- Saga
- funcionalidades adicionales de negocio
- cambios en reglas o invariantes del dominio
- cambios en el flujo de eventos aprobado en Bloque 2.3
- reemplazo de EventBusMemoria

## Dudas/decisiones que necesitan aprobacion antes de implementar
1. Uso de driver directo (por ejemplo psycopg) vs ORM (por ejemplo SQLAlchemy).
2. Script SQL simple vs herramienta de migraciones (por ejemplo Alembic).
3. Ejecucion de pruebas de integracion: solo local/manual vs integrada en CI.
4. Autorizacion o no de un docker-compose minimo solo para desarrollo/pruebas de PostgreSQL.
5. Convencion de nombres de variables de entorno para la conexion a PostgreSQL.
6. Si se agregan o no columnas de auditoria (fecha creacion/actualizacion) ademas de los 5 campos minimos solicitados.
