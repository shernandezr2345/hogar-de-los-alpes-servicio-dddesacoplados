# Plan Bloque 2.3 - Flujo completo de eventos entre modulos

## Estado
Plan propuesto para implementacion del Bloque 2.3.

## Objetivo
Completar el flujo in-process de eventos del servicio Entrada de Solicitudes de Partner, asegurando comunicacion desacoplada por Domain Events entre:
- Captura de Solicitudes
- Reglas de Partner
- Seguimiento de Solicitudes

## Estado base despues del Bloque 2.2
Ya existe en el proyecto:
1. Aggregate Root SolicitudPartner.
2. Eventos de dominio:
   - SolicitudPartnerRegistrada
   - ReglasDePartnerEvaluadas
   - SolicitudPartnerListaParaAtencion
   - SolicitudPartnerRechazada
3. Puerto de Event Bus en aplicacion.
4. Implementacion EventBusMemoria en infraestructura.
5. Handler de Reglas de Partner que consume SolicitudPartnerRegistrada.
6. Seguimiento como consumidor de eventos.

## Alcance del Bloque 2.3
Incluye:
- Completar la reaccion a ReglasDePartnerEvaluadas para derivar el resultado final.
- Modelar el tramo ReglasDePartnerEvaluadas -> ListaParaAtencion o Rechazada usando eventos.
- Mantener responsabilidades claras entre modulos.
- Mantener seguimiento in-memory del flujo completo.
- Agregar pruebas del flujo completo exitoso y rechazado.

No incluye:
- PostgreSQL
- Outbox
- RabbitMQ/Kafka
- CQRS
- Read Model persistente
- Event Sourcing
- Docker
- nuevos microservicios
- funcionalidades fuera del flujo de eventos

## Flujo objetivo del Bloque 2.3
RegistrarSolicitudPartner
-> Captura
-> SolicitudPartnerRegistrada
-> EventBus
-> Handler Reglas de Partner
-> evaluacion
-> ReglasDePartnerEvaluadas
-> EventBus
-> decision
  - CUMPLE -> SolicitudPartnerListaParaAtencion
  - NO_CUMPLE -> SolicitudPartnerRechazada
-> EventBus
-> Seguimiento

## Decision de diseno clave
Para respetar DDD y las invariantes del agregado:
1. El modulo Reglas no modifica atributos internos del agregado de forma directa.
2. La transicion de estado del agregado se realiza invocando comportamiento del agregado.
3. La reaccion a ReglasDePartnerEvaluadas se implementa mediante un handler de aplicacion dedicado al resultado de reglas.
4. Ese handler debe recuperar la solicitud por repositorio, ejecutar el metodo de dominio correspondiente y publicar los nuevos eventos pendientes.

## Responsabilidades por modulo
### Captura de Solicitudes
- Ejecuta el comando.
- Crea solicitud usando el Aggregate Root.
- Persiste solicitud.
- Publica eventos pendientes del agregado.
- No conoce Reglas ni Seguimiento.

### Reglas de Partner
- Consume SolicitudPartnerRegistrada.
- Evalua reglas.
- Publica ReglasDePartnerEvaluadas.
- No invoca directamente Seguimiento ni modifica estado interno fuera del agregado.

### Resultado de Reglas (nuevo comportamiento en aplicacion)
- Consume ReglasDePartnerEvaluadas.
- Carga la solicitud desde repositorio.
- Si fue_aprobada, ejecuta marcar_lista_para_atencion().
- Si no fue_aprobada, ejecuta rechazar().
- Persiste cambios.
- Publica eventos del agregado: SolicitudPartnerListaParaAtencion o SolicitudPartnerRechazada.

### Seguimiento de Solicitudes
- Consume eventos relevantes:
  - SolicitudPartnerRegistrada
  - ReglasDePartnerEvaluadas
  - SolicitudPartnerListaParaAtencion
  - SolicitudPartnerRechazada
- Mantiene estado in-memory minimo para demostrar el recorrido.

## Archivos a crear (propuestos)
1. src/solicitudes_partner/aplicacion/modulos/resultado_reglas.py
- Handler para ReglasDePartnerEvaluadas y aplicacion del resultado sobre el agregado.

2. tests/unit/solicitudes_partner/aplicacion/test_eventos_flujo_completo.py
- Pruebas de flujo completo exitoso y rechazado.

## Archivos a modificar (propuestos)
1. src/solicitudes_partner/config/bootstrap.py
- Registrar handler de resultado de reglas en el Event Bus.
- Asegurar suscripciones de seguimiento para todo el ciclo.

2. src/solicitudes_partner/aplicacion/modulos/reglas_partner.py
- Ajuste minimo para permitir dos escenarios de evaluacion en pruebas (cumple/no cumple) sin romper alcance.

3. src/solicitudes_partner/aplicacion/modulos/seguimiento.py
- Ajuste minimo para exponer estado in-memory verificable del flujo final.

## Dependencias entre capas
- Dominio:
  - Define comportamiento del agregado y eventos.
  - No conoce EventBusMemoria.
- Aplicacion:
  - Depende de puertos (EventBus y repositorio).
  - Contiene handlers y orquestacion del flujo.
- Infraestructura:
  - Implementa EventBusMemoria y repositorio memoria.
- Config:
  - Cablea suscripciones y componentes.

## Criterios de arquitectura a validar
1. No hay llamadas directas Captura -> Reglas para continuar el flujo.
2. No hay llamadas directas Reglas -> Seguimiento para continuar el flujo.
3. La continuidad del proceso ocurre por publicacion y suscripcion de eventos.
4. ReglasDePartnerEvaluadas es producido por Reglas de Partner, no por el agregado.
5. SolicitudPartnerListaParaAtencion y SolicitudPartnerRechazada salen del agregado tras aplicar resultado.

## Estrategia de pruebas
### Pruebas de flujo completo
1. Flujo exitoso:
- RegistrarSolicitudPartner -> Registrada -> Evaluacion aprobada -> ListaParaAtencion -> Seguimiento.

2. Flujo rechazado:
- RegistrarSolicitudPartner -> Registrada -> Evaluacion no aprobada -> Rechazada -> Seguimiento.

### Pruebas de desacople
3. Verificar ausencia de llamadas directas entre modulos para continuidad del flujo.
4. Verificar que seguimiento recibe eventos del ciclo completo por Event Bus.

### Regresion
5. Mantener en verde todas las pruebas existentes de Fase 1 y Bloques 2.1 y 2.2.

## Riesgos y mitigacion
1. Riesgo: acoplar evaluacion y transicion en el mismo handler sin pasar por agregado.
- Mitigacion: aplicar transiciones solo mediante metodos del agregado.

2. Riesgo: perder trazabilidad de eventos finales.
- Mitigacion: seguimiento suscrito a todos los eventos clave.

3. Riesgo: extender alcance con infraestructura externa.
- Mitigacion: limitar implementacion a in-memory/in-process.

## Definition of Done - Bloque 2.3
1. ReglasDePartnerEvaluadas dispara el resultado final por handlers via Event Bus.
2. El agregado cambia estado mediante su propio comportamiento y emite eventos finales.
3. Seguimiento recibe eventos del flujo completo en memoria.
4. No existen llamadas directas entre modulos para continuar el proceso.
5. No se implementa nada fuera del alcance del bloque.
6. Suite completa de pruebas en verde.
