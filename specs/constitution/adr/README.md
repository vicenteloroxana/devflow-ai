# Architecture Decision Records (ADR)

Registro histórico de decisiones de arquitectura del proyecto: qué se decidió, por qué, qué alternativas se descartaron y qué consecuencias se aceptaron.

**Regla:** un ADR aceptado no se edita. Si una decisión cambia, se crea un ADR nuevo que la supera (`Estado: Superseded by ADR-00N`) y el original se marca como superado. Esto preserva el porqué de cada decisión en el momento en que se tomó.

Para reglas *vigentes* del proyecto (no históricas), ver [`../workflow.md`](../workflow.md) y el [`CLAUDE.md`](../../../CLAUDE.md) en la raíz.

## Índice

| ADR | Título | Estado |
|---|---|---|
| [001](001-clean-architecture.md) | Clean Architecture: Domain aislado de Infrastructure | Aceptado |
| [002](002-cqrs-mediatr.md) | CQRS + MediatR en Application | Aceptado |
| [003](003-groq-dev-anthropic-demo.md) | Groq (dev) vs Anthropic (demo) como proveedores LLM | Aceptado |
| [004](004-pgvector-misma-instancia.md) | pgvector sobre la misma instancia PostgreSQL | Aceptado |
| [005](005-proceso-sdd-obligatorio.md) | Proceso SDD obligatorio antes de código de producción | Aceptado |
