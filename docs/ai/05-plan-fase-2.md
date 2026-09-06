# Plan Fase 2 - Domain Events In-Process

## Estado
Plan propuesto para implementacion incremental.

## Objetivo de la fase
Implementar comunicacion interna exclusivamente mediante eventos de dominio entre los modulos del servicio:
- Captura de Solicitudes
- Reglas de Partner
- Seguimiento de Solicitudes

Sin introducir infraestructura externa ni patrones fuera de alcance.

## Alcance de Fase 2
Incluye:
- Definicion de eventos de dominio como hechos de negocio.
- Mecanismo in-process/in-memory para publicar y suscribir eventos.
- Handlers por modulo interno para reaccionar a eventos.
- Integracion de eventos en el flujo de aplicacion existente.
- Pruebas unitarias del flujo por eventos.

No incluye:
- PostgreSQL.
- Transactional Outbox.
- RabbitMQ/Kafka u otro broker.
- CQRS.
- Read Model.
- Event Sourcing.
- Docker.

## Eventos de dominio de Fase 2
Eventos principales:
1. SolicitudPartnerRegistrada
2. ReglasDePartnerEvaluadas
3. SolicitudPartnerListaParaAtencion
4. SolicitudPartnerRechazada

### Semantica de negocio
- SolicitudPartnerRegistrada: se confirma que la solicitud fue creada en estado RECIBIDA.
- ReglasDePartnerEvaluadas: se evaluaron reglas para la solicitud y existe resultado.
- SolicitudPartnerListaParaAtencion: la solicitud cumple reglas y pasa a LISTA_PARA_ATENCION.
- SolicitudPartnerRechazada: la solicitud no cumple reglas y pasa a RECHAZADA.

## Reglas de diseno para eventos
1. Los eventos representan hechos ya ocurridos, no intenciones.
2. Los nombres usan lenguaje ubicuo del dominio.
3. Los payloads contienen identificadores y datos minimos necesarios.
4. No acoplar eventos a formatos de broker o infraestructura externa.

## Arquitectura objetivo en Fase 2
### Dominio
- Define tipos de eventos de dominio.
- El agregado SolicitudPartner produce eventos cuando cambian hechos de negocio.

### Aplicacion
- Publica eventos del agregado.
- Registra y ejecuta handlers por modulo interno.
- El flujo entre modulos debe ocurrir por eventos, no por invocaciones directas.

### Infraestructura
- Implementa Event Bus en memoria (in-process).
- Gestiona suscripciones y despacho sin dependencias externas.

## Flujo funcional objetivo
1. Captura de Solicitudes procesa RegistrarSolicitudPartner.
2. Se crea SolicitudPartner en estado RECIBIDA.
3. Se publica SolicitudPartnerRegistrada.
4. Reglas de Partner consume SolicitudPartnerRegistrada y evalua reglas.
5. Reglas de Partner publica ReglasDePartnerEvaluadas.
6. Si resultado es positivo, publica SolicitudPartnerListaParaAtencion.
7. Si resultado es negativo, publica SolicitudPartnerRechazada.
8. Seguimiento de Solicitudes consume eventos para mantener estado interno de seguimiento en memoria.

## Cambios propuestos por capa
### Dominio
- Agregar modulo de eventos de dominio.
- Extender el agregado para registrar eventos pendientes de publicacion.
- Mantener invariantes y estados existentes sin alterarlos.

### Aplicacion
- Separar handlers por modulo interno:
  - captura
  - reglas_partner
  - seguimiento
- Adaptar servicio de aplicacion para publicar eventos y no llamar modulos internos directamente.

### Infraestructura
- Crear EventBusMemoria con:
  - suscripcion por tipo de evento
  - publicacion de evento
  - despacho a multiples handlers

### Configuracion
- Actualizar composition root para:
  - crear bus en memoria
  - registrar handlers
  - inyectar dependencias

## Estructura de archivos sugerida
- src/solicitudes_partner/dominio/eventos.py
- src/solicitudes_partner/aplicacion/puertos_eventos.py
- src/solicitudes_partner/aplicacion/modulos/captura.py
- src/solicitudes_partner/aplicacion/modulos/reglas_partner.py
- src/solicitudes_partner/aplicacion/modulos/seguimiento.py
- src/solicitudes_partner/infraestructura/event_bus_memoria.py
- src/solicitudes_partner/config/bootstrap.py (ajuste de wiring)
- tests/unit/solicitudes_partner/aplicacion/test_eventos_flujo.py

## Criterios de aceptacion
1. Existen los cuatro eventos definidos para la fase.
2. Captura, Reglas y Seguimiento se comunican exclusivamente por eventos.
3. No hay invocaciones directas entre modulos internos para continuar el flujo.
4. No se introduce infraestructura externa.
5. Pruebas de Fase 1 siguen pasando.
6. Nuevas pruebas de flujo por eventos pasan.

## Estrategia de pruebas
Pruebas minimas a implementar:
1. Registrar solicitud publica SolicitudPartnerRegistrada.
2. SolicitudPartnerRegistrada dispara evaluacion de reglas.
3. Evaluacion positiva publica SolicitudPartnerListaParaAtencion.
4. Evaluacion negativa publica SolicitudPartnerRechazada.
5. Seguimiento recibe eventos y actualiza estado en memoria.
6. No regresion de pruebas de dominio de Fase 1.

## Riesgos y mitigaciones
1. Riesgo: simular eventos pero mantener acoplamiento directo.
   - Mitigacion: validar en pruebas que continuidad del flujo ocurre por handlers suscritos al bus.
2. Riesgo: sobreingenieria prematura.
   - Mitigacion: bus en memoria minimalista, sin outbox ni broker en esta fase.
3. Riesgo: contaminar dominio con detalles tecnicos.
   - Mitigacion: eventos como tipos de dominio; bus concreto en infraestructura.

## Trazabilidad
### Con Entrega 2
- Alinea la comunicacion asincorna por eventos entre capacidades.
- Conserva lenguaje ubicuo y hechos de negocio del flujo de solicitudes.

### Con Tutorial 3
- Mantiene capas y puertos/adaptadores.
- Reafirma inversion de dependencias: dominio define, infraestructura implementa.

### Con Blueprint Entrega 3
- Implementa exactamente los eventos definidos para evolucion incremental.
- Respeta el alcance minimo antes de introducir outbox, broker y persistencia productiva.

## Definition of Done (Fase 2)
1. Flujo interno de modulos operando por eventos in-process.
2. Cuatro eventos de negocio implementados y usados.
3. Sin CQRS, sin read model, sin outbox, sin broker, sin PostgreSQL.
4. Suite de pruebas completa en verde (Fase 1 + Fase 2).
