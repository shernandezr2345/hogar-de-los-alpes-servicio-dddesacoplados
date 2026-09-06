# Plan Bloque 2.2 - Event Bus + Handlers

## Estado
Plan aprobado para implementacion del Bloque 2.2.

## Objetivo
Implementar un Event Bus in-process/in-memory para desacoplar la comunicacion entre modulos internos del servicio:
- Captura de Solicitudes
- Reglas de Partner
- Seguimiento de Solicitudes

Este bloque cubre solamente bus y handlers internos, sin infraestructura externa.

## Alcance del Bloque 2.2
Incluye:
- Puerto/abstraccion de Event Bus en aplicacion.
- Implementacion concreta EventBusMemoria en infraestructura.
- Registro de handlers por tipo de evento.
- Publicacion de eventos y despacho a todos los handlers suscritos.
- Handler de Reglas de Partner para reaccionar a SolicitudPartnerRegistrada.
- Capacidad de Seguimiento para consumir eventos sin llamadas directas.
- Ajustes de wiring en composition root.
- Pruebas unitarias del bus y del flujo in-process.

No incluye:
- PostgreSQL
- Transactional Outbox
- RabbitMQ/Kafka
- CQRS
- Read Model
- Event Sourcing
- Docker
- nuevos microservicios
- Bloque 2.3

## Estado base antes del bloque
1. Bloque 2.1 implementado con eventos de dominio en el agregado.
2. Eventos disponibles:
   - SolicitudPartnerRegistrada
   - ReglasDePartnerEvaluadas
   - SolicitudPartnerListaParaAtencion
   - SolicitudPartnerRechazada
3. Aggregate Root emite solo eventos propios de su responsabilidad:
   - creacion -> SolicitudPartnerRegistrada
   - cambio a LISTA_PARA_ATENCION -> SolicitudPartnerListaParaAtencion
   - cambio a RECHAZADA -> SolicitudPartnerRechazada

## Flujo objetivo del Bloque 2.2
RegistrarSolicitudPartner
-> Captura de Solicitudes
-> SolicitudPartnerRegistrada
-> Event Bus
-> Handler Reglas de Partner
-> evaluacion
-> ReglasDePartnerEvaluadas

El flujo queda preparado para que eventos posteriores sean consumidos por los modulos correspondientes sin acoplamiento directo.

## Archivos a crear
1. src/solicitudes_partner/aplicacion/puertos_eventos.py
- Responsabilidad: definir contrato del bus (suscribir y publicar).
- Capa: aplicacion.

2. src/solicitudes_partner/infraestructura/event_bus_memoria.py
- Responsabilidad: implementar bus en memoria con registro por tipo y dispatch.
- Capa: infraestructura.

3. src/solicitudes_partner/aplicacion/modulos/captura.py
- Responsabilidad: orquestar captura y publicar eventos pendientes del agregado.
- Capa: aplicacion.

4. src/solicitudes_partner/aplicacion/modulos/reglas_partner.py
- Responsabilidad: handler que consume SolicitudPartnerRegistrada y publica ReglasDePartnerEvaluadas.
- Capa: aplicacion.

5. src/solicitudes_partner/aplicacion/modulos/seguimiento.py
- Responsabilidad: consumidores para observabilidad/tracking in-memory del flujo.
- Capa: aplicacion.

6. tests/unit/solicitudes_partner/infraestructura/test_event_bus_memoria.py
- Responsabilidad: validar comportamiento del bus.

7. tests/unit/solicitudes_partner/aplicacion/test_eventos_flujo.py
- Responsabilidad: validar flujo desacoplado Captura -> Bus -> Reglas.

## Archivos a modificar
1. src/solicitudes_partner/aplicacion/servicios.py
- Ajuste: usar puerto de eventos y delegar en logica de Captura para publicar eventos.
- Restriccion: no introducir llamadas directas de Captura a Reglas para continuar el flujo.

2. src/solicitudes_partner/config/bootstrap.py
- Ajuste: instanciar EventBusMemoria, registrar handlers y cablear dependencias.

## Responsabilidades por modulo
### Captura de Solicitudes
- Ejecuta command RegistrarSolicitudPartner.
- Persiste solicitud.
- Publica eventos pendientes del agregado.
- No llama ni importa logica de Reglas para continuar el flujo.

### Reglas de Partner
- Se suscribe a SolicitudPartnerRegistrada.
- Evalua reglas.
- Publica ReglasDePartnerEvaluadas.

### Seguimiento de Solicitudes
- Se suscribe a eventos relevantes.
- Reacciona sin ser invocado directamente por Captura o Reglas.

## Dependencias entre capas
- Dominio: define eventos y agregado; no conoce EventBusMemoria.
- Aplicacion: depende del puerto de eventos, no de la implementacion concreta.
- Infraestructura: implementa EventBusMemoria.
- Config: conecta implementaciones y suscripciones.

## Requisitos de arquitectura
1. No importar EventBusMemoria desde dominio.
2. No acoplar Captura con servicios de Reglas mediante llamadas directas para continuar flujo.
3. Permitir multiples handlers por tipo de evento.
4. Mantener lenguaje ubicuo en tipos de evento y handlers.

## Estrategia de pruebas
### Pruebas del bus
1. Un handler puede suscribirse a un tipo de evento.
2. Publicar evento ejecuta handler correspondiente.
3. Multiples handlers reciben el mismo evento.

### Pruebas de flujo
4. SolicitudPartnerRegistrada llega al handler de Reglas mediante Event Bus.
5. No existe llamada directa Captura -> Reglas para continuar el flujo.
6. Pruebas de Fase 1 y Bloque 2.1 continúan pasando.

## Riesgos y mitigacion
1. Riesgo: pseudo-desacople (eventos pero con llamada directa escondida).
- Mitigacion: pruebas explicitas del encadenamiento via bus.

2. Riesgo: contaminar dominio con detalles de despacho.
- Mitigacion: bus solo en aplicacion/infraestructura.

3. Riesgo: sobreingenieria prematura.
- Mitigacion: bus minimo en memoria, sin semantica distribuida.

## Definition of Done (Bloque 2.2)
1. Existe puerto de Event Bus en aplicacion.
2. Existe EventBusMemoria en infraestructura.
3. Hay suscripcion y publicacion funcional por tipo de evento.
4. Handler de Reglas consume SolicitudPartnerRegistrada via bus.
5. Captura no invoca directamente Reglas para continuar el flujo.
6. Seguimiento puede registrarse como consumidor desacoplado.
7. No se implementa nada fuera de alcance.
8. Suite de pruebas completa en verde.
