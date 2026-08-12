# ADR-001: Clean Architecture con separación estricta Domain/Application/Infrastructure/API

**Estado:** Aceptado

## Contexto
DevFlowAI (solución .NET) necesita una estructura que permita evolucionar la lógica de negocio (specs, agentes, revisión de código) sin acoplarla a detalles de infraestructura (LLMs, base de datos, GitHub API), y que sea testeable de forma aislada.

## Decisión
Se adopta Clean Architecture con 4 proyectos: `DevFlowAI.Domain`, `DevFlowAI.Application`, `DevFlowAI.Infrastructure`, `DevFlowAI.API`. Regla dura: Domain no referencia Infrastructure ni `agents/`. Controllers no contienen lógica de negocio.

## Alternativas consideradas
Arquitectura en capas tradicional (N-tier) — descartada por acoplar Domain a detalles de persistencia/LLM demasiado pronto, dificultando tests unitarios puros.

## Consecuencias
Mayor boilerplate de mapeo entre capas, a cambio de Domain testeable sin mocks de infraestructura y de poder cambiar el proveedor LLM o la BD sin tocar reglas de negocio.
