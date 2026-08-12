# ADR-002: CQRS + MediatR en la capa Application

**Estado:** Aceptado

## Contexto
El sistema orquesta múltiples pasos (generar spec → implementar → revisar → abrir PR) con distintos casos de uso que conviene desacoplar de los controllers.

## Decisión
Application usa CQRS con MediatR: cada caso de uso es un Command o Query con su Handler.

## Alternativas consideradas
Servicios de aplicación tradicionales (application services) inyectados directo en los controllers — descartado porque MediatR permite agregar pipeline behaviors (logging, validación) sin tocar cada handler, y mantiene los controllers delgados por regla del proyecto.

## Consecuencias
Indirección adicional para seguir el flujo de un caso de uso (hay que buscar el Handler), a cambio de controllers sin lógica de negocio y pipeline transversal reutilizable.
