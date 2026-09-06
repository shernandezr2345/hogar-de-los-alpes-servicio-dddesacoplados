# Blueprint Entrega 3 - Servicio Entrada de Solicitudes de Partner

## Estado
Aprobado para implementacion incremental.

## Objetivo
Definir un blueprint minimo para la Entrega 3, alineado con:
- Arquitectura orientada a eventos, lenguaje ubicuo y limites de contexto
- Arquitectura Hexagonal + DDD tactico por capas.

## Alcance general de Entrega 3
Implementar un unico servicio desplegable: **Entrada de Solicitudes de Partner**.

## Decisiones clave
1. Aggregate Root unico: **SolicitudPartner**.
2. Estados oficiales del agregado:
   - RECIBIDA
   - LISTA_PARA_ATENCION
   - RECHAZADA
3. Regla de duplicidad:
   - El agregado protege sus invariantes.
   - El servicio de aplicacion verifica existencia previa consultando el repositorio por puerto.
   - En fase de PostgreSQL se agregara restriccion UNIQUE (partner_id, referencia_externa).
4. El repositorio en memoria es temporal para desarrollo y pruebas en FASE 1.
5. Sin Event Sourcing.
6. Sin sobreingenieria ni patrones innecesarios.

## Fase 1 (implementada)
Incluye unicamente:
- Estructura de carpetas por capas.
- Dominio.
- Aggregate Root SolicitudPartner.
- Value Objects minimos.
- Reglas de negocio del agregado.
- Puertos/interfaces.
- Separacion dominio/aplicacion/infraestructura.
- Pruebas unitarias del dominio.

No incluye:
- Eventos.
- CQRS.
- Read Model.
- Outbox.
- Broker.
- Docker.
- PostgreSQL.

## Modelo de dominio minimo
### Aggregate Root
- SolicitudPartner.

### Entidades
- SolicitudPartner (unica entidad necesaria para FASE 1).

### Value Objects
- SolicitudId
- PartnerId
- ReferenciaExterna
- TipoServicio
- EstadoSolicitud

### Reglas del agregado
1. Toda solicitud nueva inicia en estado RECIBIDA.
2. No se permite crear solicitud duplicada por PartnerId + ReferenciaExterna.
3. Transiciones validas:
   - RECIBIDA -> LISTA_PARA_ATENCION
   - RECIBIDA -> RECHAZADA
4. Transiciones invalidas (ejemplo):
   - RECHAZADA -> LISTA_PARA_ATENCION

## Casos de uso minimos
### Command
- RegistrarSolicitudPartner

### Query
- ConsultarEstadoSolicitudPartner

## Arquitectura por capas (hexagonal)
### Dominio
- Contiene reglas, estados, Value Objects, entidad raiz y puerto de repositorio.
- No depende de frameworks ni de detalles de persistencia.

### Aplicacion
- Orquesta casos de uso (command/query).
- Usa puertos del dominio para persistir/consultar.
- No contiene reglas de negocio nucleares del agregado.

### Infraestructura
- Implementa adaptadores tecnicos.
- En FASE 1 solo repositorio en memoria temporal.
- En fases posteriores reemplazo por PostgreSQL sin romper dominio.

## Estructura de archivos de referencia
- src/solicitudes_partner/dominio/
- src/solicitudes_partner/aplicacion/
- src/solicitudes_partner/infraestructura/
- src/solicitudes_partner/config/
- tests/unit/solicitudes_partner/dominio/

## Evidencia DDD en la solucion
1. Lenguaje ubicuo en nombres del dominio (SolicitudPartner, RECIBIDA, LISTA_PARA_ATENCION, RECHAZADA).
2. Invariantes dentro del agregado.
3. Value Objects con validaciones propias.
4. Puerto de repositorio definido en dominio.

## Evidencia Hexagonal en la solucion
1. Dependencias apuntan al dominio.
2. Repositorio definido como interfaz (puerto) y resuelto con adaptador en memoria.
3. Servicio de aplicacion como orquestador sin conocimiento de tecnologia concreta.
4. Composition root para conectar dependencias.

## Relacion con Entrega 2
- Se conserva el lenguaje y semantica del flujo de solicitudes de partner.
- Se mantiene consistencia con el estado LISTA_PARA_ATENCION.
- Se prepara la evolucion incremental hacia eventos y outbox en fases siguientes.

## Relacion con Tutorial 3
- Misma separacion por capas: API/Aplicacion/Dominio/Infraestructura.
- Mapeo de responsabilidades y puertos/adaptadores.
- Dominio aislado de persistencia y framework.

## Fases posteriores (solo referencia, no implementadas aqui)
1. FASE 2: eventos de dominio internos.
2. FASE 3: outbox transaccional y publicacion confiable.
3. FASE 4: adaptador PostgreSQL y restriccion UNIQUE.
4. FASE 5: evolucion de lectura para CQRS cuando sea necesario.
