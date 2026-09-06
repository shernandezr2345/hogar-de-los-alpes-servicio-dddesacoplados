# Revision Bloque 2.3

## Objetivo
Validar que el Bloque 2.3 completa el flujo in-process de eventos entre modulos del servicio Entrada de Solicitudes de Partner, manteniendo DDD y arquitectura hexagonal.

## Arquitectura implementada
Se implemento un flujo de eventos desacoplado en un unico servicio, con separacion por capas:
- Dominio: Aggregate Root, eventos de dominio e invariantes.
- Aplicacion: orquestacion de casos de uso y handlers por modulo.
- Infraestructura: EventBusMemoria y repositorio en memoria.
- Configuracion: wiring de suscripciones y dependencias.

Componentes clave del bloque:
- Handler de Reglas de Partner produce ReglasDePartnerEvaluadas.
- Handler dedicado de Resultado de Reglas aplica la decision sobre el agregado.
- Seguimiento consume eventos del ciclo completo en memoria.

## Flujo de eventos
Flujo completo implementado:
1. RegistrarSolicitudPartner
2. Captura crea y persiste SolicitudPartner
3. Aggregate publica SolicitudPartnerRegistrada
4. EventBus despacha a Reglas de Partner
5. Reglas evalua y publica ReglasDePartnerEvaluadas
6. EventBus despacha a HandlerResultadoReglas
7. HandlerResultadoReglas recupera solicitud desde repositorio
8. HandlerResultadoReglas invoca en el agregado:
   - marcar_lista_para_atencion() si fue_aprobada=True
   - rechazar() si fue_aprobada=False
9. Se persiste la solicitud y se publican eventos finales:
   - SolicitudPartnerListaParaAtencion o
   - SolicitudPartnerRechazada
10. Seguimiento recibe eventos del ciclo completo.

## Desacoplamiento
Se verifico desacoplamiento entre modulos:
- Captura no invoca directamente Reglas ni Seguimiento para continuar flujo.
- Reglas no invoca directamente Seguimiento.
- La continuidad ocurre por publicacion/suscripcion en EventBus.
- El dominio no conoce EventBusMemoria.
- La aplicacion depende del puerto EventBus (inversion de dependencias).

## Pruebas
Ejecucion de suite completa:

python -m pytest -q

Resultado:

21 passed in 0.34s

Cobertura funcional validada por pruebas:
- Flujo completo aprobado.
- Flujo completo rechazado.
- Suscripcion/publicacion con multiples handlers.
- Encadenamiento por EventBus sin llamadas directas para continuidad.
- Regresion en verde para Fase 1, Bloque 2.1 y Bloque 2.2.

## Decisiones
1. ReglasDePartnerEvaluadas es emitido solo por el modulo Reglas de Partner.
2. El cambio de estado final se aplica sobre el agregado mediante metodos del dominio.
3. El resultado de reglas se procesa en un handler de aplicacion dedicado.
4. Seguimiento permanece minimo e in-memory para demostrar recepcion de eventos.
5. Se mantuvo una regla minima explicita para forzar escenarios aprobado/rechazado en pruebas.

## Alcance deliberadamente excluido
No implementado en este bloque:
- PostgreSQL
- Transactional Outbox
- RabbitMQ/Kafka
- CQRS
- Read Model persistente
- Event Sourcing
- Docker
- nuevos microservicios
- funcionalidades fuera del flujo de eventos

## Resultado
**APROBADO**
