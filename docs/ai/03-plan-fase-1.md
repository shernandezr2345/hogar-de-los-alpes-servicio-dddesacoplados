# Plan Fase 1 - Arquitectura Hexagonal + DDD

## Estado
Aprobado y documentado para ejecucion incremental.

## Objetivo de la fase
Construir la base del servicio Entrada de Solicitudes de Partner con DDD tactico y arquitectura hexagonal, sin introducir complejidad de mensajeria ni persistencia productiva.

## Alcance de Fase 1
Incluye:
- Estructura minima de carpetas por capas.
- Capa de dominio completa para SolicitudPartner.
- Aggregate Root unico: SolicitudPartner.
- Value Objects minimos.
- Reglas de negocio del agregado.
- Puertos/interfaces para persistencia.
- Capa de aplicacion para command y query minimos.
- Adaptador temporal de repositorio en memoria.
- Pruebas unitarias del dominio.

No incluye:
- Eventos de dominio.
- CQRS.
- Read Model.
- Outbox.
- Broker.
- Docker.
- PostgreSQL.
- Event Sourcing.

## Lineamientos funcionales obligatorios
1. Estados oficiales del agregado:
   - RECIBIDA
   - LISTA_PARA_ATENCION
   - RECHAZADA
2. Duplicidad por PartnerId + ReferenciaExterna:
   - El agregado protege sus invariantes.
   - El servicio de aplicacion consulta existencia previa por puerto de repositorio.
   - La restriccion UNIQUE en base de datos se difiere a fase PostgreSQL.
3. Repositorio en memoria:
   - Es temporal para desarrollo y pruebas.
   - Se reemplaza en fase posterior sin alterar dominio.

## Modelo minimo de dominio
### Aggregate Root
- SolicitudPartner.

### Entidades
- SolicitudPartner.

### Value Objects
- SolicitudId
- PartnerId
- ReferenciaExterna
- TipoServicio
- EstadoSolicitud

### Reglas de negocio minimas
1. Toda solicitud nueva inicia en RECIBIDA.
2. No se permite crear solicitud duplicada por PartnerId + ReferenciaExterna.
3. Transiciones validas:
   - RECIBIDA -> LISTA_PARA_ATENCION
   - RECIBIDA -> RECHAZADA
4. Transiciones no validas:
   - LISTA_PARA_ATENCION -> cualquier otro estado
   - RECHAZADA -> cualquier otro estado

## Casos de uso minimos de Fase 1
### Command
- RegistrarSolicitudPartner.

### Query
- ConsultarEstadoSolicitudPartner.

## Plan de trabajo (orden recomendado)
1. Crear estructura de carpetas por capas.
2. Implementar excepciones de dominio.
3. Implementar Value Objects y estado oficial.
4. Implementar Aggregate Root y reglas internas.
5. Definir puerto de repositorio en dominio.
6. Implementar servicio de aplicacion con validacion de duplicidad via puerto.
7. Implementar adaptador temporal de repositorio en memoria.
8. Implementar composition root minimo.
9. Implementar pruebas unitarias de dominio.
10. Ejecutar pruebas y registrar evidencia.

## Entregables de la fase
1. Dominio aislado de infraestructura.
2. Aplicacion orquestando casos de uso minimos.
3. Infraestructura temporal en memoria.
4. Suite de pruebas unitarias del dominio en verde.
5. Documentacion del blueprint y del plan de fase.

## Criterios de aceptacion
1. Existe un solo Aggregate Root: SolicitudPartner.
2. Se usan exactamente los estados aprobados.
3. No hay implementacion de eventos ni outbox.
4. No hay implementacion de CQRS/read model.
5. No hay dependencia de PostgreSQL.
6. El dominio no depende de frameworks.
7. Las pruebas unitarias del dominio pasan al 100 por ciento.

## Estrategia de pruebas en la fase
Pruebas unitarias enfocadas a dominio:
- Validacion de Value Objects.
- Estado inicial del agregado.
- Reglas de transicion de estado.
- Rechazo de duplicidad en creacion cuando existe_previa es verdadero.

## Riesgos y controles
1. Riesgo: contaminar dominio con detalles tecnicos.
   - Control: puertos en dominio y adaptadores en infraestructura.
2. Riesgo: ampliar alcance con patrones de fases futuras.
   - Control: checklist de no incluye y revision de alcance antes de merge.
3. Riesgo: inconsistencia de lenguaje de estados.
   - Control: pruebas especificas para estados oficiales.

## Trazabilidad arquitectonica
### Relacion con Entrega 2
- Conserva lenguaje ubicuo del flujo de solicitudes de partner.
- Mantiene consistencia con LISTA_PARA_ATENCION.
- Deja preparada la evolucion hacia outbox y backbone en fases siguientes.

### Relacion con Tutorial 3 de Arquitectura Hexagonal
- Separa dominio, aplicacion e infraestructura.
- Dominio define contratos, infraestructura implementa adaptadores.
- Servicio de aplicacion coordina casos de uso.
- Composition root centraliza el ensamblaje.

## Definicion de terminado (DoD) de Fase 1
1. Estructura de carpetas creada.
2. Dominio implementado con Aggregate Root y Value Objects minimos.
3. Casos de uso minimos de aplicacion implementados.
4. Repositorio en memoria funcionando para pruebas.
5. Pruebas unitarias del dominio ejecutadas y en verde.
6. Sin implementaciones de fases posteriores.
