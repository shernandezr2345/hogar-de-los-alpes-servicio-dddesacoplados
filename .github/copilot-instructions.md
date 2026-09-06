# Instrucciones del proyecto

Este proyecto corresponde a la Entrega 3 del curso
Diseño y Construcción de Aplicaciones No Monolíticas.

## Objetivo

Implementar uno de los servicios de la arquitectura de
Hogar de los Alpes siguiendo:

- Domain-Driven Design
- Arquitectura Hexagonal
- Domain Model
- Aggregates
- Entities
- Value Objects
- Command
- Query
- Domain Events
- Persistencia mediante PostgreSQL

## Restricciones

- No implementar funcionalidades innecesarias.
- El servicio debe ser pequeño y demostrable.
- Debe utilizar una base de datos real PostgreSQL.
- Debe existir al menos un Command.
- Debe existir al menos un Query.
- Deben existir eventos relacionados con la transacción.
- La comunicación entre módulos debe realizarse mediante eventos de dominio.
- Mantener separación entre dominio, aplicación e infraestructura.
- Aplicar inversión de dependencias.
- No introducir patrones que no sean necesarios.

## Referencia académica

El repositorio:

tutorial-3-arquitectura-hexagonal

es la referencia principal para la implementación
de Arquitectura Hexagonal y DDD.

No copiar literalmente el dominio del tutorial.
Adaptar los conceptos al dominio de Hogar de los Alpes.